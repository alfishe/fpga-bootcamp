# TODO.md — FPGA Knowledge Base Build Plan

> Auto-generated plan. Update statuses as work progresses. See [AGENTS.md](AGENTS.md) for quality standards.
> **Last synced:** 2026-04-25 — matched against actual filesystem content.

---

## Phase 0: Overview (`00_overview/`)

| # | Task | File | Status |
|---|---|---|---|
| 0.1 | FPGA market landscape | `00_overview/landscape.md` | ✅ COMPLETE |
| 0.2 | History of FPGA technology | `00_overview/history.md` | ✅ COMPLETE |
| 0.3 | Process technology nodes | `00_overview/technology_nodes.md` | ✅ COMPLETE |
| 0.4 | Vendor comparison matrix | `00_overview/vendor_comparison.md` | ✅ COMPLETE |

## Phase 1: Architecture (`02_architecture/`)

| # | Task | File | Status |
|---|---|---|---|
| 1.1 | LUTs & CLBs across vendors | `02_architecture/fabric/luts_and_clbs.md` | ✅ COMPLETE |
| 1.2 | BRAM & URAM deep dive | `02_architecture/fabric/bram_and_uram.md` | ✅ COMPLETE |
| 1.3 | DSP slices (DSP48/DSP58) | `02_architecture/fabric/dsp_slices.md` | ✅ COMPLETE |
| 1.4 | Routing & interconnect | `02_architecture/fabric/routing.md` | ✅ COMPLETE |
| 1.5 | Clocking (PLL/MMCM/DCM) | `02_architecture/infrastructure/clocking.md` | ✅ COMPLETE |
| 1.6 | IO standards & SERDES | `02_architecture/infrastructure/io_standards.md` | ✅ COMPLETE |
| 1.7 | Configuration & bitstream | `02_architecture/infrastructure/configuration.md` | ✅ COMPLETE |
| 1.8 | SoC architecture overview | `02_architecture/soc/README.md` | ✅ COMPLETE |
| 1.9 | Hard processor integration (generic) | `02_architecture/soc/hard_processor_integration.md` | ✅ COMPLETE |
| 1.10 | AXI bridges & interconnect (generic) | `02_architecture/soc/axi_bridges_and_interconnect.md` | ✅ COMPLETE |
| 1.11 | Memory hierarchy | `02_architecture/soc/memory_hierarchy.md` | ✅ COMPLETE |
| 1.12 | Boot architecture | `02_architecture/soc/boot_architecture.md` | ✅ COMPLETE |
| 1.13 | Intel HPS-FPGA deep dive | `02_architecture/soc/hps_fpga_intel_soc.md` | ✅ COMPLETE |
| 1.14 | Xilinx PS-PL deep dive | `02_architecture/soc/hps_fpga_xilinx_zynq.md` | ✅ COMPLETE |
| 1.15 | Microchip MSS-Fabric deep dive | `02_architecture/soc/hps_fpga_microchip_soc.md` | ✅ COMPLETE |
| 1.16 | CPLD architecture & macrocells | `02_architecture/cpld/cpld_architecture.md` | ✅ COMPLETE |
| 1.17 | Intel MAX family (MAX V, MAX 10) | `02_architecture/cpld/intel_max_family.md` | ✅ COMPLETE |
| 1.18 | CPLD vs FPGA: when to use which | `02_architecture/cpld/cpld_vs_fpga.md` | ✅ COMPLETE |
| 1.19 | Non-volatile programmable logic | `02_architecture/cpld/non_volatile_logic.md` | ✅ COMPLETE |
| 1.20 | Hybrid: RF direct sampling (RFSoC) | `02_architecture/hybrid/rf_direct_sampling.md` | ⏳ STUB |
| 1.21 | Hybrid: AI Engine arrays (Versal) | `02_architecture/hybrid/ai_engine_arrays.md` | ⏳ STUB |
| 1.22 | Hybrid: HBM integration | `02_architecture/hybrid/hbm_integration.md` | ⏳ STUB |

