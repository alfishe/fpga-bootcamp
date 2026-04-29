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

## References

| Source |
|---|
| Vitis HLS User Guide (UG1399) |
| Intel HLS Compiler User Guide |
| Bambu HLS Documentation |
