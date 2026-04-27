[← Section Home](README.md) · [← Project Home](../README.md)

# Timing Closure — From Red Numbers to a Passing Design

Timing closure is the iterative process of making a design meet all setup and hold constraints at the target clock frequency. It consumes 30–60% of a typical FPGA project schedule. Unlike functional bugs — which produce wrong outputs — timing failures produce **no outputs at all** (the design won't generate a bitstream) or, worse, **intermittent failures** that depend on temperature, voltage, and silicon lot.

This article covers the methodology end-to-end: reading timing reports, identifying the real bottlenecks, and applying fixes ordered from highest-impact to most surgical.

> **Prerequisites:** You understand [create_clock, set_input_delay, set_output_delay](sdc_basics.md) and [false/multicycle paths](false_paths.md). If not, start there — bad constraints are the #1 cause of timing failures.

---

## The Timing Closure Loop

```
┌──────────────────────────────────────────────────────────┐
│           THE TIMING CLOSURE ITERATION LOOP              │
│                                                          │
│   1. Write RTL + constraints                             │
│          ↓                                               │
│   2. Synthesis → Place & Route → Timing report            │
│          ↓                                               │
│   3. Read slack values ←──────────────────────┐          │
│          ↓                                    │          │
│   4. Slack ≥ 0? ──Yes──► DONE                 │          │
│          │                                    │          │
│         No                                     │          │
│          ↓                                    │          │
│   5. Identify worst path(s) in report         │          │
│          ↓                                    │          │
│   6. Apply fix: ──────────────────────────────┘          │
│      a) Fix constraints (wrong period, missing false)    │
│      b) Logic fix (pipeline, restructure, duplicate)     │
│      c) Physical fix (floorplan, fanout, placement)      │
│      d) Tool effort (seed sweep, phys_opt, retiming)     │
└──────────────────────────────────────────────────────────┘
```

The loop repeats until every endpoint has **positive slack** across all process corners and operating conditions.

---

## Reading the Timing Report

### Slack: The One Number That Matters

```
Slack = Required Time − Arrival Time

Positive slack → path meets timing (margin exists)
Zero slack     → path exactly meets timing (no margin)
Negative slack  → path FAILS timing
```

Every FPGA timing report is structured around four key metrics:

| Metric | Meaning | What You Read |
|---|---|---|
| **WNS** (Worst Negative Slack) | The most-negative slack across all setup paths | "How badly am I failing?" |
| **TNS** (Total Negative Slack) | Sum of all negative slacks | "How widespread is the problem?" |
| **WHS** (Worst Hold Slack) | Most-negative hold slack | "Is hold timing failing?" |
| **THS** (Total Hold Slack) | Sum of all negative hold slacks | "How many hold violations?" |

### Interpreting a Path Report

```
Slack (VIOLATED): -1.234 ns
  Source:          state_machine/current_state_reg[2]/Q
  Destination:     output_fifo/wr_data_reg[7]/D
  Path Group:      sys_clk
  Path Type:       Max at Slow Corner
  Requirement:     10.000 ns
  Data Path Delay: 9.876 ns (logic 45%, net 55%)    ← THE DIAGNOSIS
  Clock Path Skew: 0.321 ns
  Clock Uncertainty: 0.150 ns
```

**What to look at:**
1. **Slack sign and magnitude** — Negative? How bad?
2. **Data Path Delay breakdown** — 55% net delay → physical problem (too far apart). 80% logic delay → too many LUT levels. Near 50/50 → balanced, needs pipelining.
3. **Requirement** — Is the clock period what you think it is? (Verify constraints.)
4. **Source/Destination** — Are these registers on the same clock? Different clocks? If different, should this be a false path?

### Common Report Commands

```tcl
# Vivado
report_timing_summary -file timing.rpt
report_timing -from [get_cells ...] -to [get_cells ...] -delay_type min_max

# Quartus
report_timing -npaths 100 -file timing.rpt
report_timing -from *state_machine* -to *output_fifo* -detail full_path

# All tools
report_clock_interaction       # Cross-clock path matrix
report_datasheet               # IO timing summary
```

---

## Fix Strategy 1: Constraint Problems (Fix First!)

Before touching RTL or floorplan, verify your constraints. At least 40% of "timing failures" are actually mis-specified constraints.

### Common Constraint Bugs

| Symptom | Likely Cause | Check |
|---|---|---|
| All paths in one clock domain fail | Wrong clock period in `create_clock` | `report_clocks` |
| PLL-generated clock paths fail | Missing `create_generated_clock` for PLL output | `report_clock_networks` |
| Cross-domain paths show violations | Clocks not set as asynchronous | Add `set_clock_groups -asynchronous` |
| IO pins fail consistently | Missing `set_input_delay` / `set_output_delay` | `report_datasheet` |
| Path between static config registers fails | Should be false path | `set_false_path` from config register source |

**Rule:** Always run `check_timing` (SDC) / `report_methodology` (Vivado) to catch missing constraints before diving into the timing report.

---

## Fix Strategy 2: Logic-Level Fixes

When constraints are correct and timing still fails, reduce the logic depth.

### 2a. Pipelining — The Universal Fix

Insert a register stage to cut a long combinatorial path into two shorter ones:

```
BEFORE (1 cycle, 45 LUT levels):     AFTER (2 cycles, ~23 levels each):
┌───┐   ┌─────────────────┐  ┌───┐   ┌───┐   ┌────────┐  ┌───┐   ┌────────┐  ┌───┐
│FF0│──→│  Big Cloud of   │─→│FF1│   │FF0│──→│ Half A │─→│FFp│──→│ Half B │─→│FF1│
└───┘   │  Combinatorial  │  └───┘   └───┘   └────────┘  └───┘   └────────┘  └───┘
        │  Logic (LUTs)   │
        └─────────────────┘
Slack: -2.1 ns                         Slack: +0.4 ns (+ added latency of 1 cycle)
```

```verilog
// Before: single-cycle multiply-add chain
always @(posedge clk)
    result <= (a * b) + (c * d) + (e * f) + offset;

// After: pipelined across 2 cycles
reg [47:0] partial1, partial2;
always @(posedge clk) begin
    partial1 <= (a * b) + (c * d);      // Stage 1
    partial2 <= (e * f) + offset;       // Stage 1 (parallel)
    result   <= partial1 + partial2;    // Stage 2
end
```

**Trade-off:** +1 cycle latency, +N registers. Almost always worth it.

### 2b. Retiming — Let the Tool Do It

Retiming moves registers across combinatorial logic to balance pipeline stages:

```tcl
# Vivado: global retiming (synthesis option)
synth_design -retiming

# Quartus: physical synthesis retiming
set_global_assignment -name PHYSICAL_SYNTHESIS_REGISTER_RETIMING ON
```

> Retiming works well for DSP-heavy designs with balanced arithmetic chains. It can break verification if your RTL relies on specific register boundaries for functional behavior — test thoroughly.

### 2c. Logic Duplication — Fix High Fanout

A register driving 5,000 loads creates a routing bottleneck. The tool must replicate the driver and route each copy to a subset of loads:

```verilog
// Before: single control register drives 5,000 loads
// After: tool auto-duplicates (no RTL change needed) but you can help:

(* fanout_limit = 256 *) reg [7:0] ctrl;  // Tell synthesis to replicate
```

```tcl
# XDC: limit fanout
set_property MAX_FANOUT 256 [get_cells ctrl_reg*]

# QSF: duplicate high-fanout nets
set_global_assignment -name AUTO_MAX_FANOUT_LIMIT 256
```

### 2d. Operator Selection — Area vs Speed

Fast operators consume more resources but produce shallower logic:

| Operation | Slow (area-optimized) | Fast (speed-optimized) |
|---|---|---|
| Adder | Ripple-carry chain | Carry-lookahead / DSP48 |
| Multiplier | LUT-based (pipelined soft) | DSP slice (single-cycle) |
| Barrel shifter | LUT cascade | Dedicated MUXF7/F8 |
| Comparator | LUT chain | Carry-chain comparator |
| Counter | LUT-based binary | DSP-accumulate or LFSR |

```verilog
// Force DSP for speed-critical multiply
(* use_dsp = "yes" *) reg [17:0] product;
always @(posedge clk)
    product <= a * b;  // Maps to DSP48, 1 cycle
```

---

## Fix Strategy 3: Physical-Level Fixes

When logic depth is reasonable but routes are too long, the problem is physical.

### 3a. Floorplanning — Pblocks and LogicLock

Constrain related logic to a physical region to minimize wire length:

```tcl
# XDC: create a Pblock for the critical datapath
create_pblock pblock_critical
add_cells_to_pblock pblock_critical [get_cells critical_pipeline_*]
resize_pblock pblock_critical -add {SLICE_X20Y100:SLICE_X80Y200}

# SDC-on-Quartus: LogicLock region
set_global_assignment -name LL_ENABLED ON -section_id "critical_region"
set_global_assignment -name LL_HEIGHT 20 -section_id "critical_region"
```

### 3b. Register Placement Near IO

Place IO registers in the IOB (IO Block) to eliminate routing delay to the pin:

```tcl
# XDC: push registers into IOB
set_property IOB TRUE [get_cells {data_out_reg[*]}]

# QSF: fast input/output register
set_instance_assignment -name FAST_INPUT_REGISTER ON -to data_in*
set_instance_assignment -name FAST_OUTPUT_REGISTER ON -to data_out*
```

### 3c. Location Assignment for Critical Cells

Manually place the source and destination of the #1 critical path close together:

```tcl
# XDC: place source and destination in adjacent sites
set_property LOC SLICE_X42Y100 [get_cells crit_src_reg]
set_property LOC SLICE_X44Y100 [get_cells crit_dst_reg]
```

**Use this sparingly** — over-constraining placement reduces the tool's freedom and can make other paths worse.

---

## Fix Strategy 4: Tool-Directed Optimization

### 4a. Seed Sweeps

P&R uses a pseudo-random seed. Different seeds produce different placements — sometimes dramatically different:

```tcl
# Vivado: sweep seeds
for {set s 1} {$s <= 10} {incr s} {
    place_design -directive Explore -seed $s
    route_design
    # Check WNS; keep best result
}

# Quartus: seed sweep via design space explorer
# Tools → Design Space Explorer → Seed sweep
```

### 4b. Physical Optimization

Post-placement optimizations that clone registers, restructure LUTs, and rewire nets:

```tcl
# Vivado: physical optimization in placement and routing
opt_design
place_design
phys_opt_design                    # Register cloning, LUT retiming
route_design
phys_opt_design -directive AggressiveExplore  # Post-route optimization

# Quartus: physical synthesis
set_global_assignment -name PHYSICAL_SYNTHESIS_COMBO_LOGIC ON
set_global_assignment -name PHYSICAL_SYNTHESIS_REGISTER_DUPLICATION ON
```

### 4c. Strategy/Directive Selection

Different directives optimize for different goals:

| Tool | Directive | Use When |
|---|---|---|
| Vivado | `Default` | First pass baseline |
| Vivado | `Explore` | WNS > -0.5 ns, need better placement |
| Vivado | `AggressiveExplore` | WNS > -2.0 ns, last resort |
| Vivado | `RuntimeOptimized` | Quick iteration, don't care about QoR |
| Quartus | `Performance (Aggressive)` | High effort, tight timing |
| Quartus | `Performance (High effort)` | Maximum effort, long compile |

---

## Hold Timing — The Hidden Failure Mode

Setup violations prevent the design from working. **Hold violations can cause failure at any clock speed** — including speeds far below the target frequency — and are not fixable by slowing the clock.

### Why Hold Fails

```
Setup check: data must arrive BEFORE next clock edge
Hold check:  data must be STABLE for t_hold AFTER the clock edge

            ┌─────┐         ┌─────┐
  clk       ┘     └─────────┘     └─────────
            ↑     ↑         ↑
            │     │         └─ t_hold window
            │     └─ data must stay valid until here
            └─ launching edge
```

If data changes too quickly after the clock edge (short path), the old value is corrupted before the register latches it.

### Fixing Hold Violations

| Fix | Why It Works |
|---|---|
| **Add delay to the data path** (LUT, routing detour) | Gives more time before data changes |
| **Reduce clock skew** (balance clock tree) | Less difference in clock arrival between source and destination |
| **Restructure logic** (remove bypass paths) | Data that skips combinatorial logic arrives too quickly |
| **Insert LUT1 buffer** | Adds ~0.3 ns of delay per LUT |

> In most tools, hold violations are **automatically fixed** during routing by inserting delay. If they persist after routing, they are a sign of extreme clock skew or a very fast bypass path.

---

## Multi-Corner Multi-Mode (MCMM)

A design must meet timing across **all** process corners, voltages, and temperatures — not just at nominal conditions:

| Corner | Temperature | Voltage | Affects |
|---|---|---|---|
| **Slow** | 85°C / 100°C | V_min | **Setup** (worst-case delay) |
| **Fast** | −40°C | V_max | **Hold** (least delay → fastest paths) |

The tool analyzes all corners automatically. If your design passes at Slow and fails at Fast, you have hold violations that only appear at low temperature and high voltage — dangerous because they won't show up on a warm bench prototype.

---

## Timing Closure Checklist

| Step | Check | Command |
|---|---|---|
| 1 | All clocks defined? | `report_clocks` / `report_clock_networks` |
| 2 | Generated clocks present? | Manually verify every PLL/MMCM output |
| 3 | IO delays set for all ports? | `report_datasheet` |
| 4 | Async clock groups excluded? | `report_clock_interaction` |
| 5 | False paths declared? | Review for over-broad exceptions |
| 6 | Multicycle paths declared? | Verify hold = setup − 1 |
| 7 | `check_timing` / `report_methodology` clean? | No unconstrained endpoints |
| 8 | WNS < 0? If yes → identify worst path group | `report_timing_summary` |
| 9 | WHS < 0? If yes → check fast corner | `report_timing -delay_type min` |
| 10 | Logic depth ≤ 20 LUT levels per cycle? | Review path report datapath |
| 11 | High-fanout nets (< 5000 loads each)? | `report_high_fanout_nets` |
| 12 | Used multiple seeds if margin < 0.200 ns? | Seed sweep |
| 13 | Phys_opt / physical synthesis enabled? | If margin < 0.500 ns, enable |
| 14 | Floorplan applied to critical paths? | Only if logic fixes exhausted |
| 15 | Final WNS ≥ +0.050 ns across all corners? | Margin for production variation |

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **Fixing RTL before checking constraints** | Hours wasted optimizing a path with wrong clock period | Run `check_timing` first |
| **Ignoring hold violations** | "The design worked on my desk but fails at customer site" | Check min-delay corner |
| **Over-constraining** | set_clock_groups too narrow; P&R fights unnecessary paths | Only group truly async clocks |
| **Pipelining without functional verification** | Adding latency breaks data alignment | Simulate after each pipeline insertion |
| **Seed-sweeping without understanding why** | Lucky seed passes; next build fails | Find root cause before accepting a seed-dependent result |
| **Floorplanning too early** | Constrained P&R produces worse global results | Floorplan only after logic fixes exhausted and worst paths identified |
| **Using `set_false_path` too broadly** | Paths that should be timed are excluded | Use `-from`/`-to` as specific as possible |

---

## Further Reading

| Article | What It Covers |
|---|---|
| [sdc_basics.md](sdc_basics.md) | Constraint syntax reference — start here if constraints are wrong |
| [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md) | CDC patterns that prevent timing violations between clock domains |
| [clock_domain_crossing.md](clock_domain_crossing.md) | CDC constraint methodology — set_clock_groups, max_delay |
| [false_paths.md](false_paths.md) | When to use false paths safely |
| [multicycle_paths.md](multicycle_paths.md) | Multicycle setup and hold adjustment |
| [io_timing.md](io_timing.md) | Source-synchronous IO timing closure |
| [floorplanning.md](../03_design_flow/floorplanning.md) | Floorplanning methodology |
| Xilinx UG906 | Vivado Design Suite — Timing Closure |
| Intel AN 584 | Timing Closure Methodology for Advanced FPGA Designs |
