# FPGA & SoC Embedded Linux — The Developer's Source of Truth

**From LUTs to Linux userland**

> *Everything the datasheets imply but never explain in one place.*
>
> A comprehensive, self-contained technical reference for FPGA development across all major vendors — covering device architecture, design flow, HDL, timing closure, embedded Linux integration, and open-source tooling. Written for developers building on real hardware, soft cores, and vendor dev boards.

---

## Why This Exists

FPGA documentation is fragmented across thousands of datasheets, archaic PDF user guides, scattered wiki pages, and tribal knowledge locked in vendor forums. Each vendor reinvents terminology, constraint syntax, and IP packaging. This repository consolidates it into a single, cross-linked, searchable knowledge base — verified against actual silicon errata, reference manuals, and open-source toolchain behavior.

### What's Inside

| Layer | Coverage |
|---|---|
| **Overview** | FPGA landscape, vendor comparison matrix, technology nodes, history |
| **Vendors & Families** | Intel/Altera (Cyclone V anchor), Xilinx (7-series, UltraScale+, Versal, Zynq), Lattice (ECP5, MachXO, CrossLink-NX), Gowin (LittleBee, Arora), Microchip (PolarFire, SmartFusion), others |
| **Architecture** | LUTs/CLBs, BRAM/URAM, DSP slices, clocking (PLL/MMCM/DCM), IO standards, SERDES, routing, configuration, **CPLD & non-volatile logic** |
| **Design Flow** | Synthesis, placement, routing, bitstream generation, floorplanning, partial reconfiguration |
| **HDL & Synthesis** | Verilog (Gateway 1983 → IEEE 1364), SystemVerilog (Superlog+Vera → IEEE 1800), VHDL (VHSIC program → IEEE 1076), legacy HDLs (AHDL/ABEL/PALASM), inference rules, vendor pragmas, CDC coding, state machines |
| **Timing & Constraints** | SDC/XDC/QSF syntax, clock domain crossing (CDC), false paths, multicycle paths, timing closure methodology, IO timing |
| **IP & Cores** | Bus protocols (AXI4/Wishbone/Avalon/APB), DDR controllers (MIG/UniPHY), PCIe blocks, transceivers, vendor IP ecosystems, IP packaging & reuse (FuseSoC, IP-XACT), licensing |
| **Verification** | Simulation (ModelSim, XSim, Verilator), formal verification (SymbiYosys), UVM, cocotb, testbench patterns |
| **Debug & Tools** | ILA/SignalTap, OpenOCD, JTAG boundary scan, logic analyzers, remote debugging, Tcl scripting |
| **Board Design** | High-speed signal integrity, power integrity, BGA escape routing, thermal design, configuration interfaces |
| **Embedded Linux** | Device tree overlays, U-Boot porting, kernel drivers for FPGA fabric, Buildroot/Yocto, FPGA Manager, remote update |
| **Soft Cores & SoC Design** | RISC-V ISA deep dive, MicroBlaze, Nios II/V, open RISC-V cores (VexRiscv, PicoRV32, NEORV32, SERV, Ibex, BOOM, Rocket, CVA6), SoC architecture: bus matrix design, memory map planning, interrupt routing, DMA, multi-core coherency, Chipyard |
| **Open Source & Open Hardware** | Retro computing platforms (MiSTer, MiST, Analogue openFPGA), open development boards (ULX3S, OrangeCrab, iCEBreaker, Tang Nano), CPU core catalogs, memory controllers, video/display (OSSC), networking & PCIe, GPU compute, notable initiatives (OpenTitan, PULP, FOSSi, CHIPS Alliance), LiteX ecosystem |
| **Toolchains** | Vivado, Quartus Prime, Diamond/Radiant, Gowin EDA, open-source (Yosys, nextpnr, F4PGA), CI/CD for hardware, HLS overview |
| **References** | Command cheatsheets, pinout tables, register map templates, constraint quick-reference, error codes |
| **Case Studies** | Real projects, bring-up sequences, DDR debugging, PCIe bringup, common failure modes |

### Quick Start

