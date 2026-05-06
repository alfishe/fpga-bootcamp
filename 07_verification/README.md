[← Home](../README.md)

# 07 — Verification

Making sure your design works before it hits silicon. Starts with the **language primitives** SystemVerilog provides for verification, then **co-simulation** with external models, through to **simulators**, **frameworks**, and protocol-specific VIPs.

## Index

| File | Topic |
|---|---|
| [sv_verification.md](sv_verification.md) | SystemVerilog verification primitives: assertions (SVA), functional coverage, constrained-random, classes, virtual interfaces, clocking blocks |
| [co_simulation.md](co_simulation.md) | Multi-language co-simulation: Verilog/SystemVerilog/C/C++ via DPI-C, MATLAB/Simulink, QEMU+SystemC for SoC, mixing VHDL with SV |
| [simulation_overview.md](simulation_overview.md) | Simulator comparison: Vivado XSim, ModelSim/Questa, Verilator, GHDL, Icarus, cocotb integration |
| [testbench_patterns.md](testbench_patterns.md) | Self-checking testbenches, reference models, scoreboards, coverage collection, constrained-random |
| [formal_verification.md](formal_verification.md) | SymbiYosys: assertions (assert/assume/cover), bounded model checking, k-induction, cover properties |
| [cocotb.md](cocotb.md) | Python-based coroutine testbenches: setup, writing tests in Python for Verilog/VHDL, async/await patterns |
| [verilator.md](verilator.md) | Verilator deep dive: C++ testbench authoring, tracing (VCD/FST), coverage, linting, multi-threaded sim, cocotb integration, CI/CD |
| [ghdl.md](ghdl.md) | GHDL deep dive: VHDL-2008 simulation, analyze/elaborate/run flow, textio, PSL assertions, cocotb integration, synthesis to Yosys |
| [uvm_overview.md](uvm_overview.md) | UVM basics for FPGA: agents, drivers, monitors, sequencers, scoreboards, factory override, TLM ports |
| [protocol_checkers.md](protocol_checkers.md) | AXI, Avalon, Wishbone protocol assertion VIPs and bus functional models (BFMs) |
| [coverage_methodology.md](coverage_methodology.md) | Coverage methodology: code coverage (statement/branch/MCDC/toggle/FSM), functional coverage (covergroups, cross coverage), assertion coverage, coverage-driven verification (CDV), coverage closure |

