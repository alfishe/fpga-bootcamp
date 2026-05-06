[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# AXI Bridges & Interconnect — CPU ↔ FPGA Communication Topologies

The AXI bus fabric is the nervous system of every FPGA SoC. Bridges connect the CPU subsystem to the FPGA fabric, and the interconnect topology determines bandwidth, latency, coherency, and whether your design deadlocks under load. This article covers the four fundamental bridge patterns, AXI-3 vs AXI-4 protocol differences, bandwidth budgets for common platforms, and interconnect topology evolution from simple crossbars to Network-on-Chip (NoC).

> [!NOTE]
> For memory hierarchy and DDR bandwidth contention, see [Memory Hierarchy](memory_hierarchy.md). For cache coherency details (ACP, ACE, CCI), see [Multi-Core Coherency](../../11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md). For AXI4 protocol specifics, see [AXI4 Family](../../06_ip_and_cores/bus_protocols/axi4_family.md).

---

## Four Bridge Patterns

Every FPGA SoC implements four fundamental communication paths between CPU and FPGA:

```
┌────────── CPU ───────────┐
│  ┌──────┐  ┌──────┐     │
│  │Core 0│  │Core 1│      │
│  └──┬───┘  └──┬───┘     │
│     │         │          │
│  ┌──▼─────────▼──────┐   │
│  │  L2 Cache + SCU   │   │
│  └──┬─────────┬──────┘   │
│     │         │          │
│  ┌──▼──┐  ┌──▼───┐     │
│  │GP   │  │HP/ACP│     │
│  │M_AXI│  │S_AXI │     │
│  └──┬──┘  └──┬───┘     │
└─────┼────────┼──────────┘
      │        │
┌─────▼────────▼──────────┐
│  AXI Interconnect        │
│  (Crossbar / NIC / NoC)  │
└─────┬────────┬──────────┘
      │        │
┌─────▼──┐ ┌──▼──────────┐
│ FPGA   │ │ DDR Ctrl    │
│ Slaves │ │ (shared)    │
└────────┘ └─────────────┘
```

| Bridge | Direction | Cyclone V Name | Zynq-7000 Name | Width | Typical Throughput |
|---|---|---|---|---|---|
| CPU → FPGA (control) | PS/HPS → PL | **HPS-to-FPGA (H2F)** | M_AXI_GP | 32–64 bit | ~200–800 MB/s |
| CPU → FPGA (lightweight) | PS/HPS → PL | **Lightweight H2F (LWH2F)** | (via M_AXI_GP) | 32 bit | ~100 MB/s |
| FPGA → DDR (data) | PL → DDR | **FPGA-to-SDRAM (F2S)** | S_AXI_HP | 64–128 bit | ~1.6–6.4 GB/s |
| FPGA → CPU memory | PL → PS/HPS | **FPGA-to-HPS (F2H)** | (via S_AXI_HP) | 64 bit | ~1.6 GB/s |

### Bridge Selection Guide

| Need | Bridge | Why |
|---|---|---|
| CPU reads/writes FPGA registers | GP / H2F / LWH2F | Low bandwidth, register-width access |
| FPGA streams data to DDR | HP / F2S | High bandwidth, burst-capable |
| FPGA and CPU share data coherently | ACP | Snoop-coherent with CPU L2 cache |
| FPGA needs independent DDR access | F2S with own port | No CPU involvement in data path |

---

## AXI-3 vs AXI-4

| Feature | AXI-3 | AXI-4 |
|---|---|---|
| Write data interleaving | Yes (WID signal) | No (WID removed) |
| Burst length | 1–16 beats | 1–256 beats |
| Used by | Intel HPS (Cyclone V, Arria 10) | Xilinx PS (Zynq, MPSoC), most IP vendors |
| Self-checking | ❌ Harder to verify ordering | ✅ Easier — no interleaving |
| QoS signaling | No | Yes (AxQOS signals) |
| Region signals | No | Yes (AxREGION, up to 16 regions) |

**Key pitfall:** connecting Intel's AXI-3 HPS bridge to an AXI-4-only IP core. The IP core ignores WID, and interleaved write data arrives in wrong order. Solution: insert an AXI-3-to-AXI-4 protocol converter (e.g., Intel's AXI Clock Bridge in mode "AXI-3 slave to AXI-4 master").

