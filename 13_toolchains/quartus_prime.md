[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Altera Quartus Prime — Design Suite for Cyclone, Arria, Stratix, Agilex

Quartus Prime is Altera's design environment for all FPGA families from MAX 10 through Agilex. The "Prime" branding (since v15.1) distinguishes it from the older "Quartus II" (v13.1 and earlier, Cyclone IV and prior). This article covers the practical aspects of using Quartus Prime that every FPGA developer needs: build flows, QSF/SDC constraints, Platform Designer, SignalTap debug, incremental compilation, and the many pitfalls that differ from Vivado.

> **Company status:** Altera is now an independent company (Jan 2025). Intel acquired Altera in 2015, operated it as the Programmable Solutions Group (PSG), then spun it back out. Silver Lake acquired 51% in Sep 2025; Intel retains 49%. The tools work identically — same executables, same commands. Downloads and documentation now live at [altera.com](https://www.altera.com). For the full timeline, see the [Altera independence documentation summary](#altera-independence-timeline).

> **Prerequisites:** For Tcl scripting patterns, see [Tcl Scripting](../08_debug_and_tools/tcl_scripting.md). For SDC constraint syntax, see [SDC Basics](../05_timing_and_constraints/sdc_basics.md). For cross-vendor constraint reference, see [Constraint Quick Reference](../14_references/constraint_quickref.md). For quick command reference, see [Command Cheatsheet](../14_references/command_cheatsheet.md).

---

## Editions

| Edition | Devices Supported | Cost |
|---|---|---|
| **Quartus Prime Lite** | Cyclone V, Cyclone 10 LP, MAX 10 | Free |
| **Quartus Prime Standard** | Arria V/GZ/10, Stratix V, Cyclone 10 GX | Paid (~$3,000+) |
| **Quartus Prime Pro** | Agilex 5/7/9, Stratix 10, Arria 10 (advanced features) | Paid (~$4,000+) |

**Key differences between editions:**

| Feature | Lite | Standard | Pro |
|---|---|---|---|
| **Partial Reconfiguration** | No | No | Yes |
| **Hyper-Retry (Agilex)** | No | No | Yes |
| **Signal Tap with PR** | No | No | Yes |
| **Design Partition reuse** | No | Limited | Full |
| **Interface Planner** | No | No | Yes |
| **HPS configuration (Agilex SoC)** | No | No | Yes |

**For DE10-Nano/MiSTer:** Quartus Prime Lite is sufficient — Cyclone V is fully supported.

---

## QSF and SDC — The Dual Constraint System

Unlike Vivado (single XDC file), Quartus uses two separate constraint systems:

| File | Purpose | Format | Example |
|---|---|---|---|
| **`.qsf`** (Quartus Settings File) | Pin assignments, IO standards, device selection, compilation options, IP search paths | `set_global_assignment` / `set_instance_assignment` | `set_location_assignment PIN_A12 -to clk` |
| **`.sdc`** (Synopsys Design Constraints) | Timing: clocks, I/O delays, false paths, clock groups | Standard SDC Tcl | `create_clock -period 10.0 [get_ports clk]` |

**Key difference from Vivado:** QSF handles everything physical; SDC handles everything timing. In Vivado, a single XDC file does both.

### QSF Pin Assignment Patterns

```tcl
# ═══ Physical constraints go in .qsf ═══

# Device selection
set_global_assignment -name DEVICE 5CSEBA6U23I7
set_global_assignment -name FAMILY "Cyclone V"

# Source files
set_global_assignment -name VERILOG_FILE ../rtl/top.v
set_global_assignment -name SYSTEMVERILOG_FILE ../rtl/axi_slave.sv
set_global_assignment -name VHDL_FILE ../rtl/crc32.vhd

# Pin assignments
set_location_assignment PIN_A12 -to clk_50m
set_location_assignment PIN_B8  -to rst_n
set_location_assignment PIN_C10 -to led[0]
set_location_assignment PIN_C11 -to led[1]

# IO standards
set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to clk_50m
set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to rst_n
set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to led[*]

# Drive strength and pull-ups
set_instance_assignment -name CURRENT_STRENGTH_NEW 12MA -to led[*]
set_instance_assignment -name WEAK_PULL_UP_RESISTOR ON -to i2c_sda

# SDC file reference (timing constraints live separately)
set_global_assignment -name SDC_FILE ../constraints/top.sdc
```

### SDC Timing Constraints

```tcl
# ═══ Timing constraints go in .sdc ═══

# Base clock
create_clock -name clk_50m -period 20.0 [get_ports clk_50m]

# PLL generated clocks (Altera PLL auto-generates these if you use
# the ALTPLL IP — but verify with report_clocks)
create_generated_clock -name clk_100m \
    -source [get_pins {pll_inst|altpll_component|auto_generated|pll1|inclk[0]}] \
    [get_pins {pll_inst|altpll_component|auto_generated|pll1|clk[0]}]

# Async clock groups
set_clock_groups -asynchronous \
    -group [get_clocks clk_50m] \
    -group [get_clocks clk_100m]

# False path on async reset
set_false_path -from [get_ports rst_n]

# I/O timing for external SDRAM
set_output_delay -clock clk_100m -max 3.0 [get_ports sdram_dq[*]]
set_output_delay -clock clk_100m -min 0.0 [get_ports sdram_dq[*]]
```

> **Important:** Unlike Vivado XDC, Quartus SDC constraints are **order-independent** — they are processed as a set, not sequentially. This means you can organize them logically without worrying about forward references.

---

## Build Flow — Complete Tcl Script

```tcl
#!/usr/bin/env quartus_sh -t
# ═══════════════════════════════════════════════════════
#  quartus_build.tcl — Full build from command line
#  Usage: quartus_sh -t quartus_build.tcl
# ═══════════════════════════════════════════════════════

set PROJECT "my_design"
set TOP     "top"
set PART    "5CSEBA6U23I7"
set FAMILY  "Cyclone V"

# ── 1. Create project ──
project_new $PROJECT -overwrite -part $PART -family $FAMILY

# ── 2. Add source files ──
set_global_assignment -name TOP_LEVEL_ENTITY $TOP
set_global_assignment -name VERILOG_FILE ../rtl/top.v
set_global_assignment -name SYSTEMVERILOG_FILE ../rtl/datapath.sv
set_global_assignment -name VHDL_FILE ../rtl/crc32.vhd

# ── 3. Add constraints ──
set_global_assignment -name SDC_FILE ../constraints/top.sdc

# Pin assignments (could also be in a separate .qsf include)
set_location_assignment PIN_A12 -to clk_50m
set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to clk_50m

# ── 4. Compilation options ──
set_global_assignment -name OPTIMIZATION_TECHNIQUE SPEED
set_global_assignment -name SYNTH_TIMING_DRIVEN_SYNTHESIS ON
set_global_assignment -name ROUTER_TIMING_OPTIMIZATION_LEVEL MAXIMUM
set_global_assignment -name PLACEMENT_EFFORT_MULTIPLIER 4.0
set_global_assignment -name ROUTER_EFFORT_MULTIPLIER 4.0

# ── 5. Run full compilation ──
load_package flow
execute_flow -compile

# ── 6. Reports ──
load_report
set f [open ../build/timing_summary.txt w]
puts $f [report_timing -npaths 10 -detail_full]
close $f
unload_report

# ── 7. Generate programming files ──
# SOF (SRAM Object File) — for JTAG programming
# POF (Programmer Object File) — for flash programming
# Both are generated automatically in output_files/

project_close
```

### Running Individual Stages

```bash
# Full compilation (synthesis + fitter + assembly + timing)
quartus_sh --flow compile my_design

# Individual stages
quartus_map my_design       # Analysis & Synthesis
quartus_fit my_design       # Fitter (Place & Route)
quartus_asm my_design       # Assembler (generate .sof)
quartus_sta my_design       # Timing Analyzer (TimeQuest)

# Generate POF from SOF (for flash programming)
quartus_cpf -c output_files/my_design.sof output_files/my_design.pof

# Generate RBF (Raw Binary File) for HPS loading
quartus_cpf -c output_files/my_design.sof output_files/my_design.rbf
```

### Incremental Compilation (Design Partitions)

Quartus's design partition system lets you recompile only changed parts of the design — similar to Vivado's incremental build, but more granular:

```tcl
# Define a partition (in .qsf or Tcl)
set_global_assignment -name PARTITION root_partition -section_id Top
set_global_assignment -name PARTITION_COLOR 16764057 -section_id Top

# After successful compilation, export the partition
# (preserves synthesis + placement results)
export_assignments

# On next build, only changed partitions are recompiled
# Unchanged partitions reuse their previous results
```

| Partition State | What Happens | Rebuild Time |
|---|---|---|
| **Source Changed** | Full recompile (synthesis + fitter) | 100% |
| **Source Unchanged, post-fit** | Reuse previous results | ~0% |
| **Source Unchanged, post-synth** | Reuse synthesis, re-run fitter | ~50% |

> **Note:** This is particularly powerful for SoC designs where the HPS configuration is stable and only the FPGA fabric changes. You can freeze the HPS partition and only recompile the fabric.

---

## Platform Designer (Qsys)

Platform Designer is Quartus's visual SoC assembly tool — the Altera equivalent of Vivado's IP Integrator. It replaced SOPC Builder in Quartus II 13.0.

### Tcl-Based System Creation

For reproducible builds, create Platform Designer systems from Tcl:

```tcl
# Create a new Platform Designer system
qsys_create my_system

# Add HPS (Cyclone V SoC)
qsys_add_instance hps_0 altera_hps
qsys_set_parameter hps_0 {F2SDRAM_TYPE} {1}
qsys_set_parameter hps_0 {F2SDRAM_WIDTH} {128}

# Add Nios II soft processor
qsys_add_instance nios2_qsys_0 altera_nios2_qsys
qsys_set_parameter nios2_qsys_0 {cpuArchitecture} {Nios II/f}

# Add AXI GPIO
qsys_add_instance gpio_0 altera_avalon_pio
qsys_set_parameter gpio_0 {width} {8}

# Connect: Nios data master → GPIO slave
qsys_connect nios2_qsys_0.data_master gpio_0.s1

# Connect: HPS → Nios (via AXI bridge)
qsys_connect hps_0.h2f_axi_master nios2_qsys_0.custom_instruction_master

# Export GPIO ports to top level
qsys_export gpio_0 external {exported_pio}

# Generate HDL
qsys_generate my_system -synth
```

### Avalon vs AXI in Platform Designer

| Interface | Direction | Use Case | Auto-Arbiter? |
|---|---|---|---|
| **Avalon-MM** | Memory-mapped (read/write registers) | Peripherals: UART, SPI, GPIO, I2C | Yes — built into interconnect |
| **Avalon-ST** | Streaming (data flow) | Video, DSP, packet pipelines | No — point-to-point only |
| **AXI4** | Memory-mapped (compatible mode) | Interop with Xilinx IP, DDR controllers | Yes — via AXI interconnect IP |
| **AXI4-Stream** | Streaming (compatible mode) | Interop with Xilinx streaming IP | No — point-to-point only |
| **Avalon Conduit** | Custom signal bundle | Clock, reset, GPIO, custom interfaces | No — manual connection |

> **Tip:** Use Avalon-MM for register-style peripherals (UART, SPI). Use Avalon-ST for high-throughput data paths (video, DSP). Only use AXI compatibility mode when you need to integrate Xilinx-origin IP.

### Platform Designer Gotchas

| Pitfall | What Happens | Fix |
|---|---|---|
| **Forgetting to generate HDL** | Synthesis fails — `.qsys` is metadata, not HDL | Run `qsys_generate` or "Generate HDL" in GUI |
| **Clock domain crossing in PD** | No automatic CDC insertion | Add clock crossing bridge or dual-clock FIFO IP |
| **Memory map overlaps** | Linker assigns overlapping address ranges | Check "Base" column in Address Map tab; fix conflicts |
| **HPS bridge not exported** | HPS-FPGA bridges are invisible in top-level HDL | Export bridge interfaces in Platform Designer |
| **Nios II reset vector wrong** | Processor boots from wrong address | Set reset_vector to EPCS/flash, exception_vector to on-chip RAM |

---

## SignalTap II — On-Chip Logic Analyzer

SignalTap II is Quartus's on-chip debug tool — the Altera equivalent of Vivado's ILA. It has one major advantage over ILA: you can add/change SignalTap probes **without recompiling** (using the SignalTap instance in "post-fit" mode).

### Adding SignalTap Probes

**Method 1 — GUI (Development):**
1. Tools → SignalTap II Logic Analyzer
2. Add nodes: right-click → "Add Nodes" → browse design hierarchy
3. Set trigger conditions (e.g., `valid` rising edge)
4. Set sample depth (256–16384 samples)
5. Compile (SignalTap consumes MLAB/BRAM for capture buffer)

**Method 2 — preserve_signal TCL (Reproducible):**

```tcl
# In your .qsf, mark signals for SignalTap visibility
set_instance_assignment -name PRESERVE_SIGNAL ON -to "my_module:inst|counter[31:0]"
```

**Method 3 — Tcl SignalTap control (Automation):**

```tcl
# sigtap_capture.tcl — Automated SignalTap capture
load_package stp

# Open programmer and detect device
set cable [lindex [get_hardware_names] 0]
set device [lindex [get_device_names -hardware_name $cable] 0]

# Open SignalTap session
open_session -name "stp1" -hardware_name $cable -device_name $device

# Run SignalTap and wait for trigger
run
while {[string equal [get_state -name "stp1"] "RUNNING"]} {
    after 100
}

# Export captured data
export_data -name "stp1" -csv "capture.csv"
close_session -name "stp1"
```

### SignalTap vs Vivado ILA

| Feature | SignalTap II | Vivado ILA |
|---|---|---|
| **Add probes without recompiling** | Yes (post-fit mode) | No — must recompile |
| **Trigger conditions** | Multi-level, state-based | Single trigger per ILA core |
| **Sample depth** | Up to 16384 per instance | Limited by BRAM budget |
| **Storage type** | MLAB or M4K/M9K/M20K/BRAM | BRAM only |
| **Tcl automation** | Full (`quartus_stp`) | Full (`create_debug_core`) |
| **Multiple instances** | Yes | Yes |
| **Export formats** | CSV, VCD, WAV | VCD, CSV |

---

## IP Management

### QIP Files — The Quartus IP Format

Unlike Vivado's `.xci` files, Quartus uses **QIP** (Quartus IP) files to bundle IP:

| File | Purpose |
|---|---|
| **`.qip`** | Tcl script that adds all source files, constraints, and compilation settings for one IP |
| **`.qsys`** | Platform Designer system definition (references multiple `.qip` files) |
| **`.v`/`.sv`/`.vhd`** | Generated HDL (synthesis and simulation) |

```tcl
# Add IP to your project (in .qsf)
set_global_assignment -name QIP_FILE ../ip/altpll/altpll.qip
set_global_assignment -name QIP_FILE ../ip/fifo/fifo.qip

# Add IP search path (for custom IP)
set_global_assignment -name IP_SEARCH_PATHS /path/to/my/ip/|
```

### Creating Custom IP for Platform Designer

Custom IP needs a `_hw.tcl` file that describes the interfaces and parameters:

```tcl
# my_uart_hw.tcl — Platform Designer component descriptor

# Module definition
set_module_property NAME my_uart
set_module_property VERSION 1.0
set_module_property DISPLAY_NAME "Custom UART"

# Add files
add_file my_uart.v {SYNTHESIS SIMULATION}

# Avalon-MM slave interface (register access)
add_interface s1 avalon end
add_interface_port s1 address address Input 3
add_interface_port s1 writedata writedata Input 32
add_interface_port s1 readdata readdata Output 32
add_interface_port s1 chipselect chipselect Input 1
add_interface_port s1 write write Input 1

# Conduit interface (TX/RX pins)
add_interface external conduit end
add_interface_port external tx tx Output 1
add_interface_port external rx rx Input 1

# Clock and reset
add_interface clock clock end
add_interface_port clock clk clk Input 1
add_interface reset reset end
add_interface_port reset reset_n reset_n Input 1

# Parameters
add_parameter BAUD_RATE INTEGER 115200
set_parameter_property BAUD_RATE DISPLAY_NAME "Baud Rate"
set_parameter_property BAUD_RATE ALLOWED_RANGES {9600 19200 38400 57600 115200 921600}
```

For more detail on IP packaging, see [Intel IP Packaging](../06_ip_and_cores/ip_reuse/intel_packaging.md).

---

## Quartus vs Vivado — Key Differences

| Aspect | Quartus Prime | Vivado |
|---|---|---|
| **Constraint system** | Dual: `.qsf` (physical) + `.sdc` (timing) | Single `.xdc` (both) |
| **Constraint order** | Order-independent (SDC processed as set) | Order-sensitive (XDC processed top-to-bottom) |
| **Project file** | `.qpf` + `.qsf` (human-readable Tcl) | `.xpr` (XML-based, not human-friendly) |
| **IP format** | `.qip` (Tcl) + `.qsys` (JSON-like) | `.xci` (XML) |
| **Block design tool** | Platform Designer | IP Integrator |
| **On-chip debug** | SignalTap II (can add without recompile) | ILA (must recompile) |
| **Bus standard** | Avalon-MM / Avalon-ST (native), AXI (compat) | AXI4 family (native) |
| **Incremental build** | Design Partitions (granular) | Incremental compile (checkpoint-based) |
| **Timing analyzer** | TimeQuest (SDC) | Vivado STA (XDC) |
| **Simulator** | ModelSim-Altera (bundled with Lite) | xsim (built-in) |
| **License model** | Node-locked or floating (FlexNet) | Node-locked or floating |
| **Linux support** | Full (official) | Full (official) |

---

## Version Notes

| Version | Key Feature | Notes |
|---|---|---|
| **Quartus Prime 25.x** | Latest; Agilex 5/7 full support | Current release |
| **Quartus Prime 24.x** | Agilex 5 initial support | Stable |
| **Quartus Prime 21.x** | Last with Cyclone V Lite Edition support | Stable for MiSTer |
| **Quartus Prime 18.x** | Last widely used for Cyclone V | Good MiSTer compatibility |
| **Quartus II 13.0sp1** | Last version for Cyclone III/IV | Separate download; Windows XP era |

> **MiSTer note:** Most MiSTer cores build with Quartus Prime 17.0–21.x. Newer versions may require constraint or IP updates.

> **Version pinning:** Like Vivado, `.qpf`/`.qsf` files may not open in newer versions. Always archive your project before upgrading.

---

## Common Pitfalls and Solutions

### Build Failures

| Problem | Error Message | Fix |
|---|---|---|
| **Missing clock constraint** | `Error: Timing requirements for clock were not met` with unconstrained paths | Every input clock needs `create_clock` in `.sdc` |
| **Pin assignment conflict** | `Error: Pin <name> has multiple locations` | Check `.qsf` for duplicate `set_location_assignment` |
| **QIP file not found** | `Error: Can't find matching QIP file` | Add `set_global_assignment -name QIP_FILE` to `.qsf` |
| **Fitter placement failure** | `Error: Can't place <number> HSSI channels` | Transceiver placement is fixed — check pinout against transceiver bank locations |
| **SDC entity name mismatch** | `Warning: Ignored SDC command: could not find <name>` | SDC entity names must match HDL hierarchy exactly, including `|` path separators |

### Timing Closure

| Symptom | Likely Cause | Fix |
|---|---|---|
| **Failing setup on a clock domain** | Logic too deep for the period | Increase `PLACEMENT_EFFORT_MULTIPLIER` to 4–10 |
| **Failing setup after adding SignalTap** | SignalTap consumes routing resources | Reduce sample depth or move SignalTap to a less congested partition |
| **Hold violations** | Usually a corner case in I/O timing | Check `report_timing -hold`; ensure PLL phase shift is correct |
| **Inconsistent timing between runs** | Fitter seed randomization | Set `SEED` in `.qsf`: `set_global_assignment -name SEED 42` |

### Quartus GUI Issues

| Issue | Fix |
|---|---|
| **Compilation takes forever** | Close the "Compilation Report" tab during build — it updates continuously and slows things down |
| **SignalTap won't install** | Ensure SignalTap `.stp` file is added to project: `set_global_assignment -name SIGNALTAP_FILE my_stp.stp` |
| **Platform Designer can't find IP** | Check IP Search Path: Tools → Options → IP Catalog → Search Paths |
| **ModelSim-Altera not found** | Set `set_global_assignment -name EDA_SIMULATION_TOOL "ModelSim-Altera (Verilog)"` in `.qsf` |

---

## Altera Independence Timeline

| Date | Event |
|---|---|
| **2015** | Intel acquires Altera for ~$16.7B, rebrands as Intel PSG |
| **Late 2023** | Intel announces plan to spin out PSG as a standalone business |
| **Feb 2024** | Altera brand revived; Sandra Rivera appointed CEO |
| **Jan 2025** | Altera officially independent |
| **May 2025** | Raghib Hussain succeeds Rivera as CEO |
| **Sep 2025** | Silver Lake closes 51% acquisition ($8.75B); Intel retains 49% |
| **2026** | Altera operates as world's largest pure-play independent FPGA company |

**Impact on tooling:** None. Quartus Prime works identically. Downloads moved to [altera.com](https://www.altera.com). Existing Intel FPGA licenses remain valid; new licenses via Altera. Altera can now use multiple foundries (Intel + TSMC).

---

## Best Practices

1. **Use `quartus_sh --flow compile` for CI** — one command runs synthesis → fit → assembly → timing.
2. **Archive project before Quartus upgrade** — `.qpf`/`.qsf` files may not open in newer versions.
3. **SDC constraints are order-independent** — unlike Xilinx XDC, Quartus SDC is processed as a set.
4. **Never commit `db/` or `incremental_db/`** — these are build artifacts. Commit `.qsf`, `.sdc`, `.qip`, and `.qsys` files.
5. **Use `SEED` for reproducible builds** — `set_global_assignment -name SEED 42` eliminates fitter randomness.
6. **Prefer Tcl-generated Platform Designer systems** — GUI-dragged systems are not reproducible. Use `qsys_*` Tcl commands.
7. **Use ModelSim-Altera for simulation** — it's bundled with Quartus Lite and much better than xsim for complex designs.
8. **Export your design partition when stable** — saves compilation time for the unchanged parts of your design.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Quartus Prime Pro — Getting Started](https://docs.altera.com/r/docs/683463/current) | Altera | Project management, design flow overview, compilation basics |
| [Quartus Prime Pro — Design Compilation](https://docs.altera.com/r/docs/683236/current) | Altera | Synthesis, fitter, optimization strategies |
| [Quartus Prime Pro — Platform Designer](https://docs.altera.com/r/docs/683609/current) | Altera | System integration, Avalon/AXI interfaces, IP assembly |
| [Quartus Prime Pro — Scripting](https://docs.altera.com/r/docs/683432/current) | Altera | Tcl command reference, scripted build flows |
| [Quartus Prime Pro — Debug Tools](https://docs.altera.com/r/docs/683819/current) | Altera | SignalTap II, Signal Probe, In-System Sources and Probes |
| [Quartus Prime Pro — Programmer](https://docs.altera.com/r/docs/683039/current) | Altera | JTAG programming, flash configuration, standalone programmer |
| [Altera Software Installation & Licensing](https://docs.altera.com/r/docs/683472/current) | Altera | Download, install, license setup |
| [Tcl Scripting](../08_debug_and_tools/tcl_scripting.md) | This KB | Quartus Tcl patterns, SignalTap automation |
| [SDC Basics](../05_timing_and_constraints/sdc_basics.md) | This KB | SDC constraint syntax, cross-vendor comparison |
| [Constraint Quick Reference](../14_references/constraint_quickref.md) | This KB | XDC / SDC / QSF / LPF rosetta stone |
| [Command Cheatsheet](../14_references/command_cheatsheet.md) | This KB | Quick-reference commands for all vendors |
| [Intel IP Packaging](../06_ip_and_cores/ip_reuse/intel_packaging.md) | This KB | `_hw.tcl` format, custom IP for Platform Designer |
