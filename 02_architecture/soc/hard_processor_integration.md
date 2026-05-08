[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Hard Processor Integration — CPU-FPGA Coupling Models

How hardened CPU cores are physically integrated with FPGA fabric on the same die determines everything about your SoC architecture: boot sequence, interconnect topology, coherency model, and software development flow. This article covers the architectural tradeoffs between ARM Cortex-A, Cortex-R, Cortex-M, RISC-V, and soft processor implementations, and how each vendor chooses different coupling strategies.

> [!NOTE]
> For AXI bridge details and bandwidth budgets, see [AXI Bridges & Interconnect](axi_bridges_and_interconnect.md). For memory topology and DDR contention, see [Memory Hierarchy](memory_hierarchy.md). For boot architecture, see [Boot Architecture](boot_architecture.md).

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

## Coupling Model Decision Guide

```mermaid
graph TD
    A[Need Linux?] -->|"Yes"| B{Hard CPU available?}
    A -->|"No"| C{Need determinism?}
    B -->|"Yes"| D[Use hard CPU: Cortex-A9/A53/RISC-V]
    B -->|"No"| E[VexRiscv with MMU: only realistic soft-Linux]
    C -->|"Yes"| F{Hard Cortex-M/R5 available?}
    C -->|"No"| G[Soft CPU: Nios II, MicroBlaze, PicoRV32]
    F -->|"Yes"| H[Use hard Cortex-M3 or R5F]
    F -->|"No"| G
    D --> I{Need real-time + Linux?}
    I -->|"Yes"| J[MPSoC: A53 + R5F lockstep]
    I -->|"No"| K[Single-domain: Cyclone V, Zynq-7000]
## CPU-FPGA Interface Mechanisms

The physical coupling between hard CPU and FPGA fabric determines bandwidth, latency, and coherency. Four mechanisms exist across vendors:

| Mechanism | Example | Bandwidth | Latency | Coherency |
|---|---|---|---|---|
| **AXI port (GP/HP/ACP)** | Zynq-7000 M_AXI_GP | 0.2–6.4 GB/s | 10–30 cycles | ACP only |
| **Cache-coherent interconnect** | MPSoC CCI-400 | 1.2–12.8 GB/s | 5–15 cycles | Full (ACE) |
| **Network-on-Chip (NoC)** | Versal, Agilex 7 | 10–100+ GB/s | 2–5 cycles | Full |
| **Mailbox / scratchpad** | SmartFusion2 | <100 MB/s | 50+ cycles | None |

### AXI Port Taxonomy (Zynq/MPSoC)

| Port | Direction | Width | Use Case |
|---|---|---|---|
| **M_AXI_GP0/GP1** | PS → PL | 32-bit | CPU reads/writes FPGA registers (control plane) |
| **S_AXI_GP0/GP1** | PL → PS | 32/64-bit | FPGA accesses PS peripherals (DMA status) |
| **S_AXI_HP0–HP3** | PL → DDR | 32/64-bit | FPGA DMA engines stream data to/from DDR |
| **ACP** | PL → L2 cache | 64-bit | FPGA shares cache with CPU (coherent path) |

### Intel HPS Bridge Taxonomy (Cyclone V / Arria 10)

| Bridge | Direction | Width | Use Case |
|---|---|---|---|
| **H2F** | HPS → FPGA | 32/64-bit | CPU accesses FPGA slaves (register maps) |
| **LWH2F** | HPS → FPGA | 32-bit | Lightweight register access (low latency) |
| **F2H** | FPGA → HPS | 32/64-bit | FPGA accesses HPS peripherals or SDRAM |
| **F2S (×6)** | FPGA → SDRAM | 64–256-bit | FPGA DMA masters access shared DDR directly |

---

## Address Map Design Patterns

When a hard CPU and FPGA share a memory-mapped address space, the address map must be planned before RTL coding begins.

### Pattern 1: Flat Shared Address Space
```
0x0000_0000 ────── 0x3FFF_FFFF  Hard CPU DDR (1 GB)
0x4000_0000 ────── 0x4FFF_FFFF  FPGA BRAM / registers (256 MB window)
0x8000_0000 ────── 0xBFFF_FFFF  FPGA peripherals (1 GB window)
```
CPU accesses FPGA by reading/writing the 0x4000_xxxx range. FPGA accesses DDR via F2S/HP ports.

### Pattern 2: Split Address Space with Mailbox
```
0x0000_0000 ────── 0x3FFF_FFFF  CPU DDR (private)
0x4000_0000 ────── 0x7FFF_FFFF  FPGA DDR (private)
0xFF00_0000 ────── 0xFF00_0FFF  Mailbox (shared BRAM, 4 KB)
```
No shared DDR — each domain owns its memory. Communication only through a small mailbox buffer. Eliminates contention but requires copying.

### Pattern 3: Cache-Coherent Shared DDR (MPSoC Only)
```
0x0000_0000 ────── 0x7FFF_FFFF  Shared DDR (coherent via CCI-400)
0x8000_0000 ────── 0x8FFF_FFFF  FPGA BRAM registers
```
Both CPU and FPGA see the same physical memory. No flush/invalidate needed. Requires ACE-Lite ports on MPSoC.

---

## Interrupt Routing

Hard CPU interrupt routing is vendor-specific and affects real-time determinism:

| Source | Cyclone V HPS | Zynq-7000 | MPSoC | PolarFire SoC |
|---|---|---|---|---|
| FPGA → CPU IRQ | 64 IRQ inputs to GIC | 16 PL→PS IRQ lines | 128 PL→PS IRQ (GIC-400) | Direct to PLIC |
| CPU → FPGA | Software-generated IRQ via MMIO | 16 PS→PL IRQ lines | 4 × GIQ to PL | Via shared register |
| Priority | GIC (ARM Generic Interrupt Controller) | GIC-400 per-core | GIC-400 with affinity | RISC-V PLIC (53 priorities) |
| Real-time capable | Limited (shared GIC) | FIQ for one PL IRQ | Separate R5F NVIC for low-latency | U54 hart 0 for RT |

**Best practice:** Reserve a dedicated FIQ or high-priority PLIC entry for latency-critical FPGA interrupts (e.g., sample-ready from an ADC). Do not share with general-purpose Linux-handled interrupts.

---

## Boot Partitioning: Who Loads First?

Hard CPU and FPGA boot in a defined order that varies by vendor:

| Device | Boot Order | FPGA Config Method | Key Constraint |
|---|---|---|---|
| **Zynq-7000** | PS → PL | FSBL loads bitstream via PCAP | PL unconfigured until FSBL explicitly loads it |
| **Zynq MPSoC** | PMU → FSBL → PL | PMU firmware can load PL early | R5F can be up before PL is ready |
| **Cyclone V SoC** | HPS → FPGA | U-Boot SPL loads .rbf via FPP ×16 | FPGA config ~50–500 ms, HPS waits |
| **PolarFire SoC** | E51 monitor → MSS → Fabric | Auto-loads from eNVM at power-on | Fabric ready before Linux boots |

**Pattern:** If the hard CPU needs FPGA accelerators during boot, ensure the bitstream loads before the driver probes. Use U-Boot's `fpga load` command before `bootm`.

---

## Power Domain Interactions

Hard CPU and FPGA fabric often share power rails on the same die, creating thermal and power sequencing dependencies:

| Device | Power Domains | Sequencing | Thermal Coupling |
|---|---|---|---|
| **Zynq-7000** | PS (always on), PL (independent) | PS must be up first; PL can be powered down independently | Low — separate voltage regulators |
| **Zynq MPSoC** | LPD, FPD, PL (3 domains) | LPD → FPD → PL; PL can be isolated | Moderate — shared package |
| **Cyclone V SoC** | HPS + FPGA share VCC | Must power both; no independent shutdown | High — shared core rail |
| **PolarFire SoC** | MSS + Fabric separate | Fabric auto-configures from eNVM at power-on | Low — flash-based, no config SRAM |

**Thermal warning:** On Cyclone V SoC, if the FPGA fabric runs at 90% utilization with heavy switching, the shared die temperature rise can force the Cortex-A9 to throttle. Monitor `temp_sensor` output in Linux.

---

## DMA Architecture Between CPU and FPGA

| DMA Type | Direction | Mechanism | Typical Bandwidth |
|---|---|---|---|
| **CPU-initiated (MMIO)** | CPU → FPGA registers | `memcpy` or `ioremap` write via M_AXI_GP / H2F | 100–800 MB/s |
| **Scatter-gather DMA** | FPGA → DDR | FPGA DMA engine reads descriptor table from DDR, transfers data | 1.6–12.8 GB/s |
| **ACP DMA** | FPGA → CPU L2 | FPGA writes directly into L2 cache via ACP port | 0.8–3.2 GB/s |
| **Cache-coherent DMA** | Bidirectional | CCI-400/NoC ensures coherency automatically | 1.2–12.8 GB/s |

**When to use ACP vs HP:**
- ACP: FPGA writes small, frequently-accessed data structures that the CPU will read (e.g., status flags, ring buffer descriptors). Latency matters more than throughput.
- HP: FPGA streams large buffers to DDR that the CPU will process later (e.g., video frames, ADC samples). Throughput matters more than coherency.

---

## Debug Access to Hard CPU Subsystem

| Debug Task | Tool | Access Method |
|---|---|---|
| CPU register peek/poke | GDB via OpenOCD | JTAG → DAP → Cortex-A9 debug registers |
| FPGA register peek/poke | SignalTap / ILA | JTAG → FPGA TAP → internal logic |
| Shared DDR peek | GDB + `x/100x 0x10000000` | Via CPU load/store |
| Interrupt storm diagnosis | `/proc/interrupts` | Linux running on hard CPU |
| Bus bandwidth monitoring | Intel MPSec / Xilinx AXI Performance Monitor | Hardware counters on AXI interconnect |

---

## Best Practices

1. **Don't default to soft CPU if a hard one is available** — hard CPU saves ~2K LEs and runs at 4–8× the clock speed.
2. **Pair hard CPU + soft CPU** — MPSoC's dual R5F + quad A53 is the canonical pattern: real-time cores handle deterministic tasks, application cores run Linux.
3. **Soft CPU for debug/control, hard CPU for compute** — simple Nios II for JTAG UART + register peek/poke; hard Cortex-A9 for video processing.
4. **Consider RISC-V for open ISA** — PolarFire SoC's hard U54 cluster avoids ARM licensing concerns; see [PolarFire SoC IP](../../06_ip_and_cores/vendor_ip/microchip_ip.md)
5. **Use the vendor's BSP** — never write a custom boot loader from scratch; use Xilinx PetaLinux, Intel GSRD, or Microchip SoftConsole as your starting point

---

## Pitfalls

### 1. Hard CPU Clock Must Be Stable Before FPGA Access
On all SoC devices, the hard CPU must complete its PLL configuration and clock setup before the FPGA fabric can be accessed. If your FPGA logic tries to read HPS registers during early boot, the bridge may not be ready.

**Fix:** In your FPGA RTL, wait for a `fpga_mgr` or `h2f_reset` signal from the HPS before attempting any bridge transactions.

### 2. Soft CPU Cannot Run Linux Realistically
Soft CPUs run at 50–250 MHz with limited memory. Running Linux on a soft CPU is technically possible (VexRiscv with MMU) but performance is poor — expect 10–50× slower than a hard Cortex-A9.

**Fix:** Use soft CPUs for bare-metal control only. If you need Linux, use a device with a hard CPU.

### 3. PolarFire SoC RISC-V Boot is Complex
The 5-core RISC-V cluster requires a multi-stage boot (eNVM → E51 monitor → U54 cores → Linux). This is significantly more complex than ARM's single-stage U-Boot.

**Fix:** Use Microchip's Hart Software Services (HSS) and SoftConsole examples. Do not attempt to write a custom RISC-V boot loader.

---

## References

| Source | Path |
|---|---|
| Cyclone V SoC HPS TRM | Intel FPGA documentation |
| Zynq-7000 TRM (UG585) | AMD/Xilinx documentation |
| Zynq MPSoC TRM (UG1085) | AMD/Xilinx documentation |
| PolarFire SoC User Guide (UG0820) | Microchip documentation |
| Nios II Processor Reference Guide | Intel FPGA documentation |
| MicroBlaze Processor Reference Guide (UG984) | AMD/Xilinx documentation |
| [AXI Bridges & Interconnect](axi_bridges_and_interconnect.md) | This repository |
| [Memory Hierarchy](memory_hierarchy.md) | This repository |
| [Boot Architecture](boot_architecture.md) | This repository |
| [Soft Cores & SoC Design](../../11_soft_cores_and_soc_design/README.md) | This repository |