| You are... | Start here |
|---|---|
| **New to FPGAs (MiSTer path)** | [Cyclone V & MiSTer](01_vendors_and_families/README.md) → [Architecture basics](02_architecture/README.md) → [Design flow overview](03_design_flow/overview.md) |
| **Choosing a vendor** | [Vendor comparison matrix](00_overview/vendor_comparison.md) → [Vendor family guides](01_vendors_and_families/README.md) |
| **Writing HDL** | [Verilog & SV](04_hdl_and_synthesis/verilog_sv/verilog.md) → [VHDL](04_hdl_and_synthesis/vhdl/vhdl_basics.md) → [Synthesis inference rules](04_hdl_and_synthesis/inference_rules.md) → [Timing constraints](05_timing_and_constraints/sdc_basics.md) |
| **Power-On to Linux userland** | [Configuration modes](02_architecture/infrastructure/configuration.md) → [Bitstream generation](03_design_flow/bitstream.md) → [Embedded Linux overview](10_embedded_linux/overview.md) → [U-Boot](10_embedded_linux/uboot.md) |
| **Building an SoC** | [Soft cores overview](11_soft_cores_and_soc_design/README.md) → [Bus matrix design](11_soft_cores_and_soc_design/soc_design/bus_matrix_design.md) → [Memory map planning](11_soft_cores_and_soc_design/soc_design/memory_map_design.md) |
| **Exploring open projects** | [Open source & HW overview](12_open_source_open_hardware/README.md) → [MiSTer deep dive](12_open_source_open_hardware/retro_computing/mister.md) → [OSSC](12_open_source_open_hardware/video_display/ossc.md) |
| **Using open-source tools** | [Yosys & nextpnr](13_toolchains/open_source_flow.md) → [LiteX ecosystem](12_open_source_open_hardware/litex/litex_overview.md) |
| **Debugging hardware** | [ILA/SignalTap guide](08_debug_and_tools/ila_signaltap.md) → [JTAG/OpenOCD](08_debug_and_tools/openocd.md) |
| **Reverse engineering FPGA designs** | [Bitstream format overview](02_architecture/infrastructure/configuration.md) → [Open-source tooling for analysis](13_toolchains/open_source_flow.md) |

---

> **Scope:** All major FPGA vendors and families from low-cost (iCE40, LittleBee) to high-end (Versal, Agilex). Coverage spans bare-metal FPGA design, soft-core SoC integration, embedded Linux on hard SoC platforms (Zynq, Cyclone V SoC, PolarFire SoC), and the open-source FPGA ecosystem (MiSTer, LiteX, OSSC, open cores & toolchains).

## Sources

| Reference | URL / Path |
|---|---|
| Xilinx UG900 (Constraints Guide) | https://docs.xilinx.com/ |
| Intel Quartus Prime Handbook | https://www.intel.com/content/www/us/en/docs/programmable/ |
| Lattice Technical Documentation | https://www.latticesemi.com/support/technicaldocuments |
| Gowin Documentation | https://www.gowinsemi.com/en/support/documentation/ |
| Yosys Manual | https://yosyshq.readthedocs.io/ |
| RISC-V Specs | https://riscv.org/technical/specifications/ |
| Linux Device Tree Spec | https://www.devicetree.org/specifications/ |

---

## Documentation Map

### 00 — Overview
| File | Topic |
|---|---|
| [landscape.md](00_overview/landscape.md) | FPGA market landscape, technology evolution, when to choose FPGA vs ASIC vs MCU |
| [vendor_comparison.md](00_overview/vendor_comparison.md) | Side-by-side vendor matrix: cost, tooling, ecosystem, IO standards, support quality |
| [history.md](00_overview/history.md) | From Xilinx XC2064 to modern 3D FPGAs — architectural evolution timeline |
| [technology_nodes.md](00_overview/technology_nodes.md) | Process technology impact on FPGA characteristics: power, speed, density |

