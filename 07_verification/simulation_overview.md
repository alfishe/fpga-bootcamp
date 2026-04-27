[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Simulation Overview — FPGA Verification Landscape

Simulation is the first line of defense against FPGA bugs. Before a single bit is synthesized, simulation validates that the RTL behaves as intended. The FPGA ecosystem offers a spectrum of simulators — from vendor-locked free tools to industrial-grade commercial products to fully open-source options.

---

## The Simulator Landscape

| Simulator | Type | Language Support | License | Best For |
|---|---|---|---|---|
| **QuestaSim/ModelSim** | Commercial (Siemens) | VHDL, Verilog, SV, UVM, SVA | Paid (free Intel/Intel Starter, Microsemi DE) | Mixed-language, UVM, large designs |
| **Synopsys VCS** | Commercial | VHDL, Verilog, SV, UVM, SVA | Paid | ASIC-grade verification, highest performance |
| **Cadence Xcelium** | Commercial | VHDL, Verilog, SV, UVM, SVA | Paid | ASIC-grade, parallel simulation |
| **Vivado XSim (xsim)** | Vendor-free (Xilinx) | VHDL, Verilog, SV (subset) | Free (with Vivado) | Xilinx designs, IP simulation |
| **Quartus Sim (Questa Intel Starter)** | Vendor-free (Intel) | VHDL, Verilog, SV (subset) | Free (with Quartus) | Intel designs, limited to 10k lines |
| **Active-HDL** | Commercial (Aldec) | VHDL, Verilog, SV (subset) | Paid / Student | VHDL-focused, Windows native |
| **Riviera-PRO** | Commercial (Aldec) | VHDL, Verilog, SV, UVM | Paid | Advanced VHDL/Verilog/SV |
| **GHDL** | Open-source | VHDL (full 2008, partial 2019) | GPL / free | Open-source VHDL, CI/CD |
| **Icarus Verilog (iverilog)** | Open-source | Verilog (subset of 2005), limited SV | GPL / free | Quick Verilog simulation, CI/CD |
| **Verilator** | Open-source | Verilog + SV (synthesizable subset) → C++/SystemC | LGPL / free | Ultra-fast sim, CI/CD, large designs |
| **cocotb** | Open-source (testbench framework) | Python-driven, sim-agnostic | BSD / free | Python testbenches, co-simulation |
| **nvc** | Open-source | VHDL (focus on IEEE 1076-2019) | GPL / free | Modern VHDL, fast compile |

---

## How Each Simulator Fits the FPGA Flow

### Vivado XSim — The Xilinx Default

```
RTL (.v/.vhd) ──→ xvlog/xvhdl (analysis) ──→ xelab (elaboration) ──→ xsim (simulation)
                                   │                           │
                                   └── Vendor libraries        └── Waveform (.wdb)
                                       (unisims, secureip)
```

- Integrated: `Run Behavioral Simulation` from Vivado
- Automatically compiles Xilinx IP simulation libraries (unisims, simprims)
- Supports SDF back-annotation for post-synthesis/post-route timing simulation
- Waveform viewer included (limited compared to Questa/Verdi)
- Free, unlimited design size

### Questa Intel Starter Edition

```
RTL ──→ vlog/vcom (compile) ──→ vsim (simulate)
                       │               │
                       └── Intel libs  └── Wave window (.wlf)
                           (altera_mf, lpm, cyclonev)
```

- Free with Quartus Prime (Lite or Standard)
- Performance limit: 10,000 executable lines (enough for most FPGA modules)
- No UVM/coverage in free edition (need full Questa for that)
- Wavelength `.wlf` format; can convert to VCD

### Verilator — The Speed King

```bash
# Verilator: compile Verilog → C++, then simulate as native code
verilator --cc --build -j 0 top.v
./obj_dir/Vtop        # Runs at 100-1000x faster than interpreted simulators
```

- **Linting mode**: `verilator --lint-only` catches synthesis issues without testbench
- Compiles to C++ or SystemC; testbench is written in C++ (or Python via cocotb)
- VCD/FST waveform output
- No VHDL support, limited SV support (synthesizable subset only)
- Ideal for CI/CD: fast regression in seconds, not minutes

### Icarus Verilog — Quick & Simple

```bash
iverilog -o sim.vvp top.v tb.v
vvp sim.vvp            # Run simulation
```

- Verilog-focused, limited SystemVerilog (basic always_ff/always_comb, no UVM)
- Fast compile, slower simulation (interpreted)
- VCD output — any waveform viewer (GTKWave, Surfer)
- Perfect for quick checks and small modules

### GHDL — The VHDL Open-Source Champion

```bash
ghdl -a --std=08 top.vhd      # Analyze
ghdl -e --std=08 tb           # Elaborate
ghdl -r tb --vcd=wave.vcd     # Run
```

- Full VHDL-2008 support (one of the most complete implementations)
- Partial VHDL-2019 support
- Can generate Verilog/SystemC netlists via `--synth` for Yosys
- VCD/FST/GHW waveform output
- **cocotb compatible** — use Python to drive VHDL testbenches

---

## cocotb — Python Testbenches

cocotb (COroutine-based COsimulation TestBench) lets you write testbenches in Python, driving any simulator:

```python
# test_my_dut.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_fifo(dut):
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units='ns').start())

    # Reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    # Write data
    dut.wr_en.value = 1
    dut.wr_data.value = 0xAB
    await RisingEdge(dut.clk)

    # Check output
    assert dut.rd_data.value == 0xAB, "Data mismatch!"
```

### Simulator Backends

| Simulator | VPI/VHPI/GPI Interface | cocotb Support |
|---|---|---|
| Questa/ModelSim | FLI (VHDL), VPI (Verilog) | Yes (both) |
| Vivado XSim | VPI | Yes |
| Icarus Verilog | VPI | Yes |
| Verilator | VPI (wrapper) | Yes |
| GHDL | VPI | Yes |
| VCS | VPI | Yes |
| Aldec Riviera-PRO | VHPI/VPI | Yes |

cocotb is simulator-agnostic — switch backends by changing `make` variables:
```makefile
# Makefile
SIM ?= icarus       # or questa, xsim, verilator, ghdl, vcs
TOPLEVEL_LANG ?= verilog
```

---

## Waveform Viewers

| Tool | Format | License | Notes |
|---|---|---|---|
| **GTKWave** | VCD, FST, GHW, LXT | GPL / free | Classic open-source viewer; limited performance on large traces |
| **Surfer** | VCD, FST | MIT / free | Modern, fast, GPU-accelerated; written in Rust |
| **Vivado Waveform** | .wdb (proprietary) | Free (with Vivado) | Integrated with Xilinx flow |
| **Questa Wave** | .wlf (proprietary) | Paid / free starter | Part of Questa GUI |
| **Verdi / DVE** | VCD, FSDB | Paid (Synopsys) | ASIC-grade debugging; powerful signal tracing |
| **Scansion** | VCD | Free | Lightweight macOS viewer |

---

## Simulation Levels

```
┌── Behavioral (RTL) ──────────────────────────────────────┐
│ Fastest. Validates functional correctness.                │
│ No timing. Typically 0-delay or unit-delay (#1).         │
│ Run this FIRST for every module.                          │
└──────────────────────────────────────────────────────────┘
                           ↓
┌── Post-Synthesis (Gate-Level) ───────────────────────────┐
│ Netlist + SDF. Validates synthesis result.               │
│ Includes cell delays, no routing delays.                 │
│ Run for critical blocks (state machines, CDC).           │
│ Much slower than behavioral (~10-100x).                   │
└──────────────────────────────────────────────────────────┘
                           ↓
┌── Post-Route (Timing) ───────────────────────────────────┐
│ Full netlist + SDF (cell + routing delays).              │
│ Validates timing closure at the gate level.              │
│ Very slow (~100-1000x behavioral).                       │
│ Run ONLY for I/O interfaces and critical paths.          │
│ Not for full system — use STA (static timing) instead.   │
└──────────────────────────────────────────────────────────┘
```

---

## Choosing a Simulation Stack

```
┌─ Commercial / ASIC-grade? ──────────────────────────────► Questa / VCS / Xcelium
│
├─ Xilinx only, free?
│   ├─ Verilog/SV synthesis subset ───────────────────────► XSim (vendor default)
│   └─ Need UVM? ─────────────────────────────────────────► Questa (pay for UVM license)
│
├─ Intel only, free?
│   ├─ Small modules (<10k lines) ────────────────────────► Questa Intel Starter
│   └─ Larger designs ────────────────────────────────────► Questa (pay) or Verilator
│
├─ Open-source + Verilog ─────────────────────────────────► Verilator (speed) or Icarus (simplicity)
│
├─ Open-source + VHDL ────────────────────────────────────► GHDL (complete VHDL)
│
├─ Python testbenches ────────────────────────────────────► cocotb + any backend
│
└─ CI/CD regression ──────────────────────────────────────► Verilator + cocotb (fast, scriptable)
```

---

## Quick-Start Commands

| Simulator | Compile | Run | Waveform |
|---|---|---|---|
| **Vivado XSim** | `xvlog top.v tb.v` + `xelab tb -snapshot sim` | `xsim sim --tclbatch run.tcl` | `open_wave_database wave.wdb` |
| **Questa** | `vlog top.v tb.v` | `vsim -c tb -do "run -all"` | `vsim -gui tb` |
| **Verilator** | `verilator --cc --build top.v --exe tb.cpp` | `./obj_dir/Vtop` | `--trace` for VCD generation |
| **Icarus** | `iverilog -o sim.vvp top.v tb.v` | `vvp sim.vvp` | `$dumpfile("wave.vcd"); $dumpvars;` in testbench |
| **GHDL** | `ghdl -a top.vhd tb.vhd` + `ghdl -e tb` | `ghdl -r tb --vcd=wave.vcd` | GTKWave/wave.vcd |
| **cocotb** | (auto via Makefile) | `make SIM=icarus` | `--vcd` flag in Makefile |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Simulating without reset** | X-propagation, all signals 'X' | Assert reset for at least 2 clock cycles at simulation start |
| **Using blocking assignments for clocked logic** | Race conditions; simulation ≠ synthesis | Use `<=` (non-blocking) for `always @(posedge clk)` in Verilog |
| **Forgetting timescale** | All delays are 0 or nanosecond ambiguity | Add `` `timescale 1ns/1ps `` at top of testbench |
| **Vendor IP simulation libraries missing** | "Module not found" errors | Compile vendor sim libraries first: `compile_simlib` (Vivado), EDA Simulation Library Compiler (Quartus) |
| **Verilator: unsupported SV construct** | "UNSUPPORTED" errors | Stick to synthesizable SV subset; move UVM/testbench constructs to C++ side |
| **XSim: slow elaboration** | `xelab` takes minutes | Use `-generic_top` or split into smaller modules |
| **Mismatched VHDL/Verilog top in cocotb** | GPI errors, signals not found | Set `TOPLEVEL_LANG` correctly in Makefile |

---

## Further Reading

| Article | Topic |
|---|---|
| [testbench_patterns.md](testbench_patterns.md) | Self-checking testbenches, BFMs, scoreboards |
| [formal_verification.md](formal_verification.md) | Formal verification with SymbiYosys |
| [cocotb.md](cocotb.md) | cocotb Python testbenches deep dive |
| [uvm_overview.md](uvm_overview.md) | UVM (Universal Verification Methodology) |
| [sv_verification.md](sv_verification.md) | SystemVerilog for verification: assertions, coverage, randomization |
