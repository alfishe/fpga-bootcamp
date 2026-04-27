# TODO.md — FPGA Knowledge Base Build Plan

> Auto-generated plan. Update statuses as work progresses. See [AGENTS.md](AGENTS.md) for quality standards.

---

## Phase 0: Overview (`00_overview/`)

| # | Task | File | Status |
|---|---|---|---|
| 0.1 | FPGA market landscape | `00_overview/landscape.md` | ✅ COMPLETE |
| 0.2 | History of FPGA technology | `00_overview/history.md` | ✅ COMPLETE |
| 0.3 | Process technology nodes | `00_overview/technology_nodes.md` | ✅ COMPLETE |
| 0.4 | Vendor comparison matrix | `00_overview/vendor_comparison.md` | ⬜ PENDING |

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
| 3.2 | Xilinx families | `01_vendors_and_families/xilinx/` | ⬜ PENDING |
| 3.3 | Lattice families | `01_vendors_and_families/lattice/` | ⬜ PENDING |
| 3.4 | Microchip families | `01_vendors_and_families/microchip/` | ⬜ PENDING |
| 3.5 | Gowin families | `01_vendors_and_families/gowin/` | ⬜ PENDING |
| 3.6 | Other vendors | `01_vendors_and_families/others/` | ⬜ PENDING |

### 3.1.1: Cyclone V Anchor Deep Dive

| # | Task | File | Status |
|---|---|---|---|
| 3.1.1 | HPS-FPGA address map | `cyclone_v/soc/address_map.md` | ⬜ PENDING |
| 3.1.2 | Boot sequence (ROM → Linux) | `cyclone_v/soc/boot_sequence.md` | ⬜ PENDING |
| 3.1.3 | Transceivers deep dive (GX/GT) | `cyclone_v/fpga_only/transceivers.md` | ⬜ PENDING |
| 3.1.4 | Cyclone V vs Zynq-7000 | `cyclone_v/vs_zynq7000.md` | ⬜ PENDING |
| 3.1.5 | MiSTer platform specifics | `cyclone_v/soc/mister_platform.md` | ⬜ PENDING |

## Phase 4: HDL & Synthesis (`04_hdl_and_synthesis/`)

| # | Task | File | Status |
|---|---|---|---|
| 4.1 | Verilog basics for synthesis | `04_hdl_and_synthesis/verilog_basics.md` | ⬜ PENDING |
| 4.2 | SystemVerilog synthesis | `04_hdl_and_synthesis/systemverilog_synthesis.md` | ⬜ PENDING |
| 4.3 | VHDL basics | `04_hdl_and_synthesis/vhdl_basics.md` | ⬜ PENDING |
| 4.4 | Inference rules | `04_hdl_and_synthesis/inference_rules.md` | ⬜ PENDING |
| 4.5 | Vendor pragmas | `04_hdl_and_synthesis/vendor_pragmas.md` | ⬜ PENDING |
| 4.6 | CDC coding patterns | `04_hdl_and_synthesis/cdc_coding.md` | ⬜ PENDING |
| 4.7 | State machines | `04_hdl_and_synthesis/state_machines.md` | ⬜ PENDING |

## Phase 5: Timing & Constraints (`05_timing_and_constraints/`)

| # | Task | File | Status |
|---|---|---|---|
| 5.1 | SDC/XDC/QSF basics | `05_timing_and_constraints/sdc_basics.md` | ⬜ PENDING |
| 5.2 | Clock domain crossing | `05_timing_and_constraints/clock_domain_crossing.md` | ⬜ PENDING |
| 5.3 | False paths | `05_timing_and_constraints/false_paths.md` | ⬜ PENDING |
| 5.4 | Multicycle paths | `05_timing_and_constraints/multicycle_paths.md` | ⬜ PENDING |
| 5.5 | Timing closure methodology | `05_timing_and_constraints/timing_closure.md` | ⬜ PENDING |
| 5.6 | IO timing | `05_timing_and_constraints/io_timing.md` | ⬜ PENDING |

## Phase 6: IP & Cores (`06_ip_and_cores/`)

| # | Task | File | Status |
|---|---|---|---|
| 6.1 | Bus protocols (AXI4/Wishbone/Avalon) | `06_ip_and_cores/bus_protocols/` | ⬜ PENDING |
| 6.2 | Vendor IP ecosystems | `06_ip_and_cores/vendor_ip/` | ⬜ PENDING |
| 6.3 | Interconnect deep dive | `06_ip_and_cores/interconnect/` | ⬜ PENDING |
| 6.4 | DDR controllers | `06_ip_and_cores/ddr/` | ⬜ PENDING |
| 6.5 | PCIe hard blocks | `06_ip_and_cores/pcie/` | ⬜ PENDING |
| 6.6 | Transceivers | `06_ip_and_cores/transceivers/` | ⬜ PENDING |
| 6.7 | Other hard IP | `06_ip_and_cores/other_hard_ip/` | ⬜ PENDING |
| 6.8 | IP reuse & packaging | `06_ip_and_cores/ip_reuse/` | ⬜ PENDING |

