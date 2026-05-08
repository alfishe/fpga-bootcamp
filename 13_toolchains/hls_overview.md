[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# High-Level Synthesis — C/C++ to Gates

HLS compiles C/C++/SystemC into HDL (Verilog/VHDL). It promises faster development and easier algorithm porting — but delivers only when you understand the abstraction gap between sequential software and parallel hardware.

---

## HLS Tools Landscape

| Tool | Vendor | Input | Output | Cost |
|---|---|---|---|---|
| **Vitis HLS** | Xilinx/AMD | C/C++/OpenCL | Verilog/VHDL + IP-XACT | Free (included in Vivado) |
| **Intel HLS Compiler** | Intel/Altera | C++ | Verilog + IP Catalog | Free (included in Quartus Pro) |
| **Catapult HLS** | Siemens EDA | C++/SystemC | Verilog/VHDL | Paid (enterprise) |
| **Bambu HLS** | Politecnico di Milano | C | Verilog | Open-source (GPL) |
| **LegUp HLS** | University of Toronto | C | Verilog | Open-source |
| **Stratus HLS** | Cadence | C++/SystemC | Verilog/VHDL | Paid (enterprise) |

---

## When HLS Wins vs When It Hurts

### HLS Wins

| Scenario | Why |
|---|---|
| **Algorithmic IP** (FFT, filter, crypto, ML inference) | C/C++ already exists; porting to hand-RTL takes months |
| **Control-heavy finite state machines** | Writing FSM by hand is error-prone; HLS infers FSM from code flow |
| **Rapid prototyping** | Test algorithms in C, push a button, get working RTL in hours |
| **Iterative tuning** | Try unroll=2, pipeline=II-1, array_partition=cyclic — each takes seconds to rebuild |

### HLS Hurts

| Scenario | Why |
|---|---|
| **Low-latency datapaths (single-cycle response)** | HLS inserts pipeline registers; latency is compiler-chosen, not architect-chosen |
| **Tight timing closure ( >300 MHz)** | HLS-generated logic may not meet timing; manual pipelining in RTL gives finer control |
| **Resource-minimal designs ( sub-1K LUTs)** | HLS overhead (AXI wrappers, control logic) may consume 500+ LUTs before your algorithm starts |
| **CDC, reset, clock gating** | HLS doesn't express hardware-level concerns; you control these in wrapper HDL |

---

## Key HLS Pragmas

| Pragma | What It Does | Example |
|---|---|---|
| **PIPELINE** | Overlap loop iterations | `#pragma HLS PIPELINE II=1` → one iteration per clock |
| **UNROLL** | Replicate loop body in hardware | `#pragma HLS UNROLL factor=4` → 4× parallelism, 4× area |
| **ARRAY_PARTITION** | Split array across BRAM banks | `#pragma HLS ARRAY_PARTITION variable=A cyclic factor=4` → 4 BRAMs, 4× bandwidth |
| **DATAFLOW** | Task-level pipelining between functions | Functions run concurrently, streaming data through FIFOs |
| **INLINE** | Remove function call overhead | Inlined function merges into caller's pipeline |
| **INTERFACE** | Specify AXI4/AXIS/AP_FIFO ports | `#pragma HLS INTERFACE axis port=data` → AXI4-Stream |

---

## HLS Flow (Vitis HLS)

```
1. Write C/C++ algorithm + testbench
2. Run C simulation (verifies algorithm correctness)
3. Add HLS pragmas (PIPELINE, UNROLL, ARRAY_PARTITION)
4. C Synthesis → Verilog/VHDL + timing/area reports
5. C/RTL Co-simulation (verifies RTL matches C)
6. Export RTL as Vivado IP → use in block design
7. Run Vivado synthesis + implementation (real timing, not estimated)
```

**Critical insight:** HLS timing/resource estimates in step 4 are optimistic. Only step 7 (real Vivado P&R) gives accurate QoR. The HLS "II=1" guarantee may break at 300 MHz post-route.

---

## Best Practices

1. **Start from a working C model** — HLS can't fix algorithm bugs; it faithfully implements them in hardware.
2. **HLS testbench in C, timing closure in Vivado** — trust C simulation for function; trust Vivado for timing.
3. **Use `INTERFACE` pragma early** — AXI4-Stream gives best throughput; default AXI4-Lite is for control registers.
4. **One function = one pipeline** — HLS pipelines within a function. Decompose large functions for better pipelining.
5. **Use arbitrary-precision types** — `ap_int<N>` saves resources vs 32-bit `int` for narrow datapaths.
6. **Avoid dynamic memory** — no `malloc`, `new`, or recursive functions in synthesizable HLS code.
7. **Bound all loops** — HLS needs to know the maximum trip count to schedule hardware.

---

## HLS Data Types

### Xilinx Vitis HLS — `ap_int` / `ap_fixed`

```cpp
#include <ap_int.h>
#include <ap_fixed.h>

ap_int<8>   narrow_val;       // 8-bit signed integer
ap_uint<12> sensor_raw;      // 12-bit unsigned integer
ap_fixed<16,4> fixed_val;   // 16-bit fixed-point: 4 integer bits, 12 fractional

// Custom types save resources:
// int (32-bit) → 1 DSP + carry logic
// ap_int<8>   → 1 LUT8 or half a DSP
// ap_fixed<16,4> → 1 DSP for multiply
```

### Intel HLS — `ac_int` / `ac_fixed`

```cpp
#include <ac_int.h>
#include <ac_fixed.h>

ac_int<8, true>   signed_narrow;   // 8-bit signed
ac_int<12, false> unsigned_sensor; // 12-bit unsigned
ac_fixed<16,4,AC_RND> fixed_round; // 16-bit with rounding
```

| Vendor | Integer | Fixed-Point | Arbitrary Width | Header |
|--------|---------|-------------|----------------|--------|
| Xilinx | `ap_int<N>` | `ap_fixed<W,I>` | Yes | `<ap_int.h>` |
| Intel | `ac_int<N,S>` | `ac_fixed<W,I,Q,O>` | Yes | `<ac_int.h>` |
| Bambu | Standard C types | — | Limited | — |

---

## Intel HLS Compiler Specifics

Intel HLS (part of Quartus Prime Pro) compiles C++ to Verilog targeting Intel FPGAs:

```bash
# Intel HLS build flow
i++ -march=Arria10 -o hello_world hello_world.cpp
# Generates: hello_world.prj/ directory with Verilog

# With simulation
i++ -march=Arria10 -ghdl -o hello_world hello_world.cpp testbench.cpp
```

| Feature | Intel HLS | Vitis HLS |
|---------|-----------|-----------|
| Input language | C++ (ANSI) | C/C++/OpenCL |
| Output | Verilog + Quartus IP | Verilog/VHDL + Vivado IP |
| Interface | Avalon-MM / Avalon-ST | AXI4 / AXI4-Stream |
| Simulation | ModelSim integration | XSim / Vitis cosim |
| Thread model | Component-based (explicit) | Function-based (implicit) |

**Intel HLS component model:**

```cpp
#include "HLS/hls.h"

component int adder(int a, int b) {
    return a + b;
}

// The 'component' keyword marks a function as a hardware accelerator
// Each component gets Avalon-MM slave + interrupt + status registers
```

---

## Bambu HLS — Open-Source

[Bambu](https://github.com/ferrandi/PandA-bambu) is the most mature open-source HLS tool:

```bash
# Install Bambu
sudo apt install bambu

# Compile C to Verilog
bambu -lm --device-name=xc7a35t algorithm.c

# With simulation
bambu -lm --simulate algorithm.c
```

**Bambu strengths:**
- Fully open-source (GPL)
- Targets multiple FPGA vendors via Yosys backend
- Supports various C constructs including `for`, `while`, `switch`
- Good for academic research and experimentation

**Bambu limitations:**
- No AXI interface inference (must add wrappers manually)
- Limited pragma support vs vendor tools
- Smaller community vs Vitis/Intel HLS

---

## Quick-Start: Vitis HLS FIR Filter

```cpp
#include <ap_int.h>
#define N_TAPS 16

typedef ap_int<16> coeff_t;
typedef ap_int<16> data_t;
typedef ap_int<32> acc_t;

void fir_filter(
    data_t data_in,
    coeff_t coeffs[N_TAPS],
    data_t *data_out
) {
    #pragma HLS INTERFACE axis port=data_in
    #pragma HLS INTERFACE axis port=data_out
    #pragma HLS INTERFACE s_axilite port=coeffs bundle=ctrl
    #pragma HLS PIPELINE II=1

    static data_t shift_reg[N_TAPS];
    acc_t acc = 0;

    // Shift register
    SHIFT: for (int i = N_TAPS - 1; i > 0; i--) {
        #pragma HLS UNROLL
        shift_reg[i] = shift_reg[i - 1];
    }
    shift_reg[0] = data_in;

    // MAC
    MAC: for (int i = 0; i < N_TAPS; i++) {
        #pragma HLS UNROLL
        acc += shift_reg[i] * coeffs[i];
    }

    *data_out = acc >> 15;  // Q15 scaling
}
```

**Synthesis command:**

```tcl
# Vitis HLS Tcl
open_project fir_prj
add_files fir.cpp
set_top fir_filter
open_solution sol1
set_part {xc7a35tcsg324-1}
create_clock -period 10
csim_design
csynth_design
cosim_design
export_design -format ip_catalog
```

---

## Cross-References

| Topic | Article |
|-------|---------|
| HLS concepts and pragmas (detailed) | [HLS Overview](../04_hdl_and_synthesis/hls/hls_overview.md) |
| Advanced HLS patterns and optimization | [Advanced HLS Patterns](../16_advanced_topics/advanced_hls_patterns.md) |
| Vitis/Vivado toolchain | [Vivado](vivado.md) |
| Quartus Prime toolchain | [Quartus Prime](quartus_prime.md) |
| Edge AI deployment (HLS for ML) | [Edge AI](../16_advanced_topics/edge_ai_deployment.md) |
