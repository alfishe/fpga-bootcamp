[← Advanced Topics Home](README.md) · [← Project Home](../README.md)

# FPGA + Edge AI Deployment — Practical Inference on Programmable Logic

Running AI inference at the edge means processing sensor data (camera, microphone, LIDAR, IMU) locally, with latency measured in microseconds and power budgets in watts — not kilowatts. FPGAs sit between microcontrollers (too slow) and GPUs (too power-hungry) for many edge AI workloads. This article covers the practical frameworks, deployment flows, and performance trade-offs for running neural networks on FPGAs.

For advanced HLS patterns used in AI acceleration, see [Advanced HLS Patterns](advanced_hls_patterns.md). For ML accelerator open-source cores, see [ML Accelerators](../12_open_source_open_hardware/gpu_compute/ml_accelerators.md). For hardware acceleration overview, see [Hardware Acceleration](hardware_acceleration.md).

---

## Where FPGA Fits in the Edge AI Stack

| Platform | Latency | Throughput | Power | Typical Use Case |
|----------|---------|-----------|-------|-----------------|
| **MCU (Cortex-M)** | 10–100 ms | 1–10 inf/s | 10–100 mW | Keyword spotting, simple anomaly |
| **FPGA** | 0.01–1 ms | 10–1000 inf/s | 1–10 W | Real-time vision, motor control, radio processing |
| **Edge GPU (T4, Jetson)** | 1–10 ms | 100–1000 inf/s | 10–75 W | Multi-camera, multi-model |
| **Cloud GPU (A100, H100)** | 10–100 ms (incl. network) | 10K+ inf/s | 300–700 W | Training, large-batch inference |
| **Edge TPU (Coral)** | 1–5 ms | 50–400 inf/s | 2 W | Quantized vision models |
| **NPU (mobile SoC)** | 0.5–5 ms | 30–500 inf/s | 1–5 W | Phone-embedded AI |

**FPGA advantages:** Custom datatypes (INT4, bfloat16, fixed-point), deterministic latency, reconfigurable for model updates, direct sensor interface (MIPI, LVDS, ADC).

---

## Deployment Frameworks

### 1. AMD Vitis AI

The official flow for deploying on Xilinx/AMD FPGAs (Zynq, Alveo, Versal):

```
┌────────────┐    ┌─────────────┐    ┌────────────┐    ┌───────────────┐
│  Training  │───►│  Quantize   │───►│  Compile   │───►│  Runtime      │
│  (PyTorch/ │    │  (Vitis     │    │  (Vitis AI │    │  (VART /      │
│   TF/Keras)│    │   Quantizer)│    │   Compiler)│    │   DPU driver) │
└────────────┘    └─────────────┘    └────────────┘    └───────────────┘
     .pt/.h5         .xmodel           .xmodel            FPGA
```

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| **Vitis AI Model Zoo** | Pre-quantized models | — | .xmodel files |
| **Vitis AI Quantizer** | INT8/FP16 quantization | Float model + calibration data | Quantized .xmodel |
| **Vitis AI Compiler** | Map to DPU instruction set | Quantized .xmodel | DPU executable |
| **DPU IP** | Hardware neural accelerator | Compiled model | Inference results |
| **VART** | Runtime API (C++/Python) | Compiled model | Inference calls |

**Supported boards:** ZCU102/104, KV260, VCK190, Alveo cards.

```python
# Vitis AI runtime example (Python)
from vitis_ai_runtime import DpuRunner

runner = DpuRunner("dpu_model.xmodel")
# Prepare input
input_data = preprocess(frame)  # NHWC, INT8
# Run inference
outputs = runner.execute(input_data)
# Post-process
result = postprocess(outputs[0])
```

### 2. Intel OpenVINO + FPGA

Intel's OpenVINO framework had an FPGA backend (now deprecated for discrete FPGAs, but still relevant for Intel SoC FPGAs):

```python
# OpenVINO with Intel FPGA backend
from openvino.runtime import Core

core = Core()
# List available devices
print(core.available_devices)  # ['CPU', 'GPU', 'HETERO:FPGA,CPU']

# Load model for FPGA
model = core.read_model("model.xml")
compiled = core.compile_model(model, "HETERO:FPGA,CPU")
infer = compiled.create_infer_request()
```

> **Note:** Intel discontinued the discrete FPGA plugin in OpenVINO 2022.1. For new Intel FPGA AI projects, use the Intel AI Suite or direct HLS.

### 3. hls4ml — ML to HLS for FPGAs

