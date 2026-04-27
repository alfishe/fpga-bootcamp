[← Home](../README.md)

# 04 — HDL & Synthesis

Writing hardware description languages that synthesize correctly and efficiently. Covers legacy vendor-specific HDLs, VHDL, Verilog/SystemVerilog, high-level synthesis (HLS), and cross-cutting topics: inference rules, vendor pragmas, CDC coding patterns, and safe state machine design.

## Index

### HDL Families

| Folder | Coverage |
|---|---|---|
| [legacy_hdl/](legacy_hdl/README.md) | Ancient/vendor-specific HDLs: AHDL, ABEL, PALASM — languages that predate modern Verilog/VHDL |
| [vhdl/](vhdl/README.md) | **VHDL-2008** for synthesis: entities, architectures, processes, records, generics |
| [verilog_sv/](verilog_sv/README.md) | **Verilog-2001** and **SystemVerilog** for synthesis: always blocks, interfaces, structs, packages |
| [hls/](hls/README.md) | **High-Level Synthesis**: scheduling, pipelining, loop unroll, array partition, interface synthesis |

### Cross-HDL Topics

| File | Topic |
|---|---|---|
| [inference_rules.md](inference_rules.md) | What HDL pattern infers what hardware: RAM, ROM, multiplier, shift register, latch vs flop |
| [vendor_pragmas.md](vendor_pragmas.md) | Xilinx attributes, Altera synthesis directives, Gowin pragmas, keep/dont_touch, async_reg |
| [cdc_coding.md](cdc_coding.md) | HDL patterns for clock domain crossing: 2-FF synchronizer, handshake, async FIFO, MCP |
| [state_machines.md](state_machines.md) | Safe FSM encoding: one-hot vs binary vs Gray, reset strategies, unreachable state recovery |
