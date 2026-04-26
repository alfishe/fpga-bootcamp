[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# AXI Bridges & Interconnect — CPU ↔ FPGA Communication

The AXI bus fabric is the nervous system of every FPGA SoC. This article covers the bridge architectures, bandwidth budgets, AXI protocol differences, and the interconnect topologies that determine how fast your CPU and FPGA can talk to each other.

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

---

## AXI-3 vs AXI-4

| Feature | AXI-3 | AXI-4 |
|---|---|---|
| Write data interleaving | Yes (WID signal) | No (WID removed) |
| Burst length | 1–16 beats | 1–256 beats |
| Used by | Intel HPS (Cyclone V, Arria 10) | Xilinx PS (Zynq, MPSoC), most IP vendors |
| Self-checking | ❌ Harder to verify ordering | ✅ Easier — no interleaving |

**Key pitfall:** connecting Intel's AXI-3 HPS bridge to an AXI-4-only IP core. The IP core ignores WID, and interleaved write data arrives in wrong order. Solution: insert an AXI-3-to-AXI-4 protocol converter (e.g., Intel's AXI Clock Bridge in mode "AXI-3 slave to AXI-4 master").

---

## Bandwidth Budget: Cyclone V SoC (DE10-Nano)

| Resource | Peak Throughput | Condition |
|---|---|---|
| HPS-to-FPGA (H2F) | 100 MHz × 64-bit = 800 MB/s | Max fabric side clock |
| FPGA-to-HPS (F2H) | 100 MHz × 64-bit = 800 MB/s | Max fabric side clock |
| FPGA-to-SDRAM ×6 | 200 MHz × 256-bit = 51.2 Gbps ×6 masters | Aggregate (6 ports share DDR controller) |
| HPS DDR (CPU side) | 400 MHz × 32-bit = 25.6 Gbps = 3.2 GB/s | 1 GB DDR3 on DE10-Nano |
| Lightweight H2F | 100 MHz × 32-bit = 400 MB/s | 100 MHz fabric clock |

**Contention:** all six F2S masters plus the two Cortex-A9 cores plus DMA engines share the 3.2 GB/s HPS DDR controller. No QoS. No reservation. If FPGA F2S master 0 issues a tight read loop on DDR, Cortex-A9 Linux can stall for microseconds.

---

## Interconnect Topologies

| Device | Interconnect | Topology | Coherency | QoS |
|---|---|---|---|---|
| Cyclone V SoC | ARM NIC-301 | Single crossbar | None | No |
| Zynq-7000 | ARM PL301 + SCU | Dual crossbar (GP + HP) | Via ACP only | No |
| Zynq MPSoC | ARM CCI-400 | Cache Coherent Interconnect | Full (ACP + ACE-Lite) | Yes (CCI QoS) |
| PolarFire SoC | AXI4 Bus Matrix | Single coherent matrix | Full (all ports) | Limited |
| Versal ACAP | Hard NoC | 2D-mesh, 256-bit, ~2 Tbps | Yes | Yes (per-path QoS) |

---

## Best Practices

1. **Don't touch LWH2F during active DMA** — lightweight bridge shares HPS-to-FPGA bandwidth. If H2F is streaming bulk data, LWH2F register reads stall. Use a separate register bank in FPGA BRAM accessible via F2H.
2. **Rate-limit F2S masters** — without QoS, one F2S port can starve all others. Implement credit-based or round-robin arbitration in FPGA fabric.
3. **ACP over HP for shared data structures** — on Zynq-7000, use ACP when FPGA and CPU share data. Use HP for bulk streaming where cache is irrelevant.

---

## References

| Source | Path |
|---|---|
| AMBA AXI and ACE Protocol Specification (IHI 0022E) | ARM |
| Cyclone V HPS Technical Reference Manual | Intel |
| Zynq-7000 TRM (UG585), Chapter 24 (AXI Interfaces) | Xilinx/AMD |
| ARM CoreLink NIC-301 TRM | ARM |