[hls4ml](https://github.com/fastml/hls4ml) converts ML models directly to Vivado HLS C++ code:

```python
import hls4ml
import tensorflow as tf

# Train a simple model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(16,)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(5, activation='softmax')
])

# Convert to HLS
hls_config = hls4ml.utils.config_from_keras_model(model, granularity='model')
hls_config['Model']['Precision'] = 'ap_fixed<16,6>'
hls_config['Model']['ReuseFactor'] = 1

hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    hls_config=hls_config,
    output_dir='hls4ml_prj',
    part='xc7a35tcsg324-1'   # Artix-7 35T
)

# Compile HLS
hls_model.compile()

# Build bitstream
hls_model.build(csim=False, export=True, bitfile=True)
```

**hls4ml resource estimates for common models:**

| Model | FPGA | LUTs | FFs | BRAM | DSP | Latency | Clock |
|-------|------|------|-----|------|-----|---------|-------|
| 3-layer FC (16→64→32→5) | Artix-7 35T | ~8K | ~5K | 4 | 8 | 25 cycles | 100 MHz |
| CNN (small, 32×32 input) | Zynq 7020 | ~25K | ~15K | 20 | 32 | 500 cycles | 100 MHz |
| Jet tagging (4-layer) | Kintex-7 325T | ~30K | ~20K | 30 | 64 | 80 cycles | 200 MHz |

### 4. FINN — Quantized NN on Xilinx

[FINN](https://github.com/Xilinx/finn) by AMD/Xilinx Research focuses on **extremely quantized** networks (1–4 bit weights/activations):

```python
from finn.core.modelwrapper import ModelWrapper
from finn.transformation import general as gtrans

# Load ONNX model
model = ModelWrapper("breast_cancer.onnx")

# Apply quantization (2-bit weights, 2-bit activations)
from finn.transformation.fpgadataflow.quantize import QuantizeTransformation
model = model.transform(QuantizeTransformation(2, 2))

# Generate accelerator for PYNQ board
from finn.transformation.fpgadataflow.create_dataflow_partition import (
    CreateDataflowPartition,
)
model = model.transform(CreateDataflowPartition())
```

**FINN targets:** PYNQ-Z1, ZCU104, Alveo, custom Zynq boards. Best for BNN (Binary Neural Networks) and Ternary Weight Networks.

---

## Quantization for FPGA

### Datatype Selection

| Datatype | Bits | Dynamic Range | DSP/LUT Cost | Accuracy vs FP32 |
|----------|------|--------------|-------------|------------------|
| FP32 | 32 | ±3.4e38 | 1 DSP (post-Vivado 2020) | Baseline |
| FP16 | 16 | ±6.5e4 | 1 DSP | -0.1–1% |
| bfloat16 | 16 | ±3.4e38 | 1 DSP | < 0.1% |
| INT8 | 8 | ±127 | 1 DSP (MAC) | -0.5–3% |
| INT4 | 4 | ±7 | LUTs (no DSP) | -2–10% |
| Binary (1-bit) | 1 | {-1, +1} | XNOR + popcount | -5–20% |
| Fixed-point <16,6> | 16 | ±512 | 1 DSP | -0.1–1% |

**Guideline:** Start with INT8 quantization. If accuracy loss is acceptable, you get 2× throughput vs FP16 on the same DSP count. If not, try bfloat16.

### Quantization-Aware Training (QAT)

Better than post-training quantization (PTQ) for INT8 and below:

```python
# PyTorch QAT example
import torch.quantization as quant

model = MyModel()
model.qconfig = quant.get_default_qat_qconfig('fbgemm')  # x86
# For FPGA: use custom qconfig with appropriate observer
model = quant.prepare_qat(model)

# Fine-tune for a few epochs
for epoch in range(5):
    train(model, train_loader)

# Convert to quantized model
model = quant.convert(model)
```

---

## FPGA AI Architecture Patterns

### 1. Systolic Array (Weight-Stationary)

```
     ┌───┐ ┌───┐ ┌───┐ ┌───┐
I0──►│PE │►│PE │►│PE │►│PE │──►O0
     │×+ │ │×+ │ │×+ │ │×+ │
     └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘
       │W0    │W1    │W2    │W3
     ┌─┴─┐ ┌─┴─┐ ┌─┴─┐ ┌─┴─┐
I1──►│PE │►│PE │►│PE │►│PE │──►O1
     │×+ │ │×+ │ │×+ │ │×+ │
     └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘
       │W0    │W1    │W2    │W3
     ┌─┴─┐ ┌─┴─┐ ┌─┴─┐ ┌─┴─┐
I2──►│PE │►│PE │►│PE │►│PE │──►O2
     └───┘ └───┘ └───┘ └───┘
```

Each PE: multiply-accumulate. Weights loaded once, inputs stream through. Used by: DPU, FINN, Vortex GPU.

### 2. Vector Processor (Instruction-Driven)

```
┌──────────────────────────────────────────┐
│           Scalar Control Core            │
│   (RISC-V / MicroBlaze / ARM Cortex)    │
└─────────────┬────────────────────────────┘
              │ instructions
              ▼
┌──────────────────────────────────────────┐
│         Vector / Tensor Unit             │
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │Lane 0 │ │Lane 1 │ │Lane 7 │  ×8     │
│  │MAC    │ │MAC    │ │MAC    │         │
│  └───────┘ └───────┘ └───────┘         │
│  + local scratchpad (BRAM)              │
└──────────────────────────────────────────┘
```

More flexible than systolic array — can run different layer types. Used by: VTA (TVM), custom RISC-V + vector extensions.

### 3. Streaming Pipeline (Layer-Fused)

```
Input ──►[Conv1]──►[ReLU]──►[Pool]──►[Conv2]──►[ReLU]──►[FC]──► Output
          BRAM      comb     comb      BRAM      comb     BRAM
         (weights)                    (weights)           (weights)
```

Each layer is a dedicated hardware block, pipelined back-to-back. Zero off-chip memory access between layers. Highest throughput, lowest latency, but least flexible.

**Best for:** Single-model deployment (e.g., one specific object detector).

---

## Real-World Deployment Examples

### Object Detection on Zynq (hls4ml + PYNQ)

```
Total pipeline:
  Camera → MIPI CSI-2 RX → Preprocess (resize, normalize) →
  CNN accelerator (hls4ml bitstream) → NMS (ARM) → Display

Resources (Zynq 7020):
  PL: 35K LUTs, 50K FFs, 85 BRAM, 120 DSP
  PS: ARM Cortex-A9 @ 650 MHz
  Throughput: 30 FPS @ 320×240
  Latency: 15 ms end-to-end
  Power: 2.5W total
```

### Keyword Spotting on Lattice iCE40 (TinyFPGA BX)

```
Pipeline:
  Microphone → PDM → Feature extraction (MEL) →
  1D CNN (3-layer, INT8) → ArgMax → LED output

Resources (iCE40 UP5K):
  2K LUTs, 1 DSP (as MAC), 16 SPRAM
  Throughput: 1 inference per 10 ms
  Power: 50 mW
```

---

## Performance Benchmarking

### Metrics

| Metric | Definition | Unit |
|--------|-----------|------|
| **Inference latency** | Time from input ready to output valid | ms |
| **Throughput** | Inferences per second | inf/s |
| **FPS** | Frames per second (for vision) | fps |
| **GOP/s** | Giga-operations per second | GOP/s |
| **GOP/s/W** | Energy efficiency | GOP/s/W |
| **Utilization** | % of peak compute achieved | % |

### FPGA vs GPU Benchmark (ResNet-50, batch=1)

| Platform | Precision | Latency | Throughput | Power | GOP/s/W |
|----------|-----------|---------|-----------|-------|---------|
| Xilinx ZCU104 (DPU B4096) | INT8 | 3.2 ms | 312 fps | 15W | 5.2 |
| NVIDIA Jetson Nano (GPU) | FP16 | 12 ms | 83 fps | 10W | 1.6 |
| NVIDIA T4 (GPU) | INT8 | 1.3 ms | 770 fps | 70W | 2.1 |
| Coral Edge TPU | INT8 | 2.5 ms | 400 fps | 2W | 18.4 |
| Xilinx VCK190 (AIE) | INT8 | 0.5 ms | 2000 fps | 30W | 12.7 |

> **Note:** FPGA efficiency advantage is largest at batch=1 (low latency), where GPU underutilization is worst.

---

## Cross-References

| Topic | Article |
|-------|---------|
| Advanced HLS patterns | [Advanced HLS Patterns](advanced_hls_patterns.md) |
| ML accelerator open-source cores | [ML Accelerators](../12_open_source_open_hardware/gpu_compute/ml_accelerators.md) |
| Hardware acceleration overview | [Hardware Acceleration](hardware_acceleration.md) |
| DSP slices architecture | [DSP Slices](../02_architecture/fabric/dsp_slices.md) |
| BRAM architecture | [BRAM & URAM](../02_architecture/fabric/bram_and_uram.md) |
| Power estimation | [Power Estimation](../02_architecture/infrastructure/power_estimation.md) |