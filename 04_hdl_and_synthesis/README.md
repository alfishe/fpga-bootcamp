[← Home](../README.md)

# 04 — HDL & Synthesis

Writing hardware description languages that synthesize correctly and efficiently. Covers the three major HDLs (Verilog, SystemVerilog, VHDL), inference rules that map code to silicon primitives, vendor pragmas, CDC coding patterns, and safe state machine design.

## Index

| File | Topic |
|---|---|
| [verilog_basics.md](verilog_basics.md) | Verilog-2001 for synthesis: always blocks, non-blocking vs blocking assignment, inferring structures |
| [systemverilog_synthesis.md](systemverilog_synthesis.md) | SV constructs safe for synthesis: always_ff/always_comb, enums, structs, interfaces, packages |
| [vhdl_basics.md](vhdl_basics.md) | VHDL-2008 for synthesis: entities, architectures, processes, records, generics |
| [inference_rules.md](inference_rules.md) | What HDL pattern infers what hardware: RAM, ROM, multiplier, shift register, latch vs flop |
| [vendor_pragmas.md](vendor_pragmas.md) | Xilinx attributes, Altera synthesis directives, Gowin pragmas, keep/dont_touch, async_reg |
| [cdc_coding.md](cdc_coding.md) | HDL patterns for clock domain crossing: 2-FF synchronizer, handshake, async FIFO, MCP |
| [state_machines.md](state_machines.md) | Safe FSM encoding: one-hot vs binary vs Gray, reset strategies, unreachable state recovery |
