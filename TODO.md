# TODO.md — FPGA Knowledge Base Build Plan

> Auto-generated plan. Update statuses as work progresses. See [AGENTS.md](AGENTS.md) for quality standards.
> **Last synced:** 2026-05-04 — Tier 4–7 + Legacy HDL deep dives complete. All gap analysis articles now at Deep tier quality.

---

## Phase 6: IP & Cores (`06_ip_and_cores/`)

| # | Task | File | Status |
|---|---|---|---|
| 6.1 | Chip-to-chip interfaces (PCIe, CXL, CCIX, UCIe) | `06_ip_and_cores/external_interfaces/chip_to_chip_interfaces.md` | COMPLETE |
| 6.2 | Parallel buses (68000, Zorro, ISA, PCI) | `06_ip_and_cores/external_interfaces/parallel_buses.md` | COMPLETE |
| 6.3 | High-speed serial interfaces — USB soft IP and hardened | `06_ip_and_cores/external_interfaces/high_speed_serial_interfaces.md` | COMPLETE |

## Phase 8 Additions (`08_debug_and_tools/`)

| # | Task | File | Status |
|---|---|---|---|
| 8.7 | Commercial JTAG / Boundary scan tools | `08_debug_and_tools/commercial_jtag_tools.md` | COMPLETE |

## Phase 16: Advanced Applications (`16_advanced_topics/`)

| # | Task | File | Status |
|---|---|---|---|
| 16.1 | Dynamic Function eXchange (DFX) | `16_advanced_topics/dfx_partial_reconfiguration.md` | COMPLETE |
| 16.2 | Hardware Acceleration (ML, Blockchain, Custom Algorithms) | `16_advanced_topics/hardware_acceleration.md` | COMPLETE |
| 16.3 | Advanced Networking & SmartNICs (DPDK/TOE) | `16_advanced_topics/networking_smartnics.md` | COMPLETE |
| 16.4 | Hardware Security & Trust (Secure Boot/PUF) | `16_advanced_topics/hardware_security.md` | COMPLETE |
| 16.5 | Advanced HLS Patterns & Optimization | `16_advanced_topics/advanced_hls_patterns.md` | COMPLETE |
| 16.6 | FPGA as a Service (FaaS) & Cloud | `16_advanced_topics/fpga_as_a_service.md` | COMPLETE |
| 16.7 | Compute Comparison: FPGA vs GPU vs TPU | `16_advanced_topics/fpga_vs_gpu_vs_tpu.md` | COMPLETE |


---

## Phase 13: Toolchain Deep Dives (`13_toolchains/`)

| # | Task | File | Status |
|---|---|---|---|
| 13.1 | Vivado — full build flow, Tcl scripting, debug, IP packaging | `13_toolchains/vivado.md` | COMPLETE |
| 13.2 | Quartus Prime — build flow, Tcl scripting, Platform Designer | `13_toolchains/quartus_prime.md` | COMPLETE |

## Phase 04: HLS Expansion (`04_hdl_and_synthesis/hls/`)

| # | Task | File | Status |
|---|---|---|---|
| 4.1 | HLS Overview — pragmas, synthesis flow, code examples | `04_hdl_and_synthesis/hls/hls_overview.md` | COMPLETE |

## Phase 07: Verification Deep Dives (`07_verification/`)

| # | Task | File | Status |
|---|---|---|---|
| 7.1 | UVM for FPGA — class hierarchy, testbench example, build/run | `07_verification/uvm_overview.md` | COMPLETE |
| 7.2 | Formal Verification — AXI protocol proof, JasperGold, multi-tool | `07_verification/formal_verification.md` | COMPLETE |
| 7.3 | Cocotb — real testbench examples, Makefile, sim integration | `07_verification/cocotb.md` | COMPLETE |
| 7.4 | Verilator — C++ testbench, tracing, coverage, linting, CI/CD | `07_verification/verilator.md` | COMPLETE |
| 7.5 | GHDL — VHDL-2008 sim, PSL, cocotb, Yosys synthesis | `07_verification/ghdl.md` | COMPLETE |

## Phase 09: Boards & Board Design Expansion (`09_boards_and_board_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 9.1 | Power Integrity — PDN tool walkthrough, multi-rail sequencing, simulation | `09_boards_and_board_design/power_integrity.md` | COMPLETE |
| 9.2 | High-Speed Signals — SI simulation, eye diagrams, loss budgets | `09_boards_and_board_design/high_speed_signals.md` | COMPLETE |