### 01 — Vendors & Families
| Folder | Coverage |
|---|---|
| [altera_intel/](01_vendors_and_families/altera_intel/) | **Cyclone V, MAX 10, Cyclone 10, Arria 10, Stratix 10, Agilex 5/7, Intel SoC (Cyclone V SoC, Agilex SoC)** |
| [xilinx/](01_vendors_and_families/xilinx/) | 7-series (Artix, Kintex, Virtex), UltraScale/UltraScale+, Versal ACAP, Zynq-7000, Zynq MPSoC/RFSOC |
| [lattice/](01_vendors_and_families/lattice/) | ECP5, MachXO2/3, CrossLink-NX/CrossLinkU-NX, CertusPro-NX, iCE40 (UltraPlus, Ultra) |
| [gowin/](01_vendors_and_families/gowin/) | LittleBee (GW1N), Arora (GW2A), Tang series dev boards, Gowin EDA |
| [microchip/](01_vendors_and_families/microchip/) | PolarFire/PolarFire SoC, SmartFusion2/IGLOO2, Mi-V RISC-V ecosystem |
| [others/](01_vendors_and_families/others/) | Efinix Trion/Titanium, QuickLogic EOS S3, NanoXplore, Achronix Speedster7t |

### 02 — Architecture
| Folder | Coverage |
|---|---|
| [fabric/](02_architecture/fabric/) | **LUTs & CLBs** (4-input, 6-input, fracturable, ALM/Slice), **BRAM & URAM** (18Kb/36Kb/20Kb, dual-port, ECC), **DSP slices** (DSP48/DSP58, cascading, pipelining), **routing** (interconnect, switch matrices, congestion) |
| [infrastructure/](02_architecture/infrastructure/) | **Clocking** (PLL/MMCM/DCM, global/regional networks), **IO standards** (LVDS, SSTL, HSTL, LVCMOS, SERDES, bank constraints), **configuration** (bitstream format, SPI/BPI/JTAG/SelectMAP, encryption, authentication) |
| [soc/](02_architecture/soc/) | **Hard CPU + FPGA integration**: HPS/PS bridge architectures, AXI-3/4/NoC interconnect, cache coherency models (ACP/CCI-400/CHI), memory hierarchy, boot architecture. Vendor deep dives: [Intel HPS-FPGA](02_architecture/soc/hps_fpga_intel_soc.md), [Xilinx PS-PL](02_architecture/soc/hps_fpga_xilinx_zynq.md), [Microchip MSS-Fabric](02_architecture/soc/hps_fpga_microchip_soc.md) |
| [cpld/](02_architecture/cpld/) | **CPLD & non-volatile logic**: macrocells, AND-OR arrays, flash/antifuse/SONOS, Intel MAX V/MAX 10, CPLD vs FPGA decision framework, devboard reference |

### 03 — Design Flow
| File | Topic |
|---|---|
| [overview.md](03_design_flow/overview.md) | End-to-end design flow: RTL → synthesis → place & route → bitstream → configuration |
| [project_structure.md](03_design_flow/project_structure.md) | Recommended directory layout, revision control for HDL, IP versioning, constraint files |
| [synthesis.md](03_design_flow/synthesis.md) | Synthesis engine behavior, optimization strategies, resource sharing, retiming, FSM extraction |
| [netlist.md](03_design_flow/netlist.md) | Netlist formats across all vendors: EDIF, structural Verilog, VQM/QDB/QXP (Intel), DCP (Xilinx), NGO (Lattice), RTLIL/JSON (Yosys) — cross-vendor interchange, ECO, inspection |
| [place_and_route.md](03_design_flow/place_and_route.md) | Placement algorithms (simulated annealing, analytical), routing congestion, physical optimization |
| [bitstream.md](03_design_flow/bitstream.md) | Bitstream generation, compression, encryption, authentication, partial reconfiguration (DFX) |
| [floorplanning.md](03_design_flow/floorplanning.md) | Manual floorplanning, pblock/LogicLock constraints, region constraints, IO planning |

### 04 — HDL & Synthesis
| File | Topic |
|---|---|
| [verilog_sv/](04_hdl_and_synthesis/verilog_sv/README.md) | **Verilog** (IEEE 1364) and **SystemVerilog** (IEEE 1800): origins at Gateway (1983), C-like philosophy, multi-parent lineage, dual design/verification roles, UVM ecosystem |
| [vhdl/](04_hdl_and_synthesis/vhdl/README.md) | **VHDL** (IEEE 1076): DoD VHSIC origins (1981), Ada heritage, strong typing, IEEE 1076-1987 through 2019, PSL verification, OSVVM/UVVM |
| [legacy_hdl/](04_hdl_and_synthesis/legacy_hdl/README.md) | Ancient/vendor-specific HDLs: AHDL, ABEL, PALASM — languages that predate modern Verilog/VHDL |
| [hls/](04_hdl_and_synthesis/hls/README.md) | **High-Level Synthesis**: scheduling, pipelining, loop unroll, array partition, interface synthesis |
| [inference_rules.md](04_hdl_and_synthesis/inference_rules.md) | What HDL pattern infers what hardware: RAM, ROM, multiplier, shift register, latch vs flop |
| [vendor_pragmas.md](04_hdl_and_synthesis/vendor_pragmas.md) | Xilinx attributes, Altera synthesis directives, Gowin pragmas, keep/dont_touch, async_reg |
| [cdc_coding.md](04_hdl_and_synthesis/cdc_coding.md) | HDL patterns for clock domain crossing: 2-FF synchronizer, handshake, async FIFO, MCP |
| [state_machines.md](04_hdl_and_synthesis/state_machines.md) | Safe FSM encoding: one-hot vs binary vs Gray, reset strategies, unreachable state recovery |

