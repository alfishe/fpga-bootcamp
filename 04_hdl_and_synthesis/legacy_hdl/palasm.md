[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# PALASM (PAL Assembler) — The First PLD Design Language

PALASM is one of the earliest hardware description languages, developed by Monolithic Memories (MMI) in the late 1970s for programming PAL (Programmable Array Logic) devices. It describes fuse-map configurations using Boolean product terms and sum terms — mapping directly to the physical AND-OR matrix of a PAL device.

---

## Overview

PALASM predates ABEL, AHDL, Verilog, and VHDL — it is the ancestor of all hardware description languages. Before PALASM, PAL devices were programmed by manually calculating which fuses to blow in the AND-OR matrix. PALASM automated this by allowing designers to write Boolean equations that the assembler converted to fuse maps.

The language is minimal because PAL devices are minimal: a PAL16L8 has 8 outputs, each driven by a 7-input AND-OR array with fixed pin assignments. There's no hierarchy, no parameters, no state machines — just Boolean equations mapped to fuses.

---

## PAL Device Architecture

```
                    AND Array (programmable)
                    ┌─────────────────────────┐
  Inputs ───────────┤  ──┐  ┐  ┐  ┐  ┐  ┐  ┐  │
  (pins 1–9,11)     │    │  │  │  │  │  │  │  │
                    │    └──┴──┴──┴──┴──┴──┘  │
                    │         Product Terms   │
                    │                         │
                    │  ──┐  ┐  ┐  ┐  ┐  ┐  ┐  │
                    │    │  │  │  │  │  │  │  │
                    │    └──┴──┴──┴──┴──┴──┘  │
                    │         Product Terms   │
                    └────────────┬────────────┘
                                 │
                    OR Array (fixed) ──► Outputs
                                      (pins 12–19)
```

In a PAL:
- The **AND array** is programmable (you choose which inputs connect to which product terms)
- The **OR array** is fixed (each output has a fixed number of product terms)
- PALASM equations map directly to the AND array fuses

---

## Example — Simple AND-OR Logic in PALASM

```palasm
PAL16L8
; pin assignments
CLK     /CK 1
A0 A1 A2 A3 A4 A5 A6 A7 /IN 2 3 4 5 6 7 8 9
/OE     /OE 11
Y0 Y1 Y2 Y3 Y4 Y5 Y6 Y7 /OUT 19 18 17 16 15 14 13 12

; boolean equations
/Y0 = /A0 * /A1 * /A2 * /A3
/Y1 = A0 + A1 + A2 + A3
```

### Translation to Verilog

```verilog
// Same logic in Verilog
module pal_logic (
    input  [3:0] a,
    output y0, y1
);
    assign y0 = ~a[0] & ~a[1] & ~a[2] & ~a[3];  // AND
    assign y1 = a[0] | a[1] | a[2] | a[3];       // OR
endmodule
```

### Translation to ABEL

```abel
" Same logic in ABEL
MODULE pal_logic
    A0, A1, A2, A3  PIN 2, 3, 4, 5;
    Y0, Y1          PIN 19, 18 ISTYPE 'com';

EQUATIONS
    Y0 = !A0 & !A1 & !A2 & !A3;
    Y1 = A0 # A1 # A2 # A3;
END
```

---

## PALASM Syntax Reference

| Element | Syntax | Example |
|---|---|---|
| **Device declaration** | `PAL16L8` | Must be first line |
| **Pin assignment** | `name PIN number` | `A0 2` |
| **Active-low** | `/name` | `/Y0` |
| **AND (product)** | `*` | `A0 * A1` |
| **OR (sum)** | `+` | `A0 + A1` |
| **NOT (complement)** | `/` | `/A0` |
| **Comment** | `;` | `; this is a comment` |
| **Equation** | `pin = expression` | `Y0 = A0 * A1` |

---

## Supported PAL Devices

| Device | Inputs | Outputs | Product Terms/Output | Registered | Notes |
|---|---|---|---|---|---|
| **PAL10H8** | 10 | 8 | 2 | No | Simplest PAL |
| **PAL16L8** | 10 | 8 | 7 | No | Most common combinatorial PAL |
| **PAL16R8** | 8 | 8 | 8 | Yes | 8 registered outputs |
| **PAL16R6** | 10 | 6+2 | 8 | Mixed | 6 registered + 2 combinatorial |
| **PAL20L8** | 14 | 8 | 7 | No | Wider input PAL |
| **PAL22V10** | 12 | 10 | 8–16 | Configurable | Most flexible PAL, still manufactured |

---

## PALASM vs ABEL

| Feature | PALASM | ABEL |
|---|---|---|
| **Developer** | Monolithic Memories (MMI) | Data I/O |
| **Year introduced** | ~1978 | ~1983 |
| **Abstraction** | Direct fuse-map equations | Higher-level (truth tables, state machines) |
| **Pin assignment** | Explicit in source | Explicit in source |
| **Device support** | PAL-only | PAL, GAL, CPLD |
| **Test vectors** | No | Yes (`TEST_VECTORS`) |
| **Simulation** | No | Yes (built-in) |
| **Hierarchy** | No | Limited |
| **Successor** | ABEL superseded it | Verilog/VHDL superseded it |

---

## Legacy Status

| Aspect | Assessment |
|---|---|
| **Last actively used** | 1990s (PAL/GAL devices, pre-CPLD era) |
| **Tool support** | Historical — WinCUPL, Atmel-ProChip can read PALASM syntax |
| **Current relevance** | Understanding the origins of programmable logic and fuse-map architecture |
| **Migration path** | PALASM → ABEL → Verilog for any new design |
| **Reason to learn** | Maintaining legacy PAL designs, understanding PAL architecture |

> **PAL devices are still manufactured**: Atmel/Microchip ATF16V8 and ATF22V10 are modern equivalents of the PAL16V8 and PAL22V10. They can be programmed using modern tools that accept PALASM-like syntax (WinCUPL).

---

## Historical Significance

PALASM established several conventions that persist in modern HDLs:

1. **Pin-level design entry** — the idea that hardware design starts with pin assignments
2. **Boolean equation syntax** — `Y = A * B + C` carried directly into ABEL and influenced Verilog
3. **Active-low notation** — the `/Y` convention for active-low signals persists in schematic conventions
4. **The assembler paradigm** — PALASM was an "assembler" that produced a binary (fuse map), establishing the HDL → binary compilation model that Verilog and VHDL follow

---

## References

- [PALASM Documentation (MMI, 1978)](https://www.retrotechnology.com/herb_stuff/palasm.html) — scanned original manual
- [Monolithic Memories PAL Handbook](https://bitsavers.org/) — historical reference
- [WinCUPL (Atmel/Microchip)](https://www.microchip.com/) — modern tool that supports PALASM-like syntax
- [ABEL](abel.md) — PALASM's successor
- [AHDL](ahdl.md) — Altera's CPLD language
