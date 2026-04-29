[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# Tcl Scripting — Automating Vendor FPGA Tools

Every major FPGA vendor toolchain exposes a Tcl API. Mastering it means you never click through GUI wizards — you script builds, automate analysis, and run regression tests in CI. This covers Vivado Tcl, Quartus Tcl, and the non-project (scripted) flow.

---

## Why Tcl?

Tcl is the embedded scripting language of EDA tools. It was chosen in the 1990s because:
- Simple syntax (everything is a string → easy to generate programmatically)
- Built-in event loop for GUI integration
- Extensible — vendors add thousands of custom commands

Today, Tcl is the ONLY way to:
- Automate builds without the GUI (CI/CD)
- Generate reports and extract timing data
- Script ILA/SignalTap trigger conditions
- Control Vivado/Quartus in non-project mode

---

## Vivado Tcl

### Non-Project Mode (Scripted Flow)

```tcl
# vivado_build.tcl — Full build without GUI

# Create in-memory project (no .xpr file)
create_project -in_memory -part xc7z020clg400-1

# Add source files
add_files -norecurse {
    ../rtl/top.v
    ../rtl/axi_slave.v
    ../rtl/pipeline.v
}
add_files -fileset constrs_1 ../constraints/top.xdc

# Set top module
set_property top top [current_fileset]

# Synthesis
launch_runs synth_1 -jobs 8
wait_on_run synth_1

# Check timing after synthesis (optional but recommended)
open_run synth_1
report_timing_summary -file syn_timing.rpt

# Implementation
launch_runs impl_1 -jobs 8
wait_on_run impl_1

# Post-route reports
open_run impl_1
report_timing_summary -file timing.rpt
report_utilization -file utilization.rpt
report_power -file power.rpt

# Generate bitstream
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

# Export hardware for Vitis/SDK
write_hw_platform -fixed -include_bit -file design.xsa
```

### Common Vivado Tcl Commands

| Command | Purpose |
|---|---|
| `get_pins -of [get_cells]` | Navigate netlist hierarchy |
| `get_clocks` / `get_clock_domains` | Inspect clock constraints |
| `report_timing -from [get_pins] -to [get_pins]` | Path-specific timing |
| `report_drc` | Design rule check (pre-bitstream) |
| `get_property SLACK [get_timing_paths]` | Extract worst slack |
| `write_bitstream -force` | Generate .bit file |
| `write_debug_probes` | Write ILA probe file (.ltx) |

---

## Quartus Tcl

### Non-Project Flow (Quartus)

```tcl
# quartus_build.tcl — Scripted build

# Project setup
project_new top -overwrite -family "Cyclone V" \
    -part 5CSEBA6U23I7

# Add source files
set_global_assignment -name VERILOG_FILE ../rtl/top.v
set_global_assignment -name VERILOG_FILE ../rtl/axi_slave.v
set_global_assignment -name SDC_FILE ../constraints/top.sdc

# Set top-level entity
set_global_assignment -name TOP_LEVEL_ENTITY top

# Compile
load_package flow
execute_flow -compile

# Reports
load_report
report_timing -panel "Timing Analyzer||Timing Analyzer Summary"

# Generate SOF
project_close
```

### Quartus-Specific Tcl Tools

| Tool | Purpose | Example |
|---|---|---|
| `quartus_sh` | Shell/synthesis flow | `quartus_sh -t build.tcl` |
| `quartus_stp` | SignalTap control | `quartus_stp -t sigtap_capture.tcl` |
| `quartus_pgm` | Programmer | `quartus_pgm -c "USB-Blaster" -m JTAG -o "p;output.sof"` |
| `quartus_cdb` | Chip database (timing netlist) | `quartus_cdb top --merge=on` |
| `quartus_fit` | Fitter only | `quartus_fit top` |
| `quartus_sta` | Timing Analyzer standalone | `quartus_sta top` |

### SignalTap Capture Script

```tcl
# sigtap_capture.tcl — Automated SignalTap capture

# Open programmer and detect device
set cable [lindex [get_hardware_names] 0]
set device [lindex [get_device_names -hardware_name $cable] 0]

# Open SignalTap file
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

---

## Common Automation Patterns

### CI Build Script Skeleton

```tcl
# ci_build.tcl — CI-optimized with exit codes

proc run_build {} {
    # Init
    set start [clock seconds]

    # Synthesis
    if {[catch {synth_design -top top -part $::part} err]} {
        puts "SYNTHESIS FAILED: $err"
        exit 1
    }

    # Check timing pre-route
    if {[get_property SLACK [get_timing_paths -max_paths 1]] < 0} {
        puts "TIMING VIOLATION in synthesis — aborting"
        exit 2
    }

    # Implementation
    if {[catch {place_design; route_design} err]} {
        puts "PLACE & ROUTE FAILED: $err"
        exit 3
    }

    # Post-route timing
    set wns [get_property SLACK [get_timing_paths -max_paths 1]]
    puts "Worst Negative Slack: $wns ns"
    if {$wns < -0.300} {
        exit 4  ;# Fail if slack worse than -300 ps
    }

    set elapsed [expr {[clock seconds] - $start}]
    puts "Build completed in ${elapsed}s"
    exit 0
}

run_build
```

### Extracting Timing from Multiple Corners

```tcl
# Report timing across all corners (multi-corner analysis)
foreach corner {slow_0C slow_85C fast_0C fast_85C} {
    set_operating_conditions -name $corner
    report_timing -file "timing_${corner}.rpt"
}
```

---

## Best Practices

1. **Always set exit codes** — CI needs to know if the build passed. `exit 0` for success, non-zero for failure.
2. **Use non-project mode for CI** — project mode stores state in `.xpr`/`.qpf` files that drift. Scripted mode is reproducible.
3. **Version-control the Tcl scripts, not the project files** — `.tcl` files diff cleanly; `.xpr` files don't.
4. **Include timing checks in the build script** — don't wait for a human to open the timing report.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Missing `-in_memory` for Vivado project** | `.xpr` file created, pollutes CI workspace | Use `create_project -in_memory` |
| **`wait_on_run` missed** | Next step runs before synthesis/impl completes | Always `wait_on_run` after `launch_runs` |
| **Tcl variable substitution bug** | Square brackets `[]` interpreted as command substitution | Use braces `{}` instead of quotes for strings with brackets |
| **Quartus project file conflict** | Multiple CI jobs overwrite same `.qsf` | Set `PROJECT_OUTPUT_DIRECTORY` per-job |

---

## References

| Source | Path |
|---|---|
| Vivado Tcl Command Reference (UG835) | Xilinx / AMD |
| Vivado Design Suite Tcl Guide (UG894) | Xilinx / AMD |
| Quartus Prime Tcl Scripting Manual | Intel FPGA Documentation |
| Quartus Command-Line Scripting (quartus_sh) | Intel FPGA Documentation |
