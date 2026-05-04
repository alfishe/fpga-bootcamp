[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Cocotb — Python-Based Coroutine Testbenches

Cocotb (COroutine-based COsimulation TestBench) is the dominant open-source verification framework for FPGA — write tests in Python that drive Verilog/VHDL simulation through any simulator backend.

This article covers setup, real testbench examples, the Makefile and runner workflows, cocotb-bus for AXI/Avalon verification, and CI/CD integration.

---

## Why Cocotb for FPGA

| Advantage | Detail |
|---|---|
| **Python** | Rich ecosystem: numpy for DSP verification, PIL for image processing, scipy for math |
| **Simulator-agnostic** | Same test works on Verilator, Icarus, ModelSim, Questa, Xcelium, GHDL |
| **Coroutine model** | `async/await` patterns match hardware concurrency naturally |
| **Open source** | Free, BSD-licensed, no vendor lock-in |
| **CI-friendly** | Headless, scriptable, generates JUnit XML |
| **No testbench HDL** | Testbench is pure Python — no `initial` blocks, no timescale, no Verilog testbench files |

---

## Installation and Setup

```bash
# Install cocotb (requires Python 3.7+)
pip install cocotb

# Install bus extensions for AXI/Avalon
pip install cocotbext-axi

# Install a simulator (pick one)
sudo apt install iverilog       # Icarus Verilog — simplest
sudo apt install verilator      # Verilator — fastest
sudo apt install ghdl           # GHDL — for VHDL

# Verify installation
cocotb-config --makefiles
# Should output: /path/to/cocotb/makefiles
```

---

## Test 1: Simple Counter Verification

The "hello world" of FPGA verification — a counter that increments on each clock cycle:

**DUT (counter.v):**
```verilog
module counter (
    input  wire        clk,
    input  wire        rst,
    input  wire        inc,
    output reg  [7:0]  cnt
);
    always @(posedge clk) begin
        if (rst)       cnt <= 8'd0;
        else if (inc)  cnt <= cnt + 1;
    end
endmodule
```

**Test (test_counter.py):**
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

@cocotb.test()
async def test_counter_reset(dut):
    """Counter resets to 0 and stays 0 when not incrementing."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Apply reset
    dut.rst.value = 1
    dut.inc.value = 0
    await ClockCycles(dut.clk, 5)

    # Release reset — counter should be 0
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    assert dut.cnt.value == 0, f"After reset, cnt={dut.cnt.value}, expected 0"

    # Without inc, counter stays 0
    await ClockCycles(dut.clk, 10)
    assert dut.cnt.value == 0, f"Counter changed without inc: cnt={dut.cnt.value}"


@cocotb.test()
async def test_counter_increment(dut):
    """Counter increments by 1 each cycle when inc=1."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.inc.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

    # Increment for 200 cycles
    dut.inc.value = 1
    for i in range(200):
        await RisingEdge(dut.clk)
        # cnt updates on the NEXT edge, so check after increment
        expected = (i + 1) % 256
        assert dut.cnt.value == expected, \
            f"Cycle {i}: cnt={dut.cnt.value}, expected {expected}"


@cocotb.test()
async def test_counter_wraparound(dut):
    """Counter wraps from 255 to 0."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.inc.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst.value = 0

    # Force counter to 254 via backdoor load (if DUT supports it)
    # Or: count 255 cycles from 0
    dut.inc.value = 1
    for i in range(256):  # Count 0→255→0
        await RisingEdge(dut.clk)

    # After 256 increments, counter should wrap to 0
    assert dut.cnt.value == 0, \
        f"After 256 increments, cnt={dut.cnt.value}, expected 0 (wraparound)"
```

**Makefile:**
```makefile
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/../rtl/counter.v
TOPLEVEL = counter
MODULE = test_counter
include $(shell cocotb-config --makefiles)/Makefile.sim
```

```bash
make SIM=icarus
# 3 tests pass: reset, increment, wraparound
```

---

## Test 2: FIFO with Backpressure

This is a more realistic test — verifying a FIFO with randomized backpressure (ready/valid handshaking):

**Test (test_fifo.py):**
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, First
import random

class FifoBfm:
    """Bus Functional Model — drives FIFO signals."""
    def __init__(self, dut):
        self.dut = dut

    async def write(self, data):
        """Write one word to FIFO (wait until not full)."""
        self.dut.wr_data.value = data
        self.dut.wr_en.value = 1
        while self.dut.full.value:
            await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.wr_en.value = 0

    async def read(self):
        """Read one word from FIFO (wait until not empty)."""
        self.dut.rd_en.value = 1
        while self.dut.empty.value:
            await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        data = self.dut.rd_data.value.integer
        self.dut.rd_en.value = 0
        return data


@cocotb.test()
async def test_fifo_write_read(dut):
    """Write N values, read them back, verify order and data."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    bfm = FifoBfm(dut)
    test_data = [random.randint(0, 255) for _ in range(15)]

    # Write all values
    for val in test_data:
        await bfm.write(val)

    # Read all values back
    for expected in test_data:
        actual = await bfm.read()
        assert actual == expected, \
            f"Read {actual}, expected {expected}"

    # FIFO should now be empty
    assert dut.empty.value, "FIFO not empty after reading all data"


@cocotb.test()
async def test_fifo_concurrent_rw(dut):
    """Simultaneous read and write with backpressure."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    bfm = FifoBfm(dut)
    test_data = list(range(32))

    # Write in background
    async def writer():
        for val in test_data:
            await bfm.write(val)

    # Read in background
    read_data = []
    async def reader():
        for _ in test_data:
            val = await bfm.read()
            read_data.append(val)

    # Run both concurrently
    write_task = cocotb.start_soon(writer())
    read_task = cocotb.start_soon(reader())

    await First(write_task.join(), read_task.join())
    await Timer(100, units="ns")  # Let reads finish

    assert read_data == test_data, \
        f"Data mismatch: got {read_data}, expected {test_data}"
```

**Key pattern:** The `FifoBfm` class encapsulates signal-level driving into reusable methods. Tests call `bfm.write()` and `bfm.read()` — no signal-level details in the test logic.

---

## Test 3: AXI-Lite Slave with cocotbext-axi

For real-world FPGA verification, you need to talk AXI. The [cocotbext-axi](https://github.com/alexforencich/cocotbext-axi) library provides ready-made AXI masters and slaves:

**Test (test_axi_slave.py):**
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotbext.axi import AxiLiteBus, AxiLiteMaster

@cocotb.test()
async def test_axi_write_read(dut):
    """Write registers via AXI-Lite, read back, verify."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    # Create AXI-Lite master connected to DUT signals
    axi_master = AxiLiteMaster(
        AxiLiteBus.from_prefix(dut, "s_axi"),  # Auto-discovers s_axi_* signals
        dut.clk,
        dut.rst_n,
        reset_active_level=False
    )

    # Write to register 0 (address 0x00)
    await axi_master.write_dword(0x00, 0xDEADBEEF)
    # Write to register 1 (address 0x04)
    await axi_master.write_dword(0x04, 0xCAFEBABE)

    # Read back
    val0 = await axi_master.read_dword(0x00)
    val1 = await axi_master.read_dword(0x04)

    assert val0 == 0xDEADBEEF, f"Reg 0: read {val0:#x}, expected 0xDEADBEEF"
    assert val1 == 0xCAFEBABE, f"Reg 1: read {val1:#x}, expected 0xCAFEBABE"


@cocotb.test()
async def test_axi_all_registers(dut):
    """Write to all 16 registers, read back, verify all."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    axi_master = AxiLiteMaster(
        AxiLiteBus.from_prefix(dut, "s_axi"),
        dut.clk, dut.rst_n, reset_active_level=False
    )

    # Write unique pattern to each register
    for i in range(16):
        addr = i * 4
        data = (i << 24) | 0x12345678
        await axi_master.write_dword(addr, data)

    # Read back and verify
    for i in range(16):
        addr = i * 4
        expected = (i << 24) | 0x12345678
        actual = await axi_master.read_dword(addr)
        assert actual == expected, \
            f"Reg {i} (0x{addr:02x}): read 0x{actual:08x}, expected 0x{expected:08x}"
```

**Makefile for AXI test:**
```makefile
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/../rtl/axi_lite_slave.v
TOPLEVEL = axi_lite_slave
MODULE = test_axi_slave
include $(shell cocotb-config --makefiles)/Makefile.sim
```

> **Note:** `AxiLiteBus.from_prefix(dut, "s_axi")` auto-discovers signals named `s_axi_awaddr`, `s_axi_awvalid`, etc. Your DUT ports must follow this naming convention.

---

## Trigger Reference

Triggers are the core of cocotb — they control when a coroutine resumes:

| Trigger | Resumes When | Use Case |
|---|---|---|
| `RisingEdge(signal)` | Signal goes 0→1 | Sync to clock edge |
| `FallingEdge(signal)` | Signal goes 1→0 | Sync to negative edge |
| `ClockCycles(signal, N)` | N rising edges of signal | Wait N cycles |
| `Timer(time, units="ns")` | Absolute time elapsed | Wait fixed delay |
| `ReadOnly()` | After all signal updates (SimPhase) | Read stable outputs |
| `NextTimeStep()` | Next simulation time step | Break event-order dependency |
| `Combine(*coros)` | All coroutines complete | Wait for parallel tasks to finish |
| `First(*coros)` | First coroutine completes | Wait for either timeout or event |
| `with_timeout(coro, timeout, units)` | Coroutine completes or timeout | Prevent infinite waits |
| `Event()` | Manually set | Custom synchronization between coroutines |
| `Lock()` | Acquire/release | Mutual exclusion for shared resources |

### Timeout Pattern

```python
from cocotb.triggers import with_timeout, RisingEdge

@cocotb.test()
async def test_with_timeout(dut):
    """Wait for done signal, but fail if it takes too long."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for done, but timeout after 10 µs
    try:
        await with_timeout(RisingEdge(dut.done), 10, units="us")
    except cocotb.TriggerException:
        assert False, "DUT didn't assert done within 10 µs"
```

---

## Makefile vs Python Runner

Cocotb supports two ways to build and run tests:

### Option 1: Makefile (Traditional)

```makefile
# Makefile
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(PWD)/../rtl/my_design.v
TOPLEVEL = my_design
MODULE = test_my_design
include $(shell cocotb-config --makefiles)/Makefile.sim
```

```bash
make SIM=icarus           # Run with Icarus
make SIM=verilator        # Run with Verilator
make SIM=ghdl             # Run with GHDL (VHDL)
make SIM=xsim             # Run with Vivado XSim
```

### Option 2: Python Runner (cocotb 1.7+)

The newer approach — no Makefile needed, everything in Python:

```python
# run_tests.py
import cocotb
import cocotb.runner

def test_runner():
    runner = cocotb.runner.get_runner("icarus")  # or "verilator", "ghdl", etc.
    runner.build(
        verilog_sources=["../rtl/my_design.v"],
        hdl_toplevel="my_design",
    )
    runner.test(
        hdl_toplevel="my_design",
        test_module="test_my_design",
    )

if __name__ == "__main__":
    test_runner()
```

```bash
python run_tests.py
```

| Aspect | Makefile | Python Runner |
|---|---|---|
| Setup | Simple 5-line Makefile | More verbose but fully Python |
| IDE integration | External build step | Native `pytest` / `unittest` integration |
| CI/CD | `make` command | `python run_tests.py` |
| Flexibility | Make variables for sim config | Python code for sim config |
| Recommended for | Quick starts, small projects | Larger projects, IDE users |

---

## VHDL Designs with cocotb + GHDL

Cocotb works with VHDL designs via GHDL's VPI interface:

```makefile
# Makefile for VHDL
SIM = ghdl
TOPLEVEL_LANG = vhdl
VHDL_SOURCES = $(PWD)/../rtl/counter.vhd
TOPLEVEL = counter
MODULE = test_counter
include $(shell cocotb-config --makefiles)/Makefile.sim
```

The Python test file is identical — cocotb is language-agnostic at the testbench level. Signal names come from the VHDL entity port names.

---

## Scoreboard Pattern

For designs with independent input/output streams, use a scoreboard to track expected vs actual results:

```python
class Scoreboard:
    def __init__(self):
        self.expected = []
        self.errors = 0

    def add_expected(self, data):
        """Called when stimulus is sent to DUT."""
        self.expected.append(data)

    def check_actual(self, data):
        """Called when output appears from DUT."""
        if len(self.expected) == 0:
            self.errors += 1
            print(f"ERROR: Unexpected output: {data}")
            return
        expected = self.expected.pop(0)
        if data != expected:
            self.errors += 1
            print(f"ERROR: Expected {expected}, got {data}")

    def report(self):
        if self.errors == 0 and len(self.expected) == 0:
            print("PASS: Scoreboard matched")
        else:
            print(f"FAIL: {self.errors} mismatches, "
                  f"{len(self.expected)} missing outputs")


# Usage in test
@cocotb.test()
async def test_with_scoreboard(dut):
    sb = Scoreboard()
    bfm = FifoBfm(dut)
    # ... setup clock, reset ...

    async def writer():
        for val in test_data:
            sb.add_expected(val)
            await bfm.write(val)

    async def reader():
        for _ in test_data:
            val = await bfm.read()
            sb.check_actual(val)

    cocotb.start_soon(writer())
    await reader()
    sb.report()
    assert sb.errors == 0
```

---

## CI/CD Integration

### GitHub Actions with Verilator

```yaml
# .github/workflows/test.yml
name: FPGA Regression

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y verilator
          pip install cocotb cocotbext-axi

      - name: Run tests
        working-directory: fpga/07_verification
        run: |
          make SIM=verilator  # Fastest simulator for CI

      - name: Publish test results
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Cocotb Results
          path: results.xml
          reporter: java-junit
```

### Generating JUnit XML

```makefile
# Add to Makefile
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps
# JUnit XML output (for CI reporting)
MODULE = test_my_design
COCOTB_RESULTS_FILE = results.xml
```

Or with the Python runner:
```python
runner.test(
    hdl_toplevel="my_design",
    test_module="test_my_design",
    results_xml="results.xml",
)
```

---

## Cocotb Extensions Ecosystem

| Extension | What It Provides | GitHub |
|---|---|---|
| **cocotbext-axi** | AXI4, AXI4-Lite, AXI4-Stream master/slave | [alexforencich/cocotbext-axi](https://github.com/alexforencich/cocotbext-axi) |
| **cocotbext-spi** | SPI master/slave | [alexforencich/cocotbext-spi](https://github.com/alexforencich/cocotbext-spi) |
| **cocotbext-uart** | UART transmitter/receiver | [alexforencich/cocotbext-uart](https://github.com/alexforencich/cocotbext-uart) |
| **cocotbext-i2c** | I2C master | [alexforencich/cocotbext-i2c](https://github.com/alexforencich/cocotbext-i2c) |
| **cocotbext-pcie** | PCIe TLP generation/parsing | [alexforencich/cocotbext-pcie](https://github.com/alexforencich/cocotbext-pcie) |
| **cocotbext-wishbone** | Wishbone bus interface | Various |

### Writing Your Own Extension

```python
# my_bus_bfm.py
from cocotb.bus import BusDriver

class MyAxiMaster(BusDriver):
    _signals = ["awvalid", "awready", "awaddr",
                "wvalid", "wready", "wdata",
                "bvalid", "bready", "bresp"]

    def __init__(self, entity, name, clock, **kwargs):
        BusDriver.__init__(self, entity, name, clock, **kwargs)

    async def write(self, addr, data):
        self.bus.awaddr.value = addr
        self.bus.awvalid.value = 1
        self.bus.wdata.value = data
        self.bus.wvalid.value = 1
        await self._wait_for_signal(self.bus.awready)
        await self._wait_for_signal(self.bus.wready)
        # ... etc.
```

---

## When to Use Cocotb vs SV Testbench vs UVM

| Scenario | Cocotb | SystemVerilog Testbench | UVM |
|---|---|---|---|
| Algorithm/DSP verification (FFT, filter) | ✅ Python + numpy | Limited math | Overkill |
| Image/audio processing | ✅ PIL, scipy, matplotlib | No | No |
| Protocol checking (AXI, SPI) | ✅ cocotbext-axi | ✅ SVA assertions | ✅ UVM agents |
| Scoreboard/reference model | ✅ Python scoreboard | ✅ SV class-based | ✅ Built-in |
| Constrained-random stimulus | ✅ Python `random` | ✅ SV constraint solver | ✅ Built-in |
| UVM-style reusable VIP | Limited | Possible | ✅ Factory pattern |
| Team of 3+ verification engineers | ❌ Ad-hoc | ❌ Each writes own | ✅ Standard methodology |
| CI regression | ✅ Python-native | Via TCL scripts | Via TCL scripts |
| Large SoC with 5+ bus interfaces | ❌ Hard to coordinate | ❌ Unstructured | ✅ Agent per interface |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **No clock started** | `RisingEdge` hangs forever | Always `cocotb.start_soon(Clock(...).start())` before any test logic |
| **Signal not driven** | Read returns `Value('zzzz')` | Drive input: `dut.signal.value = 0` |
| **Missing `await`** | Test runs but never waits for clock | Every `RisingEdge`, `Timer`, `ClockCycles` must be `await`ed |
| **GPI errors** | "Unable to find signal" | Check signal name matches DUT hierarchy: `dut.module_name.signal` |
| **Cocotb version mismatch** | Import errors, API changes | Use `pip install cocotb==2.0` for version pinning |
| **Verilator + 4-state logic** | X/Z not detected | Verilator is 2-state; use Icarus or Questa for X-propagation testing |
| **Large tests with no timeout** | Simulation hangs on bug | Always use `with_timeout()` for any wait loop |
| **Race condition on signal read** | Read value before DUT updates it | Use `ReadOnly()` trigger to sample after DUT has updated |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Cocotb Documentation](https://docs.cocotb.org/) | cocotb.org | Complete API reference, quickstart, examples |
| [Cocotb Quickstart](https://docs.cocotb.org/en/stable/quickstart.html) | cocotb.org | Step-by-step first testbench |
| [Cocotb Build System](https://docs.cocotb.org/en/stable/building.html) | cocotb.org | Makefile and runner configuration |
| [Cocotb Extensions Guide](https://docs.cocotb.org/en/stable/extensions.html) | cocotb.org | Writing reusable bus drivers |
| [cocotbext-axi](https://github.com/alexforencich/cocotbext-axi) | GitHub | AXI4/AXI-Lite/AXI-Stream master/slave for cocotb |
| [Simulation Overview](simulation_overview.md) | This KB | Simulator comparison and setup |
| [UVM Overview](uvm_overview.md) | This KB | UVM testbench framework |
| [Formal Verification](formal_verification.md) | This KB | SymbiYosys, property checking |
