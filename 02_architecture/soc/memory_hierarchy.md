[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Memory Hierarchy — On-Die Memory Topology

How memory is organized across the CPU and FPGA domains, from cache hierarchies to shared DDR controllers. The memory path your data takes determines latency, bandwidth, and whether you need to worry about cache coherency at all.

---

## The Memory Pyramid (FPGA SoC view)

```
Size:   KB ◄─────────────────────────────────► GB
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

---

## Cache Coherency Deep Dive

| Coherency Model | Who Has It | How | Software Impact |
|---|---|---|---|
| **Fully coherent** | PolarFire SoC (all ports), MPSoC (ACP/ACE) | Hardware snoops L2, auto-invalidation | None — CPU and FPGA see same memory |
| **ACP coherent** | Zynq-7000 (ACP port only) | FPGA injects into SCU snoop queue | Only ACP traffic is coherent; HP still bypasses |
| **Non-coherent** | Cyclone V SoC (all bridges) | Nothing — F2S bypasses L2 | Manual cache flush (`flush_cache_range`, `ioremap`) |
| **No cache at all** | SmartFusion2 (Cortex-M3 has no L2) | N/A | None — no virtual memory |

---

## Best Practices

1. **Reserve DDR bandwidth before design starts** — calculate worst-case aggregate bandwidth for CPU + DMA + FPGA. If total exceeds 70% of DDR peak, add FPGA-side FIFOs.
2. **Use FPGA BRAM as the first line of buffering** — keep large, frequent transactions in FPGA BRAM, not DDR.
3. **Cache coherency is not free** — ACP on Zynq-7000 adds ~2 cycles of latency vs HP. For pure streaming, HP is faster.

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS TRM — SDRAM Controller Subsystem | Intel |
| Zynq-7000 TRM — DDR Memory Controller (Chapter 10) | Xilinx/AMD |
| PolarFire SoC — Memory Subsystem (UG0820) | Microchip |
| ARM Cortex-A9 MPCore TRM — SCU | ARM DDI 0407I |