## Phase 11: SoC Design Expansion (`11_soft_cores_and_soc_design/soc_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 11.1 | DMA Architecture — register maps, descriptor formats, Linux API | `11_soft_cores_and_soc_design/soc_design/dma_architecture.md` | COMPLETE |
| 11.2 | Multi-Core Coherency — ACP vs CCI vs ACE, cache stashing | `11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md` | COMPLETE |
| 11.3 | Memory Map Design — address decoder patterns, AXI address filtering | `11_soft_cores_and_soc_design/soc_design/memory_map_design.md` | COMPLETE |
| 11.4 | Interrupt Routing — GIC, PLIC, NVIC, FPGA IRQ mapping | `11_soft_cores_and_soc_design/soc_design/interrupt_routing.md` | COMPLETE |

---

## Gap Analysis Results (2026-04-25)

### Thin Articles (< 80 lines, non-README) — Priority Tier 1 (Core Technical)

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| G.1 | Protocol Checkers — AXI/Avalon/WB VIPs and BFM | `07_verification/protocol_checkers.md` | 581 | COMPLETE |
| G.2 | Bus Matrix Design — topologies, arbitration | `11_soft_cores_and_soc_design/soc_design/bus_matrix_design.md` | 307 | COMPLETE |
| G.3 | RISC-V ISA — instruction set, extensions | `11_soft_cores_and_soc_design/riscv/riscv_isa.md` | 298 | COMPLETE |
| G.4 | RISC-V Privileged — modes, CSRs, Sv32/39 | `11_soft_cores_and_soc_design/riscv/riscv_privileged.md` | 264 | COMPLETE |
| G.5 | MicroBlaze — Xilinx soft core | `11_soft_cores_and_soc_design/vendor_soft/microblaze.md` | 235 | COMPLETE |
| G.6 | Nios II/V — Intel soft core | `11_soft_cores_and_soc_design/vendor_soft/nios_family.md` | 204 | COMPLETE |
| G.7 | Gowin EDA — toolchain | `13_toolchains/gowin_eda.md` | 210 | COMPLETE |
| G.8 | Diamond/Radiant — Lattice toolchain | `13_toolchains/diamond_radiant.md` | 210 | COMPLETE |
| G.9 | Open-Source Flow — Yosys + nextpnr + F4PGA | `13_toolchains/open_source_flow.md` | 317 | COMPLETE |
| G.10 | Common Failures — typical FPGA bugs | `15_case_studies/common_failures.md` | 229 | COMPLETE |

### Thin Articles — Priority Tier 2 (RISC-V Cores, 42–71 lines)

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| G.11 | VexRiscv — SpinalHDL Linux-capable core | `11_soft_cores_and_soc_design/riscv_cores/vexriscv.md` | 414 | COMPLETE |
| G.12 | PicoRV32 — minimal RISC-V | `11_soft_cores_and_soc_design/riscv_cores/picorv32.md` | 370 | COMPLETE |
| G.13 | NEORV32 — well-documented core | `11_soft_cores_and_soc_design/riscv_cores/neorv32.md` | 343 | COMPLETE |
| G.14 | SERV — bit-serial RISC-V | `11_soft_cores_and_soc_design/riscv_cores/serv.md` | 307 | COMPLETE |
| G.15 | Ibex/CV32E — OpenTitan core | `11_soft_cores_and_soc_design/riscv_cores/ibex_cv32e.md` | 326 | COMPLETE |
| G.16 | High-Perf RISC-V — BOOM/Rocket/CVA6 | `11_soft_cores_and_soc_design/riscv_cores/high_perf_riscv_cores.md` | 287 | COMPLETE |
| G.17 | Chipyard/Rocket Chip — SoC generators | `11_soft_cores_and_soc_design/soc_design/chipyard_rocket_chip.md` | 311 | COMPLETE |

### Thin Articles — Priority Tier 3 (Open HW, 42–65 lines)

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| G.18 | MiSTer — retro computing platform | `12_open_source_open_hardware/retro_computing/mister.md` | 446 | COMPLETE |
| G.19 | OSSC — open source scan converter | `12_open_source_open_hardware/video_display/ossc.md` | 290 | COMPLETE |
| G.20 | LiteX Core Ecosystem | `12_open_source_open_hardware/litex/litex_core_ecosystem.md` | 468 | COMPLETE |
| G.21 | OpenTitan — root of trust | `12_open_source_open_hardware/initiatives/opentitan.md` | 297 | COMPLETE |
| G.22 | LiteX Overview — Python SoC builder | `12_open_source_open_hardware/litex/litex_overview.md` | 517 | COMPLETE |

### Quality Issues Found

