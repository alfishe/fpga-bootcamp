[← 02 Architecture Home](../README.md) · [← Hybrid Home](README.md) · [← Project Home](../../../README.md)

# AI Engine Arrays — On-Die Compute Accelerators

Beyond programmable logic, modern FPGA architectures integrate hardened AI compute arrays — specialized VLIW/SIMD processor grids that deliver GPU-class throughput at FPGA-class latency and power. The flagship is Xilinx Versal AI Engine, but Intel (AI Tensor Blocks) and Achronix (MLP) follow similar philosophies.

---

## Why AI Engines? The FPGA Compute Gap

| Compute Method | Peak Throughput | Latency | Power | Flexibility |
|---|---|---|---|---|
| **Soft DSP (FPGA fabric)** | 1–10 TOPS | ~5 ns | Medium | Highest — any operation |
| **Hard AI Engine array** | 20–200 TOPS | ~1 ns (tile-to-tile) | Low (hardened) | High — programmable SIMD |
| **External GPU (PCIe)** | 100–1000 TOPS | ~10 µs (PCIe round-trip) | High (200W+) | Fixed — CUDA/OpenCL only |
| **ASIC (TPU, Inferentia)** | 100–500 TOPS | ~1 ns | Lowest | None — fixed function |

AI Engines fill the gap: higher throughput than soft DSP, lower latency than PCIe-attached GPU, more programmable than ASIC.

---

## Xilinx Versal AI Engine (AIE)

### Tile Architecture

```
┌──────────── AI Engine Tile ────────────┐
│  ┌──────────────────────────────────┐  │
│  │  VLIW SIMD Core (7-way)          │  │
│  │  ├─ 2× Load Units               │  │
│  │  ├─ 1× Store Unit               │  │
│  │  ├─ 2× Multiply-Accumulate      │  │
│  │  └─ 1× ALU (scalar/vector)      │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │  Data Memory: 32 KB (4 banks)    │  │
│  │  Program Memory: 16 KB           │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │  AXI4-Stream Switch              │  │
│  │  ├─ 2× Stream inputs            │  │
│  │  ├─ 2× Stream outputs           │  │
│  │  ├─ Cascade input/output        │  │
│  │  └─ DMA (to/from NoC)           │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

### Key Parameters

| Parameter | AIE (Gen 1, 7nm) | AIE-ML (Gen 2, 7nm) |
|---|---|---|
| **Clock** | 1.0–1.25 GHz | 1.0–1.25 GHz |
| **Data types** | INT8, INT16, CINT16, FP32 | INT4, INT8, INT16, BFLOAT16, CINT16, FP32 |
| **INT8 MACs/tile/cycle** | 16 (2×8) | 64 (8×8) |
| **INT8 TOPS/tile** | 0.128 | 0.512 |
| **FP32 MACs/tile/cycle** | 8 (2×4) | 8 (2×4) |
| **Tiles per device** | 150–400 | 304–472 |
| **Peak INT8 TOPS (max device)** | ~51 TOPS | ~240 TOPS |
| **Peak BFLOAT16 TFLOPS** | Not supported | ~120 TFLOPS |

---

## AI Engine Array Topology

```
Column 0      Column 1      Column 2      ...    Column 49
┌────────┐    ┌────────┐    ┌────────┐           ┌────────┐
│ Tile   │←──→│ Tile   │←──→│ Tile   │←── ... ──→│ Tile   │  Row 0
│ (0,0)  │ AXIS│ (0,1)  │ AXIS│ (0,2)  │           │ (0,49) │
└───┬────┘    └───┬────┘    └───┬────┘           └───┬────┘
    │ Cascade     │ Cascade     │ Cascade             │ Cascade
┌───▼────┐    ┌───▼────┐    ┌───▼────┐           ┌───▼────┐
│ Tile   │←──→│ Tile   │←──→│ Tile   │←── ... ──→│ Tile   │  Row 1
│ (1,0)  │ AXIS│ (1,1)  │ AXIS│ (1,2)  │           │ (1,49) │
└───┬────┘    └───┬────┘    └───┬────┘           └───┬────┘
    │ Cascade     │ Cascade     │ Cascade             │ Cascade
   ...          ...          ...                    ...
┌───▼────┐    ┌───▼────┐    ┌───▼────┐           ┌───▼────┐
│ Tile   │←──→│ Tile   │←──→│ Tile   │←── ... ──→│ Tile   │  Row 7
│ (7,0)  │ AXIS│ (7,1)  │ AXIS│ (7,2)  │           │ (7,49) │
└────────┘    └────────┘    └────────┘           └────────┘
     │              │              │                    │
     └──────────────┴──────────────┴────────────────────┘
                         │
              AXI4-Stream Network-on-Chip (NoC)
                         │
              ┌──────────▼──────────┐
              │  FPGA Fabric         │
              │  (Adaptable Engines) │
              │  + DDR/HBM/PCIe      │
              └─────────────────────┘