## Phase 2: Design Flow (`03_design_flow/`)

| # | Task | File | Status |
|---|---|---|---|
| 2.1 | End-to-end flow overview | `03_design_flow/overview.md` | ✅ COMPLETE |
| 2.2 | Project structure & revision control | `03_design_flow/project_structure.md` | ✅ COMPLETE |
| 2.3 | Synthesis deep dive | `03_design_flow/synthesis.md` | ✅ COMPLETE |
| 2.4 | Netlist formats & fundamentals | `03_design_flow/netlist.md` | ✅ COMPLETE |
| 2.5 | Place & route | `03_design_flow/place_and_route.md` | ✅ COMPLETE |
| 2.6 | Bitstream generation | `03_design_flow/bitstream.md` | ✅ COMPLETE |
| 2.7 | Floorplanning | `03_design_flow/floorplanning.md` | ✅ COMPLETE |

## Phase 3: Vendors & Families (`01_vendors_and_families/`)

| # | Task | File | Status |
|---|---|---|---|
| 3.1 | Intel/Altera families (Cyclone V anchor) | `01_vendors_and_families/altera_intel/` | 🔄 IN PROGRESS |
| 3.2 | Xilinx families (7series, US+, Versal) | `01_vendors_and_families/xilinx/` | ⏳ STUB |
| 3.3 | Lattice families (ECP5, iCE40, CertusPro, CrossLink) | `01_vendors_and_families/lattice/` | ⏳ STUB |
| 3.4 | Microchip families (PolarFire, SmartFusion2) | `01_vendors_and_families/microchip/` | ⏳ STUB |
| 3.5 | Gowin families (LittleBee, Arora) | `01_vendors_and_families/gowin/` | ⏳ STUB |
| 3.6 | Other vendors (Achronix, Efinix, QuickLogic, etc.) | `01_vendors_and_families/others/` | ⏳ STUB |

### 3.1.1: Cyclone V Anchor Deep Dives

| # | Task | File | Status |
|---|---|---|---|
| 3.1.1 | Cyclone V SoC overview (HPS + bridges, variants, boot) | `cyclone_v/soc/README.md` | ✅ COMPLETE |
| 3.1.2 | HPS-FPGA interaction comprehensive guide (all 8 methods, bandwidth, decision matrix) | `cyclone_v/soc/hps_fpga_interaction.md` | ✅ COMPLETE |
| 3.1.3 | HPS-FPGA address map deep dive | `cyclone_v/soc/address_map.md` | ⬜ PENDING |
| 3.1.4 | Boot sequence deep dive (ROM → Linux, FPGA config via FPP) | `cyclone_v/soc/boot_sequence.md` | ⬜ PENDING |
| 3.1.5 | Transceivers deep dive (GX/GT variants) | `cyclone_v/fpga_only/transceivers.md` | ⬜ PENDING |
| 3.1.6 | Cyclone V SoC vs Zynq-7000 comparative analysis | `cyclone_v/vs_zynq7000.md` | ⬜ PENDING |
| 3.1.7 | MiSTer platform specifics | `cyclone_v/soc/mister_platform.md` | ⬜ PENDING |

### Also needed — other vendor SoC deep dives

| # | Task | File | Status |
|---|---|---|---|
| 3.2.1 | Xilinx Zynq-7000 SoC deep dive | `xilinx/7series/soc/` | ⬜ PENDING |
| 3.2.2 | Xilinx MPSoC deep dive | `xilinx/ultrascale_plus/soc/` | ⬜ PENDING |
| 3.4.1 | Microchip PolarFire SoC deep dive | `microchip/polarfire/soc/` | ⬜ PENDING |

## Phase 4: HDL & Synthesis (`04_hdl_and_synthesis/`)

