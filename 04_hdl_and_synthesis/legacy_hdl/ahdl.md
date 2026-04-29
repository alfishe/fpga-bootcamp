[← Legacy HDL Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# Altera HDL (AHDL)

> **Stub — planned content. Full article to be written in a future documentation pass.**

Altera HDL (AHDL) is a proprietary textual design entry language used with Altera/Intel MAX and older FPGA families. It uses Boolean equations, truth tables, and state machine declarations, compiling directly to Altera-specific primitives.

## Example — 3-State Buffer in AHDL

```ahdl
SUBDESIGN tri_state_example
(
    data_in[7..0]   : INPUT;
    enable          : INPUT;
    data_out[7..0]  : BIDIR;
)
BEGIN
    data_out[] = TRI(data_in[], enable);
END;
```

AHDL compiles to Altera primitives (LCELL, SOFT, TRI) — a closer-to-silicon abstraction than Verilog/VHDL.

## Legacy Status

- **Last actively used**: Early 2010s (MAX II/MAX V CPLDs)
- **Tool support**: Quartus II (legacy editions)
- **Relevance**: Understanding legacy Altera designs, CPLD pin-level timing

## Original Stub Description

Altera HDL (AHDL) is a proprietary textual design entry language used with Altera/Intel MAX and older FPGA families. It uses Boolean equations, truth tables, and state machine declarations, compiling directly to Altera-specific primitives.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
