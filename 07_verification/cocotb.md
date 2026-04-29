[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Cocotb — Python-Based Coroutine Testbenches

Cocotb (COroutine-based COsimulation TestBench) is the dominant open-source verification framework for FPGA — write tests in Python that drive Verilog/VHDL simulation.

---

## Why Cocotb for FPGA

| Advantage | Detail |
|---|---|
| **Python** | Rich ecosystem: numpy for DSP verification, PIL for image processing, scipy for math |
| **Simulator-agnostic** | Same test works on Verilator, Icarus, ModelSim, Questa, Xcelium, GHDL |
| **Coroutine model** | `async/await` patterns match hardware concurrency naturally |
| **Open source** | Free, MIT-licensed, no vendor lock-in |
| **CI-friendly** | Headless, scriptable, generates JUnit XML |

## Basic Structure

```python
import cocotb
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles

@cocotb.test()
async def my_first_test(dut):
    """Test that counter increments."""
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Drive inputs
    dut.rst.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst.value = 0

    # Check output
    await RisingEdge(dut.clk)
    assert dut.cnt.value == 0, f"Expected 0, got {dut.cnt.value}"
```

## Key Patterns

| Pattern | Use Case |
|---|---|
| `ClockCycles(dut.clk, N)` | Wait N clock cycles |
| `Timer(ns, units="ns")` | Wait absolute time |
| `RisingEdge(dut.sig)` / `FallingEdge(dut.sig)` | Edge detection |
| `await cocotb.start(python_function(dut))` | Fork parallel coroutine |
| `Join(coroutine)` + `First(coroutine1, coroutine2)` | Wait for any/all |
| `dut.sig.value = X` | Drive signal (int, BinaryValue, hex string) |
| `dut.sig.value.integer` | Read back as Python int |

## Simulator Setup

```makefile
# Makefile — works with any simulator
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES += $(PWD)/../rtl/my_design.v
TOPLEVEL = my_design
MODULE = test_my_design
include $(shell cocotb-config --makefiles)/Makefile.sim
```

## When to Use Cocotb vs SV Testbench

| Scenario | Cocotb | SystemVerilog Testbench |
|---|---|---|
| Algorithm/DSP verification (FFT, filter) | ✅ Python + numpy | No (limited math) |
| Image/audio processing | ✅ PIL, scipy, matplotlib | No |
| Protocol checking (AXI, SPI) | ✅ cocotb-bus extensions | ✅ SVA assertions |
| UVM-style testbench | Possible but verbose | ✅ UVM is native |
| CI regression | ✅ Python scripting | Possible via TCL scripts |

---

## Original Stub Description

Python-based coroutine testbenches: setup, writing tests in Python for Verilog/VHDL, async/await patterns

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../README.md)
- [README.md](README.md)
