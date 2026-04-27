[← Section Home](README.md) · [← Project Home](../README.md)

# Multicycle Paths — When One Clock Cycle Isn't Enough

Not every path needs to complete in a single clock cycle. A multiplier, a deep combinatorial cloud spanning multiple pipeline stages, or a slow control path may legitimately require 2, 3, or more cycles. A **multicycle path** tells the STA tool: "this path gets N cycles for setup, not 1."

The key insight that trips up most engineers: **declaring a multicycle setup affects both setup AND hold analysis.** If you get the hold adjustment wrong, the tool will create hold violations that don't exist in reality — or worse, mask real ones.

---

## The Problem Multicycle Paths Solve

Without multicycle constraints, every path is analyzed as single-cycle:

```
Default (1-cycle):                Multicycle (2-cycle setup):
clk  ┌─┐  ┌─┐  ┌─┐               clk  ┌─┐  ┌─┐  ┌─┐
     ┘ └──┘ └──┘ └──                  ┘ └──┘ └──┘ └──

Launch at edge 0                    Launch at edge 0
Capture at edge 1  ←── 10 ns req.   Capture at edge 2  ←── 20 ns req.
     ↑                                        ↑
     └── The tool's default assumption       └── Multicycle: 2× budget
     (path must complete in 1 cycle)          (path has 2 cycles to complete)
```

---

## set_multicycle_path — Syntax

```tcl
# N-cycle setup (N=2 means 2 cycles for data to arrive)
set_multicycle_path -setup 2 \
    -from [get_cells src_reg*] \
    -to   [get_cells dst_reg*]

# Hold adjustment — MUST be set to N−1
set_multicycle_path -hold  1 \
    -from [get_cells src_reg*] \
    -to   [get_cells dst_reg*]
```

## The Golden Rule: Hold = Setup − 1

This is the #1 multicycle path mistake. Without the hold adjustment, the tool still assumes hold must be met at the **default capturing edge**, which is the edge BEFORE the multicycle capture edge:

```
Without hold adjustment (default hold check at edge 0):
clk  ┌─┐  ┌─┐  ┌─┐
     ┘ └──┘ └──┘ └──
Launch at edge 0        |
Hold check at edge 0 ←──┘   ← TOOL ADDS VIOLATION HERE
                                (data hasn't even been launched yet!)

With hold adjustment (-hold 1):
clk  ┌─┐  ┌─┐  ┌─┐
     ┘ └──┘ └──┘ └──
Launch at edge 0           |
Hold check at edge 1 ←─────┘   ← Correct: hold checked at the intermediate edge
```

**Every `-setup N` must be followed by `-hold N−1`.** The single exception: source and destination are on different clock edges of the same clock (e.g., negedge-to-posedge), where the default hold edge may already be correct.

---

## Common Multicycle Patterns

### Pattern 1: Pipelined Multiplier (Setup 4, Hold 3)

```verilog
// 4-cycle multiplier: input registered, 3 pipeline stages + 1 output reg = 4 cycles
reg [15:0] a_r, b_r;
reg [31:0] mult_stage1, mult_stage2, mult_result;
always @(posedge clk) begin
    a_r <= a; b_r <= b;                         // Stage 0
    mult_stage1 <= a_r * b_r;                   // Stage 1 (DSP48, 1 cycle)
    mult_stage2 <= mult_stage1 + offset;         // Stage 2
    mult_result <= mult_stage2;                  // Stage 3
end
```

```tcl
# Path: a_r/b_r → mult_result takes 4 cycles
set_multicycle_path -setup 4 -from [get_cells a_r_reg] -to [get_cells mult_result_reg*]
set_multicycle_path -hold  3 -from [get_cells a_r_reg] -to [get_cells mult_result_reg*]
```

### Pattern 2: Slow Control Path (Setup 8, Hold 7)

```verilog
// Status register: CPU writes, takes many cycles to propagate through
// state machine before result is captured by status_reg
always @(posedge clk) begin
    if (cpu_write) ctrl_reg <= cpu_data;        // Source
    // ... deep state machine (7 cycles of logic) ...
    status_reg <= computed_status;              // Destination — 8 cycles later
end
```

```tcl
set_multicycle_path -setup 8 -from [get_cells ctrl_reg] -to [get_cells status_reg]
set_multicycle_path -hold  7 -from [get_cells ctrl_reg] -to [get_cells status_reg]
```