| # | Task | File | Status |
|---|---|---|---|
| 4.1 | Verilog: origins, history, standards, philosophy | `04_hdl_and_synthesis/verilog_sv/verilog.md` | ✅ COMPLETE |
| 4.2 | SystemVerilog: lineage, design+verification, UVM, IEEE 1800 | `04_hdl_and_synthesis/verilog_sv/systemverilog.md` | ✅ COMPLETE |
| 4.3 | VHDL: VHSIC origins, strong typing, IEEE 1076, verification | `04_hdl_and_synthesis/vhdl/vhdl_basics.md` | ✅ COMPLETE |
| 4.4 | Inference rules (flop vs latch, RAM, ROM, DSP, SRL, MUX) | `04_hdl_and_synthesis/inference_rules.md` | ✅ COMPLETE |
| 4.5 | Vendor pragmas (Xilinx/Intel/Gowin/Synplify attribute reference) | `04_hdl_and_synthesis/vendor_pragmas.md` | ✅ COMPLETE |
| 4.6 | CDC patterns (metastability, 2-FF, pulse sync, Gray code, async FIFO, MCP) | `04_hdl_and_synthesis/cdc_coding.md` | ✅ COMPLETE |
| 4.7 | FSM design (encoding, Moore/Mealy, reset, safe recovery) | `04_hdl_and_synthesis/state_machines.md` | ✅ COMPLETE |
| 4.8 | HLS overview (C-to-gates, Vivado HLS, Vitis, Intel HLS, Bambu) | `04_hdl_and_synthesis/hls/hls_overview.md` | ⏳ STUB |
| 4.9 | Legacy HDLs: ABEL, AHDL, PALASM | `04_hdl_and_synthesis/legacy_hdl/` | ⏳ STUB |

## Phase 5: Timing & Constraints (`05_timing_and_constraints/`)

| # | Task | File | Status |
|---|---|---|---|
| 5.1 | SDC/XDC/QSF basics | `05_timing_and_constraints/sdc_basics.md` | ✅ COMPLETE |
| 5.2 | Clock domain crossing | `05_timing_and_constraints/clock_domain_crossing.md` | ✅ COMPLETE |
| 5.3 | False paths | `05_timing_and_constraints/false_paths.md` | ✅ COMPLETE |
| 5.4 | Multicycle paths | `05_timing_and_constraints/multicycle_paths.md` | ✅ COMPLETE |
| 5.5 | Timing closure methodology | `05_timing_and_constraints/timing_closure.md` | ✅ COMPLETE |
| 5.6 | IO timing | `05_timing_and_constraints/io_timing.md` | ✅ COMPLETE |

## Phase 6: IP & Cores (`06_ip_and_cores/`)

| # | Task | File | Status |
|---|---|---|---|
| 6.1 | Bus protocols: AXI4 family deep dive | `06_ip_and_cores/bus_protocols/axi4_family.md` | ✅ COMPLETE |
| 6.2 | Bus protocols: Wishbone, Avalon, APB, TileLink | `06_ip_and_cores/bus_protocols/other_buses.md` | ✅ COMPLETE |
| 6.3 | DDR: Intel DDR controllers | `06_ip_and_cores/ddr/intel_ddr.md` | ✅ COMPLETE |
| 6.4 | DDR: Xilinx DDR controllers (MIG) | `06_ip_and_cores/ddr/xilinx_ddr.md` | ✅ COMPLETE |
| 6.5 | DDR: Lattice & others DDR | `06_ip_and_cores/ddr/lattice_others_ddr.md` | ✅ COMPLETE |
| 6.6 | DDR: Pin planning & timing | `06_ip_and_cores/ddr/ddr_pin_planning.md` | ✅ COMPLETE |
| 6.7 | Interconnect: AXI crossbar, width/data converters | `06_ip_and_cores/interconnect/` | ✅ COMPLETE |
| 6.8 | PCIe: Hard blocks, configuration, DMA | `06_ip_and_cores/pcie/` | ✅ COMPLETE |
| 6.9 | Vendor IP ecosystems (Intel, Xilinx, Lattice, Microchip, Gowin) | `06_ip_and_cores/vendor_ip/` | ⏳ STUB |
| 6.10 | Transceivers: basics, IP usage, protocol support | `06_ip_and_cores/transceivers/` | ⏳ STUB |
| 6.11 | Other hard IP: Ethernet MAC, signal processing, video/audio | `06_ip_and_cores/other_hard_ip/` | ⏳ STUB |
| 6.12 | IP reuse: FuseSoC, Intel/Xilinx packaging, licensing | `06_ip_and_cores/ip_reuse/` | ⏳ STUB |