### 05 — Timing & Constraints
| File | Topic |
|---|---|
| [sdc_basics.md](05_timing_and_constraints/sdc_basics.md) | SDC/XDC/QSF constraint syntax: create_clock, create_generated_clock, set_input_delay, set_output_delay |
| [clock_domain_crossing.md](05_timing_and_constraints/clock_domain_crossing.md) | Metastability theory, MTBF calculation, synchronizer chains, gray-code FIFOs, handshake protocols |
| [false_paths.md](05_timing_and_constraints/false_paths.md) | set_false_path, set_clock_groups (-asynchronous), async reset paths, static signals |
| [multicycle_paths.md](05_timing_and_constraints/multicycle_paths.md) | set_multicycle_path: setup multiplier, hold adjustment, fractional cycles, common mistakes |
| [timing_closure.md](05_timing_and_constraints/timing_closure.md) | Methodology: analyze slack, identify critical paths, fix strategies (pipelining, retiming, physical) |
| [io_timing.md](05_timing_and_constraints/io_timing.md) | Source-synchronous interfaces, center vs edge-aligned capture, forwarded clocks, RGMII/SDR/DDR |

### 06 — IP & Cores
| Folder | Coverage |
|---|---|
| [bus_protocols/](06_ip_and_cores/bus_protocols/) | **AXI4 family** (AXI4, AXI4-Lite, AXI4-Stream: channels, handshake, burst, ordering), **Wishbone, Avalon, APB/AHB** (comparison matrix) |
| [vendor_ip/](06_ip_and_cores/vendor_ip/) | Xilinx IP Integrator, Intel Platform Designer (Qsys), Lattice Clarity, Microchip SmartDesign, Gowin IP generator |
| [interconnect/](06_ip_and_cores/interconnect/) | AXI Interconnect deep dive: crossbar vs shared bus, address decoding, QoS arbitration, deadlock, data width/clock converters |
| [ddr/](06_ip_and_cores/ddr/) | MIG (Xilinx), UniPHY/EMIF (Intel), DDR controllers for Lattice/Microchip/Gowin, pin planning |
| [pcie/](06_ip_and_cores/pcie/) | Integrated PCIe hard blocks (Gen1–Gen5), BAR configuration, MSI/MSI-X, DMA (XDMA), endpoint vs root port |
| [transceivers/](06_ip_and_cores/transceivers/) | Multi-gigabit transceivers (GTP/GTH/GTY/GTM), PMA+PCS architecture, CDR, pre/de-emphasis, equalization, line rates |
| [other_hard_ip/](06_ip_and_cores/other_hard_ip/) | Hard Ethernet MACs (1G/10G/25G/100G), video/audio IP, FFT/FIR/DDS/CORDIC signal processing blocks |
| [ip_reuse/](06_ip_and_cores/ip_reuse/) | IP packaging (IP-XACT, component.xml, _hw.tcl), **FuseSoC** package manager & build system, IP licensing (vendor vs open-source: MIT/LGPL/GPL/Apache/CERN OHL) |