- 0 articles still contain `## Planned Content` / `## Original Stub Description` sections (down from 13)
- 0 broken cross-references detected in expanded articles
- All gap analysis articles are now at Deep tier quality — no stale stubs remain

### New Articles (2026-05-04)

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| N.1 | Arduino + FPGA Boards — MCU/FPGA hybrids | `09_boards_and_board_design/arduino_fpga_boards.md` | 472 | COMPLETE |

### Tier 4: Core Catalogs & Networking

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| T4.1 | RISC-V Cores Catalog | `12_open_source_open_hardware/cores_catalog/riscv_cores_catalog.md` | ~200 | COMPLETE |
| T4.2 | Ethernet Cores | `12_open_source_open_hardware/networking/ethernet_cores.md` | ~250 | COMPLETE |
| T4.3 | PCIe Cores | `12_open_source_open_hardware/networking/pcie_cores.md` | 234 | COMPLETE |
| T4.4 | Peripheral Core Catalog | `12_open_source_open_hardware/cores_catalog/peripheral_cores_catalog.md` | ~350 | COMPLETE |
| T4.5 | GPU Cores | `12_open_source_open_hardware/gpu_compute/gpu_cores.md` | ~220 | COMPLETE |
| T4.6 | ML Accelerators | `12_open_source_open_hardware/gpu_compute/ml_accelerators.md` | ~270 | COMPLETE |
| T4.7 | USB Cores | `12_open_source_open_hardware/networking/usb_cores.md` | ~260 | COMPLETE |

### Tier 5: Retro & Display

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| T5.1 | Analogue Pocket + openFPGA | `12_open_source_open_hardware/retro_computing/analogue_openfpga.md` | ~240 | COMPLETE |
| T5.2 | Display Cores (VGA/DVI/HDMI) | `12_open_source_open_hardware/video_display/display_cores.md` | ~310 | COMPLETE |
| T5.3 | RetroTINK & Open Scalers | `12_open_source_open_hardware/video_display/retrotink_and_scalers.md` | ~210 | COMPLETE |
| T5.4 | Other Retro Platforms | `12_open_source_open_hardware/retro_computing/other_retro_platforms.md` | ~220 | COMPLETE |
| T5.5 | MiST — Original Retro Platform | `12_open_source_open_hardware/retro_computing/mist.md` | ~220 | COMPLETE |

### Tier 6: Boards & Memory

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| T6.1 | Hobbyist & Dev Boards | `12_open_source_open_hardware/open_boards/hobbyist_boards.md` | ~200 | COMPLETE |
| T6.2 | High-End Boards | `09_boards_and_board_design/high_end_boards.md` | ~230 | COMPLETE |
| T6.3 | Repurposed Boards | `09_boards_and_board_design/repurposed_boards.md` | ~150 | COMPLETE |
| T6.4 | SDRAM Controllers | `12_open_source_open_hardware/memory_controllers/sdram_controllers.md` | ~230 | COMPLETE |
| T6.5 | DDR Controllers | `12_open_source_open_hardware/memory_controllers/ddr_controllers.md` | ~225 | COMPLETE |
| T6.6 | Specialized Memory | `12_open_source_open_hardware/memory_controllers/specialized_memory.md` | ~320 | COMPLETE |

### Tier 7: Initiatives

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| T7.1 | PULP Platform | `12_open_source_open_hardware/initiatives/pulp_platform.md` | ~150 | COMPLETE |
| T7.2 | FOSSi & CHIPS Alliance | `12_open_source_open_hardware/initiatives/fossi_chips_alliance.md` | ~140 | COMPLETE |
| T7.3 | Open-Source EDA Tooling | `12_open_source_open_hardware/initiatives/open_source_eda.md` | ~190 | COMPLETE |

### Legacy HDL

| # | Task | File | Lines | Status |
|---|---|---|---|---|
| L.1 | ABEL | `04_hdl_and_synthesis/legacy_hdl/abel.md` | ~140 | COMPLETE |
| L.2 | AHDL | `04_hdl_and_synthesis/legacy_hdl/ahdl.md` | ~140 | COMPLETE |
| L.3 | PALASM | `04_hdl_and_synthesis/legacy_hdl/palasm.md` | ~160 | COMPLETE |

---

## Legend

| Symbol | Meaning |
|---|---|
| PENDING | File does not exist; not started |
| STUB | File exists — outline only, needs expansion |
| EXPAND | File exists with content (50–100 lines) — needs deeper coverage, code examples, verified references |
| IN PROGRESS | Currently writing / expanding |
| COMPLETE | Written with substantial content (50+ lines), reviewed |
| BLOCKED | Waiting on dependency |