```

Tiles communicate via three paths:
1. **AXI4-Stream (horizontal)** — low-latency neighbor-to-neighbor, ideal for systolic arrays
2. **Cascade (vertical)** — accumulator chain for long dot-product pipelines (e.g., 4096-tap FIR)
3. **NoC DMA** — bulk data movement to/from FPGA fabric, DDR, or HBM

---

## Intel AI Tensor Block (Agilex)

Intel's approach is different — AI Tensor Blocks are hardened DSP variants, not a separate processor array:

| Property | Intel AI Tensor Block | Xilinx AI Engine |
|---|---|---|
| **Architecture** | Hardened systolic array inside DSP block | Independent VLIW processor array |
| **Data types** | INT8, INT16, FP16, FP32, BFLOAT16 | INT4/8/16, BFLOAT16, CINT16, FP32 |
| **Peak INT8 TOPS** | ~10–60 TOPS (device-dependent) | ~51–240 TOPS |
| **Programming model** | Inferred from HDL (DSP inference) | Explicit C/C++ kernel + graph compiler |
| **Integration** | Inside FPGA fabric DSP columns | Separate die region, NoC-connected |

Intel's tensor blocks are simpler to use (inferred from HDL DSP patterns) but less flexible for arbitrary compute graphs.

---

## Achronix Machine Learning Processor (MLP)

Speedster7t devices include hardened MLP blocks alongside traditional DSP:

| Property | Achronix MLP | Xilinx AI Engine |
|---|---|---|
| **Architecture** | Hardened matrix multiply (4×4 or 8×8) | Programmable VLIW tiles |
| **Data types** | INT8, INT16, FP16, BFLOAT16 | INT4/8/16, BFLOAT16, CINT16, FP32 |
| **Peak INT8 TOPS** | ~40–60 TOPS (7t1500) | ~51–240 TOPS |
| **Latency** | 1 cycle (fixed-pipeline) | 1–7 cycles (VLIW-programmable) |

MLP blocks are closer to Intel's approach — fixed-function but very low latency.

---

## Programming Model (AI Engine)

```
┌─────────────────────────────────────┐
│  AI Engine Kernel (C/C++)            │
│  - VLIW auto-vectorized by compiler  │
│  - #pragma for unroll, pipelining    │
│  - Intrinsics for SIMD control       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Adaptive Data Flow Graph (C++)      │
│  - Nodes = kernels                   │
│  - Edges = AXI4-Stream connections   │
│  - Compiler maps to physical tiles   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Vitis AI Engine Compiler (v++ -c)   │
│  - Maps graph to tile grid           │
│  - Routes streams through NoC        │
│  - Generates tile binaries           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  System Link (Vitis v++ -l)          │
│  - Connects AIE graph to PL kernels  │
│  - Configures NoC, DDR, PS bridges   │
│  - Produces final .pdi (PDI image)   │
└─────────────────────────────────────┘
```

---

## Use Cases

| Application | Why AI Engine | Example Throughput |
|---|---|---|
| **5G Massive MIMO beamforming** | 64×64 matrix multiplies per OFDM symbol at 100 µs deadline | 400 tiles → 64 beams real-time |
| **Radar range-Doppler processing** | 2D FFT pipeline: 4096-pt FFT cascaded through 8 tiles in column | 1 µs per 4096-pt FFT |
| **Image signal processing (ISP)** | Per-pixel operations (demosaic, denoise, HDR merge) streamed row-by-row | 8K60 video real-time |
| **Financial simulation (Monte Carlo)** | Thousands of independent random walks, each in a tile | 400× parallelism vs single CPU core |
| **Genomics (Smith-Waterman)** | Systolic array for sequence alignment across tile grid | 1000× faster than CPU Smith-Waterman |

---

## Best Practices

1. **Design for stream, not memory** — AIE tiles have only 32 KB local data memory. Keep data flowing through AXI4-Stream, not buffered locally.
2. **Cascade for accumulation** — use vertical cascade for long dot products (FIR, GEMM output reduction) to avoid stream bandwidth bottlenecks.
3. **Group tiles into "graphs" logically** — the compiler maps better when you express parallelism as a graph of connected kernels.
4. **NoC bandwidth is limited** — each tile has 2×32-bit stream ports. Aggregate NoC bandwidth must be budgeted at graph level.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Tile memory overflow** | Kernel stalls, throughput drops | Profile with `aie_trace`; split across more tiles |
| **Stream deadlock** | Graph hangs at runtime | Ensure all stream paths have consumers; use `aiesimulator` for cycle-accurate debug |
| **FP32 throughput assumption** | Expecting 51 TOPS but getting 12.8 TFLOPS | INT8 TOPS ≠ FP32 TFLOPS — 1 INT8 MAC ≠ 1 FP32 MAC; check data types |
| **PL-to-AIE bandwidth bottleneck** | PL kernels starved for AIE output | Use wider NoC ports (128-bit); double-buffer PL-side |

---

## References

| Source | Path |
|---|---|
| Versal AI Engine Architecture Manual (AM009) | Xilinx / AMD |
| Vitis AI Engine User Guide (UG1076) | Xilinx / AMD |
| Versal ACAP AI Engine Programming (UG1079) | Xilinx / AMD |
| Agilex AI Tensor Block User Guide | Intel FPGA Documentation |
| Speedster7t MLP Architecture | Achronix |
