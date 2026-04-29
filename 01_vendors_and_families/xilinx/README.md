[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-B — Xilinx / AMD

The market leader in FPGA density and tooling maturity. Founded in 1984 (co-invented the FPGA), acquired by AMD in 2022 for ~$49B. Xilinx covers the entire spectrum: from $10 Spartan-7 to $50K+ Versal Premium with AI Engines. The 7-series is the workhorse generation (28nm, Vivado-native, open-source toolchain progress), UltraScale+ pushes density to 3.8M LEs with 16nm FinFET, and Versal (7nm ACAP) introduces a hard NoC and SIMD AI Engine arrays.

---

## History & Corporate Context

| Year | Event |
|---|---|
| 1984 | Founded by Ross Freeman, Bernie Vonderschmitt, Jim Barnett — invented the FPGA |
| 1998 | Introduced Virtex — first million-gate FPGA |
| 2012 | 7-series launch + Vivado Design Suite (replaced ISE for new designs) |
| 2015 | UltraScale+ at 16nm FinFET — MPSoC with quad A53, RFSoC with direct RF |
| 2019 | Versal ACAP announced — NoC interconnect, AI Engines, 7nm |
| 2022 | Acquired by AMD (~$49B). Xilinx became "AMD Adaptive and Embedded Computing Group" |
| 2025 | Altera separates from Intel (Silver Lake 51% acquisition) — AMD/Xilinx now the only Big-2 FPGA vendor still inside a larger semiconductor company |

---

## Technology Evolution

| Generation | Process | Key Innovation | Toolchain |
|---|---|---|---|
| 7-series (2012) | 28nm | Unified architecture, Vivado-native, ACP coherent port (Zynq) | Vivado / ISE (legacy) |
| UltraScale (2014) | 20nm | ASIC-like clocking, CARRY8, denser CLBs (8 slices) | Vivado only |
| UltraScale+ (2015) | 16nm FinFET | URAM (288 Kb), MPSoC (A53+R5F+GPU+VCU), RFSoC (direct RF), HBM | Vivado only |
| Versal (2019) | 7nm | NoC (2D mesh), AI Engines (VLIW SIMD), PCIe Gen5, 112G PAM4, DDR5 | Vitis / Vivado |

---

## Key Architectural Differentiators

1. **ACP (Accelerator Coherency Port) — Zynq-7000 only.** FPGA logic snoops Cortex-A9 L2 cache via SCU. No software cache management needed for shared data structures. Unique at this price point.
2. **CCI-400 Snoop Filter — Zynq MPSoC.** ARM CoreLink coherent interconnect avoids broadcast snoops. FPGA masters get coherent access through 128-bit HPC ports at 9.6 GB/s.
3. **NoC (Network-on-Chip) — Versal.** Replaces traditional AXI crossbar with 2D mesh. QoS-guaranteed, deadlock-free routing between PS, PL, AI Engines, DDR, and transceivers.
4. **AI Engines — Versal.** 400-tile VLIW SIMD arrays (~4 TFLOPS INT8) on-die. Each tile: 32KB data memory, vector processor, direct NoC access. Not programmable logic — they're hardened compute tiles.
5. **RFSoC direct RF — UltraScale+.** 14-bit ADCs at 4–6.5 GSPS, DACs at up to 10 GSPS. Eliminates external JESD204B converter chips. Direct sampling to S-band.

---

## Family Directories

| Directory | Coverage |
|---|---|
| [7series/](7series/README.md) | **7-Series (28nm)** — Spartan-7, Artix-7, Kintex-7, Virtex-7, Zynq-7000 (SoC with dual Cortex-A9, [ACP coherency](7series/soc/README.md)). FOSS toolchain: Project X-Ray + SymbiFlow. Cyclone V comparison included |
| [ultrascale_plus/](ultrascale_plus/README.md) | **UltraScale & UltraScale+ (20/16nm)** — Kintex/Virtex UltraScale+, Zynq MPSoC (quad A53 + dual R5F, [CCI-400 coherent](ultrascale_plus/soc/README.md), GPU, VCU), RFSoC (direct RF ADCs/DACs). URAM, CARRY8, HBM |
| [versal/](versal/README.md) | **Versal ACAP (7nm)** — AI Engines (400-tile VLIW SIMD, ~4 TFLOPS), NoC (2D mesh), PCIe Gen5, 112G PAM4, DDR5. Xilinx vs Intel generation comparison |

---

## Family Comparison

| Family | Process | LEs (max) | Transceivers | Key CPU | Unique Trait | Price Range |
|---|---|---|---|---|---|---|
| **Spartan-7** | 28nm | 102K | None | None | Lowest Xilinx entry, FOSS target | $10–40 |
| **Artix-7** | 28nm | 215K | 6.6 Gbps (×16) | None | Best FOSS support, Arty boards | $15–100 |
| **Kintex-7** | 28nm | 478K | 12.5 Gbps (×32) | None | Balanced perf/dollar mid-range | $50–500 |
| **Virtex-7** | 28nm | 1,955K | 28 Gbps (×96) | None | Maximum 28nm density | $500–10K+ |
| **Zynq-7000** | 28nm | 444K | 12.5 Gbps (×16) | 2× Cortex-A9 | **ACP** cache-coherent FPGA | $20–500 |
| Kintex US+ | 16nm | 1,143K | 28.2 Gbps (×76) | None | URAM (288 Kb blocks) | $100–2K |
| Virtex US+ | 16nm | 3,780K | 58 Gbps (×128) | None | HBM2 option, max density | $1K–50K+ |
| **Zynq MPSoC** | 16nm | 1,143K | 16.3 Gbps (×48) | 4× A53 + 2× R5F | GPU (Mali-400), VCU codec | $50–3K |
| **Zynq RFSoC** | 16nm | 930K | 28.2 Gbps (×48) | 4× A53 + 2× R5F | Direct RF ADCs/DACs on-die | $1K–10K+ |
| Versal AI Edge | 7nm | ~500K | 25 Gbps | 2× A72 + 2× R5F | AI Engines optimized for low-latency | $200–5K |
| Versal Premium | 7nm | ~2,000K | 112G PAM4 | 2× A72 + 2× R5F | NoC, 400G Ethernet, PCIe Gen5 | $5K–50K+ |

---

## Development Board Highlights

| Board | Family | Key Spec | Price | Best For |
|---|---|---|---|---|
| Arty A7-100T | Artix-7 | 101K LUTs, DDR3, Arduino header | ~$249 | General FPGA, LiteX-friendly |
| Zybo Z7-20 | Zynq-7000 | Dual A9, 53K LUTs, HDMI, Pmod | ~$199 | Embedded Linux + FPGA entry |
| PYNQ-Z2 | Zynq-7000 | Dual A9, 53K LUTs, Python framework | ~$199 | Python FPGA development |
| Cora Z7-07S | Zynq-7000 | Single A9, 23K LUTs | ~$99 | Cheapest Xilinx SoC |
| ZCU102 | Zynq MPSoC | 600K LUTs, Quad A53 + Dual R5F | ~$3,495 | Flagship MPSoC eval |
| ZCU111 | Zynq RFSoC | 930K LUTs, 8× ADC + 8× DAC | ~$8,995 | Direct RF sampling eval |
| VCK190 | Versal AI Core | AI Engines, NoC, PCIe Gen5 | ~$8,495 | Versal AI Engine development |

---

## Best Practices

1. **Artix-7 is the default for new pure-FPGA designs** — best FOSS toolchain support, affordable boards, and strong LiteX integration.
2. **Zynq-7000 when you need Linux + FPGA** — ACP eliminates an entire class of cache-coherency bugs. Cyclone V SoC has no equivalent.
3. **Zynq MPSoC for 64-bit + video** — quad A53, GPU, and hardware video codec in one package. The generational leap from Zynq-7000.
4. **RFSoC eliminates external converters** — if your design currently uses JESD204B ADC/DAC chips, RFSoC collapses them into the FPGA package, saving board space, power, and BOM cost.
5. **Versal only if you need AI Engines or NoC QoS** — traditional FPGA fabric is cheaper and more flexible for designs that don't leverage the ACAP-specific hardened blocks.

## Pitfalls

1. **PL power domain is OFF after PS boot on Zynq-7000** — you must explicitly enable it via FSBL, U-Boot, or Linux FPGA Manager. Not automatic like Cyclone V HPS.
2. **Vivado version lock-in** — designs are NOT forward-compatible across Vivado major versions. A 2019.2 project won't open cleanly in 2023.1. Pin the version in CI.
3. **Zynq-7000 ACP is 64-bit only, 1 port** — only one AXI manager can use it. Multiple accelerators must share or arbitrate.
4. **Versal NoC requires a different mental model** — you're not designing AXI interconnect in fabric anymore. The NoC is pre-built, QoS-configured, and must be understood as a routed network, not a crossbar.
5. **ISE is dead for new designs** — Spartan-6 and Virtex-6 are ISE-only and should not be used for new projects. Spartan-7 is the ISE→Vivado migration path.

---

## References

| Source | Description |
|---|---|
| AMD/Xilinx Documentation Portal | https://docs.xilinx.com |
| Zynq-7000 TRM (UG585) | Definitive Zynq-7000 technical reference |
| Zynq MPSoC TRM (UG1085) | Definitive MPSoC technical reference |
| Versal ACAP TRM (AM011) | Versal architecture manual |
| Vivado Design Suite User Guide (UG910) | Vivado toolchain guide |
| Project X-Ray | https://github.com/f4pga/prjxray — 7-series bitstream documentation |