### 07 — Verification
| File | Topic |
|---|---|
| [simulation_overview.md](07_verification/simulation_overview.md) | Simulator comparison: Vivado XSim, ModelSim/Questa, Verilator, GHDL, Icarus, cocotb integration |
| [testbench_patterns.md](07_verification/testbench_patterns.md) | Self-checking testbenches, reference models, scoreboards, coverage collection, constrained-random |
| [formal_verification.md](07_verification/formal_verification.md) | SymbiYosys: assertions (assert/assume/cover), bounded model checking, k-induction, cover properties |
| [cocotb.md](07_verification/cocotb.md) | Python-based coroutine testbenches: setup, writing tests in Python for Verilog/VHDL, async/await patterns |
| [uvm_overview.md](07_verification/uvm_overview.md) | UVM basics for FPGA: agents, drivers, monitors, sequencers, scoreboards, factory override, TLM ports |
| [protocol_checkers.md](07_verification/protocol_checkers.md) | AXI, Avalon, Wishbone protocol assertion VIPs and bus functional models (BFMs) |

### 08 — Debug & Tools
| File | Topic |
|---|---|
| [ila_signaltap.md](08_debug_and_tools/ila_signaltap.md) | Xilinx ILA vs Intel SignalTap: trigger setup, probe routing, memory depth trade-offs, Tcl control |
| [openocd.md](08_debug_and_tools/openocd.md) | OpenOCD for FPGA JTAG: configuration scripts, SVF/XSVF bitstream playback, flash programming |
| [jtag_boundary_scan.md](08_debug_and_tools/jtag_boundary_scan.md) | Boundary scan (IEEE 1149.1), BSDL files, EXTEST/SAMPLE/PRELOAD, board-level interconnect test |
| [logic_analyzers.md](08_debug_and_tools/logic_analyzers.md) | External LA integration (Saleae, DSLogic, sigrok), decoding protocols (UART, SPI, I2C, AXI stream) |
| [remote_debugging.md](08_debug_and_tools/remote_debugging.md) | Debugging embedded Linux on SoC FPGAs: JTAG + GDB, kgdb, early printk, /dev/mem, devmem2 |
| [tcl_scripting.md](08_debug_and_tools/tcl_scripting.md) | Vendor tool automation: Vivado Tcl, Quartus Tcl (quartus_stp), non-project mode, report generation |

### 09 — Board Design
| File | Topic |
|---|---|
| [high_speed_signals.md](09_board_design/high_speed_signals.md) | Signal integrity: impedance control, length matching, differential pairs, vias, insertion loss, crosstalk |
| [power_integrity.md](09_board_design/power_integrity.md) | Power rails & sequencing, decoupling capacitor selection, PDN design, IR drop, current transients |
| [bga_routing.md](09_board_design/bga_routing.md) | BGA escape routing strategies, layer stackup design, via types (through, blind, buried, microvia) |
| [thermal_design.md](09_board_design/thermal_design.md) | Junction temperature estimation, heat sink selection, airflow, power dissipation models, thermal vias |
| [configuration_interfaces.md](09_board_design/configuration_interfaces.md) | Flash selection (QSPI, eMMC, NAND), config pin strapping, fallback/multi-boot, remote update |

### 10 — Embedded Linux
| Article | Topic |
|---|---|
| [soc_linux_architecture.md](10_embedded_linux/soc_linux_architecture.md) | SoC from Linux kernel's perspective — HPS/PS vs PL domains, bridge topology, cache coherency (ACP vs non-coherent) |
| [boot_flow.md](10_embedded_linux/boot_flow.md) | Common boot flow: universal sequence, boot media, SD formatting, FPGA config timing, secure boot, failure diagnostics |
| [boot_flow_intel_soc.md](10_embedded_linux/boot_flow_intel_soc.md) | Intel/Altera SoC boot: Cyclone V, Arria 10, Agilex. BSEL, preloader, FPP/AVST config, secure boot |
| [boot_flow_xilinx_zynq.md](10_embedded_linux/boot_flow_xilinx_zynq.md) | Xilinx Zynq boot: Zynq-7000, MPSoC, Versal. CSU/PMC, PCAP, bootgen, ATF/PMUFW, RSA/AES/PUF secure boot |
| [boot_flow_microchip_soc.md](10_embedded_linux/boot_flow_microchip_soc.md) | Microchip SoC boot: PolarFire (RISC-V), SmartFusion2. System Controller, HSS, OpenSBI, Flash-based config |
| [hps_fpga_bridges.md](10_embedded_linux/hps_fpga_bridges.md) | **★ HPS↔FPGA interaction** — AXI bridges, ioremap, userspace mmap, interrupt routing (FPGA → GIC), DMA setup, cache coherency patterns |
| [device_tree_and_overlays.md](10_embedded_linux/device_tree_and_overlays.md) | Device tree for FPGA SoCs, reserved-memory, FPGA Manager configfs, device tree overlay compilation and loading |
| [kernel_drivers_and_dma.md](10_embedded_linux/kernel_drivers_and_dma.md) | Three driver patterns: UIO, platform driver, VFIO. DMA Engine cyclic DMA, buffer type selection |
| [build_and_update.md](10_embedded_linux/build_and_update.md) | Buildroot vs Yocto for FPGA SoCs, OTA bitstream updates (A/B scheme, fallback, secure boot) |

