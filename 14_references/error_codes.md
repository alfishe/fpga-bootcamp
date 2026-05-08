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

## Vivado Implementation Errors

| Error | Message Text | Root Cause | Resolution |
|---|---|---|---|
| **[Place 30-492]** | `Unplaced ports` | I/O placement conflict | Check pin assignments for conflicts in the same bank |
| **[Place 30-574]** | `Non-clock resource driving clock` | Clock routed through fabric | Use clock-capable pins; add `CLOCK_DEDICATED_ROUTE TRUE` |
| **[Route 35-39]** | `Route is partially routed` | Congestion or over-constraint | Floorplan the design; reduce utilization |
| **[DRC 18-155]** | `Diff pair not placed together` | P/N pins in different sites | Place both on the same differential pair site |
| **[DRC 23-20]** | `REQP-1614 VCCO conflict` | Different IOSTANDARD on same bank | All pins in a bank must use the same VCCO |

---

## Quartus Fitter Errors

| Error ID | Message | Root Cause | Resolution |
|---|---|---|---|
| **18243** | `Fitter placement error` | Can't meet timing + placement simultaneously | Add floorplan assignments; relax fitter effort |
| **19551** | `Input pin driven by I/O element` | Signal connects through IO element incorrectly | Check bidirectional pin assignments |
| **21610** | `PLL could not be placed` | No PLL site near clock input | Move clock pin assignment to a clock-capable pin |
| **29313** | `Router transit time limit exceeded` | Route too long for timing | Add pipeline register or floorplan closer placement |

---

## Timing Closure Errors

| Symptom | Vendor | Typical Error | Resolution Steps |
|---|---|---|---|
| **Negative setup slack** | Any | WNS < 0 | 1) Check constraints are correct 2) Add pipeline stages 3) Reduce logic levels 4) Floorplan |
| **Negative hold slack** | Any | WHS < 0 | 1) Usually a constraint issue (missing `set_clock_groups`) 2) Check for false paths 3) Don't over-constrain |
| **Intra-clock path failure** | Any | Path within one domain fails | 1) Add registers 2) Use faster speed grade 3) Optimize logic |
| **Inter-clock path failure** | Any | CDC path fails | 1) Add synchronizer 2) Add `set_clock_groups -asynchronous` 3) Check missing constraints |
| **Pulse width violation** | Vivado | WPWS < 0 | Duty cycle distortion; check PLL/MMCM configuration |

---

## Simulation Errors

| Error | Simulator | Cause | Fix |
|---|---|---|---|
| **X (unknown) in simulation** | All | Uninitialized signal or undriven net | Initialize all regs in `initial` block; check for missing drivers |
| **Z (high-impedance) in simulation** | All | Undriven tri-state net | Check `if-else` branches cover all cases; add default assignments |
| **$finish called** | Icarus/Vivado | Testbench explicitly ended | Normal if intentional; if unexpected, check testbench timeout logic |
| **Simulation hangs** | All | Zero-delay loop or circular dependency | Check for combinational loops; add #1 delays for debug |
| **VHDL `access violation`** | ModelSim | Reading uninitialized signal | Initialize signals in architecture declarations |

---

## Bitstream & Configuration Errors

| Error | Vendor | Symptom | Fix |
|---|---|---|---|
| **DONE pin not asserted** | Xilinx | FPGA won't configure | Check flash image; verify power rails; check INIT_B status |
| **CRC error during config** | Xilinx | Configuration aborts | Bitstream corrupted; check flash integrity; verify encryption key |
| **CONF_DONE error** | Intel | FPGA won't configure | Similar to DONE; check programming cable and JTAG speed |
| **SEU error** | Xilinx/Intel | Soft error in config memory | Run configuration scrubbing; check error injection circuitry |
| **Bitstream authentication fail** | Any | Encrypted bitstream rejected | Verify AES key matches; check key delivery mechanism |

---

## Universal Debug Flow

When you hit an error, follow this sequence before asking for help:

1. **Read the ENTIRE error message** — not just the first line
2. **Check the .log/.rpt file** — full context often reveals root cause
3. **Google the error code** — `[Place 30-574]` (in quotes) + vendor name
4. **Check the synthesis schematic** — is the logic what you expect?
5. **Simplify** — reduce to minimal design that reproduces the error
6. **Compare with a known-working design** — diff constraints and settings
7. **Check vendor forums** — Xilinx Forums, Intel Community, r/FPGA
8. **Check the constraint file** — 50% of timing errors are missing or wrong constraints

---

## Quick Diagnosis: Error Category → Action

| Error Category | First Action | Second Action |
|---|---|---|
| **Synthesis error** | Check HDL syntax and module ports | Check if all files are in the source list |
| **DRC error** | Read the full DRC message; it tells you exactly what's wrong | Fix the pin/standard/bank conflict |
| **Placement error** | Check if utilization < 80% | Add floorplan (Pblocks/LogicLock) |
| **Routing error** | Reduce congestion | Check for over-constrained placement |
| **Timing error** | Verify constraints first (most common cause) | Add pipeline stages or floorplan |
| **Config error** | Check power sequencing | Verify flash image and JTAG connection |
| **Simulation mismatch** | Compare against C reference model | Check for uninitialized signals |

---

## Cross-References

| Topic | Article |
|---|---|
| Constraint syntax reference | [Constraint Quickref](constraint_quickref.md) |
| Timing closure techniques | [SDC Basics](../05_timing_and_constraints/sdc_basics.md) |
| DDR calibration errors | [Debugging DDR](../15_case_studies/debugging_ddr.md) |
| PCIe link training errors | [PCIe Bringup](../15_case_studies/pcie_bringup.md) |
| Board bring-up troubleshooting | [Bring-Up Checklist](../15_case_studies/bring_up_checklist.md) |