## Phase 7: Verification (`07_verification/`)

| # | Task | File | Status |
|---|---|---|---|
| 7.1 | Simulation overview | `07_verification/simulation_overview.md` | ⬜ PENDING |
| 7.2 | Testbench patterns | `07_verification/testbench_patterns.md` | ⬜ PENDING |
| 7.3 | Formal verification (SymbiYosys) | `07_verification/formal_verification.md` | ⬜ PENDING |
| 7.4 | cocotb Python testbenches | `07_verification/cocotb.md` | ⬜ PENDING |
| 7.5 | UVM overview | `07_verification/uvm_overview.md` | ⬜ PENDING |
| 7.6 | Protocol checkers & BFMs | `07_verification/protocol_checkers.md` | ⬜ PENDING |

## Phase 8: Debug & Tools (`08_debug_and_tools/`)

| # | Task | File | Status |
|---|---|---|---|
| 8.1 | ILA vs SignalTap | `08_debug_and_tools/ila_signaltap.md` | ⬜ PENDING |
| 8.2 | OpenOCD & JTAG | `08_debug_and_tools/openocd.md` | ⬜ PENDING |
| 8.3 | JTAG boundary scan | `08_debug_and_tools/jtag_boundary_scan.md` | ⬜ PENDING |
| 8.4 | Logic analyzers | `08_debug_and_tools/logic_analyzers.md` | ⬜ PENDING |
| 8.5 | Remote debugging (GDB/kgdb) | `08_debug_and_tools/remote_debugging.md` | ⬜ PENDING |
| 8.6 | Tcl scripting automation | `08_debug_and_tools/tcl_scripting.md` | ⬜ PENDING |

## Phase 9: Board Design (`09_board_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 9.1 | High-speed signal integrity | `09_board_design/high_speed_signals.md` | ⬜ PENDING |
| 9.2 | Power integrity & PDN | `09_board_design/power_integrity.md` | ⬜ PENDING |
| 9.3 | BGA escape routing | `09_board_design/bga_routing.md` | ⬜ PENDING |
| 9.4 | Thermal design | `09_board_design/thermal_design.md` | ⬜ PENDING |
| 9.5 | Configuration interfaces | `09_board_design/configuration_interfaces.md` | ⬜ PENDING |

## Phase 10: Embedded Linux (`10_embedded_linux/`)

| # | Task | File | Status |
|---|---|---|---|
| 10.1 | SoC Linux architecture overview | `10_embedded_linux/soc_linux_architecture.md` | ⬜ PENDING |
| 10.2 | Boot flow — vendor-agnostic common | `10_embedded_linux/boot_flow.md` | ✅ COMPLETE |
| 10.3 | Boot flow — Intel SoC deep dive | `10_embedded_linux/boot_flow_intel_soc.md` | ✅ COMPLETE |
| 10.4 | Boot flow — Xilinx Zynq deep dive | `10_embedded_linux/boot_flow_xilinx_zynq.md` | ✅ COMPLETE |
| 10.5 | Boot flow — Microchip SoC deep dive | `10_embedded_linux/boot_flow_microchip_soc.md` | ✅ COMPLETE |
| 10.6 | HPS-FPGA bridges & interaction | `10_embedded_linux/hps_fpga_bridges.md` | ⬜ PENDING |
| 10.7 | Device tree & overlays | `10_embedded_linux/device_tree_and_overlays.md` | ⬜ PENDING |
| 10.8 | Kernel drivers & DMA | `10_embedded_linux/kernel_drivers_and_dma.md` | ⬜ PENDING |
| 10.9 | Build systems & OTA updates | `10_embedded_linux/build_and_update.md` | ⬜ PENDING |

## Phase 11: Soft Cores & SoC Design (`11_soft_cores_and_soc_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 11.1 | RISC-V ISA deep dive | `11_soft_cores_and_soc_design/riscv/` | ⬜ PENDING |
| 11.2 | Vendor soft processors | `11_soft_cores_and_soc_design/vendor_soft/` | ⬜ PENDING |
| 11.3 | Open RISC-V cores catalog | `11_soft_cores_and_soc_design/riscv_cores/` | ⬜ PENDING |
| 11.4 | Other ISA cores | `11_soft_cores_and_soc_design/other_isa/` | ⬜ PENDING |
| 11.5 | SoC design patterns | `11_soft_cores_and_soc_design/soc_design/` | ⬜ PENDING |