## Phase 7: Verification (`07_verification/`)

| # | Task | File | Status |
|---|---|---|---|
| 7.1 | Simulation tools overview | `07_verification/simulation_overview.md` | ✅ COMPLETE |
| 7.2 | Testbench patterns & methodology | `07_verification/testbench_patterns.md` | ✅ COMPLETE |
| 7.3 | SystemVerilog verification primitives (SVA, coverage, constrained-random) | `07_verification/sv_verification.md` | ✅ COMPLETE |
| 7.4 | Co-simulation (DPI-C, MATLAB, QEMU+SystemC, VHDL+SV mixing) | `07_verification/co_simulation.md` | ✅ COMPLETE |
| 7.5 | Formal verification (SymbiYosys) | `07_verification/formal_verification.md` | ⏳ STUB |
| 7.6 | cocotb Python testbenches | `07_verification/cocotb.md` | ⏳ STUB |
| 7.7 | UVM overview | `07_verification/uvm_overview.md` | ⏳ STUB |
| 7.8 | Protocol checkers & BFMs | `07_verification/protocol_checkers.md` | ⏳ STUB |

## Phase 8: Debug & Tools (`08_debug_and_tools/`)

| # | Task | File | Status |
|---|---|---|---|
| 8.1 | ILA vs SignalTap | `08_debug_and_tools/ila_signaltap.md` | ⏳ STUB |
| 8.2 | OpenOCD & JTAG setup | `08_debug_and_tools/openocd.md` | ⏳ STUB |
| 8.3 | JTAG boundary scan | `08_debug_and_tools/jtag_boundary_scan.md` | ⏳ STUB |
| 8.4 | Logic analyzers | `08_debug_and_tools/logic_analyzers.md` | ⏳ STUB |
| 8.5 | Remote debugging (GDB/kgdb) | `08_debug_and_tools/remote_debugging.md` | ⏳ STUB |
| 8.6 | Tcl scripting automation | `08_debug_and_tools/tcl_scripting.md` | ⏳ STUB |

## Phase 9: Board Design (`09_board_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 9.1 | High-speed signal integrity | `09_board_design/high_speed_signals.md` | ⏳ STUB |
| 9.2 | Power integrity & PDN | `09_board_design/power_integrity.md` | ⏳ STUB |
| 9.3 | BGA escape routing | `09_board_design/bga_routing.md` | ⏳ STUB |
| 9.4 | Thermal design | `09_board_design/thermal_design.md` | ⏳ STUB |
| 9.5 | Configuration interfaces | `09_board_design/configuration_interfaces.md` | ⏳ STUB |

## Phase 10: Embedded Linux (`10_embedded_linux/`)

