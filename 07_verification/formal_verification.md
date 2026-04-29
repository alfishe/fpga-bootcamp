[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Formal Verification with SymbiYosys

Formal verification proves your design is correct for ALL possible inputs — not just the ones you thought to test. SymbiYosys makes this practical for FPGA designs.

---

## What Formal Verification Proves

| Method | Checks | When Used |
|---|---|---|
| **Assert** | Property must ALWAYS hold | Safety properties, protocol compliance |
| **Assume** | Constrain input space | "Assume input valid stays high for ≤4 cycles" |
| **Cover** | Does this state ever occur? | Coverage: "Does my FSM reach ERROR state?" |
| **BMC** (Bounded Model Check) | Property holds for first N cycles | Quick check, finds shallow bugs fast |
| **k-induction** | Property holds for ALL cycles | Prove properties unbounded |

## Quick Example — Counter Doesn't Overflow

```systemverilog
module counter (
    input clk, rst,
    input inc,
    output reg [7:0] cnt
);
    always @(posedge clk) begin
        if (rst)       cnt <= 0;
        else if (inc)  cnt <= cnt + 1;
    end

    // Formal: cnt never exceeds 255
    `ifdef FORMAL
        // Counter should always stay within range
        assert property (@(posedge clk) cnt < 256);

        // Reset works
        assert property (@(posedge clk) disable iff (rst)
            $past(rst) |-> cnt == 0);
    `endif
endmodule
```

## SymbiYosys Flow

```bash
# 1. Write assertions in Verilog (above)
# 2. Create .sby config file:
sby --yosys "yosys -m ghdl" -f counter.sby

# counter.sby:
[options]
mode bmc
depth 20

[engines]
smtbmc yices

[script]
read_verilog -formal counter.v
prep -top counter

[files]
counter.v

# 3. Run:
sby -f counter.sby
```

## When Formal Beats Simulation

| Scenario | Formal | Simulation |
|---|---|---|
| Protocol compliance (AXI: "valid → ready ack within 16 cycles") | ✅ Proven for all cycles | ❌ Only tested for stimulus provided |
| Corner-case state space (state machine deadlock) | ✅ Exhaustive | ❌ Hard to trigger |
| Arithmetic overflow | ✅ Proven or counterexample found | ❌ Very wide inputs impractical |
| PCIe link training | ❌ Too many state variables | ✅ Required for analog behavior |

## FPGA-Specific Limitations

- **Vendor IP blocks** (MIG, PCIe hard block) are black boxes — can't formally verify them
- **DSP/Multipliers** — formal tools may not model Xilinx DSP48E2 or Intel variable-precision DSP accurately
- **Transceivers** — analog behavior can't be formalized
- **Large designs** — state space explosion; use assume-guarantee to verify modules individually

---

## Original Stub Description

SymbiYosys: assertions (assert/assume/cover), bounded model checking, k-induction, cover properties

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../README.md)
- [README.md](README.md)
