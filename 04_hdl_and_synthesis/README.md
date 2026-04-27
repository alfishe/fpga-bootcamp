[← Home](../README.md)

# 04 — HDL & Synthesis

Writing hardware description languages that synthesize correctly and efficiently. Covers legacy vendor-specific HDLs, VHDL, Verilog/SystemVerilog, high-level synthesis (HLS), and cross-cutting topics: inference rules, vendor pragmas, CDC coding patterns, and safe state machine design.

## Index

### HDL Families

| Folder | Coverage |
|---|---|
| [legacy_hdl/](legacy_hdl/README.md) | Ancient/vendor-specific HDLs: AHDL, ABEL, PALASM — languages that predate modern Verilog/VHDL |
| [vhdl/](vhdl/README.md) | **VHDL** (IEEE 1076): origins in the DoD VHSIC program (1981), Ada heritage, strong typing, standards evolution from 1987 through 2019, PSL verification, OSVVM/UVVM, synthesis subset |
| [verilog_sv/](verilog_sv/README.md) | **Verilog** (IEEE 1364) and **SystemVerilog** (IEEE 1800): origins at Gateway (1983), C-like philosophy, multi-parent lineage (Superlog + Vera + Verilog), dual design/verification roles, UVM ecosystem, synthesis subset |
| [hls/](hls/README.md) | **High-Level Synthesis**: scheduling, pipelining, loop unroll, array partition, interface synthesis |

### Cross-HDL Topics

| File | Topic |
|---|---|
| [inference_rules.md](inference_rules.md) | What HDL pattern infers what hardware: RAM, ROM, multiplier, shift register, latch vs flop |
| [vendor_pragmas.md](vendor_pragmas.md) | Xilinx attributes, Altera synthesis directives, Gowin pragmas, keep/dont_touch, async_reg |
| [cdc_coding.md](cdc_coding.md) | HDL patterns for clock domain crossing: 2-FF synchronizer, handshake, async FIFO, MCP |
| [state_machines.md](state_machines.md) | Safe FSM encoding: one-hot vs binary vs Gray, reset strategies, unreachable state recovery |