| # | Task | File | Status |
|---|---|---|---|
| 10.1 | SoC Linux architecture overview | `10_embedded_linux/soc_linux_architecture.md` | ✅ COMPLETE |
| 10.2 | Boot flow — vendor-agnostic common | `10_embedded_linux/boot_flow.md` | ✅ COMPLETE |
| 10.3 | Boot flow — Intel SoC deep dive | `10_embedded_linux/boot_flow_intel_soc.md` | ✅ COMPLETE |
| 10.4 | Boot flow — Xilinx Zynq deep dive | `10_embedded_linux/boot_flow_xilinx_zynq.md` | ✅ COMPLETE |
| 10.5 | Boot flow — Microchip SoC deep dive | `10_embedded_linux/boot_flow_microchip_soc.md` | ✅ COMPLETE |
| 10.6 | HPS-FPGA bridges — vendor-agnostic overview | `10_embedded_linux/hps_fpga_bridges.md` | ✅ COMPLETE |
| 10.6a | HPS-FPGA bridges — Intel SoC deep dive | `10_embedded_linux/hps_fpga_bridges_intel_soc.md` | ✅ COMPLETE |
| 10.6b | HPS-FPGA bridges — Xilinx Zynq deep dive | `10_embedded_linux/hps_fpga_bridges_xilinx_zynq.md` | ✅ COMPLETE |
| 10.6c | HPS-FPGA bridges — Microchip SoC deep dive | `10_embedded_linux/hps_fpga_bridges_microchip_soc.md` | ✅ COMPLETE |
| 10.7 | Device tree & overlays | `10_embedded_linux/device_tree_and_overlays.md` | ✅ COMPLETE |
| 10.8 | Kernel drivers & DMA | `10_embedded_linux/kernel_drivers_and_dma.md` | ✅ COMPLETE |
| 10.9 | Build systems & OTA updates | `10_embedded_linux/build_and_update.md` | ✅ COMPLETE |
| 10.10 | Embedded Linux overview (alternate) | `10_embedded_linux/overview.md` | ⏳ STUB |
| 10.11 | U-Boot deep dive | `10_embedded_linux/uboot.md` | ⏳ STUB |

## Phase 11: Soft Cores & SoC Design (`11_soft_cores_and_soc_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 11.1 | RISC-V ISA: RV32I/RV64I, extensions | `11_soft_cores_and_soc_design/riscv/riscv_isa.md` | ⏳ STUB |
| 11.2 | RISC-V privileged: M/S/U modes, CSRs, PMP | `11_soft_cores_and_soc_design/riscv/riscv_privileged.md` | ⏳ STUB |
| 11.3 | MicroBlaze / MicroBlaze-V (Xilinx) | `11_soft_cores_and_soc_design/vendor_soft/microblaze.md` | ⏳ STUB |
| 11.4 | Nios II / Nios V (Intel) | `11_soft_cores_and_soc_design/vendor_soft/nios_family.md` | ⏳ STUB |
| 11.5 | VexRiscv (SpinalHDL, MMU, Linux) | `11_soft_cores_and_soc_design/riscv_cores/vexriscv.md` | ⏳ STUB |
| 11.6 | PicoRV32 (minimal RV32IMC) | `11_soft_cores_and_soc_design/riscv_cores/picorv32.md` | ⏳ STUB |
| 11.7 | NEORV32 (best docs, integrated SoC) | `11_soft_cores_and_soc_design/riscv_cores/neorv32.md` | ⏳ STUB |
| 11.8 | SERV (bit-serial, smallest RISC-V) | `11_soft_cores_and_soc_design/riscv_cores/serv.md` | ⏳ STUB |
| 11.9 | Ibex / CV32E40P (OpenTitan) | `11_soft_cores_and_soc_design/riscv_cores/ibex_cv32e.md` | ⏳ STUB |
| 11.10 | High-perf RISC-V survey (BOOM, Rocket, CVA6, XiangShan) | `11_soft_cores_and_soc_design/riscv_cores/high_perf_riscv_cores.md` | ⏳ STUB |
| 11.11 | Other ISA soft cores (SPARC, OpenRISC, POWER9, MIPS, MSP430, Z80/6502/68000) | `11_soft_cores_and_soc_design/other_isa/other_isa_cores.md` | ⏳ STUB |
| 11.12 | Bus matrix design | `11_soft_cores_and_soc_design/soc_design/bus_matrix_design.md` | ⏳ STUB |
| 11.13 | Memory map planning | `11_soft_cores_and_soc_design/soc_design/memory_map_design.md` | ⏳ STUB |
| 11.14 | Interrupt routing | `11_soft_cores_and_soc_design/soc_design/interrupt_routing.md` | ⏳ STUB |
| 11.15 | DMA architecture | `11_soft_cores_and_soc_design/soc_design/dma_architecture.md` | ⏳ STUB |
| 11.16 | Rocket Chip / Chipyard | `11_soft_cores_and_soc_design/soc_design/chipyard_rocket_chip.md` | ⏳ STUB |
| 11.17 | Multi-core coherency | `11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md` | ⏳ STUB |