### 11 — Soft Cores & SoC Design
| Folder / File | Coverage |
|---|---|
| [riscv/](11_soft_cores_and_soc_design/riscv/) | **RISC-V ISA** (RV32I/RV64I, M/A/F/D/C/B/V extensions), **privileged architecture** (M/S/U modes, CSRs, Sv32/Sv39/Sv48, PMP, PLIC/CLINT/CLIC) |
| [vendor_soft/](11_soft_cores_and_soc_design/vendor_soft/) | **MicroBlaze / MicroBlaze-V** (Xilinx), **Nios II / Nios V** (Intel/Altera) — configuration, buses, BSP, migration paths |
| [riscv_cores/](11_soft_cores_and_soc_design/riscv_cores/) | Open RISC-V deep dives: **VexRiscv** (SpinalHDL, Linux MMU), **PicoRV32** (minimal), **NEORV32** (best docs), **SERV** (bit-serial), **Ibex** (OpenTitan), **BOOM/Rocket/CVA6/XiangShan** (high-perf survey) |
| [other_isa/](11_soft_cores_and_soc_design/other_isa/) | OpenRISC (mor1kx), LEON3/4 (SPARC V8), Microwatt (POWER9), ZPU, Plasma (MIPS), NEO430 (MSP430) |
| [soc_design/](11_soft_cores_and_soc_design/soc_design/) | **Bus matrix design** (topologies, address decoding, concurrency), **memory map planning** (base addresses, apertures, DT binding), **interrupt routing** (PLIC design, affinity, priority), **DMA architecture** (centralized vs distributed, scatter-gather, iDMA), **Rocket Chip / Chipyard** (Chisel generators, TileLink, Diplomacy), **multi-core coherency** (snooping, directory, AXI4 ACE-Lite) |

### 12 — Open Source & Open Hardware
| Folder | Coverage |
|---|---|
| [retro_computing/](12_open_source_open_hardware/retro_computing/) | **MiSTer** (DE10-Nano, framework, 100+ cores, SDRAM add-ons), **MiST**, **Analogue openFPGA**, **SiDi / ZX-Uno / Replay / MARS / MiSTeX** |
| [open_boards/](12_open_source_open_hardware/open_boards/) | **ULX3S** (ECP5), **OrangeCrab** (ECP5), **iCEBreaker** (iCE40), **TinyFPGA BX**, **ButterStick**, **Tang Nano** (Gowin), repurposed boards (Colorlight i5/i9) |
| [cores_catalog/](12_open_source_open_hardware/cores_catalog/) | **RISC-V core shopping guide** (VexRiscv, PicoRV32, NEORV32, SERV, BOOM, Rocket, CVA6, Ibex, XiangShan), **non-RISC-V cores**, **peripheral core collections** |
| [memory_controllers/](12_open_source_open_hardware/memory_controllers/) | **Open SDRAM controllers** (stffrdhrn/sdram-controller, LiteDRAM), **DDR1/2/3/4** (WangXuan95, ultraembedded, oprecomp), **HyperRAM/QSPI PSRAM/SRAM** |
| [video_display/](12_open_source_open_hardware/video_display/) | **OSSC** (Open Source Scan Converter, Lattice ECP3, zero-lag line multiplication), **OSSC Pro**, **RetroTINK** line, **GBS-Control**, **Project F** display controller, open HDMI/DVI TX cores |
| [networking/](12_open_source_open_hardware/networking/) | **verilog-ethernet** (1G/10G/25G by Alex Forencich), **Corundum** (100G open NIC), **verilog-pcie** (DMA, AXI bridges), **open USB cores** (device/host/ULPI) |
| [gpu_compute/](12_open_source_open_hardware/gpu_compute/) | **VeriGPU** (educational), **Vortex GPGPU** (RISC-V), **Ventus GPGPU** (THU), **TinyGPU**, **NVDLA** (NVIDIA open NPU), **hls4ml/FINN** for ML acceleration |
| [initiatives/](12_open_source_open_hardware/initiatives/) | **OpenTitan** (lowRISC + Google, silicon root of trust, RISC-V Ibex), **PULP Platform** (ETH Zürich, parallel ultra-low-power), **FOSSi Foundation / CHIPS Alliance / LibreCores**, open-source EDA survey (Yosys, nextpnr, OpenROAD, SkyWater PDK) |
| [litex/](12_open_source_open_hardware/litex/) | **LiteX** deep dive: Migen/Python SoC builder, supported boards & CPUs, Linux-capable configs, core ecosystem (LiteDRAM, LiteEth, LitePCIe, LiteSATA, LiteSDCard, LiteSPI, LiteICLink) |

