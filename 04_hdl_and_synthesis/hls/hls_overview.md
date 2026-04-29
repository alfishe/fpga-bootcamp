[← HLS Home](README.md) · [← HDL & Synthesis Home](../README.md) · [← Project Home](../../../README.md)

# HLS Overview

High-Level Synthesis transforms algorithmic C/C++/OpenCL code into RTL — scheduling operations into clock cycles, allocating hardware resources, and generating pipelined datapaths. For FPGA developers, HLS bridges the gap between software prototyping and hardware implementation.

---

## Core HLS Concepts

| Concept | What It Does | Impact |
|---|---|---|
| **Scheduling** | Assigns operations to clock cycles | Determines latency and throughput |
| **Pipelining** | Overlaps execution of loop iterations | II=1 means 1 result per cycle after pipeline fill |
| **Loop Unrolling** | Replicates loop body N times | N× throughput, N× area |
| **Array Partitioning** | Splits array across multiple BRAM banks | Eliminates memory bandwidth bottleneck |
| **Interface Synthesis** | Generates AXI-Stream/AXI4/AXI-Lite ports | Defines how C arguments map to hardware IO |

## Major HLS Tools

| Tool | Vendor | Input | FPGA Targets | Notes |
|---|---|---|---|---|
| **Vitis HLS** | Xilinx | C/C++/OpenCL | Xilinx 7-series, Ultrascale+, Versal | Most mature, wide adoption |
| **Intel HLS** | Intel | C++ | Intel Agilex, Stratix 10, Arria 10 | Formerly Intel FPGA SDK for OpenCL |
| **Catapult HLS** | Siemens | C++/SystemC | Xilinx, Intel (via RTL export) | ASIC-grade, expensive |
| **Bambu** | PoliMi (open-source) | C | Xilinx 7-series | Academic, PandA framework |

## When HLS Makes Sense

| ✅ Good for HLS | ❌ Bad for HLS |
|---|---|
| DSP algorithms (FIR, FFT, matrix multiply) | Precise cycle-level control logic |
| Computer vision / ML inference pipelines | Hand-crafted state machines |
| High-throughput packet processing | Clock domain crossing logic |
| Prototyping before RTL implementation | Resource-constrained designs (iCE40) |

---

## Original Stub Description

High-Level Synthesis fundamentals: scheduling, pipelining, loop unrolling, array partitioning, and interface synthesis. Covers the conceptual bridge between algorithmic C/C++/OpenCL and generated RTL.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## See Also

- [Toolchains: HLS Overview](../../13_toolchains/hls_overview.md) — Vendor-specific HLS tools (Vitis HLS, Intel HLS Compiler, Catapult, Bambu)

## Referenced By

- [README.md](README.md)
