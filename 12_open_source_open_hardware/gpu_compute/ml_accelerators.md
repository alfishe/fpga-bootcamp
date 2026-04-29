[← 12 Open Source Open Hardware Home](../README.md) · [← Gpu Compute Home](README.md) · [← Project Home](../../../README.md)

# ML Accelerators on FPGA

Open-source deep learning inference accelerators targeting FPGA fabric — from NVIDIA's NVDLA to framework-to-FPGA compilation flows.

---

## Major Projects

| Project | Origin | Type | Framework | FPGA Targets | Key Trait |
|---|---|---|---|---|---|
| **NVDLA** | NVIDIA | Configurable NPU (convolution + activation + pooling) | Caffe, ONNX | Xilinx, Intel | Open-source hardware spec, full RTL, large |
| **FINN** | Xilinx Research | Quantized NN compiler → dataflow FPGA | Brevitas → FINN | Zynq, Alveo | Best for Xilinx, extreme low latency (μs) |
| **hls4ml** | CERN / FastML | ML → HLS (Vivado HLS / Catapult) | TensorFlow, PyTorch, Keras | Xilinx, Intel | Low latency ML for physics triggers, \u003c100 ns inference |
| **VTA** | Apache TVM | Generic tensor accelerator | TVM (own compiler) | Pynq (Zynq) | End-to-end: TVM compiler → RTL, research platform |
| **DNNWeaver** | Georgia Tech | DNN accelerator generator | Caffe | Xilinx | Academic, parameterized systolic array generation |

## Framework Comparison

| Property | NVDLA | FINN | hls4ml | VTA |
|---|---|---|---|---|
| **Input format** | ONNX / Caffe model | PyTorch → quantized | TensorFlow / PyTorch | TVM Relay IR |
| **Quantization** | INT8, INT16 | Binary / INT1–4 | Arbitrary fixed-point | INT8 |
| **FPGA families** | Xilinx, Intel (open) | Xilinx (Zynq, Alveo) | Xilinx, Intel (HLS backend) | Xilinx (Pynq) |
| **Latency target** | ~1 ms | \u003c1 μs | \u003c100 ns (trigger) | ~10 ms |
| **Complexity** | High (full NPU) | Medium | Low (Python API) | Medium |

## When to Use Each

| Use Case | Recommended | Why |
|---|---|---|
| I want a full NPU architecture to study | **NVDLA** | Complete open-source spec, headless/small/large config |
| I need ultra-low latency (\u003c1 μs) on Xilinx | **FINN** | Dataflow streaming architecture, no DRAM bottleneck |
| I'm a physicist wanting ML in trigger path | **hls4ml** | Designed for \u003c100 ns inference, HLS-friendly output |
| I want compiler co-design flexibility | **VTA** | TVM ecosystem, can modify both hardware and compiler |

---

## Original Stub Description

**NVDLA** (NVIDIA open-source deep learning accelerator), **hls4ml** (ML-to-FPGA for low latency), **FINN** (Xilinx, quantized neural networks), open-source NPU/TPU-in-FPGA projects

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
