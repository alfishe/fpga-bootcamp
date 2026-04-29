[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# PALASM (PAL Assembler)

> **Stub — planned content. Full article to be written in a future documentation pass.**

PALASM is one of the earliest hardware description languages, developed by Monolithic Memories (MMI) for programming PAL (Programmable Array Logic) devices. It describes fuse-map configurations using Boolean product terms and sum terms.

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

PALASM directly maps to PAL fuse arrays — each product term line corresponds to a physical AND gate row in the PAL matrix.

## Legacy Status

- **Last used**: 1990s (PAL/GAL devices, pre-CPLD era)
- **Tool support**: Historical, WinCUPL, Atmel-ProChip
- **Relevance**: Understanding the origins of programmable logic and fuse-map architecture

## Original Stub Description

PALASM is one of the earliest hardware description languages, developed by Monolithic Memories (MMI) for programming PAL (Programmable Array Logic) devices. It describes fuse-map configurations using Boolean product terms and sum terms.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