## Phase 12: Open Source & Open Hardware (`12_open_source_open_hardware/`)

| # | Task | File | Status |
|---|---|---|---|
| 12.1 | Retro computing: MiSTer platform | `12_open_source_open_hardware/retro_computing/mister.md` | ⏳ STUB |
| 12.2 | Retro computing: MiST platform | `12_open_source_open_hardware/retro_computing/mist.md` | ⏳ STUB |
| 12.3 | Retro computing: Analogue OpenFPGA | `12_open_source_open_hardware/retro_computing/analogue_openfpga.md` | ⏳ STUB |
| 12.4 | Retro computing: other platforms | `12_open_source_open_hardware/retro_computing/other_retro_platforms.md` | ⏳ STUB |
| 12.5 | Open boards: hobbyist (TinyFPGA, OrangeCrab, ULX3S) | `12_open_source_open_hardware/open_boards/hobbyist_boards.md` | ⏳ STUB |
| 12.6 | Open boards: high-end (Alveo, NetFPGA) | `12_open_source_open_hardware/open_boards/high_end_boards.md` | ⏳ STUB |
| 12.7 | Open boards: repurposed (DE10-Nano, Arty) | `12_open_source_open_hardware/open_boards/repurposed_boards.md` | ⏳ STUB |
| 12.8 | Core catalogs: RISC-V cores | `12_open_source_open_hardware/cores_catalog/riscv_cores_catalog.md` | ⏳ STUB |
| 12.9 | Core catalogs: other ISA cores | `12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md` | ⏳ STUB |
| 12.10 | Core catalogs: peripheral cores | `12_open_source_open_hardware/cores_catalog/peripheral_cores_catalog.md` | ⏳ STUB |
| 12.11 | Memory controllers: DDR, SDRAM, specialized | `12_open_source_open_hardware/memory_controllers/` | ⏳ STUB |
| 12.12 | Video & display: OSSC, RetroTINK, display cores | `12_open_source_open_hardware/video_display/` | ⏳ STUB |
| 12.13 | Networking: Ethernet cores, USB, PCIe open | `12_open_source_open_hardware/networking/` | ⏳ STUB |
| 12.14 | GPU compute & ML accelerators | `12_open_source_open_hardware/gpu_compute/` | ⏳ STUB |
| 12.15 | Initiatives: OpenTitan, PULP, FOSSi, CHIPS Alliance | `12_open_source_open_hardware/initiatives/` | ⏳ STUB |
| 12.16 | LiteX: overview, core ecosystem, SoC builder | `12_open_source_open_hardware/litex/` | ⏳ STUB |

## Phase 13: Toolchains (`13_toolchains/`)

| # | Task | File | Status |
|---|---|---|---|
| 13.1 | Vivado | `13_toolchains/vivado.md` | ⏳ STUB |
| 13.2 | Quartus Prime | `13_toolchains/quartus_prime.md` | ⏳ STUB |
| 13.3 | Lattice Diamond/Radiant | `13_toolchains/diamond_radiant.md` | ⏳ STUB |
| 13.4 | Gowin EDA | `13_toolchains/gowin_eda.md` | ⏳ STUB |
| 13.5 | Open-source flow (Yosys/nextpnr) | `13_toolchains/open_source_flow.md` | ⏳ STUB |
| 13.6 | CI/CD for hardware | `13_toolchains/cicd_hardware.md` | ⏳ STUB |
| 13.7 | HLS overview | `13_toolchains/hls_overview.md` | ⏳ STUB |