### 13 — Toolchains
| File | Topic |
|---|---|
| [vivado.md](13_toolchains/vivado.md) | Xilinx Vivado: project vs non-project mode, Tcl scripting, IP integrator, synthesis & implementation strategies |
| [quartus_prime.md](13_toolchains/quartus_prime.md) | Intel Quartus Prime: Platform Designer, Timing Analyzer, SignalTap, quartus_sh/quartus_stp Tcl |
| [diamond_radiant.md](13_toolchains/diamond_radiant.md) | Lattice Diamond vs Radiant: toolchain selection, project migration, Reveal debugger |
| [gowin_eda.md](13_toolchains/gowin_eda.md) | Gowin EDA: device support, synthesis, placement, GAO (Gowin Analyzer Oscilloscope) |
| [open_source_flow.md](13_toolchains/open_source_flow.md) | Yosys + nextpnr + F4PGA (SymbiFlow successor): supported families (iCE40, ECP5, Gowin, Xilinx 7-series), limitations, workflow |
| [cicd_hardware.md](13_toolchains/cicd_hardware.md) | CI/CD for FPGA: Jenkins/GitHub Actions, Docker containers for vendor tools, bitstream artifact management, regression testing |
| [hls_overview.md](13_toolchains/hls_overview.md) | High-Level Synthesis: Vivado HLS/Vitis HLS, Intel HLS compiler, Catapult, Bambu, pipeline/unroll/array_partition pragmas, when HLS helps vs when it hurts |

### 14 — References
| File | Topic |
|---|---|
| [command_cheatsheet.md](14_references/command_cheatsheet.md) | Vendor tool command quick-reference: Vivado Tcl, quartus_sh, yosys, nextpnr, openocd commands |
| [pinout_tables.md](14_references/pinout_tables.md) | Common package pinout patterns, bank/IO assignments, clock-capable pin locations per family |
| [register_map_template.md](14_references/register_map_template.md) | Standard register map documentation template for custom AXI/Avalon/Wishbone peripherals |
| [constraint_quickref.md](14_references/constraint_quickref.md) | XDC/SDC/QSF/LPF/PDC constraint syntax side-by-side reference by command category |
| [error_codes.md](14_references/error_codes.md) | Common vendor tool error/warning codes (Vivado, Quartus, Yosys/nextpnr) and resolution steps |

### 15 — Case Studies
| File | Topic |
|---|---|
| [bring_up_checklist.md](15_case_studies/bring_up_checklist.md) | New board bring-up sequence: power, JTAG chain, configuration, first blinky, first bitstream |
| [debugging_ddr.md](15_case_studies/debugging_ddr.md) | DDR memory calibration failures: read/write leveling failures, DQS gate issues, diagnosis & resolution |
| [pcie_bringup.md](15_case_studies/pcie_bringup.md) | PCIe link training debug: LTSSM state traversal, equalization, eye diagrams, common pitfalls |
| [litex_soc_build.md](15_case_studies/litex_soc_build.md) | Building a complete Linux-capable SoC with LiteX on ECP5 (ULX3S) and Artix-7 (Arty) |
| [common_failures.md](15_case_studies/common_failures.md) | Frequently encountered failures: metastability, timing violations, power sequencing, configuration, clocking |
