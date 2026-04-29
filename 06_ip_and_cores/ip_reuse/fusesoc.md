[← 06 Ip And Cores Home](../README.md) · [← Ip Reuse Home](README.md) · [← Project Home](../../../README.md)

# FuseSoC — IP Package Manager & Build System

FuseSoC is the de facto standard build system for open-source HDL projects. It handles dependency resolution, tool-agnostic build orchestration, and CI integration across Verilog, SystemVerilog, and VHDL codebases, targeting every major FPGA vendor from a single `.core` description file.

---

## What Problem FuseSoC Solves

| Without FuseSoC | With FuseSoC |
|---|---|
| Clone repo → figure out file list → set include paths manually | `fusesoc run --target=synth mycore` |
| Hard-coded vendor Tcl scripts per project | One `.core` file works with Vivado, Quartus, Diamond, Radiant, Verilator, Icarus, etc. |
| "Which version of that UART core works with this project?" | Pinned dependency versions in `.core` file |
| No automated linting | `fusesoc run --target=lint mycore` runs Verilator lint automatically |

---

## Core File Anatomy

A `.core` file (YAML with a `.core` extension) describes a single IP block:

```yaml
CAPI=2
name: ::my_uart:1.0
description: Simple UART with AXI4-Lite wrapper

filesets:
  rtl:
    files:
      - rtl/uart_tx.sv
      - rtl/uart_rx.sv
      - rtl/uart_axi_wrapper.sv
    file_type: systemVerilogSource
  tb:
    files:
      - tb/uart_tb.sv
    file_type: systemVerilogSource

parameters:
  DATA_WIDTH:
    datatype: int
    default: 8
    description: Bits per word
  BAUD_DIV:
    datatype: int
    default: 434
    description: Clock divider for baud rate

targets:
  default:
    filesets: [rtl]
    parameters: [DATA_WIDTH, BAUD_DIV]
  sim:
    filesets: [rtl, tb]
    toplevel: uart_tb
  lint:
    filesets: [rtl]
    tools:
      verilator:
        mode: lint-only
  synth_xilinx:
    filesets: [rtl]
    tools:
      vivado:
        part: xc7a35t-cpg236-1
```

---

## Dependency Resolution

FuseSoC pulls dependencies from a **core library** (local or remote):

```bash
# Add a core library (local directory or Git repo)
fusesoc library add my_cores /path/to/my/cores
fusesoc library add fusesoc_cores https://github.com/fusesoc/fusesoc-cores

# Check what's available
fusesoc list-cores

# Run a core (fetches deps automatically)
fusesoc run ::my_uart:1.0 --target=synth_xilinx
```

Dependencies declared in the core file:
```yaml
# my_uart.core depends on another core:
depend:
  - ::axi4_lite_if:1.0
```

FuseSoC recursively resolves the dependency tree before building.

---

## Tool Backend Matrix

| Tool | FuseSoC Backend | What It Does |
|---|---|---|
| **Vivado** | `vivado` | Generates Tcl project script, runs synth/impl |
| **Quartus** | `quartus` | Generates .qsf, runs compilation |
| **Diamond** | `diamond` | Lattice Diamond project generation |
| **Radiant** | `radiant` | Lattice Radiant project generation |
| **Verilator** | `verilator` | Lint-only or full simulation (C++ model) |
| **Icarus Verilog** | `icarus` | Simulation with iverilog |
| **ModelSim/Questa** | `modelsim` | Professional simulation |
| **Spyglass** | `spyglass` | Linting (requires license) |
| **Yosys** | `yosys` | Open-source synthesis |
| **GHDL** | `ghdl` | VHDL simulation and synthesis |

---

## CI Integration

FuseSoC is built for CI. A typical GitHub Actions workflow:

```yaml
name: FPGA CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: |
          pip install fusesoc
          sudo apt install verilator
          fusesoc library add my_lib .
      - name: Lint
        run: fusesoc run --target=lint ::my_core:1.0
      - name: Simulate
        run: fusesoc run --target=sim ::my_core:1.0
```

---

## When to Use FuseSoC vs Vendor IP Flow

| Scenario | Use |
|---|---|
| Open-source HDL project (GitHub) | **FuseSoC** — single `.core` file, works everywhere |
| Multi-vendor IP (targets Xilinx + Intel) | **FuseSoC** — one build system for all |
| CI/CD pipeline for hardware | **FuseSoC** — headless, scriptable, platform-agnostic |
| Vendor-specific IP (MIG, Platform Designer) | **Vendor IP flow** — no way to abstract vendor IP |
| Single-vendor, single-tool team | Either — vendor flow may be simpler |

---

## Best Practices

1. **Pin dependency versions** — use tags or commit hashes in `depend:`
2. **Separate RTL from testbench** — different `filesets` for synth vs sim
3. **CI from day 1** — FuseSoC makes this trivial, don't wait
4. **One `.core` per repository** — not per file. FuseSoC can reference files across subdirectories
5. **`default` target should synthesize** — it's what most users expect

---

## References

- [FuseSoC GitHub](https://github.com/olofk/fusesoc)
- [FuseSoC User Guide](https://fusesoc.readthedocs.io/)
- [FuseSoC Cores Library](https://github.com/fusesoc/fusesoc-cores)
- [Edalize (EDA tool abstraction library)](https://github.com/olofk/edalize) — used internally by FuseSoC
