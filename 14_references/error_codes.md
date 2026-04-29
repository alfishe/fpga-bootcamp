[← 14 References Home](README.md) · [← Project Home](../../README.md)

# Common Vendor Tool Errors & Resolution

Decoding cryptic FPGA tool errors is half the battle. This reference catalogs frequently encountered error codes from Vivado, Quartus, Yosys, and nextpnr with resolution steps.

---

## Vivado Common Errors

| Error | Message Text | Root Cause | Resolution |
|---|---|---|---|
| **[DRC 23-20]** | `Rule violation (REQP-1712) Input clock driver` | Unconstrained clock | Add `create_clock` to the input port |
| **[Timing 38-282]** | `The design did not meet timing` | Setup/hold violations | Review `report_timing_summary`, add pipeline stages or relax constraints |
| **[Opt 31-67]** | `A LUT cell has a constant input → trimmed` | Unused inputs optimized away | Normal if intentional. Check if signal was expected to be used. |
| **[Synth 8-3331]** | `Unconnected port` | Module port unconnected at instantiation | Connect or explicitly tie to 0. Not an error but generates warnings. |
| **[Place 30-574]** | `Poor placement for routing` | Congested region | Floorplan with pblocks, reduce utilization, or change I/O pinout |
| **[Route 35-54]** | `Net has unroutable placement` | Over-constrained routing | Relax placement, add more routing layers if possible |
| **[Bitstream 30-73]** | `DONE pin not asserted` | Configuration failure | Check INIT_B state, verify flash image, check power sequencing |

### Vivado Tcl Debug Commands
```tcl
# Show critical warnings only
report_critical_warnings -file crit.rpt

# Detailed timing for one path
report_timing -from [get_pins src/Q] -to [get_pins dst/D] -file path.rpt

# Why is a net unrouted?
report_route_status -unrouted
```

---

## Quartus Common Errors

| Error ID | Message | Root Cause | Resolution |
|---|---|---|---|
| **12006** | `Node instance instantiates undefined entity` | Missing source file | Add file to project or fix toplevel name |
| **13076** | `Cannot locate PLL` | PLL constraints impossible to meet | Check input clock frequency, PLL divider ranges |
| **14801** | `Output pin stuck at VCC/GND` | Constant-driven output | Check logic driving that pin — it's been synthesized to constant |
| **17015** | `Can't place I/O pin` | Pin location conflict | Check pin assignment, look for double-assigned pin |
| **176310** | `Can't fit design in device` | Over-utilization (>100%) | Reduce logic, enable optimization, or move to larger device |
| **18923** | `Illegal clock domain crossing detected` | Unconstrained CDC | Add `set_false_path` or `set_clock_groups -asynchronous` |

### Quartus Debug Commands
```bash
# Chip planner for visualizing placement
quartus_cdb my_project --chip_planner

# Resource utilization breakdown
quartus_fit --report_utilization=full my_project

# Design partition for incremental compilation
quartus_sh --flow compile my_project --incremental
```

---

## Yosys Common Errors

| Error | Message | Resolution |
|---|---|---|
| `ERROR: Module not found` | Missing module definition | Check file paths, verify all modules are in source list |
| `WARNING: found logic loop` | Combinational loop detected | Add register to break loop; combinational loops are unsynthesizable |
| `ERROR: Multiple non-tristate drivers` | Net driven by multiple always blocks | Use only one always block per signal, or use tri-state only at top level |
| `ERROR: Unsupported SystemVerilog feature` | SV feature not supported in Yosys | Rewrite using Verilog-2005 compatible syntax or use Verilator for SV |

---

## nextpnr Common Errors

| Error | Message | Resolution |
|---|---|---|
| `ERROR: Unable to place cell X at BEL Y` | Placement conflict | Relax placement constraints or use `--placed-skip` to ignore |
| `ERROR: Timing constraints not met` | Failed to meet timing | Increase clock period, pipeline design, or use `--ignore-timing` for bring-up |
| `ERROR: No route for net` | Congestion, impossible route | Reduce utilization, change pinout, or use `--router router2` (alt router) |

### nextpnr Debug Flags
```bash
# Generate visual placement/routing
nextpnr-ecp5 --json synth.json --textcfg config.txt \
    --placed-svg placed.svg --routed-svg routed.svg

# Relax timing for initial bring-up
nextpnr-ecp5 --json synth.json --ignore-timing
```

---

## Universal Debug Flow

When you hit an error, follow this sequence before asking for help:

1. **Read the ENTIRE error message** — not just the first line
2. **Check the .log/.rpt file** — full context often reveals root cause
3. **Google the error code** — `[Place 30-574]` (in quotes) + vendor name
4. **Check the synthesis schematic** — is the logic what you expect?
5. **Simplify** — reduce to minimal design that reproduces the error
6. **Compare with a known-working design** — diff constraints and settings
