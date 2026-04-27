[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Hard Processor Integration — CPU-FPGA Coupling Models

How hardened CPU cores are physically integrated with FPGA fabric on the same die. Covers the architectural tradeoffs between ARM Cortex-A, Cortex-R, Cortex-M, RISC-V, and soft processor implementations, and how each vendor chooses different coupling strategies.

---

## Hard vs Soft CPU

| Property | Hard CPU | Soft CPU (e.g. Nios II, MicroBlaze, PicoRV32) |
|---|---|---|
| Silicon area | Dedicated die region, fixed | Consumes FPGA LEs, BRAM, DSP |
| Clock speed | 600 MHz – 1.5 GHz | 50–250 MHz (fabric-limited) |
| Power | Hardened, lower dynamic power | Higher (fabric switching) |
| Flexibility | Fixed peripheral set | Any peripheral you implement |
| Boot | Boots independently (has own ROM) | Must be loaded into fabric first |

> **Beyond this overview:** For deep dives on soft CPU selection, pipeline architecture, vendor-specific configuration (MicroBlaze, Nios II/V), open-source RISC-V cores, bus matrix design, and full SoC integration — see **[Section 11 — Soft Cores & SoC Design](../../11_soft_cores_and_soc_design/README.md)**.

---

## Vendor Integration Models (Hard CPUs)

| Vendor / Family | Hard CPU | Cores | Max Clock | Fabric Interface |
|---|---|---|---|---|
| Intel Cyclone V / Arria 10 | Cortex-A9 (ARMv7-A) | 2 | 800–925 MHz / 1.2 GHz | 3× AXI-3 bridges (H2F, F2H, LWH2F) + 6× F2S |
| Intel Stratix 10 | Cortex-A53 (ARMv8-A) | 4 | 1.2 GHz | AXI-4 bridges + SDRAM interconnect |
| Intel Agilex 7 | Cortex-A53 (ARMv8-A) | 4 | ~1.5 GHz | AXI-4 + NoC (chiplet EMIB interconnect) |
| Intel Agilex 5 | Cortex-A76 + Cortex-A55 | 2+2 | 1.8 / 1.5 GHz | AXI-4 bridges + DDR4/5/LPDDR4/5 |
| Xilinx Zynq-7000 | Cortex-A9 (ARMv7-A) | 2 | 667–866 MHz | 2× M_AXI_GP + 2× S_AXI_GP + 4× S_AXI_HP + 1× ACP |
| Xilinx MPSoC | Cortex-A53 + Cortex-R5F | 4 + 2 | 1.3 GHz / 600 MHz | AXI + ACP + CCI (Cache Coherent Interconnect) |
| Xilinx Versal | Cortex-A72 + Cortex-R5F | 2 + 2 | TBD | Hard NoC (2D-mesh AXI4-Stream) |
| Microchip SmartFusion2 | Cortex-M3 (ARMv7-M) | 1 | 166 MHz | AHB bus matrix + FPGA fabric |
| Microchip PolarFire SoC | RISC-V U54 + E51 | 4 + 1 | 667 MHz | Coherent AXI4 bus matrix |
| Gowin GW1NSR | PicoRV32 (RV32IMC) | 1 | ~30 MHz | Wishbone / custom bus |

---

## Soft CPU Comparison

| CPU | Vendor | ISA | LUTs (typical) | fmax (approx) | Notes / Deep Dive |
|---|---|---|---|---|---|
| **Nios II/f** | Intel | 32-bit RISC | 1,400–1,800 | 200+ MHz | 3 variants: /e, /s, /f. [→ Nios II/V deep dive](../../11_soft_cores_and_soc_design/vendor_soft/nios_family.md) |
| **Nios V/m** | Intel | RV32IMC | ~1,200 | 150+ MHz | RISC-V Nios successor. [→ Nios II/V deep dive](../../11_soft_cores_and_soc_design/vendor_soft/nios_family.md) |
| **MicroBlaze** | Xilinx | 32-bit RISC | 1,000–2,500 | 200+ MHz | 3–5 stage pipeline, AXI4. [→ MicroBlaze deep dive](../../11_soft_cores_and_soc_design/vendor_soft/microblaze.md) |
| **PicoRV32** | Open-source | RV32IMC | 750–2,000 | 150+ MHz | Minimal footprint, PCPI co-proc. [→ PicoRV32 deep dive](../../11_soft_cores_and_soc_design/riscv_cores/picorv32.md) |
| **VexRiscv** | Open-source | RV32IMC / RV64 | 1,000–2,000 | 200+ MHz | SpinalHDL, optional MMU (Linux). [→ VexRiscv deep dive](../../11_soft_cores_and_soc_design/riscv_cores/vexriscv.md) |
| **NEORV32** | Open-source | RV32IMC | 1,200–2,500 | 100+ MHz | Best docs, integrated SoC peripherals. [→ NEORV32 deep dive](../../11_soft_cores_and_soc_design/riscv_cores/neorv32.md) |

> **For a quick side-by-side comparison of ALL RISC-V soft cores** (pipeline depth, extensions, utilization, fmax, Linux support): [RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/riscv_cores_catalog.md).
> 
> **Non-RISC-V options** — OpenRISC (mor1kx), LEON3/4 (SPARC V8), Microwatt (POWER9), and retro-ISA cores (Z80, 6502, 68000): see [Other ISA Cores](../../11_soft_cores_and_soc_design/other_isa/README.md) and [Other ISA Catalog](../../12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md).

---

## When to Use What

| Scenario | Recommendation |
|---|---|
| Linux required, hard CPU available | Use hard CPU (Cortex-A9/A53/RISC-V U54) — see [Vendor Integration Models](#vendor-integration-models-hard-cpus) above |
| Linux required, no hard CPU | Soft CPU + Linux is slow; consider [VexRiscv with MMU](../../11_soft_cores_and_soc_design/riscv_cores/vexriscv.md) as the only realistic option |
| Bare-metal control, hard CPU available | Hard Cortex-M3 / R5F — deterministic, low power |
| Bare-metal control, no hard CPU | [Nios II/V](../../11_soft_cores_and_soc_design/vendor_soft/nios_family.md) or [MicroBlaze](../../11_soft_cores_and_soc_design/vendor_soft/microblaze.md) — ~2K LEs, good enough |
| Custom ISA needed | Soft RISC-V: [VexRiscv](../../11_soft_cores_and_soc_design/riscv_cores/vexriscv.md) (configurable), [NEORV32](../../11_soft_cores_and_soc_design/riscv_cores/neorv32.md) (best docs) |
| Ultra-low-cost (<$10 FPGA) | [PicoRV32](../../11_soft_cores_and_soc_design/riscv_cores/picorv32.md) or Gowin GW1NSR hard core |

---

## Further Reading

| Destination | What you'll find |
|---|---|
| **[Section 11 — Soft Cores & SoC Design](../../11_soft_cores_and_soc_design/README.md)** | Soft core selection, RISC-V ISA, SoC bus architecture, multi-core coherency |
| [Vendor Soft Processors](../../11_soft_cores_and_soc_design/vendor_soft/README.md) | MicroBlaze / MicroBlaze-V config & BSP, Nios II → Nios V migration |
| [Open-Source RISC-V Cores](../../11_soft_cores_and_soc_design/riscv_cores/README.md) | VexRiscv, PicoRV32, NEORV32, SERV, Ibex, high-perf (BOOM/Rocket/CVA6) |
| [Other ISA Soft Cores](../../11_soft_cores_and_soc_design/other_isa/README.md) | LEON3 (SPARC), mor1kx (OpenRISC), Microwatt (POWER9), retro (Z80/6502/68000) |
| [SoC Design Patterns](../../11_soft_cores_and_soc_design/soc_design/README.md) | Bus matrix topologies, memory maps, interrupt routing, DMA architecture |
| [RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/riscv_cores_catalog.md) | Quick comparison: all RISC-V cores side by side |
| [Peripheral Core Catalog](../../12_open_source_open_hardware/cores_catalog/peripheral_cores_catalog.md) | Ready-to-use Wishbone/AXI peripherals (I2C, SPI, UART, GPIO) |

---

## Best Practices

1. **Don't default to soft CPU if a hard one is available** — hard CPU saves ~2K LEs and runs at 4–8× the clock speed.
2. **Pair hard CPU + soft CPU** — MPSoC's dual R5F + quad A53 is the canonical pattern: real-time cores handle deterministic tasks, application cores run Linux.
3. **Soft CPU for debug/control, hard CPU for compute** — simple Nios II for JTAG UART + register peek/poke; hard Cortex-A9 for video processing.

---

## References

| Source | Path |
|---|---|
| Cyclone V SoC HPS TRM | Intel FPGA documentation |
| Zynq-7000 TRM (UG585) | AMD/Xilinx documentation |
| PolarFire SoC User Guide (UG0820) | Microchip documentation |
| Nios II Processor Reference Guide | Intel FPGA documentation |
| MicroBlaze Processor Reference Guide (UG984) | AMD/Xilinx documentation |