> [!WARNING]
> **CDC: requires synchronizer or FIFO** when crossing from the CPU clock domain (e.g., 800 MHz Cortex-A9) to the FPGA fabric clock domain (e.g., 100 MHz). All SoC bridges include internal synchronization, but if you generate your own AXI crossing, you must handle CDC explicitly.

---

## Bandwidth Budget: Common SoC Platforms

### Cyclone V SoC (DE10-Nano)

| Resource | Peak Throughput | Condition |
|---|---|---|
| HPS-to-FPGA (H2F) | 100 MHz × 64-bit = 800 MB/s | Max fabric side clock |
| FPGA-to-HPS (F2H) | 100 MHz × 64-bit = 800 MB/s | Max fabric side clock |
| FPGA-to-SDRAM ×6 | 200 MHz × 256-bit = 51.2 Gbps ×6 masters | Aggregate (6 ports share DDR controller) |
| HPS DDR (CPU side) | 400 MHz × 32-bit = 25.6 Gbps = 3.2 GB/s | 1 GB DDR3 on DE10-Nano |
| Lightweight H2F | 100 MHz × 32-bit = 400 MB/s | 100 MHz fabric clock |

**Contention:** all six F2S masters plus the two Cortex-A9 cores plus DMA engines share the 3.2 GB/s HPS DDR controller. No QoS. No reservation. If FPGA F2S master 0 issues a tight read loop on DDR, Cortex-A9 Linux can stall for microseconds.

### Zynq MPSoC

| Resource | Peak Throughput | Condition |
|---|---|---|
| M_AXI_HPM0_FPD | 333 MHz × 64-bit = 2.6 GB/s | Full Power Domain master |
| M_AXI_HPM1_FPD | 333 MHz × 64-bit = 2.6 GB/s | Full Power Domain master |
| S_AXI_HP0_FPD | 333 MHz × 128-bit = 5.3 GB/s | High-performance slave |
| S_AXI_HP1–3_FPD | 333 MHz × 64-bit = 2.6 GB/s each | High-performance slaves |
| S_AXI_ACP | 333 MHz × 64-bit = 2.6 GB/s | Cache-coherent ACP |
| DDR4 (PS side) | 2400 MT/s × 32-bit = 9.6 GB/s | ECC optional |

---

## Interconnect Topology Evolution

| Device | Interconnect | Topology | Coherency | QoS | Bandwidth |
|---|---|---|---|---|---|
| Cyclone V SoC | ARM NIC-301 | Single crossbar | None | No | ~3.2 GB/s |
| Zynq-7000 | ARM PL301 + SCU | Dual crossbar (GP + HP) | Via ACP only | No | ~4.2 GB/s |
| Zynq MPSoC | ARM CCI-400 | Cache Coherent Interconnect | Full (ACP + ACE-Lite) | Yes (CCI QoS) | ~9.6 GB/s |
| Intel Agilex 7 | NoC + AMBA | Hard NoC (2D mesh) | Per-path | Yes | ~384 Gbps |
| PolarFire SoC | AXI4 Bus Matrix | Single coherent matrix | Full (all ports) | Limited | ~6.4 GB/s |
| Versal ACAP | Hard NoC | 2D-mesh, 256-bit, ~2 Tbps | Yes | Yes (per-path QoS) | ~2 Tbps |

### Crossbar vs NoC Decision Guide

```mermaid
graph TD
    A[How many AXI masters?] -->|"1-4"| B[Crossbar: simple, low latency]
    A -->|"5-15"| C[NIC-301 / PL301: multi-path crossbar"]
    A -->|"15+"| D[NoC: scales to hundreds of paths"]
    B --> E{Need cache coherency?}
    C --> E
    E -->|"Yes"| F[CCI / ACE interconnect"]
    E -->|"No"| G[Non-coherent crossbar"]
    D --> H[Hard NoC: Versal, Agilex"]
```

