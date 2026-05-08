[← Verification Home](README.md) · [← Project Home](../README.md)

# Simulation Methodology — Test Planning, Coverage, Regression & CI

Running a simulation and seeing waves is not verification. Verification is a **systematic process** that proves your design meets its requirements with measurable coverage. This article covers how to plan verification, measure completeness, build regression suites, and integrate simulation into CI/CD pipelines.

For testbench coding patterns, see [Testbench Patterns](testbench_patterns.md). For specific simulators, see [Simulation Overview](simulation_overview.md), [Verilator](verilator.md), or [GHDL](ghdl.md). For formal verification as a complement to simulation, see [Formal Verification](formal_verification.md).

---

## Verification Planning

### Verification Plan Template

| Section | Content |
|---------|---------|
| **Features to verify** | List of all design features from the specification |
| **Test scenarios** | Specific test cases for each feature |
| **Coverage goals** | What coverage metrics and targets |
| **Test environment** | Simulators, BFMs, scoreboards needed |
| **Pass/fail criteria** | What constitutes "verified" for each feature |
| **Schedule** | Milestones: first test, 50% coverage, coverage closure |

### Feature → Test Mapping

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────┐
│  Requirement    │─────►│  Test Case   │─────►│  Coverage    │
│  "FIFO must     │      │  test_full:  │      │  cnt_full    │
│   signal full   │      │  fill until  │      │  = 1 when    │
│   when full"   │      │  full flag   │      │  depth=max   │
└─────────────────┘      └──────────────┘      └─────────────┘
```

| Feature | Test(s) | Coverage Point |
|---------|---------|---------------|
| FIFO full detection | `test_fill_until_full` | `full` toggles 0→1 and 1→0 |
| FIFO empty detection | `test_drain_until_empty` | `empty` toggles 0→1 and 1→0 |
| FIFO overflow protection | `test_write_when_full` | `wr_en && full` → no data corruption |
| FIFO underflow protection | `test_read_when_empty` | `rd_en && empty` → no invalid data |
| Simultaneous read/write | `test_simultaneous_rw` | `wr_en && rd_en` at all fill levels |
| Reset clears FIFO | `test_reset_clears` | After reset: `empty=1`, `full=0`, `count=0` |

---

## Coverage Metrics

### Code Coverage

| Type | What It Measures | Target | Tool Support |
|------|-----------------|--------|-------------|
| **Statement (line)** | Every executable line of code hit | ≥ 95% | All simulators |
| **Branch** | Every `if/else` and `case` branch taken both ways | ≥ 90% | Most simulators |
| **Condition** | Every Boolean sub-expression evaluated T & F | ≥ 85% | Questa, VCS, XCelium |
| **Toggle** | Every net/variable toggled 0→1 and 1→0 | ≥ 90% | Most simulators |
| **FSM** | Every state visited, every transition exercised | 100% | Most simulators |
| **Expression** | All logical expression outcomes covered | ≥ 80% | Limited tool support |

### Functional Coverage (SystemVerilog)

```systemverilog
// Covergroup for FIFO fill levels
covergroup fifo_fill_cg @(posedge clk);
    fill_level: coverpoint fill_count {
        bins empty   = {0};
        bins low     = {[1:DEPTH/4]};
        bins mid     = {[DEPTH/4+1:3*DEPTH/4]};
        bins high    = {[3*DEPTH/4+1:DEPTH-1]};
        bins full    = {DEPTH};
    }
    simultaneous_rw: coverpoint {wr_en, rd_en} {
        bins rw_both = {2'b11};
        bins wr_only = {2'b10};
        bins rd_only = {2'b01};
        bins neither = {2'b00};
    }
    fill_x_rw: cross fill_level, simultaneous_rw;
endgroup
```

### Coverage Closure Flow

```
Run regression → Collect coverage → Identify holes → Write targeted tests → Repeat
     │                                         │
     │          ┌──────────────┐               │
     └─────────►│ Merge        │───────────────┘
                │ coverage DB  │
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │ Coverage     │
                │ report       │
                │              │
                │ Statement: 97%│
                │ Branch:   91% │
                │ FSM:     100% │
                │ Toggle:   88%│ ← HOLE: signals that never toggle
                └──────────────┘
```

### Coverage Merge Commands

```bash
# Questa/ModelSim
vcover merge merged.ucov test1.ucov test2.ucov test3.ucov
vcover report -details merged.ucov > coverage_report.txt

# Vivado XSim
xvcoverage report -dir coverage_data

# Verilator (via GCOV)
lcov -a test1.info -a test2.info -o merged.info
genhtml merged.info -o coverage_html

# GHDL (via GCC coverage)
gcov -a -b *.gcno
lcov --capture --directory . --output-file coverage.info
```

---

## Regression Testing

### Regression Suite Structure

```
tests/
├── smoke/            # Quick sanity tests (< 1 min each)
│   ├── test_reset.py
│   ├── test_register_rw.py
│   └── test_clocks.py
├── functional/       # Feature tests (1–10 min each)
│   ├── test_spi_xfer.py
│   ├── test_uart_loopback.py
│   └── test_fifo_fill_drain.py
├── integration/      # Multi-module tests (10–60 min each)
│   ├── test_full_soc_boot.py
│   └── test_dma_transfer.py
├── long/             # Stress / soak tests (hours)
│   ├── test_24hr_stability.py
│   └── test_random_traffic.py
└── regression.py     # Test runner script
```

### Regression with cocotb

```python
# regression.py — Run all cocotb tests with coverage
import cocotb
import logging
import subprocess
import sys

test_dirs = [
    ("smoke",           "quick"),
    ("functional",      "standard"),
    ("integration",     "thorough"),
    ("long",            "overnight"),
]

level = sys.argv[1] if len(sys.argv) > 1 else "standard"
levels = {"quick": 0, "standard": 1, "thorough": 2, "overnight": 3}
max_level = levels.get(level, 1)

passed = 0
failed = 0

for dirname, req_level in test_dirs:
    if levels[req_level] > max_level:
        continue
    result = subprocess.run(
        ["make", "-C", dirname],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        passed += 1
        print(f"  PASS: {dirname}")
    else:
        failed += 1
        print(f"  FAIL: {dirname}")
        print(result.stdout[-500:])  # last 500 chars

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(1 if failed > 0 else 0)
```

### Regression with Verilator + GTest

```makefile
# Makefile for Verilator regression
VERILATOR = verilator
VK_GLOBAL = --cc --build --trace --coverage -Wall

test: obj_dir/Vtop
	./obj_dir/Vtop

obj_dir/Vtop: rtl/top.v rtl/*.v testbench/top_test.cpp
	$(VERILATOR) $(VK_GLOBAL) -exe testbench/top_test.cpp rtl/top.v rtl/*.v

coverage: test
	lcov --capture --directory obj_dir --output-file coverage.info
	genhtml coverage.info -o coverage_html

regression:
	@echo "Running full regression..."
	@$(MAKE) clean
	@$(MAKE) test
	@$(MAKE) coverage
	@echo "Regression complete."
```

---

## Test Generation Strategies

### 1. Directed Tests

Manually written for specific requirements. Best for:
- Corner cases known from the specification
- Boundary conditions (FIFO full, counter at max)
- Error scenarios (parity error, clock loss)

### 2. Constrained-Random Tests

```systemverilog
class axi_transaction;
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand bit [3:0]  strb;
    rand bit        is_write;

    constraint addr_aligned {
        addr % 4 == 0;              // word-aligned
        addr inside {[32'h0000_0000:32'h0000_FFFF]};  // valid range
    }
    constraint strb_valid {
        // strb must be contiguous for writes
        if (is_write) {
            (strb & (strb + 1)) == 0 || strb == 4'b1111;
        }
    }
endclass
```

### 3. PSL / SVA Cover Properties

Use cover properties to verify that interesting scenarios actually occurred during simulation:

```systemverilog
// Did we ever see back-to-back transfers on AXI?
cover property @(posedge clk)
    m_valid && m_ready ##1 m_valid && m_ready;

// Did we ever see a full-to-empty transition?
cover property @(posedge clk)
    fifo_full ##1 fifo_empty;

// Did we ever see a burst of length 16?
cover property @(posedge clk)
    arlen == 4'hF;  // AXI ARLEN=15 → 16-beat burst
```

### 4. Formal Coverage

Formal tools provide their own coverage metrics:

| Metric | Meaning | Target |
|--------|---------|--------|
| **Proven** | Property holds for all reachable states | 100% of assertions |
| **Cex** | Counter-example found (bug) | 0% |
| **Undetermined** | Engine couldn't prove within bounds | Minimize |
| **Covered** | Cover property witnessed | 100% of covers |

---

## Simulation Performance Optimization

### Abstract Models for Faster Simulation

| Technique | Speedup | Accuracy Loss | When to Use |
|-----------|---------|---------------|-------------|
| **Transaction-level modeling (TLM)** | 10–100× | Behavioral only | Software development, early architecture |
| **C/C++ models via DPI** | 5–20× | Algorithmic only | DSP algorithms, packet processing |
| **Zero-delay simulation** | 2–5× | No timing | Functional verification only |
| **Verilator (cycle-based)** | 5–40× | No X/Z, no timing | Large designs, long tests |
| **Stimulus replay** | 2–10× | Same as original | Regression of known-good stimulus |

### DPI-C Acceleration Example

```c
// dsp_model.cpp — C++ model of a filter, called via DPI
#include "svdpi.h"
#include <cmath>

extern "C" void fir_filter(
    const int *coeffs, int n_coeffs,
    int input_sample, int *output_sample
) {
    static int shift_reg[256] = {0};
    long long acc = 0;
    
    // Shift in new sample
    for (int i = n_coeffs - 1; i > 0; i--)
        shift_reg[i] = shift_reg[i-1];
    shift_reg[0] = input_sample;
    
    // MAC
    for (int i = 0; i < n_coeffs; i++)
        acc += (long long)coeffs[i] * shift_reg[i];
    
    *output_sample = (int)(acc >> 15);  // Q15 fixed point
}
```

```verilog
// SystemVerilog DPI import
import "DPI-C" function void fir_filter(
    input  int coeffs[],
    input  int n_coeffs,
    input  int input_sample,
    output int output_sample
);

// Use in testbench for reference model comparison
always @(posedge clk) begin
    if (valid) begin
        fir_filter(coeffs, N_COEFFS, dut_input, ref_output);
        assert(ref_output == dut_output)
            else $error("Mismatch: ref=%0d dut=%0d", ref_output, dut_output);
    end
end
```

---

## CI/CD Integration for Simulation

### GitHub Actions — Verilator Regression

```yaml
name: Simulation Regression
on: [push, pull_request]

jobs:
  verilator-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Verilator
        run: sudo apt-get install -y verilator
      - name: Lint
        run: verilator --lint-only -Wall rtl/*.v

  verilator-sim:
    runs-on: ubuntu-latest
    needs: verilator-lint
    steps:
      - uses: actions/checkout@v4
      - name: Install Verilator
        run: sudo apt-get install -y verilator
      - name: Build and Test
        run: |
          make -C sim VERILATOR=verilator
      - name: Check Coverage
        run: |
          python3 scripts/check_coverage.py coverage.info --minimum 90

  cocotb-test:
    runs-on: ubuntu-latest
    needs: verilator-lint
    steps:
      - uses: actions/checkout@v4
      - name: Install cocotb
        run: pip install cocotb cocotb-test
      - name: Run cocotb tests
        run: |
          cd tests/cocotb
          make SIM=icarus
```

### Jenkins — Vivado + Questa Pipeline

```groovy
pipeline {
    agent { label 'fpga-build' }
    stages {
        stage('Lint') {
            steps {
                sh 'verilator --lint-only -Wall rtl/*.v'
            }
        }
        stage('Simulate') {
            steps {
                sh '''
                    vsim -c -do "run -all; quit" \
                        -coverage -covfile coverage.ucdb \
                        work.top_tb
                '''
            }
        }
        stage('Coverage Report') {
            steps {
                sh 'vcover report -details coverage.ucdb > coverage.txt'
                recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'coverage.xml']])
            }
        }
        stage('Synthesis Check') {
            steps {
                sh 'vivado -mode batch -source synth_check.tcl'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'coverage.txt, coverage.ucdb'
        }
    }
}
```

---

## Simulation Milestones

| Milestone | Typical Timeline | Coverage Target | Tests |
|-----------|-----------------|----------------|-------|
| **T0 — First sim** | Week 1 | N/A | Smoke test (reset, clock, basic IO) |
| **T1 — Block-level** | Week 2–3 | Statement ≥ 80% | All module-level directed tests |
| **T2 — Integration** | Week 4–6 | Statement ≥ 90%, Branch ≥ 80% | Multi-module, constrained-random |
| **T3 — Coverage closure** | Week 7–9 | Statement ≥ 95%, Branch ≥ 90% | Targeted tests for coverage holes |
| **T4 — Regression stable** | Week 10–12 | All targets met | Full regression, 48-hour soak test |
| **T5 — Tapeout release** | Week 12+ | All targets met + formal | Sign-off simulation with final RTL |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Testbench coding patterns | [Testbench Patterns](testbench_patterns.md) |
| Simulator comparison | [Simulation Overview](simulation_overview.md) |
| Verilator deep dive | [Verilator](verilator.md) |
| GHDL deep dive | [GHDL](ghdl.md) |
| Formal verification | [Formal Verification](formal_verification.md) |
| cocotb | [Cocotb](cocotb.md) |
| CI/CD for FPGA | [CI/CD for Hardware](../13_toolchains/cicd_hardware.md) |
