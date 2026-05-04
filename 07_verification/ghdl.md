[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# GHDL — Open-Source VHDL Simulator and Synthesis Tool

GHDL is the most complete open-source VHDL simulator, supporting VHDL-87, -93, -2008, and partial 2019. It also provides experimental synthesis to Verilog/netlist for Yosys integration. If your design is in VHDL, GHDL is the go-to open-source tool for simulation, linting, and co-simulation with cocotb.

This article covers installation, the analyze/elaborate/run flow, VHDL testbench authoring, waveform output, assertion-based verification, cocotb integration, synthesis to Yosys, and best practices.

---

## How GHDL Works

GHDL is an **ahead-of-time compiled** simulator. It analyzes VHDL source into an internal representation, elaborates the design hierarchy, and generates an executable (or LLVM IR) that runs the simulation.

```
VHDL source (.vhd)
       │
       ▼
┌────────────────┐     ┌────────────────┐     ┌───────────────┐
│  Analyze       │     │  Elaborate     │     │  Run          │
│  (ghdl -a)     │────►│  (ghdl -e)     │────►│  (ghdl -r)    │
│  Syntax check  │     │  Link hierarchy│     │  Execute sim  │
│  Semantic check│     │  Generate code │     │  VCD/FST/GHW  │
└────────────────┘     └────────────────┘     └───────────────┘
```

Unlike Verilator, GHDL supports:
- Full VHDL simulation semantics (delta cycles, resolution functions, `after` delays)
- `X` and `Z` logic values (9-value std_logic)
- Protected types, VHPI, and VPI interfaces
- `assert`/`report` for self-checking testbenches
- PSL (Property Specification Language) assertions

---

## Installation

### Linux (package manager)

```bash
# Ubuntu/Debian (LLVM backend — recommended)
sudo apt install ghdl llvm

# Fedora
sudo dnf install ghdl

# Arch
sudo pacman -S ghdl-llvm   # or ghdl-mcode for simpler setup
```

### From Source (latest version, LLVM backend)

```bash
git clone https://github.com/ghdl/ghdl
cd ghdl
mkdir build && cd build
../configure --with-llvm-config
make -j$(nproc)
sudo make install
```

### Windows

```bash
# MSYS2
pacman -S mingw-w64-x86_64-ghdl-llvm

# WSL2 (recommended for large designs)
wsl --install
# Then follow Linux instructions
```

### Verify Installation

```bash
ghdl --version
# Expected: GHDL 5.x-dev (LLVM backend)
```

### Backend Comparison

| Backend | Speed | Compile Time | Use Case |
|---|---|---|---|
| **mcode** | Fastest runtime | Fastest compile | Small designs, quick iteration |
| **LLVM** | Good runtime | Slower compile | Large designs, production (recommended) |
| **GCC** | Good runtime | Slowest compile | Maximum optimization; less common now |

---

## The GHDL Flow: Analyze, Elaborate, Run

### Step 1: Analyze (`ghdl -a`)

Parses VHDL source, checks syntax and semantics, creates work library entries:

```bash
ghdl -a --std=08 counter.vhd tb_counter.vhd
```

**Common analyze options:**

| Option | Purpose |
|---|---|
| `--std=08` | Use VHDL-2008 standard (recommended) |
| `--std=93` | Use VHDL-93 standard (legacy) |
| `--work=work` | Specify work library (default: `work`) |
| `--ieee=synopsys` | Use Synopsys-compatible IEEE libraries |
| `-Pdir` | Add directory to library search path |
| `-frelaxed-rules` | Allow some non-standard constructs |

### Step 2: Elaborate (`ghdl -e`)

Links the design hierarchy, resolves generics and ports, generates simulation code:

```bash
ghdl -e --std=08 tb_counter
```

### Step 3: Run (`ghdl -r`)

Executes the simulation:

```bash
ghdl -r tb_counter --vcd=wave.vcd --stop-time=10us
```

**Common run options:**

| Option | Purpose |
|---|---|
| `--vcd=file.vcd` | Dump VCD waveform |
| `--fst=file.fst` | Dump FST waveform (faster, compressed) |
| `--ghw=file.ghw` | Dump GHW waveform (GHDL native — supports all VHDL types) |
| `--stop-time=10us` | Stop after 10 µs of simulation time |
| `--stop-delta=1000` | Stop after 1000 delta cycles (infinite loop detection) |
| `--assert-level=error` | Stop on ERROR severity assertions |
| `--assert-level=none` | Never stop on assertions (for batch runs) |
| `--ieee-asserts=disable` | Disable IEEE library assertions |
| `--unbuffered` | Flush output immediately (CI/CD) |
| `--disp-time` | Display simulation time on assertions |
| `--sdf=min=/dut=impl.sdf` | Apply SDF timing (min/max/typ) |

---

## Example: Counter Testbench with Self-Check

```vhdl
-- counter.vhd
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
    port (
        clk   : in  std_logic;
        rst   : in  std_logic;
        en    : in  std_logic;
        count : out unsigned(7 downto 0)
    );
end entity;

architecture rtl of counter is
    signal cnt : unsigned(7 downto 0) := (others => '0');
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                cnt <= (others => '0');
            elsif en = '1' then
                cnt <= cnt + 1;
            end if;
        end if;
    end process;
    count <= cnt;
end architecture;
```

```vhdl
-- tb_counter.vhd
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_counter is end entity;

architecture sim of tb_counter is
    signal clk   : std_logic := '0';
    signal rst   : std_logic := '1';
    signal en    : std_logic := '0';
    signal count : unsigned(7 downto 0);

    constant CLK_PERIOD : time := 10 ns;  -- 100 MHz
begin
    -- DUT
    dut: entity work.counter
        port map (clk => clk, rst => rst, en => en, count => count);

    -- Clock generation
    clk <= not clk after CLK_PERIOD / 2;

    -- Stimulus
    process
        variable errors : integer := 0;
    begin
        -- Reset
        wait for 50 ns;
        rst <= '0';
        wait until rising_edge(clk);

        -- Test: count up
        en <= '1';
        for i in 1 to 200 loop
            wait until rising_edge(clk);
            if count /= to_unsigned(i, 8) then
                report "FAIL: count = " & integer'image(to_integer(count)) &
                       ", expected " & integer'image(i)
                    severity error;
                errors := errors + 1;
            end if;
        end loop;

        -- Test: disable freezes count
        en <= '0';
        wait until rising_edge(clk);
        if count /= 200 then
            report "FAIL: count changed while disabled"
                severity error;
            errors := errors + 1;
        end if;

        -- Test: reset clears count
        rst <= '1';
        wait until rising_edge(clk);
        if count /= 0 then
            report "FAIL: reset didn't clear count"
                severity error;
            errors := errors + 1;
        end if;

        -- Report
        if errors = 0 then
            report "PASS: All counter tests passed" severity note;
        else
            report "FAIL: " & integer'image(errors) & " errors" severity error;
        end if;

        -- Stop simulation
        wait;
    end process;
end architecture;
```

```bash
# Analyze, elaborate, run
ghdl -a --std=08 counter.vhd tb_counter.vhd
ghdl -e --std=08 tb_counter
ghdl -r tb_counter --vcd=counter.vcd --stop-time=100us --assert-level=error
# Output: ... PASS: All counter tests passed

# View waveform
gtkwave counter.vcd &
```

---

## Example: FIFO Testbench with Record Types

VHDL's record types make FIFO testbenches cleaner:

```vhdl
-- fifo_pkg.vhd — Shared types and constants
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package fifo_pkg is
    constant DATA_WIDTH : integer := 8;
    constant FIFO_DEPTH : integer := 16;

    subtype data_t is std_logic_vector(DATA_WIDTH-1 downto 0);

    type fifo_status_t is record
        full  : std_logic;
        empty : std_logic;
        count : integer range 0 to FIFO_DEPTH;
    end record;
end package;
```

```vhdl
-- tb_fifo.vhd
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.fifo_pkg.all;

entity tb_fifo is end entity;

architecture sim of tb_fifo is
    signal clk     : std_logic := '0';
    signal rst_n   : std_logic := '0';
    signal wr_en   : std_logic := '0';
    signal rd_en   : std_logic := '0';
    signal wr_data : data_t := (others => '0');
    signal rd_data : data_t;
    signal full    : std_logic;
    signal empty   : std_logic;

    constant CLK_PERIOD : time := 10 ns;
begin
    dut: entity work.fifo
        port map (
            clk     => clk,
            rst_n   => rst_n,
            wr_en   => wr_en,
            wr_data => wr_data,
            rd_en   => rd_en,
            rd_data => rd_data,
            full    => full,
            empty   => empty
        );

    clk <= not clk after CLK_PERIOD / 2;

    process
        variable errors : integer := 0;
    begin
        -- Reset
        wait for 50 ns;
        rst_n <= '1';
        wait until rising_edge(clk);

        -- Write 16 values
        for i in 0 to FIFO_DEPTH - 1 loop
            wr_en <= '1';
            wr_data <= std_logic_vector(to_unsigned(i, DATA_WIDTH));
            wait until rising_edge(clk);
        end loop;
        wr_en <= '0';
        wait until rising_edge(clk);

        -- Check full flag
        assert full = '1'
            report "FAIL: FIFO should be full"
            severity error;

        -- Read all values
        for i in 0 to FIFO_DEPTH - 1 loop
            rd_en <= '1';
            wait until rising_edge(clk);
            wait for 1 ns;  -- Let outputs settle
            if rd_data /= std_logic_vector(to_unsigned(i, DATA_WIDTH)) then
                report "FAIL: read " & integer'image(to_integer(unsigned(rd_data))) &
                       ", expected " & integer'image(i)
                    severity error;
                errors := errors + 1;
            end if;
        end loop;
        rd_en <= '0';
        wait until rising_edge(clk);

        -- Check empty flag
        assert empty = '1'
            report "FAIL: FIFO should be empty"
            severity error;

        -- Report
        if errors = 0 then
            report "PASS: FIFO test passed" severity note;
        else
            report "FAIL: " & integer'image(errors) & " errors" severity error;
        end if;

        wait;
    end process;
end architecture;
```

```bash
ghdl -a --std=08 fifo_pkg.vhd fifo.vhd tb_fifo.vhd
ghdl -e --std=08 tb_fifo
ghdl -r tb_fifo --vcd=fifo.vcd --stop-time=50us
```

---

## Example: UART TX Testbench with Textio

```vhdl
-- tb_uart_tx.vhd
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;  -- VHDL text I/O

entity tb_uart_tx is end entity;

architecture sim of tb_uart_tx is
    signal clk      : std_logic := '0';
    signal rst_n    : std_logic := '0';
    signal tx_start : std_logic := '0';
    signal tx_data  : std_logic_vector(7 downto 0) := (others => '0');
    signal tx_busy  : std_logic;
    signal tx_out   : std_logic;

    constant CLK_PERIOD : time := 10 ns;   -- 100 MHz system clock
    constant BAUD_RATE  : integer := 115200;
    constant BIT_PERIOD : time := 1 sec / BAUD_RATE;
begin
    dut: entity work.uart_tx
        port map (
            clk      => clk,
            rst_n    => rst_n,
            tx_start => tx_start,
            tx_data  => tx_data,
            tx_busy  => tx_busy,
            tx_out   => tx_out
        );

    clk <= not clk after CLK_PERIOD / 2;

    -- Receive process: decode UART bitstream
    process
        variable received : std_logic_vector(7 downto 0);
        variable l        : line;  -- For textio output
    begin
        wait for 100 ns;
        rst_n <= '1';

        -- Test: send 0x55 (alternating bits — worst case for timing)
        wait until rising_edge(clk);
        tx_data  <= x"55";
        tx_start <= '1';
        wait until rising_edge(clk);
        tx_start <= '0';

        -- Wait for start bit
        wait until tx_out = '0';  -- Start bit
        wait for BIT_PERIOD / 2;  -- Sample at middle of bit

        -- Receive 8 data bits
        for i in 0 to 7 loop
            wait for BIT_PERIOD;
            received(i) := tx_out;
        end loop;

        -- Check stop bit
        wait for BIT_PERIOD;
        assert tx_out = '1'
            report "FAIL: stop bit not high"
            severity error;

        -- Verify data
        assert received = x"55"
            report "FAIL: received 0x" &
                   integer'image(to_integer(unsigned(received))) &
                   ", expected 0x55"
            severity error;

        write(l, string'("PASS: UART TX test — received 0x55"));
        writeline(output, l);

        wait;
    end process;
end architecture;
```

```bash
ghdl -a --std=08 uart_tx.vhd tb_uart_tx.vhd
ghdl -e --std=08 tb_uart_tx
ghdl -r tb_uart_tx --stop-time=2ms --assert-level=error
```

---

## Waveform Output Formats

### VCD (Value Change Dump)

```bash
ghdl -r tb --vcd=wave.vcd
```

- Standard format; works with GTKWave, Surfer, and commercial viewers
- Only 4-state (0, 1, X, Z) — VHDL enumerated types are not fully represented
- File size can be large for long simulations

### FST (Fast Signal Trace)

```bash
ghdl -r tb --fst=wave.fst
```

- Compressed format; 10–50× smaller than VCD
- Faster to load in GTKWave
- Requires GTKWave 3.3+

### GHW (GHDL Waveform)

```bash
ghdl -r tb --ghw=wave.ghw
```

- GHDL's native format
- **Supports all VHDL types** (records, enumerated types, integer arrays)
- Best fidelity for VHDL-specific signals
- Only viewable in GTKWave (with GHW support)

### Format Comparison

| Format | VHDL Type Fidelity | File Size | Viewer Support | Speed |
|---|---|---|---|---|
| **VCD** | 4-state only | Large | Universal | Moderate |
| **FST** | 4-state only | Small | GTKWave | Fast |
| **GHW** | Full (records, enums) | Medium | GTKWave only | Moderate |

**Recommendation:** Use GHW during development (full type fidelity), FST for regression (speed + size).

---

## Assertion-Based Verification

GHDL supports VHDL `assert`/`report` and PSL (Property Specification Language).

### VHDL Assert

```vhdl
-- Immediate assertion (in process)
assert fifo_full = '1'
    report "FIFO should be full after 16 writes"
    severity error;

-- Concurrent assertion (continuous check)
-- VHDL-2008: PSL in VHDL
-- psl assert always (full -> not wr_en) abort rst_n;
```

### PSL Properties (VHDL-2008)

```vhdl
-- psl_counter_never_negative.vhd
architecture sim of tb_counter is
    -- PSL property: count should never underflow
    -- psl property count_nonneg is always (count >= 0);
    -- psl assert count_nonneg;
begin
    -- ...
end architecture;
```

### Assertion Severity Levels

| Severity | GHDL Default Behavior | `--assert-level` Effect |
|---|---|---|
| **Note** | Print message | Ignored |
| **Warning** | Print message | Ignored |
| **Error** | Print message + continue | `--assert-level=error` → stop simulation |
| **Failure** | Print message + stop | Always stops simulation |

**CI/CD tip:** Use `--assert-level=error` to make the simulation fail on any assertion error:

```bash
ghdl -r tb --assert-level=error --stop-time=100us
echo $?  # 0 = pass, 1 = assertion failure
```

---

## GHDL + cocotb (Python Testbench)

GHDL works with cocotb through the VPI interface:

```python
# test_counter.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter_up(dut):
    """Test counter increments when enabled."""
    cocotb.start_soon(Clock(dut.clk, 10, units='ns').start())

    # Reset
    dut.rst.value = 1
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # Count up and check
    for i in range(1, 201):
        dut.en.value = 1
        await RisingEdge(dut.clk)
        assert dut.count.value == i, f"Expected {i}, got {dut.count.value}"

@cocotb.test()
async def test_counter_disable(dut):
    """Test counter freezes when disabled."""
    cocotb.start_soon(Clock(dut.clk, 10, units='ns').start())

    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # Count to 50
    dut.en.value = 1
    for _ in range(50):
        await RisingEdge(dut.clk)

    # Disable and check frozen
    dut.en.value = 0
    frozen = dut.count.value
    await RisingEdge(dut.clk)
    assert dut.count.value == frozen, "Counter changed while disabled"
```

```makefile
# Makefile
SIM = ghdl
TOPLEVEL_LANG = vhdl
VHDL_SOURCES = counter.vhd
MODULE = test_counter
include $(shell cocotb-config --makefiles)/Makefile.sim
```

```bash
make SIM=ghdl
```

---

## GHDL Synthesis to Yosys

GHDL can synthesize VHDL to a Verilog netlist, which Yosys can then optimize and map to FPGA:

### GHDL Synthesis Plugin for Yosys

```bash
# Install ghdl-yosys-plugin
sudo apt install yosys ghdl-yosys-plugin

# Or build from source:
git clone https://github.com/ghdl/ghdl-yosys-plugin
cd ghdl-yosys-plugin
make install
```

### Synthesis Flow

```bash
# Method 1: GHDL synth → Verilog → Yosys
ghdl --synth --std=08 top.vhd -e top > top_synth.v
yosys -p "read_verilog top_synth.v; synth_xilinx -top top"

# Method 2: GHDL-Yosys plugin (direct)
yosys -p "ghdl --std=08 top.vhd -e top; synth_xilinx -top top"
```

### What Works in Synthesis

| VHDL Feature | Synthesis Support |
|---|---|
| `if`/`case` | Yes — maps to muxes and priority logic |
| `for`/`generate` | Yes — unrolls to parallel hardware |
| `process(clk)` | Yes — infers registers |
| Records | Yes — flattened to individual signals |
| `unsigned`/`signed` | Yes — maps to arithmetic |
| `std_logic_vector` | Yes — maps to wires/buses |
| `textio` | No — simulation only |
| `after` delays | No — ignored in synthesis |
| `assert`/`report` | No — simulation only |
| Protected types | No — simulation only |
| File I/O | No — simulation only |

---

## Multi-Library Projects

For designs with multiple VHDL libraries:

```bash
# Create library directories
mkdir -p work lib1 lib2

# Analyze into specific libraries
ghdl -a --std=08 --work=lib1 src/lib1_pkg.vhd src/lib1_core.vhd
ghdl -a --std=08 --work=lib2 src/lib2_pkg.vhd src/lib2_utils.vhd
ghdl -a --std=08 --work=work src/top.vhd src/tb.vhd

# Elaborate (GHDL resolves cross-library references)
ghdl -e --std=08 -Plib1 -Plib2 tb

# Run
ghdl -r tb --vcd=wave.vcd
```

**Common convention:** `lib1` and `lib2` directories contain `.cf` files (GHDL library info) created by `ghdl -a`. The `-P` flag adds them to the search path.

---

## GHDL + Verilator (VHDL + Verilog Mixed)

For mixed VHDL/Verilog projects, use GHDL to convert VHDL to Verilog, then simulate with Verilator:

```bash
# Step 1: Synthesize VHDL to Verilog
ghdl --synth --std=08 vhd_module.vhd -e vhd_module > vhd_module_synth.v

# Step 2: Simulate the Verilog with Verilator
verilator --cc --build -j 0 vhd_module_synth.v verilog_top.v --exe tb.cpp
./obj_dir/Vverilog_top
```

**Limitations:** The synthesized Verilog is a netlist (structural, not behavioral). Debugging signal names may not match original VHDL. Use this for functional verification only, not for waveform debugging of VHDL constructs.

---

## CI/CD Integration

### GitHub Actions

```yaml
name: GHDL Regression

on: [push, pull_request]

jobs:
  sim:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install GHDL
        run: |
          sudo apt update
          sudo apt install -y ghdl llvm

      - name: Analyze
        run: ghdl -a --std=08 src/*.vhd

      - name: Elaborate and Run
        run: |
          ghdl -e --std=08 tb_top
          ghdl -r tb_top --assert-level=error --stop-time=100us --fst=wave.fst

      - name: Upload Waveform
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: waveforms
          path: wave.fst
```

### Makefile for VHDL Projects

```makefile
# Makefile
GHDL = ghdl
STD  = --std=08
VHDL_SOURCES = src/counter.vhd src/fifo.vhd src/top.vhd
TB = tb_top

all: run

analyze:
	$(GHDL) -a $(STD) $(VHDL_SOURCES) tb/$(TB).vhd

elaborate: analyze
	$(GHDL) -e $(STD) $(TB)

run: elaborate
	$(GHDL) -r $(TB) --assert-level=error --stop-time=100us --fst=wave.fst

view: run
	gtkwave wave.fst &

clean:
	$(GHDL) --remove
	rm -f *.cf *.vcd *.fst *.ghw e*.o work-obj08.cf

.PHONY: all analyze elaborate run view clean
```

---

## Best Practices

### 1. Use VHDL-2008 (`--std=08`)

VHDL-2008 adds significant improvements: simplified entity instantiation, conditional/selected signal assignment, PSL integration, and more. GHDL's 2008 support is the most complete among open-source tools.

```vhdl
-- VHDL-2008: Direct entity instantiation (no component declaration)
dut: entity work.counter
    port map (clk => clk, rst => rst, count => count);

-- VHDL-2008: Conditional assignment
mux_out <= a when sel = '0' else b;

-- VHDL-2008: Conditional signal assignment with elsif
y <= a when s = "00" else
     b when s = "01" else
     c when s = "10" else
     d;
```

### 2. Use `assert` for Self-Checking Tests

```vhdl
-- Good: self-checking with meaningful messages
assert rd_data = expected_data
    report "FIFO read mismatch: got 0x" &
           to_hstring(rd_data) & ", expected 0x" & to_hstring(expected_data)
    severity error;

-- Bad: no self-check (only visual waveform inspection)
-- If you only look at waveforms, you WILL miss bugs
```

### 3. Always Set `--assert-level` in CI

```bash
# CI: stop on first assertion error
ghdl -r tb --assert-level=error

# Development: see all errors
ghdl -r tb --assert-level=failure
```

### 4. Use `--stop-delta` to Catch Infinite Delta Loops

```bash
ghdl -r tb --stop-delta=10000
# If simulation doesn't advance time after 10000 delta cycles,
# there's a combinational loop or zero-delay feedback
```

### 5. Prefer GHW for VHDL-Specific Types

```bash
# Records, enums, integers → preserved in GHW, lost in VCD
ghdl -r tb --ghw=wave.ghw
gtkwave wave.ghw  # Can inspect record fields, enum names
```

### 6. Use `--disp-time` for Debug

```bash
ghdl -r tb --disp-time --assert-level=error
# Output: 1250 ns: @assert: FAIL: FIFO should be full
# Makes it easy to find the exact time of failure
```

### 7. Separate Libraries Cleanly

```
project/
├── lib1/
│   └── src/*.vhd      -- Analyze with --work=lib1
├── lib2/
│   └── src/*.vhd      -- Analyze with --work=lib2
├── rtl/
│   └── src/*.vhd      -- Analyze with --work=work
└── tb/
    └── src/*.vhd      -- Analyze with --work=work
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Missing `--std=08`** | VHDL-2008 syntax rejected | Always specify `--std=08` |
| **Forgetting `-a` step** | `ghdl -e` can't find design units | Analyze all files before elaborate |
| **Wrong entity name in `-e`** | "unknown design unit" | Entity name is case-sensitive; match exactly |
| **Library path not set** | "library XXX not found" | Add `-Plib_dir` when elaborating |
| **`after` in testbench, no time advance** | Simulation hangs at time 0 | Use `wait for` or ensure clock is running |
| **VCD losing record types** | Record fields not visible in GTKWave | Use `--ghw` instead of `--vcd` |
| **assert without severity** | Errors don't stop simulation in CI | Use `--assert-level=error` |
| **Delta loop** | Simulation never advances time | Use `--stop-delta` to detect; fix combinational loop |

---

## GHDL vs Other VHDL Simulators

| Feature | GHDL | ModelSim/ Questa | NVC | Free VHDL Simulator |
|---|---|---|---|---|
| **VHDL-2008** | Most complete | Complete | Partial | Limited |
| **Speed** | Fast (compiled) | Moderate (interpreted) | Fast (LLVM) | Slow |
| **Synthesis** | Yes (`--synth`) | No | No | No |
| **Wave formats** | VCD, FST, GHW | WLF (VCD export) | VCD, FST | VCD |
| **Cocotb** | Yes (VPI) | Yes (VHPI/VPI) | Yes (VPI) | No |
| **PSL** | Yes | Yes (limited) | No | No |
| **SDF timing** | Yes | Yes | No | No |
| **Cost** | Free | $5K–$50K/year | Free | Free |
| **License** | GPL | Commercial | GPL | Various |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [GHDL Documentation](https://ghdl.github.io/ghdl/) | ghdl.github.io | Complete command reference, VHDL-2008 coverage |
| [GHDL GitHub](https://github.com/ghdl/ghdl) | GitHub | Issues, examples, contributing |
| [GHDL Synthesis](https://github.com/ghdl/ghdl-yosys-plugin) | GitHub | Yosys integration for VHDL synthesis |
| [Simulation Overview](simulation_overview.md) | This KB | Multi-simulator comparison |
| [Verilator](verilator.md) | This KB | Fast open-source Verilog simulator |
| [Cocotb](cocotb.md) | This KB | Python testbenches with GHDL backend |