## Phase 14: References (`14_references/`)

| # | Task | File | Status |
|---|---|---|---|
| 14.1 | Command cheatsheet | `14_references/command_cheatsheet.md` | ⏳ STUB |
| 14.2 | Pinout tables | `14_references/pinout_tables.md` | ⏳ STUB |
| 14.3 | Register map template | `14_references/register_map_template.md` | ⏳ STUB |
| 14.4 | Constraint quick-reference | `14_references/constraint_quickref.md` | ⏳ STUB |
| 14.5 | Error codes & resolution | `14_references/error_codes.md` | ⏳ STUB |

## Phase 15: Case Studies (`15_case_studies/`)

| # | Task | File | Status |
|---|---|---|---|
| 15.1 | Board bring-up checklist | `15_case_studies/bring_up_checklist.md` | ⏳ STUB |
| 15.2 | Debugging DDR failures | `15_case_studies/debugging_ddr.md` | ⏳ STUB |
| 15.3 | PCIe bringup | `15_case_studies/pcie_bringup.md` | ⏳ STUB |
| 15.4 | LiteX SoC build | `15_case_studies/litex_soc_build.md` | ⏳ STUB |
| 15.5 | Common failure modes | `15_case_studies/common_failures.md` | ⏳ STUB |

---

## Summary

| Phase | Name | Total | Complete | Stubs | Pending |
|---|---|---|---|---|---|
| 0 | Overview | 4 | 4 | 0 | 0 |
| 1 | Architecture | 22 | 19 | 3 | 0 |
| 2 | Design Flow | 7 | 7 | 0 | 0 |
| 3 | Vendors & Families | 10 | 2 | 6 | 5 (anchor deep-dives) |
| 4 | HDL & Synthesis | 9 | 7 | 2 | 0 |
| 5 | Timing | 6 | 6 | 0 | 0 |
| 6 | IP & Cores | 12 | 8 | 4 | 0 |
| 7 | Verification | 8 | 4 | 4 | 0 |
| 8 | Debug & Tools | 6 | 0 | 6 | 0 |
| 9 | Board Design | 5 | 0 | 5 | 0 |
| 10 | Embedded Linux | 13 | 11 | 2 | 0 |
| 11 | Soft Cores & SoC Design | 17 | 0 | 17 | 0 |
| 12 | Open Source & Hardware | 16 | 0 | 16 | 0 |
| 13 | Toolchains | 7 | 0 | 7 | 0 |
| 14 | References | 5 | 0 | 5 | 0 |
| 15 | Case Studies | 5 | 0 | 5 | 0 |
| **Total** | | **152** | **68 (45%)** | **79 (52%)** | **5 (3%)** |

## Cross-Cutting Tasks

| # | Task | Status |
|---|---|---|
| X.1 | Factual verification: Intel SoC CPU specs | ✅ COMPLETE |
| X.2 | Factual verification: MAX 10 classification | ✅ COMPLETE |
| X.3 | Factual verification: Zynq-7000 AXI port counts | ✅ COMPLETE |
| X.4 | Documentation map: root README.md updated with all sections | ✅ COMPLETE |
| X.5 | Consistency check: cross-links between common + sub-articles | ✅ COMPLETE |
| X.6 | Index maintenance: all README.md files point to correct articles | ✅ COMPLETE |

---

## Legend

| Symbol | Meaning |
|---|---|
| ⬜ PENDING | File does not exist; not started |
| ⏳ STUB | File exists (9–15 lines) — outline only, needs expansion |
| 🔄 IN PROGRESS | Currently writing / expanding |
| ✅ COMPLETE | Written with substantial content (50+ lines), reviewed |
| ⏸️ BLOCKED | Waiting on dependency |