## Phase 12: Open Source & Open Hardware (`12_open_source_open_hardware/`)

| # | Task | File | Status |
|---|---|---|---|
| 12.1 | Retro computing (MiSTer/MiST) | `12_open_source_open_hardware/retro_computing/` | ⬜ PENDING |
| 12.2 | Open development boards | `12_open_source_open_hardware/open_boards/` | ⬜ PENDING |
| 12.3 | Core catalogs | `12_open_source_open_hardware/cores_catalog/` | ⬜ PENDING |
| 12.4 | Open memory controllers | `12_open_source_open_hardware/memory_controllers/` | ⬜ PENDING |
| 12.5 | Video & display (OSSC) | `12_open_source_open_hardware/video_display/` | ⬜ PENDING |
| 12.6 | Open networking & PCIe | `12_open_source_open_hardware/networking/` | ⬜ PENDING |
| 12.7 | GPU compute & ML | `12_open_source_open_hardware/gpu_compute/` | ⬜ PENDING |
| 12.8 | Initiatives & foundations | `12_open_source_open_hardware/initiatives/` | ⬜ PENDING |
| 12.9 | LiteX ecosystem | `12_open_source_open_hardware/litex/` | ⬜ PENDING |

## Phase 13: Toolchains (`13_toolchains/`)

| # | Task | File | Status |
|---|---|---|---|
| 13.1 | Vivado | `13_toolchains/vivado.md` | ⬜ PENDING |
| 13.2 | Quartus Prime | `13_toolchains/quartus_prime.md` | ⬜ PENDING |
| 13.3 | Lattice Diamond/Radiant | `13_toolchains/diamond_radiant.md` | ⬜ PENDING |
| 13.4 | Gowin EDA | `13_toolchains/gowin_eda.md` | ⬜ PENDING |
| 13.5 | Open-source flow (Yosys/nextpnr) | `13_toolchains/open_source_flow.md` | ⬜ PENDING |
| 13.6 | CI/CD for hardware | `13_toolchains/cicd_hardware.md` | ⬜ PENDING |
| 13.7 | HLS overview | `13_toolchains/hls_overview.md` | ⬜ PENDING |

## Phase 14: References (`14_references/`)

| # | Task | File | Status |
|---|---|---|---|
| 14.1 | Command cheatsheet | `14_references/command_cheatsheet.md` | ⬜ PENDING |
| 14.2 | Pinout tables | `14_references/pinout_tables.md` | ⬜ PENDING |
| 14.3 | Register map template | `14_references/register_map_template.md` | ⬜ PENDING |
| 14.4 | Constraint quick-reference | `14_references/constraint_quickref.md` | ⬜ PENDING |
| 14.5 | Error codes & resolution | `14_references/error_codes.md` | ⬜ PENDING |

## Phase 15: Case Studies (`15_case_studies/`)

| # | Task | File | Status |
|---|---|---|---|
| 15.1 | Board bring-up checklist | `15_case_studies/bring_up_checklist.md` | ⬜ PENDING |
| 15.2 | Debugging DDR failures | `15_case_studies/debugging_ddr.md` | ⬜ PENDING |
| 15.3 | PCIe bringup | `15_case_studies/pcie_bringup.md` | ⬜ PENDING |
| 15.4 | LiteX SoC build | `15_case_studies/litex_soc_build.md` | ⬜ PENDING |
| 15.5 | Common failure modes | `15_case_studies/common_failures.md` | ⬜ PENDING |

## Cross-Cutting Tasks

| # | Task | Status |
|---|---|---|
| X.1 | Factual verification: Intel SoC CPU specs (Agilex 7 = A53, Agilex 5 = A76+A55) | ✅ COMPLETE |
| X.2 | Factual verification: MAX 10 is CPLD/FPGA (not SoC) | ✅ COMPLETE |
| X.3 | Factual verification: Zynq-7000 AXI port counts | ✅ COMPLETE |
| X.4 | Documentation map: root README.md updated with all sections | ✅ COMPLETE |
| X.5 | Consistency check: cross-links between common + sub-articles | ⬜ PENDING |
| X.6 | Index maintenance: all README.md files point to correct articles | 🔄 IN PROGRESS |

---

## Legend

| Symbol | Meaning |
|---|---|
| ⬜ PENDING | Not started |
| 🔄 IN PROGRESS | Currently writing |
| ✅ COMPLETE | Written, reviewed, pushed |
| ⏸️ BLOCKED | Waiting on dependency |
