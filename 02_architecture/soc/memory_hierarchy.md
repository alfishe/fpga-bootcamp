[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Memory Hierarchy — On-Die Memory Topology and Bandwidth Budgeting

How memory is organized across the CPU and FPGA domains, from cache hierarchies to shared DDR controllers, determines latency, bandwidth, and whether you need to worry about cache coherency at all. The memory path your data takes is the single most important architectural decision in an FPGA SoC design — get it wrong and no amount of RTL optimization will save your performance.

> [!NOTE]
> For AXI bridge bandwidth and interconnect topology, see [AXI Bridges & Interconnect](axi_bridges_and_interconnect.md). For cache coherency details (ACP, ACE, CCI), see [Multi-Core Coherency](../../11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md). For DDR calibration and bring-up, see [Debugging DDR](../../15_case_studies/debugging_ddr.md).

---

## The Memory Pyramid (FPGA SoC view)

```
Size:         KB ◄─────────────────────────────────► GB
Speed:  1 cycle ◄────────────────────────────────────► 100+ cycles

            L1 Cache                    On-Chip RAM
            32 KB I+D per core          64–256 KB
            ~1 cycle                    2–5 cycles
                │                           │
                └───────────┬───────────────┘
                            │
                        ┌───▼────┐
                        │L2 Cache │  On-Die
                        │0.5–2 MB │  10–20 cycles
                        └───┬─────┘
                            │
                ┌───────────┼───────────────┐
                │           │               │
            ┌───▼────┐ ┌───▼─────┐  ┌──────▼──────┐
            │DDR Ctrl│ │FPGA BRAM│  │  FPGA DDR   │  Off-Die/Soft
            │512MB–  │ │0.1–12 Mb│  │  (soft ctrl)│  50–300 cycles
            │32 GB   │ │(on-die) │  │             │
            └────────┘ └─────────┘  └─────────────┘
```

### Latency Budget by Memory Type

| Memory Type | Latency (typical) | Bandwidth | Use For |
|---|---|---|---|
| **L1 Cache** | 1 cycle (~1 ns @ 1 GHz) | ~64 GB/s per core | CPU instruction/data fetch |
| **L2 Cache** | 10–20 cycles (~10–20 ns) | ~32 GB/s shared | Hot data shared between CPU cores |
| **On-Chip RAM (OCM)** | 2–5 cycles | ~12 GB/s | Shared mailbox between CPU and FPGA |
| **FPGA BRAM** | 1–2 cycles (fabric clock) | ~38 Gbps per 36Kb block | FIFOs, line buffers, lookup tables |
| **FPGA URAM** | 1 cycle (UltraScale+) | ~72 Gbps per 288Kb block | Large FIFOs, deep buffers |
| **DDR3/DDR4 (hard ctrl)** | 50–100 cycles | 3.2–25.6 GB/s | Bulk data, frame buffers, Linux |
| **FPGA soft DDR ctrl** | 100–300 cycles | 1.6–12.8 GB/s | Custom memory interfaces |

---

## Per-Vendor Memory Topology

| Property | Cyclone V SoC | Zynq-7000 | Zynq MPSoC | PolarFire SoC |
|---|---|---|---|---|
| L1 I-Cache | 32 KB per core | 32 KB per core | 32 KB per core (A53) | 16 KB per core (U54) |
| L1 D-Cache | 32 KB per core | 32 KB per core | 32 KB per core (A53) | 16 KB per core (U54) |
| L2 Cache | 512 KB shared, ECC | 512 KB shared, shared via SCU | 1 MB shared (A53), 128 KB TCM (R5) | 2 MB shared |
| On-Chip RAM | 64 KB | 256 KB (OCM) | 256 KB (OCM) + 128 KB TCM | eNVM (boot) |
| Hard DDR Ctrl | DDR3/DDR3L/LPDDR2 | DDR3/DDR3L/LPDDR2 | DDR4/LPDDR4, ECC | DDR4/LPDDR4 |
| Max DDR | 4 GB | 1 GB (hard limit) | 32 GB | 16 GB |
| DDR bus width | 16/32 bit (HPS) | 16/32 bit (PS) | 32/64 bit (PS) | 32/64 bit |
| FPGA BRAM | M10K (10 Kb) | 36 Kb BRAM | 36 Kb BRAM + 288 Kb URAM | LSRAM (20 Kb) |
| FPGA DDR | Soft controller only | Soft or MIG IP | Soft or MIG IP | Soft or hard (DDR I/O) |

---

## BRAM vs URAM vs Distributed RAM

Xilinx UltraScale+ devices have three types of on-chip memory. Choosing the wrong type wastes resources or creates timing problems.

| Property | BRAM (36 Kb) | URAM (288 Kb) | Distributed RAM (LUTRAM) |
|---|---|---|---|
| Capacity per block | 36 Kb | 288 Kb | 64 bits per LUT |
| Ports | True dual-port | True dual-port | Single-port (simple dual-port possible) |
| Read latency | 1–2 cycles | 1 cycle | 0 cycles (combinational) |
| Max clock | ~500 MHz | ~450 MHz | Fabric-limited (~400 MHz) |
| Write | Synchronous | Synchronous | Synchronous |
| Read | Synchronous | Synchronous | Asynchronous possible |
| Best for | Small FIFOs, register files, small buffers | Deep FIFOs, large buffers, packet storage | Small scratchpads, async read needed |

### Decision Guide

| Need | Use | Why |
|---|---|---|
| FIFO < 4K entries | BRAM | True dual-port, standard FIFO IP |
| FIFO 4K–32K entries | URAM | 8× deeper per block, saves BRAM for other uses |
| Async read (same-cycle) | LUTRAM | BRAM/URAM always have 1-cycle read latency |
| Register file (32×32-bit) | BRAM | Dual-port access, fits in one BRAM18 |
| Large packet buffer (>100 KB) | URAM + external DDR | URAM for active packets, DDR for deep queues |

---

## Shared DDR Bandwidth Contention

All FPGA SoCs share the hard DDR controller between CPU and FPGA. This is the single most common performance bottleneck.

```
┌─────────┐  ┌──────────┐  ┌─────────┐
│CPU Core0│  │CPU Core1 │  │FPGA DMA │
│reads DDR│  │writes DDR│  │streaming │
└────┬────┘  └────┬─────┘  └────┬─────┘
     │            │              │
     ▼            ▼              ▼
┌────────────────────────────────────┐
│      L3 Interconnect (NIC-301)     │
│      NO QoS, NO bandwidth reserve  │
└───────────────┬────────────────────┘
                │
                ▼
┌──────────────────────────┐
│   Hard DDR Controller    │
│   Cyclone V: 3.2 GB/s     │
└──────────────────────────┘
```

| Device | F2S/HP Ports | DDR Sharing Model | QoS | Solution |
|---|---|---|---|---|
| Cyclone V SoC | 6× F2S | Flat, no arbitration | None | Rate-limit in FPGA fabric |
| Zynq-7000 | 4× S_AXI_HP | Separate HP from GP path | None | Use ACP for shared data |
| Zynq MPSoC | 6× HPC/HP | CCI-400 with QoS | Yes | Program QoS registers |
| PolarFire SoC | Coherent matrix | Single matrix, common path | Limited | FIFO burst buffering |
| Versal | NoC paths | Per-path NoC VC allocation | Yes (strict) | NoC compiler sets priorities |

### Bandwidth Budgeting Formula

To avoid DDR starvation, calculate worst-case aggregate bandwidth:

```
Aggregate = CPU_read + CPU_write + FPGA_DMA_read + FPGA_DMA_write
Available = DDR_peak × 0.7    (70% utilization rule — never plan for 100%)

If Aggregate > Available → Add FIFOs, reduce DMA burst sizes, or add a second DDR controller
```

**Example (Cyclone V SoC, DE10-Nano):**
- CPU read: ~800 MB/s (Linux page faults, program loading)
- CPU write: ~400 MB/s (network stack, filesystem)
- FPGA DMA read: ~1.2 GB/s (video frame read)
- FPGA DMA write: ~1.0 GB/s (processed frame write)
- Aggregate: 3.4 GB/s > Available (3.2 × 0.7 = 2.24 GB/s)
- **Result: DDR starvation.** Linux will stall under load.
- **Fix:** Use FPGA BRAM as intermediate buffer, reduce DMA burst size, or skip every other frame.

---

## Cache Coherency Deep Dive

| Coherency Model | Who Has It | How | Software Impact |
|---|---|---|---|
| **Fully coherent** | PolarFire SoC (all ports), MPSoC (ACP/ACE) | Hardware snoops L2, auto-invalidation | None — CPU and FPGA see same memory |
| **ACP coherent** | Zynq-7000 (ACP port only) | FPGA injects into SCU snoop queue | Only ACP traffic is coherent; HP still bypasses |
| **Non-coherent** | Cyclone V SoC (all bridges) | Nothing — F2S bypasses L2 | Manual cache flush (`flush_cache_range`, `ioremap`) |
| **No cache at all** | SmartFusion2 (Cortex-M3 has no L2) | N/A | None — no virtual memory |

### When Coherency Matters

| Scenario | Coherency Required | Approach |
|---|---|---|
| FPGA writes data, CPU reads it | Yes | Use ACP (Zynq-7000) or coherent interconnect (MPSoC, PolarFire SoC) |
| FPGA streams to DDR, CPU doesn't read same data | No | Use HP/F2S — faster than coherent path |
| Shared ring buffer between CPU and FPGA | Yes | Use coherent path or explicit cache maintenance (`dma_sync_single_for_cpu`) |
| CPU configures FPGA registers | No | Use GP/H2F — register access is not bandwidth-sensitive |

---

## On-Chip RAM (OCM) — The Hidden Resource

Most SoCs have a small but precious On-Chip Memory (OCM) that is accessible from both CPU and FPGA without going through DDR:

| Device | OCM Size | CPU Access | FPGA Access | Latency |
|---|---|---|---|---|
| Zynq-7000 | 256 KB | AXI AHB (via L2) | AXI slave port | ~10 cycles |
| Zynq MPSoC | 256 KB + 128 KB TCM | AHB + TCM port | AXI slave port | ~5 cycles |
| Cyclone V SoC | 64 KB | HPS bridge | F2H bridge | ~20 cycles |
| PolarFire SoC | eNVM only | Direct | AXI | ~5 cycles |

**Best uses for OCM:**
1. **CPU↔FPGA mailbox** — small shared memory for command/status without DDR contention
2. **Interrupt vector table** — zero-wait-state access for exception handlers
3. **Critical code sections** — lock timing-sensitive code in OCM to avoid DDR jitter
4. **DMA descriptor rings** — keep descriptor rings in OCM for fastest DMA setup

---

## Best Practices

1. **Reserve DDR bandwidth before design starts** — calculate worst-case aggregate bandwidth for CPU + DMA + FPGA. If total exceeds 70% of DDR peak, add FPGA-side FIFOs.
2. **Use FPGA BRAM as the first line of buffering** — keep large, frequent transactions in FPGA BRAM, not DDR.
3. **Cache coherency is not free** — ACP on Zynq-7000 adds ~2 cycles of latency vs HP. For pure streaming, HP is faster.
4. **Use OCM for shared mailboxes** — the 256 KB OCM on Zynq is perfect for CPU↔FPGA communication without DDR involvement.
5. **Profile DDR utilization in simulation** — use AXI performance monitors (Xilinx) or EMIF debug toolkit (Intel) to measure actual DDR utilization, not theoretical peak.

---

## Pitfalls

### 1. The Zynq-7000 1 GB DDR Limit
Zynq-7000 has a hard 1 GB DDR address space limit (32-bit DDR address). No amount of external memory can exceed this.

**Fix:** If you need more than 1 GB, use Zynq MPSoC (32 GB limit with 64-bit addressing) or add a soft DDR controller in the FPGA fabric with its own address space.

### 2. Cyclone V F2S Starvation
All six F2S ports share the same DDR controller with no QoS. A single misbehaving master can starve all others and the CPU.

**Fix:** Implement credit-based rate limiting in the FPGA fabric before each F2S master. See [Design Patterns](../../04_hdl_and_synthesis/design_patterns.md) for a rate limiter implementation.

### 3. BRAM Read Latency in Tight Loops
BRAM has a 1–2 cycle read latency. If your FSM reads BRAM and uses the data in the same cycle, you will get stale data.

**Fix:** Pipeline your BRAM reads — issue the read address in cycle N, use the read data in cycle N+1 or N+2. See [Pipeline with Backpressure](../../04_hdl_and_synthesis/design_patterns.md) for a pipelined access pattern.

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS TRM — SDRAM Controller Subsystem | Intel |
| Zynq-7000 TRM — DDR Memory Controller (Chapter 10) | Xilinx/AMD |
| Zynq MPSoC TRM — Memory Subsystem (UG1085) | Xilinx/AMD |
| PolarFire SoC — Memory Subsystem (UG0820) | Microchip |
| ARM Cortex-A9 MPCore TRM — SCU | ARM DDI 0407I |
| [AXI Bridges & Interconnect](axi_bridges_and_interconnect.md) | This repository |
| [Multi-Core Coherency](../../11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md) | This repository |
| [Debugging DDR](../../15_case_studies/debugging_ddr.md) | This repository |