---

## Deadlock Avoidance in AXI Interconnect

AXI deadlocks occur when two masters each hold a resource the other needs. Common patterns:

### 1. Same-ID Dependency
If a master issues a read with ID=5 and then a write with ID=5, the interconnect may reorder the write before the read completes, violating the master's expectation.

**Fix:** Use different IDs for independent transactions, or ensure the master waits for outstanding transactions before issuing new ones.

### 2. Multi-Master Contention Without QoS
On Cyclone V SoC, if two F2S masters continuously read from DDR, a third master can be starved indefinitely.

**Fix:** Implement round-robin arbitration in the FPGA fabric before the F2S ports. See [Round-Robin Arbiter](../../04_hdl_and_synthesis/design_patterns.md) for a synthesizable implementation.

### 3. ACP Starvation on Zynq-7000
The ACP port shares bandwidth with the SCU snoop filter. Heavy ACP traffic can slow down the CPU's own L2 cache accesses.

**Fix:** Use ACP only for small, frequent data structures that truly benefit from coherency. For bulk streaming, use HP ports.

---

## Best Practices

1. **Don't touch LWH2F during active DMA** — lightweight bridge shares HPS-to-FPGA bandwidth. If H2F is streaming bulk data, LWH2F register reads stall. Use a separate register bank in FPGA BRAM accessible via F2H.
2. **Rate-limit F2S masters** — without QoS, one F2S port can starve all others. Implement credit-based or round-robin arbitration in FPGA fabric.
3. **ACP over HP for shared data structures** — on Zynq-7000, use ACP when FPGA and CPU share data. Use HP for bulk streaming where cache is irrelevant.
4. **Match bridge width to your data path** — 32-bit bridges waste half the bandwidth of 64-bit data paths. If your FPGA processes 64-bit words, use the 64-bit H2F bridge, not LWH2F.
5. **Verify AXI protocol compliance** — use the [AXI Protocol Checkers](../../07_verification/protocol_checkers.md) in simulation to catch ID, burst, and size violations before silicon.

---

## Pitfalls

### 1. AXI-3 Bridge to AXI-4 IP (Intel Cyclone V)
Intel's HPS bridges are AXI-3. Most third-party IP is AXI-4. The WID signal mismatch causes write data ordering failures.

**Fix:** Insert an AXI-3-to-AXI-4 bridge IP. Intel provides one in their IP catalog (AXI Clock Bridge, mode "AXI-3 slave to AXI-4 master").

### 2. Fabric Clock Must Be Slower Than HPS Clock
On Cyclone V SoC, the FPGA fabric clock driving the AXI bridges must not exceed the maximum specified frequency (typically 100–150 MHz for H2F/F2H, 200 MHz for F2S). Exceeding this causes timing violations inside the HPS-to-FPGA bridge domain.

**Fix:** Use the HPS PLL to generate the fabric-side clock, and constrain it in SDC. Do not use an independent FPGA PLL.

### 3. Exclusive Access Not Supported on All Bridges
AXI exclusive access (AxLOCK signals) is not supported on Cyclone V SoC HPS bridges or Zynq-7000 GP ports. Attempting exclusive access causes undefined behavior.

**Fix:** Implement software-level mutual exclusion (spinlocks in shared BRAM) instead of relying on AXI hardware exclusivity.

---

## References

| Source | Path |
|---|---|
| AMBA AXI and ACE Protocol Specification (IHI 0022E) | ARM |
| Cyclone V HPS Technical Reference Manual | Intel |
| Zynq-7000 TRM (UG585), Chapter 24 (AXI Interfaces) | Xilinx/AMD |
| Zynq MPSoC TRM (UG1085), Chapter 18 (AXI Interconnect) | Xilinx/AMD |
| ARM CoreLink NIC-301 TRM | ARM |
| ARM CoreLink CCI-400 TRM | ARM |
| [Memory Hierarchy](memory_hierarchy.md) | This repository |
| [Multi-Core Coherency](../../11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md) | This repository |
| [AXI4 Family](../../06_ip_and_cores/bus_protocols/axi4_family.md) | This repository |
