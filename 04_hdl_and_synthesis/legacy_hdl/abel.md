[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# ABEL (Advanced Boolean Expression Language)

> **Stub — planned content. Full article to be written in a future documentation pass.**

ABEL is a hardware description and synthesis language developed by Data I/O, widely used for programming CPLDs and PALs in the 1980s–1990s. It uses truth tables, state diagrams, and Boolean equations with direct fuse-map targeting.

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

## Legacy Status

- **Last used**: Early 2000s (Xilinx XC9500, Altera MAX 7000 CPLDs)
- **Tool support**: ispLEVER Classic (Lattice), legacy versions only
- **Relevance**: Historical reference for understanding CPLD fuse-map design flow

## Original Stub Description

ABEL is a hardware description and synthesis language developed by Data I/O, widely used for programming CPLDs and PALs in the 1980s–1990s. It uses truth tables, state diagrams, and Boolean equations with direct fuse-map targeting.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
