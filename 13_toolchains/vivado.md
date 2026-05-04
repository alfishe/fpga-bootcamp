[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Xilinx Vivado — Design Suite for 7-Series, UltraScale+, Versal

Vivado is AMD/Xilinx's unified design environment for all devices from 7-series (2010) through Versal (current). It replaces the older ISE toolchain (Spartan-6/Virtex-6 and earlier) and provides synthesis, implementation, simulation, debug, and IP integration in one framework. This article covers the practical aspects of using Vivado that every FPGA developer needs: build flows, Tcl scripting, IP management, debug strategies, and the many pitfalls that waste hours if you don't know them.

> **Prerequisites:** This article assumes familiarity with the [design flow overview](../03_design_flow/overview.md) and [XDC constraints](../05_timing_and_constraints/sdc_basics.md). For Tcl scripting patterns, see [Tcl Scripting](../08_debug_and_tools/tcl_scripting.md). For quick command reference, see [Command Cheatsheet](../14_references/command_cheatsheet.md).

---

## Editions

| Edition | Devices Supported | Cost |
|---|---|---|
| **Vivado ML Standard** | All 7-series, Zynq-7000, small UltraScale+ (XCKU3P, XCZU2–5) | Free (WebPack license) |
| **Vivado ML Enterprise** | All devices including large UltraScale+, Versal | Paid (~$3,000+/year) |

**WebPack device limits:** Artix-7 up to XC7A200T, Kintex-7 up to XC7K70T, Zynq-7000 up to XC7Z030. For anything larger (Kintex UltraScale+, Zynq MPSoC, Versal), you need Enterprise.

> **Tip:** The WebPack license is node-locked (tied to one machine's MAC address). If you need to move it, you must return the license first. Enterprise licenses can be floating (network server).

---

## Project vs Non-Project Mode

| Feature | Project Mode | Non-Project Mode |
|---|---|---|
| **Storage** | `.xpr` file + directory tree | All in-memory, script-driven |
| **GUI** | Full block design, IP integrator | Tcl console only |
| **Reproducibility** | Project state drifts with GUI clicks | Script is the source of truth |
| **CI/CD** | Difficult (project files don't diff) | Ideal — scripts are version-controlled |
| **Build time** | Same implementation engine | Same |
| **Debug** | GUI ILA insertion, Signal Tap–like | Must instantiate ILA in RTL or use `create_debug_core` Tcl |
| **Best for** | Exploration, block design, IP integration | Production builds, regression, CI |

> **Recommendation:** Use project mode for initial exploration and block design. For anything that ships or is built in CI, convert to non-project Tcl script. The `write_project_tcl` command can generate a starting point, but its output is verbose — manually rewrite for clarity.

---

## Non-Project Build Flow — Complete Script

This is the production-ready Vivado build flow. Every step is a Tcl command, no GUI needed.

```tcl
#!/usr/bin/env vivado -mode batch -source
# ═══════════════════════════════════════════════════════
#  vivado_build.tcl — Non-project mode build script
#  Usage: vivado -mode batch -source vivado_build.tcl
# ═══════════════════════════════════════════════════════

set PROJECT  "my_design"
set PART     "xc7a35tcpg236-1"
set TOP      "top"

# ── 1. Create in-memory design ──
create_project -in_memory -part $PART

# ── 2. Read source files ──
read_verilog -sv [glob ../rtl/*.sv]
read_verilog [glob ../rtl/*.v]
read_vhdl [glob ../rtl/*.vhd]

# Read constraints — ORDER MATTERS for XDC
read_xdc ../constraints/clocks.xdc     ;# Clock definitions first
read_xdc ../constraints/io.xdc         ;# Pin assignments second
read_xdc ../constraints/timing.xdc     ;# Timing exceptions last

# Read vendor IP (XCI files — do NOT read generated HDL)
read_ip [glob ../ip/**/*.xci]

# ── 3. Synthesis ──
synth_design -top $TOP -part $PART \
    -verilog_define "SYNTHESIS=1" \
    -flatten_hierarchy rebuilt \
    -gated_clock_conversion auto \
    -bufg 12

# Save post-synthesis checkpoint (resume here if P&R fails)
write_checkpoint -force ../build/post_synth.dcp
report_timing_summary -file ../build/synth_timing.rpt
report_utilization -file ../build/synth_util.rpt

# ── 4. Implementation ──
opt_design
place_design
route_design

# Save post-implementation checkpoint
write_checkpoint -force ../build/post_route.dcp

# ── 5. Reports ──
report_timing_summary -max_paths 10 -file ../build/timing.rpt
report_utilization -file ../build/utilization.rpt
report_drc -file ../build/drc.rpt
report_power -file ../build/power.rpt

# ── 6. Bitstream ──
write_bitstream -force ../build/${PROJECT}.bit

# Generate SPI flash image (for BPI/SPI programming)
write_cfgmem -format mcs -size 16 -interface spix4 \
    -loadbit "up 0x0 ../build/${PROJECT}.bit" \
    -force ../build/${PROJECT}.mcs
```

### Implementation Strategies

Vivado provides preset strategies that configure the implementation engine:

| Strategy | What It Does | When to Use |
|---|---|---|
| **Default** | Balanced effort | Most designs — start here |
| **Performance_Explore** | Tries multiple placer configurations | Timing closure problems on critical paths |
| **Performance_ExplorePostRoutePhysOpt** | Post-route physical optimization | Last resort for failing setup paths |
| **Area_Optimized_High** | Aggressive area optimization | LUT-constrained designs |
| **Flow_RuntimeOptimized** | Skips optional optimization | Fast iteration during development |

```tcl
# Apply strategy in non-project mode
set_property strategy Performance_Explore [current_run impl_1]
```

### Incremental Builds

If only a small part of the design changed, incremental compile reuses the previous placement:

```tcl
# Point to the reference checkpoint from the last successful build
read_checkpoint -incremental ../build/post_route_reference.dcp

# Run implementation — unchanged cells keep their placement
place_design
route_design
```

**When it helps:** If <5% of logic changed, incremental runs are typically 2–4× faster with identical or better timing.

**When it hurts:** If >20% of logic changed, the placer fights the reference placement and may produce worse results than a clean run.

---

## Project Mode — Block Design Flow

Block design (IP Integrator) is the visual way to assemble systems from IP cores. It's the only practical way to configure complex IP like the Zynq PS, PCIe DMA, or MIPI subsystems.

### Creating a Block Design

```tcl
# Create block design
create_bd_design "system"

# Add Zynq PS (MPSoC example)
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 zynq_ps

# Apply board preset (automatically configures DDR, clocks, MIO)
set_property -dict [list \
    CONFIG.PSU__DDR__SPEED_BIN {DDR4_2400T} \
    CONFIG.PSU__DDR__DEVICE_CAPACITY {4096MBits} \
] [get_bd_cells zynq_ps]

# Add AXI GPIO
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 gpio_leds

# Connect: PS M_AXI_HPM0_FPD → GPIO S_AXI
connect_bd_intf_net [get_bd_intf_pins zynq_ps/M_AXI_HPM0_FPD] \
                    [get_bd_intf_pins gpio_leds/S_AXI]

# Auto-connect clocks and resets
apply_bd_automation_settings -config { Master /Slave Clk: "Auto" }

# Validate design (catches connectivity errors before synthesis)
validate_bd_design

# Generate HDL wrapper
make_wrapper -files [get_files system.bd] -top
add_files -norecurse ../build/sources_1/bd/system/hdl/system_wrapper.v
```

### Block Design Gotchas

| Pitfall | What Happens | Fix |
|---|---|---|
| **Forgetting `validate_bd_design`** | Synthesis fails with cryptic errors | Always validate before generating wrapper |
| **Not regenerating after IP version change** | Stale wrapper HDL, missing ports | Delete old wrapper, regenerate with `make_wrapper` |
| **External ports without `make_external`** | Signals are unconnected in wrapper | Use `make_external` on BD ports you need at top level |
| **Clock domain crossing in BD** | CDC not caught by validation | Insert AXI4-Stream Data FIFO or asynchronous FIFO IP |
| **Too many automation prompts** | Auto-connect creates spaghetti routing | Connect critical paths manually; use automation for clock/reset only |

---

## IP Management

### Instantiating IP

Three approaches, in order of preference for production:

| Method | How | Best For | Reproducible? |
|---|---|---|---|
| **XCI file + `read_ip`** | `read_ip clk_wiz.xci` | Production non-project flow | Yes — XCI is the source of truth |
| **Tcl `create_ip`** | `create_ip -name clk_wiz -vendor xilinx.com ...` | CI/CD, script-generated IP | Yes — fully scripted |
| **GUI customization** | Double-click IP in catalog | Exploration only | No — state in GUI only |

```tcl
# Method 2: Create and configure IP entirely in Tcl
create_ip -name clk_wiz -module_name clk_wiz_100 -vendor xilinx.com \
    -library ip -version 6.0

set_property -dict [list \
    CONFIG.PRIM_SOURCE {Differential_clock_capable_pin} \
    CONFIG.PRIM_IN_FREQ {200.000} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {100.000} \
    CONFIG.CLKOUT2_REQUESTED_OUT_FREQ {50.000} \
    CONFIG.USE_LOCKED {true} \
    CONFIG.USE_RESET {true} \
] [get_ips clk_wiz_100]

# Generate IP output products
generate_target all [get_ips clk_wiz_100]
```

### Packaging Custom IP

To make your own module appear in the IP catalog:

1. **Tools → Create and Package New IP** (or `ipx::package_project`)
2. Set the top-level module as the IP interface
3. Define port interfaces (AXI4-Lite, AXI4-Stream, clock, reset)
4. Add parameterization (generics → GUI customization)
5. Set supported families and default part

```tcl
# Package IP from command line
ipx::package_project -root_dir ../ip/my_ip -vendor mycorp.com \
    -library user -taxonomy /UserIP

# Add file groups
ipx::add_file_group -type {xilinx_anylanguagesim} [ipx::current_core]
ipx::add_file ../rtl/my_module.sv [ipx::get_file_groups xilinx_anylanguagesim]

# Set top module
ipx::set_core_top_module [ipx::current_core] my_module
ipx::update_checksums [ipx::current_core]
ipx::check_integrity [ipx::current_core]
ipx::save_core [ipx::current_core]
```

---

## Debug — ILA and VIO

Vivado's on-chip debug uses the Integrated Logic Analyzer (ILA) and Virtual Input/Output (VIO) cores. These are the Xilinx equivalents of Intel's SignalTap.

### ILA Instantiation in RTL

```verilog
// Mark signals for debug with the mark_debug attribute
(* mark_debug = "true" *) reg [31:0] debug_counter;
(* mark_debug = "true" *) reg        debug_valid;

// ILA core instantiation
ila_0 my_ila (
    .clk    (clk),
    .probe0 (debug_counter),  // 32-bit bus
    .probe1 (debug_valid),    // 1-bit signal
    .probe2 (state_reg)       // auto-width from port width
);
```

### Set Up Debug in Tcl (Non-Project Mode)

```tcl
# After synthesis, before implementation:
open_checkpoint ../build/post_synth.dcp

# Create ILA core
create_debug_core u_ila ila
set_property C_DATA_DEPTH 1024 [get_debug_cores u_ila]
set_property C_TRIGIN_EN false [get_debug_cores u_ila]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila]

# Add probe ports
create_debug_port u_ila probe
set_property PROBE_PORT_DATA_IDX 0 [get_debug_ports u_ila/probe1]
set_property PORT_WIDTH 32 [get_debug_ports u_ila/probe1]

# Connect probes to nets
connect_debug_port u_ila/probe1 [get_nets debug_counter[*]]
connect_debug_port u_ila/probe2 [get_nets debug_valid]

# Write debug probes file
write_debug_probes -force ../build/debug_probes.ltx

# Continue to implementation
opt_design
place_design
route_design
write_bitstream -force ../build/design_debug.bit
```

### Debug Workflow

```
1. Program device with debug bitstream + .ltx file
2. Set trigger (e.g., debug_valid rising edge)
3. Arm trigger
4. Trigger fires → captured waveforms appear in GUI
5. Analyze in waveform viewer or export to VCD
```

### ILA Depth vs BRAM Cost

| Depth | BRAM (36Kb) per 256-bit probe | When to Use |
|---|---|---|
| 256 | 1 | Quick sanity check |
| 1024 | 4 | Standard — enough for most protocols |
| 4096 | 16 | Deep capture — packet traces, long state sequences |
| 16384 | 64 | Very deep — only for small probe widths |

> **Warning:** ILA consumes BRAM that your design needs. If you're at 80%+ BRAM utilization, adding a deep ILA can push you over. Always check post-synth utilization before adding debug cores.

---

## Vivado Simulator (xsim)

The built-in simulator supports Verilog, SystemVerilog, and VHDL mixed-language simulation. It's free with Vivado but has limitations compared to Questa/ModelSim.

| Feature | xsim | Questa (paid) |
|---|---|---|
| **SystemVerilog UVM** | Limited (1.2 partial) | Full UVM 1.2 |
| **Coverage** | Functional + toggle | Full coverage (code, functional, assertion) |
| **Performance** | Adequate for <100K cycles | 5–10× faster on large designs |
| **Waveform viewer** | Vivado GUI | DVE / Qt waveform |
| **Cost** | Included with Vivado | $5K–$30K |

```tcl
# Run simulation from Tcl
launch_simulation
run 10 us
```

```bash
# Batch simulation from command line
xsim tb_top -R -log sim.log
```

**When xsim is fine:** Quick RTL sanity checks, block-level testbenches, ILA-triggered debug verification.

**When you need Questa:** UVM testbenches, large SoC simulations, coverage sign-off, regression suites.

---

## Vivado Version Compatibility

| Vivado Version | Device Support | Notes |
|---|---|---|
| **2025.x** | All through Versal | Latest features, bug fixes |
| **2024.x** | All through Versal | Current LTS-like |
| **2023.x** | All through Versal | Stable, widely used |
| **2020.x** | All through UltraScale+ | Last version that opened some older 7-series project formats |
| **2018.x** | All through UltraScale+ | Last with full 7-series IP version support |
| **ISE 14.7** | Spartan-6, Virtex-6, older | End-of-life; Windows 10/11 compatibility issues |

**Version pinning is critical:** Vivado `.xpr` files are NOT backward-compatible. A project created in 2024.1 cannot be opened in 2023.2. IP cores have the same restriction — IP generated in 2024.1 won't work in 2023.2.

---

## Common Pitfalls and Solutions

### Build Failures

| Problem | Error Message | Fix |
|---|---|---|
| **Missing clock constraint** | `[Timing 38-282] The design did not meet timing` with unconstrained paths | Every input clock needs `create_clock`. Check `report_clocks` |
| **XDC order sensitivity** | Constraints seem ignored | XDC is processed top-to-bottom. Put `create_clock` before `set_input_delay` |
| **IP not generated** | `[Common 17-55] Cannot find IP output products` | Run `generate_target all [get_ips]` before synthesis |
| **Black box in netlist** | `[Synth 8-439] module 'xxx' is a black box` | Source file not added; or Verilog define guard excluding the module |
| **Write lock on project** | `[Common 17-69] Failed to open project` | Another Vivado instance has it open. Kill zombie processes |

### Timing Closure

| Symptom | Likely Cause | Fix |
|---|---|---|
| **Failing setup on intra-clock paths** | Logic too deep for the period | Pipeline, retiming, or use `PHYS_OPT_RETIMING` |
| **Failing setup on cross-clock paths** | Missing CDC constraint | Add `set_clock_groups -asynchronous` and verify synchronizer exists in RTL |
| **Hold violations** | Rare in functional design; usually constraint issue | Check that `create_generated_clock` is correct for all PLL outputs |
| **Negative slack getting worse with each run** | Placement jitter | Set `SEED` value: `set_property SEED 42 [current_run]` |

### Vivado GUI Slowness

| Issue | Fix |
|---|---|
| **GUI takes 5+ min to open** | Disable unused plugins: `Vivado → Help → Disable/Enable Tools` |
| **Schematic viewer hangs** | Don't open schematic on large designs (>100K LUTs). Use `report_timing` instead |
| **Block design slow** | Disable animation: `Tools → Settings → BD → Animation → Off` |
| **Memory usage >32 GB** | Close unused runs: `reset_run impl_1` clears in-memory data |

---

## Vivado vs ISE Quick Reference

For developers migrating from ISE (Spartan-6/Virtex-6 era):

| ISE Concept | Vivado Equivalent |
|---|---|
| `.ise` project | `.xpr` project |
| UCF constraints | XDC constraints (Tcl-based, completely different syntax) |
| `xst` synthesis | `synth_design` (Vivado synthesis) |
| `MAP` | `opt_design` + `place_design` |
| `PAR` (Place & Route) | `place_design` + `route_design` |
| `bitgen` | `write_bitstream` |
| `impact` (programming) | `Hardware Manager` / `program_hw_devices` |
| `ChipScope` | ILA (Integrated Logic Analyzer) |
| `PlanAhead` | Vivado IDE (absorbed into Vivado) |
| `EDK` / `XPS` | IP Integrator (block design) |
| Core Generator (`coregen`) | IP Catalog (`create_ip` / GUI) |

---

## Best Practices

1. **Pin your Vivado version** — don't upgrade mid-project. `.xpr` and IP are not backward-compatible.
2. **Use `write_checkpoint` after synthesis** — saves hours if implementation fails; resume from checkpoint with `open_checkpoint`.
3. **Incremental compile saves 50%+ time** — use `read_checkpoint -incremental` when changes are small.
4. **XDC is order-sensitive** — constraints are processed sequentially. Put clock constraints first, then IO, then exceptions.
5. **Never commit `*.runs/` or `*.cache/`** — these are build artifacts. Commit `.xci` files (IP source), not generated HDL.
6. **Use `flatten_hierarchy rebuilt`** — preserves hierarchy boundaries for timing analysis while still optimizing across boundaries.
7. **Set `SEED` for reproducible builds** — `set_property SEED <value> [current_run]` eliminates placement jitter between runs.
8. **Always run `report_drc`** before bitstream generation — catches issues like disconnected pins, illegal IO standards.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [UG910 — Vivado Getting Started](https://docs.amd.com/r/en-US/ug910-vivado-getting-started) | AMD/Xilinx | Installation, licensing, first project walkthrough |
| [UG893 — Using the Vivado IDE](https://docs.amd.com/r/en-US/ug893-vivado-ide) | AMD/Xilinx | GUI navigation, project management, design flows |
| [UG835 — Tcl Command Reference](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands) | AMD/Xilinx | Complete Tcl command reference for all Vivado operations |
| [UG949 — UltraFast Design Methodology](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology) | AMD/Xilinx | Best practices for coding, constraints, and timing closure |
| [UG896 — Designing with IP](https://docs.amd.com/r/en-US/ug896-vivado-ip) | AMD/Xilinx | IP instantiation, customization, and management |
| [UG903 — Using Constraints](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints) | AMD/Xilinx | XDC syntax, timing constraints, physical constraints |
| [Tcl Scripting](../08_debug_and_tools/tcl_scripting.md) | This KB | Vivado Tcl patterns, non-project flow, netlist queries |
| [XDC / SDC / LPF Quick Reference](../14_references/constraint_quickref.md) | This KB | Cross-vendor constraint syntax comparison |
| [Command Cheatsheet](../14_references/command_cheatsheet.md) | This KB | Quick-reference commands for Vivado, Quartus, Lattice |
| [Design Flow Overview](../03_design_flow/overview.md) | This KB | Six-stage FPGA design pipeline |
| [Project Structure](../03_design_flow/project_structure.md) | This KB | Recommended directory layout, gitignore patterns |
