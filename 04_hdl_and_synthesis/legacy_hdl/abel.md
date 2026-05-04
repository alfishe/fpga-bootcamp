[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# ABEL (Advanced Boolean Expression Language)

ABEL is a hardware description and synthesis language developed by Data I/O in the early 1980s for programming CPLDs and PALs. It was one of the first HDLs that allowed designers to describe logic using Boolean equations, truth tables, and state diagrams rather than manually specifying fuse maps. ABEL targets the fuse-map level directly — each ABEL statement maps to a specific AND-OR product term in the PAL architecture.

---

## Overview

Before ABEL, PAL programming required manually calculating fuse maps — binary arrays specifying which fuses to blow in the AND-OR matrix. ABEL automated this translation: the designer wrote Boolean equations and truth tables, and the ABEL compiler generated the fuse map. This was revolutionary in 1983, making PAL/CPLD design accessible to engineers without deep knowledge of the device's internal fuse architecture.

ABEL's influence persists in modern HDL conventions: the concept of "pins," "nodes," and "equations" that ABEL formalized carried directly into Verilog and VHDL.

---

## Language Features

| Feature | Syntax | Modern Equivalent |
|---|---|---|
| **Pin declarations** | `clk PIN 1;` | Verilog port declaration |
| **Boolean equations** | `q0 := !rst & en & !q0;` | Verilog `assign` or `always` |
| **Truth tables** | `TRUTH_TABLE (...)` | Verilog `case` statement |
| **State diagrams** | `STATE_DIAGRAM ...` | Verilog `always @(posedge clk)` FSM |
| **Sets (bundles)** | `[q1, q0]` | Verilog bus `[1:0] q` |
| **Property assignments** | `ISTYPE 'reg'` | Verilog `reg` vs `wire` |
| **Test vectors** | `TEST_VECTORS (...)` | Verilog testbench |

---

## Example — 2-bit Counter in ABEL

```abel
MODULE counter
TITLE '2-bit counter with enable'

" Inputs
    clk, rst, en    PIN 1, 2, 3;
" Outputs
    q1, q0          PIN 12, 13 ISTYPE 'reg';

" Equations
    q0 := !rst & en & !q0 # !rst & !en & q0;
    q1 := !rst & en & q0 & !q1 # !rst & !en & q1 # !rst & en & !q0 & q1;

    [q1, q0].clk = clk;
END
```

### Translation to Verilog

```verilog
// Same counter in Verilog
module counter (
    input  clk, rst, en,
    output reg q1, q0
);
    always @(posedge clk) begin
        if (!rst) begin
            if (en) begin
                {q1, q0} <= {q1, q0} + 1;
            end
        end else begin
            {q1, q0} <= 2'b00;
        end
    end
endmodule
```

---

## ABEL Compilation Flow

```
ABEL Source (.abl)
       ↓
  ABEL Compiler (Data I/O)
       ↓
  Fuse Map (.jed) — JEDEC format
       ↓
  PAL/CPLD Programmer (hardware)
       ↓
  Physical PAL/CPLD device
```

| Stage | Tool | Output |
|---|---|---|
| **Compilation** | ABEL compiler | Logic optimization + fuse map |
| **Simulation** | ABEL simulator | Pre-programming verification |
| **Programming** | PAL programmer | Physical device with blown fuses |

The JEDEC (.jed) file format that ABEL produces became the industry standard for PAL/CPLD programming. It's a text file containing the fuse map as a sequence of 0s and 1s, and many modern CPLD tools still use JEDEC format.

---

## Device Support

| Device Family | Logic Elements | ABEL Support | Modern Equivalent |
|---|---|---|---|
| **PAL16L8/R8** | 8 AND-OR outputs | ✅ Full | None (obsolete) |
| **GAL16V8** | 8 macrocells | ✅ Full | ATF16V8 (still available) |
| **GAL22V10** | 10 macrocells | ✅ Full | ATF22V10 (still available) |
| **Xilinx XC9500** | 36–288 macrocells | ✅ Full (via ISE) | XC9500XL (still sold) |
| **Altera MAX 7000** | 32–256 macrocells | ✅ Full (via MAX+PLUS II) | MAX II/MAX V (Verilog only) |

---

## Legacy Status

| Aspect | Assessment |
|---|---|
| **Last actively used** | Early 2000s (Xilinx XC9500, Altera MAX 7000) |
| **Tool support** | ispLEVER Classic (Lattice), legacy ISE versions only |
| **Current relevance** | Historical reference only — understanding CPLD fuse-map design flow |
| **Migration path** | ABEL → Verilog for any new design |
| **Reason to learn** | Maintaining legacy ABEL designs, understanding PAL/CPLD architecture |

---

## Key Differences from Verilog

| Feature | ABEL | Verilog |
|---|---|---|
| **Level of abstraction** | Fuse-map (AND-OR product terms) | RTL (registers, multiplexers, FSMs) |
| **Pin assignment** | Explicit (PIN 1, PIN 2) | Separate constraints file |
| **Combinatorial vs registered** | `ISTYPE 'com'` vs `ISTYPE 'reg'` | `wire` vs `reg` + `always @(posedge clk)` |
| **Test vectors** | In-language (`TEST_VECTORS`) | Separate testbench file |
| **Target device** | Implicit (compiler maps to device) | Explicit (FPGA family selection) |
| **Hierarchy** | Limited (nested modules) | Full (module instantiation) |

---

## References

- [ABEL Language Reference (Data I/O)](https://www.dataio.com/) — original documentation
- [PAL Programming with ABEL (retro computing)](https://www.retrotechnology.com/) — hobbyist guides
- [JEDEC File Format](https://www.jedec.org/) — the .jed fuse map standard
- [AHDL (Altera HDL)](ahdl.md) — Altera's competing language
- [PALASM](palasm.md) — the predecessor to ABEL