### Pattern 3: Source-Synchronous IO (Setup 2, Hold 1)

When the FPGA captures data from an external device that changes on every OTHER clock edge:

```tcl
# DDR capture at half rate: data changes every 2 FPGA clock cycles
set_multicycle_path -setup 2 -from [get_ports ddr_data_in*] -to [get_cells capture_reg*]
set_multicycle_path -hold  1 -from [get_ports ddr_data_in*] -to [get_cells capture_reg*]
```

---

## Clock Edge Relationship — Understanding the Math

The standard single-cycle timing paths use:
- **Setup:** launch edge N → capture edge N+1
- **Hold:** launch edge N → capture edge N (same edge)

Multicycle shifts the capture edge forward:
- **Setup N:** launch edge 0 → capture edge N
- **Hold N−1:** launch edge 0 → capture edge N−1

The hold edge is always ONE cycle before the setup capture edge. This ensures data doesn't change too soon after being launched — specifically, it must remain stable until the edge just before the intended capture edge.

```
Setup=4, Hold=3:
clk  ┌─┐  ┌─┐  ┌─┐  ┌─┐  ┌─┐
     ┘0└──┘1└──┘2└──┘3└──┘4└──
      ↑              ↑    ↑
   Launch        Hold  Setup
   edge 0        edge 3  edge 4
                 (N−1)   (N)
```

---

## Cross-Vendor Syntax

| Tool | Syntax | Notes |
|---|---|---|
| SDC (Intel/Lattice/Microchip) | `set_multicycle_path -setup N -hold N−1` | Standard SDC |
| XDC (Xilinx) | Same as SDC | Identical syntax |
| Intel QSF | Not available | Use SDC `.sdc` file |

---

## Multicycle Paths vs False Paths vs Clock Groups

| Scenario | Use | Why |
|---|---|---|
| Path needs N > 1 cycles (known timing) | `set_multicycle_path -setup N` | Path IS timed — just over more cycles |
| Path never needs timing (static, CDC) | `set_false_path` | Path is NEVER timed |
| All paths between two unrelated clocks | `set_clock_groups -asynchronous` | Broad exclusion; paths have synchronizers |
| Path needs N cycles AND crosses domains | `set_multicycle_path` + `set_clock_groups` on the other domain pair | Rare; usually better to use a synchronizer |

---

## Verification

```tcl
# Check multicycle paths are applied
report_exceptions -exception_type multicycle

# Verify the setup/hold edges are what you expect
report_timing -from [get_cells src_reg] -to [get_cells dst_reg] -path_type full_clock

# Quartus: report timing with clock edges visible
report_timing -from <src> -to <dst> -detail full_path -show_routing
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **Forgetting hold = setup − 1** | Spurious hold violations from launch edge 0 to capture edge 0 | Add `set_multicycle_path -hold N−1` |
| **Setup and hold both set to N** | Hold checked at same edge as setup (edge N), which is too late — data may corrupt | Hold must be N−1 |
| **Multicycle on paths that ARE single-cycle** | Real timing violation masked by extra budget | Verify the path really needs N cycles |
| **Not updating multicycle after pipeline change** | Pipeline depth changed but constraint still says old N | Review constraints whenever pipeline depth changes |
| **Using multicycle instead of a synchronizer** | Cross-domain path with multicycle — meaningless because clocks have no fixed phase | Use synchronizer + false path, OR keep in same domain |
| **Forgetting fast corner hold check** | Hold passes at slow corner, fails at fast corner (low temp, high voltage) | Always check min-delay corner |

---

## Quick Reference

| Path Type | Setup | Hold | Notes |
|---|---|---|---|
| 2-pipe stage multiplier | 3 | 2 | Input reg → pipe1 → pipe2 → output |
| 4-pipe stage DSP chain | 5 | 4 | N = pipeline depth + 1 |
| Half-rate DDR capture | 2 | 1 | Data changes every 2 FPGA cycles |
| Slow status/control register | 4–16 | 3–15 | Verify against actual state machine depth |
| Clock divider output | 2 | 1 | Divided clock domain paths |

---

## Further Reading

| Article | Topic |
|---|---|
| [sdc_basics.md](sdc_basics.md) | Constraint syntax reference |
| [false_paths.md](false_paths.md) | When to use false path instead of multicycle |
| [timing_closure.md](timing_closure.md) | Using multicycle paths in the closure loop |
| [io_timing.md](io_timing.md) | Source-synchronous IO with multicycle constraints |
