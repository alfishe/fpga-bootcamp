[← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# Verilog & SystemVerilog

Verilog (IEEE 1364) and its superset SystemVerilog (IEEE 1800) are the most widely used HDLs in the FPGA industry. Verilog-2001 remains the synthesis baseline; SystemVerilog adds `always_ff`/`always_comb`, interfaces, assertions, and UVM foundations.

## Index

| File | Topic |
|---|---|---|
| [verilog_basics.md](verilog_basics.md) | Verilog-2001 for synthesis: always blocks, non-blocking vs blocking assignment, inferring structures |
| [systemverilog_synthesis.md](systemverilog_synthesis.md) | SV constructs safe for synthesis: always_ff/always_comb, enums, structs, interfaces, packages |

## See Also

- [VHDL](../vhdl/README.md) — Strongly-typed alternative IEEE standard
- [Legacy HDLs](../legacy_hdl/README.md) — Vendor-specific predecessors
- [Inference Rules](../inference_rules.md) — What Verilog/SV code infers in silicon
