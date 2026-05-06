[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# Simulation vs Synthesis Mismatches — Why Your Design Works in Simulation but Fails on Hardware

The most frustrating moment in FPGA development is watching a design pass all simulation tests, synthesize cleanly, and then fail on the actual board. The root cause is almost always a **simulation-synthesis mismatch**: code that behaves one way in the simulator but produces different hardware than expected. These mismatches are particularly dangerous because synthesis tools silently reinterpret ambiguous code rather than producing an error. This article catalogs every common mismatch pattern, shows the broken code, explains why it diverges, and provides the correct version.

> [!WARNING]
> **Every mismatch pattern in this article produces code that compiles and simulates correctly but synthesizes to different hardware.** There are no synthesis errors to warn you. Only a disciplined coding style prevents these bugs.

---

## Overview: Why Mismatches Occur

A simulation-synthesis mismatch happens when the **semantic model** used by the simulator differs from the **hardware model** produced by the synthesizer. The key distinctions:

| Aspect | Simulator | Synthesizer |
|---|---|---|
| **Time model** | Event-driven, zero-delay unless specified | Hardware with real propagation delays |
| **Signal types** | 4-state: 0, 1, X, Z | 2-state: 0, 1 (X and Z are meaningless in hardware) |
| **Initialization** | Variables start as X (unknown) | Flip-flops start as 0 or 1 (device-dependent) |
| **Unspecified conditions** | Maintain previous value (latch inference) | May or may not infer a latch |
| **Math operations** | Precise, unlimited width | Truncated to hardware width |
| **Feedback loops** | May resolve via iteration | Real hardware oscillates or settles unpredictably |

---

## Mismatch 1: Incomplete Sensitivity List — "The Phantom Latch"

### The Problem

A combinational `always` block with an incomplete sensitivity list simulates correctly (because the simulator re-evaluates when any input changes) but synthesizes differently depending on the vendor:

- **Vivado**: Issues a warning, infers a latch or uses the sensitivity list as-is (behavior varies)
- **Quartus**: May infer a latch for the missing signal
- **Yosys**: May issue a warning and treat the block as incomplete

### Bad Code

```verilog
// Missing 'sel' in sensitivity list
always @(a or b) begin   // BUG: 'sel' is not in the list
    case (sel)
        2'b00: y = a;
        2'b01: y = b;
        2'b10: y = a & b;
        default: y = 1'b0;
    endcase
end
```

### Why It Fails

The simulator evaluates this block only when `a` or `b` changes. When `sel` changes, the block does not re-evaluate — `y` holds its old value. The synthesizer sees the missing sensitivity and may:
1. Auto-complete the sensitivity list (Vivado 2019+), OR
2. Infer a latch for `y` (because it holds state across changes of `sel`)

Either way, the hardware behavior differs from simulation.

### The Fix

```verilog
// Verilog-2001: use always @(*) — auto-sensitivity
always @(*) begin
    case (sel)
        2'b00: y = a;
        2'b01: y = b;
        2'b10: y = a & b;
        default: y = 1'b0;
    endcase
end

// SystemVerilog: use always_comb — guaranteed complete + no latch
always_comb begin
    case (sel)
        2'b00: y = a;
        2'b01: y = b;
        2'b10: y = a & b;
        default: y = 1'b0;
    endcase
end
```

> [!NOTE]
> `always_comb` is superior to `always @(*)` because it: (1) guarantees automatic sensitivity, (2) warns if a latch would be inferred, (3) evaluates at time zero even with no stimulus.

---

## Mismatch 2: Blocking vs Non-Blocking Assignments — "The Race Condition"

### The Problem

Using blocking assignments (`=`) in sequential (clocked) blocks creates race conditions that depend on simulator evaluation order. In hardware, flip-flops update simultaneously on the clock edge — there is no sequential ordering.

### Bad Code

```verilog
// Blocking assignments in sequential logic
always @(posedge clk) begin
    temp = a & b;       // Evaluated immediately
    result = temp | c;  // Uses new temp (same cycle)
end
```

### Why It Fails

In simulation: `temp` updates before `result` is computed — so `result` uses the **new** value of `temp` in the same clock cycle. This is a 0-cycle combinational path.

In hardware: Both `temp` and `result` are flip-flops. `result` uses the **old** value of `temp` from the previous clock cycle — because flip-flops sample their inputs before the clock edge.

The synthesized hardware has a 1-cycle pipeline delay that the simulation does not.

### The Fix

```verilog
// Non-blocking assignments: all FFs sample simultaneously
always @(posedge clk) begin
    temp   <= a & b;      // Scheduled for after clock edge
    result <= temp | c;   // Uses OLD temp (previous cycle)
end

// If you need combinational logic, separate it:
// Combinational: compute next values
wire temp_next = a & b;
wire result_next = temp_next | c;

// Sequential: register the results
always @(posedge clk) begin
    temp   <= temp_next;
    result <= result_next;
end
```

**Rule**: Use `<=` (non-blocking) for all sequential blocks. Use `=` (blocking) for all combinational blocks. Never mix them.

---

## Mismatch 3: casex and casez — "The Hidden Don't Care"

### The Problem

`casex` treats both X and Z as "don't care" in both the case expression and the case items. This means a simulation value of X will match ANY case item — hiding bugs that would otherwise be caught.

### Bad Code

```verilog
always @(*) begin
    casex (sel)
        4'b000x: y = a;    // Matches 0000, 0001, and 000X
        4'b001x: y = b;    // Matches 0010, 0011, and 001X
        default: y = 1'b0;
    endcase
end
```

### Why It Fails

In simulation: if `sel` is `4'b000X`, it matches the first case item. The simulator thinks this is correct.

In synthesis: X does not exist in hardware. The synthesizer may treat the X as either 0 or 1 — producing a match that differs from the simulator's interpretation. More importantly, if `sel` is truly `4'b0001` in hardware, but the simulator tested with `4'b000X`, the test case was invalid.

### The Fix

```verilog
// Use casez (Z only as don't-care) or explicit case with all items
always_comb begin
    casez (sel)
        4'b000?: y = a;    // ? = Z only — safer than casex
        4'b001?: y = b;
        default:  y = 1'b0;
    endcase
end

// Even better: explicit one-hot with unique case
always_comb begin
    unique case (sel)
        4'b0000: y = a;
        4'b0001: y = a;
        4'b0010: y = b;
        4'b0011: y = b;
        default: y = 1'b0;
    endcase
end
```

> [!WARNING]
> **Never use `casex` in synthesizable code.** Use `casez` with explicit `?` for don't-care bits, or `unique case` / `priority case` (SystemVerilog) for synthesis directives.

---

## Mismatch 4: Initial Blocks — "The Power-On State Trap"

### The Problem

`initial` blocks execute once at simulation time zero. They have no hardware equivalent in most FPGAs — flip-flops power up in a device-dependent state (typically 0 for Xilinx, programmable for Intel), not the value assigned in the `initial` block.

### Bad Code

```verilog
reg [7:0] counter;

initial begin
    counter = 8'hFF;    // Simulation starts at 0xFF
end

always @(posedge clk) begin
    counter <= counter + 1;
end
```

### Why It Fails

In simulation: `counter` starts at `0xFF`. First clock edge increments to `0x00`.

In hardware: `counter` starts at `0x00` (Xilinx default) or an unknown value (some Intel devices). The first clock edge increments to `0x01`. The design operates with a different starting state.

### The Fix

```verilog
// Use explicit reset instead of initial
reg [7:0] counter;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        counter <= 8'hFF;     // Defined reset state
    end else begin
        counter <= counter + 1;
    end
end
```

> [!NOTE]
> For Xilinx 7-series and UltraScale+, `initial` blocks **are** supported for register initialization in the bitstream (INIT property). However, this is vendor-specific and does not work on all FPGA families. Use explicit reset for portability.

---

## Mismatch 5: Width Mismatches — "The Silent Truncation"

### The Problem

Verilog silently truncates or zero-extends when assigning between vectors of different widths. In simulation, this works as expected. In synthesis, the same truncation occurs — but the designer may not realize the upper bits are lost, leading to incorrect comparisons or arithmetic.

### Bad Code

```verilog
reg [15:0] result;
wire [7:0]  data;

assign result = data * data;   // 8×8 = 16 bits — OK, but misleading
assign result = data + data;   // 8+8 = 9 bits, but result is 16 — upper 7 bits are 0

// The real danger: comparison
wire [3:0] small_val;
wire [7:0] large_val;
wire match = (small_val == large_val);  // small_val zero-extended to 8 bits
```

### Why It Fails

The mismatch isn't between simulation and synthesis — they agree. The problem is between the designer's **intent** and the actual behavior. In VHDL, a width mismatch is a compile-time error. In Verilog, it's silently handled.

### The Fix

```verilog
// Explicit width matching — makes intent clear
wire [15:0] result;
wire [7:0]  data;

assign result = {8'b0, data} * {8'b0, data};  // Explicit zero-extension

// Or use SystemVerilog with strict linting
// In the synthesis tool, enable "width mismatch" warnings
// Vivado: set_property SEVERITY {error} [get_drc_checks NSTD-1]
```

**VHDL comparison**: VHDL would reject `small_val = large_val` at compile time with: *"type error: widths do not match."* This is one of VHDL's strongest advantages for safety.

---

## Mismatch 6: $signed and $unsigned — "The Sign Extension Surprise"

### The Problem

Verilog's type system does not carry signedness through operations. A comparison or arithmetic operation between a signed and unsigned value uses **unsigned** rules — potentially producing incorrect results.

### Bad Code

```verilog
wire signed [7:0] a = -5;       // 8'b11111011
wire [7:0] b = 8'hFB;           // 8'b11111011 (same bit pattern)
wire result = (a > 0);          // Signed comparison: -5 > 0 = FALSE
wire result2 = (b > 0);         // Unsigned comparison: 251 > 0 = TRUE

// The real trap:
wire signed [7:0] x = -10;
wire [7:0] y = 8'd50;
wire [7:0] sum = x + y;          // Treated as unsigned: 246 + 50 = overflow
                                  // Expected: -10 + 50 = 40
```

### Why It Fails

When `x` (signed) and `y` (unsigned) are added, Verilog treats the entire expression as unsigned. The value of `x` is reinterpreted as `246` (unsigned), so `246 + 50 = 296`, which truncates to `40` in 8 bits — coincidentally correct in this case, but only by luck.

### The Fix

```verilog
// Explicit sign conversion
wire signed [7:0] x = -10;
wire signed [7:0] y_signed = $signed(8'd50);
wire signed [7:0] sum = x + y_signed;  // Now signed arithmetic: -10 + 50 = 40

// Or: use consistent types throughout
wire signed [15:0] x_ext = {{8{x[7]}}, x};  // Sign-extend to 16 bits
wire signed [15:0] y_ext = {{8{1'b0}}, 8'd50};  // Zero-extend
wire signed [15:0] sum = x_ext + y_ext;
```

---

## Mismatch 7: for Loops — "The Unrolled vs Iterated Trap"

### The Problem

A `for` loop in synthesizable code must have a statically determinable iteration count. The synthesizer unrolls the loop at compile time. But if the loop body has side effects that depend on iteration order, the unrolled version may differ from the simulated iteration.

### Bad Code

```verilog
integer i;
reg [7:0] data [0:3];
reg [7:0] checksum;

always @(posedge clk) begin
    checksum = 0;
    for (i = 0; i < 4; i = i + 1) begin
        checksum = checksum + data[i];  // Blocking assignment in loop
    end
end
```

### Why It Fails

In simulation: the loop executes sequentially with blocking assignments — each iteration uses the updated `checksum`.

In synthesis: the loop is unrolled. All four additions are computed combinationally in parallel, and `checksum` gets the final result. This matches simulation **only** because the loop body is combinational.

But if the loop body contained a non-blocking assignment or a clocked operation, the behavior would diverge.

### The Fix

```verilog
// Use for loops only for combinational logic with non-blocking style
integer i;
reg [7:0] data [0:3];
reg [7:0] checksum;

always @(posedge clk) begin
    checksum <= 0;
    for (i = 0; i < 4; i = i + 1) begin
        checksum <= checksum + data[i];  // NOT a pipeline — all iterations compute same result
    end
end

// Better: explicit combinational computation
wire [9:0] checksum_comb = data[0] + data[1] + data[2] + data[3];
always @(posedge clk) begin
    checksum <= checksum_comb[7:0];
end
```

---

## Mismatch 8: Unintended Latches — "The Half-Written Case"

### The Problem

An incomplete `case` statement or `if-else` chain in a combinational block infers a latch — a level-sensitive storage element that holds its output when the clock is not active. Latches are generally undesirable in FPGA designs because they are difficult to time and can cause hold violations.

### Bad Code

```verilog
always @(*) begin
    case (opcode)
        2'b00: result = a + b;
        2'b01: result = a - b;
        // Missing: 2'b10 and 2'b11
    endcase
    // result holds previous value for missing cases → LATCH
end
```

### Why It Fails

In simulation: `result` holds its previous value for `opcode = 2'b10` and `2'b11`. This may appear correct in testing if those opcodes are never exercised.

In synthesis: a latch is inferred for `result`. The latch is transparent when the case condition is met, and holds when it is not. Latches are sensitive to glitches on `opcode` and cannot be analyzed by static timing analysis for hold checks.

### The Fix

```verilog
// Always provide a default
always_comb begin
    case (opcode)
        2'b00: result = a + b;
        2'b01: result = a - b;
        2'b10: result = a & b;
        2'b11: result = a | b;
    endcase
end

// Or use default assignment
always_comb begin
    result = '0;              // Default: drive all bits
    case (opcode)
        2'b00: result = a + b;
        2'b01: result = a - b;
        default: ;            // Keep default value
    endcase
end
```

---

## Mismatch 9: Multiplexer with Feedback — "The Combinational Loop"

### The Problem

A combinational loop occurs when a signal depends on itself through combinational logic. Simulators may resolve this differently from hardware.

### Bad Code

```verilog
// Ring oscillator — works in silicon, oscillates in simulation too
// but timing is unpredictable
assign a = ~b;
assign b = ~a;    // Combinational loop!
```

### Why It Fails

In simulation: the event scheduler may enter an infinite loop (if there is no delay) or resolve to X.

In hardware: the loop oscillates at a frequency determined by the gate delays (which are PVT-dependent). This is sometimes intentional (ring oscillator) but usually a bug.

### The Fix

```verilog
// Break combinational loops by inserting a register
always @(posedge clk) begin
    b <= ~a;
end
assign a = ~b;    // Now a is combinational, b is registered — no loop
```

---

## Mismatch 10: $display and $finish — "The Debug Artifact"

### The Problem**

System tasks like `$display`, `$monitor`, `$fwrite`, `$finish`, and `$random` are simulation-only constructs. They are ignored by synthesis — which is correct behavior. The mismatch occurs when the designer relies on `$display` output to validate a design path that isn't actually exercised in the synthesized hardware.

More subtly: `$random` in a testbench may generate a sequence that accidentally tests the exact conditions where a mismatch would appear. But the testbench itself may not be detecting the mismatch.

### The Fix

- Use `$display` for debug only — never for functional behavior
- Use assertions (`assert`) instead of `$display`-based checks — assertions can be synthesized or formally verified
- In SystemVerilog, use `cover` properties to verify that test cases actually exercise the design paths

---

## Complete Checklist: Preventing Mismatches

| # | Rule | Rationale |
|---|---|---|
| 1 | Use `always_comb` / `always @(*)` for combinational logic | Prevents incomplete sensitivity lists |
| 2 | Use `<=` (non-blocking) in sequential blocks, `=` (blocking) in combinational | Prevents race conditions |
| 3 | Never use `casex` — use `casez` or explicit `unique case` | Prevents X-matching bugs |
| 4 | Never use `initial` for functional initialization — use explicit reset | Portable power-on state |
| 5 | Provide `default` for every `case` statement | Prevents unintended latches |
| 6 | Match widths explicitly — enable width-mismatch warnings | Prevents silent truncation |
| 7 | Use `$signed()` / `$unsigned()` explicitly when mixing types | Prevents sign-extension surprises |
| 8 | Never create combinational loops | Prevents oscillation and X-state |
| 9 | Use `assert` / `$assert` instead of `$display`-based checks | Assertions can be formally verified |
| 10 | Run lint checks before synthesis (Vivado `set_msg_config`, Verilator `--lint-only`) | Catches mismatches before hardware |

---

## Vendor Linting Configuration

### Vivado

```tcl
# Elevate common mismatch warnings to errors
set_msg_config -id {Synth 8-327} -new_severity {ERROR}  ;# inferred latch
set_msg_config -id {Synth 8-350} -new_severity {ERROR}  ;# signal used but not in sensitivity list
set_msg_config -id {Synth 8-3332} -new_severity {ERROR} ;# sequential assignment uses blocking
set_msg_config -id {DRC NSTD-1} -new_severity {ERROR}   ;# unspecified I/O standard
set_msg_config -id {DRC UCIO-1} -new_severity {ERROR}   ;# unconstrained I/O
```

### Quartus

```tcl
# Enable strict analysis
set_global_assignment -name ENABLE_ADVANCED_WARNINGS ON
set_global_assignment -name WARNING_STRING "inferred latch" SEVERITY ERROR
```

### Verilator

```bash
# Comprehensive lint — catches most mismatches at compile time
verilator --lint-only -Wall -Wno-fatal design.v
# Key warnings:
#   - WIDTH: width mismatch
#   - BLKSEQ: blocking assignment in sequential block
#   - CASEINCOMPLETE: incomplete case statement
#   - CMPCONST: comparison with constant
#   - UNDRIVEN: undriven signal
```

---

## References

| Source | Description |
|---|---|
| Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis" | SNUG 1999 — the definitive paper on blocking vs non-blocking |
| Stuart Sutherland, "SystemVerilog for Design" | Covers synthesis subset, always_comb vs always @(*) |
| Xilinx UG901 — Vivado Synthesis User Guide | Supported constructs, coding style, mismatch warnings |
| Intel Quartus Pro User Guide — HDL Coding | Recommended coding style for Intel FPGAs |
| Verilator Manual — Warnings | Complete list of lint checks and their meanings |
| [CDC Coding Patterns](cdc_coding.md) | CDC-specific mismatches and synchronizer patterns |
| [Inference Rules](inference_rules.md) | What HDL pattern infers what hardware |
| [State Machines](state_machines.md) | Safe FSM encoding — related mismatch patterns |
