[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Compute Architecture Deep Dive: FPGA vs GPU vs TPU

A system-level comparison of three hardware paradigms — their microarchitecture, execution models, workload fit, and design trade-offs — aimed at engineers making silicon selection decisions.

---

## 1. Executive Summary: The Silicon Trilemma

Rather than listing specific part numbers that age quickly, we must categorize the available silicon into three distinct architectural archetypes. Each archetype represents a different set of trade-offs between flexibility, throughput, and development cost.

### 1.1 Archetype 1: The General-Purpose GPU
*Examples: NVIDIA Hopper/Blackwell, AMD Instinct*

Built around SIMT (Single Instruction, Multiple Threads) execution and deep memory hierarchies (SRAM → L2 → HBM).

*   **Pros:**
    *   **Maximum Flexibility:** Can run almost any parallelizable algorithm. If a new model architecture emerges tomorrow, a GPU can run it.
    *   **Unmatched Ecosystem:** CUDA and ROCm provide a plug-and-play experience for PyTorch and TensorFlow.
    *   **Peak Batch Throughput:** Massive aggregate FLOPS when serving large batches of stable models.
*   **Cons:**
    *   **High Latency Floor:** Warp scheduling and kernel launch overhead create a hard latency floor (typically 4–8 ms), making it poor for single-request ultra-low-latency tasks.
    *   **Power Hungry:** General-purpose flexibility requires complex control logic (branch predictors, dynamic schedulers) that consume significant power (~700W–1000W+ per chip).

### 1.2 Archetype 2: The Domain-Specific ASIC
*Examples: Google TPU, AWS Trainium, Intel Gaudi*

Domain-Specific Architectures (DSAs) sit squarely in the middle of the flexibility spectrum: less flexible than a general-purpose GPU, but far more flexible than a single-purpose fixed ASIC (like a Bitcoin miner).
They are built around massive Systolic Arrays (MXUs) and rigid dataflow patterns specifically tailored for deep learning matrix multiplication. They execute instructions like a GPU, but those instructions are overwhelmingly restricted to linear algebra.

*   **Pros:**
    *   **Extreme Power Efficiency:** Stripping away the GPU's general-purpose control logic leaves more silicon for pure arithmetic. Custom ASICs routinely achieve 30–50% better TFLOPS-per-watt than GPUs.
    *   **Massive Scale:** Architected from the ground up for warehouse-scale computing (e.g., the TPU's dedicated 3D-torus interconnects).
*   **Cons:**
    *   **Algorithmic Rigidity:** If your model relies heavily on dynamic control flow, non-matrix operations, or unsupported data types, hardware utilization collapses.
    *   **Compiler Dependency:** You are entirely at the mercy of the XLA or Synapse compiler to fuse operations and map your graph to the hardware's static layout.

### 1.3 Archetype 3: Spatial Compute (FPGA)
*Examples: AMD Versal, Intel Agilex*

Programmable logic gates and hardened DSP slices that physically rewire themselves to match the data path of the algorithm.

*   **Pros:**
    *   **Zero-Jitter Determinism:** No OS, no scheduler, no caches. Data flows through a physical pipeline with exact, nanosecond-level predictability.
    *   **Native Custom Precision:** Can wire a 3-bit or 1.58-bit ALU directly in silicon, achieving massive efficiency gains over fixed 8-bit/16-bit GPU ALUs.
    *   **Direct I/O:** Can terminate 100G network protocols directly in hardware without CPU or PCIe intervention.
*   **Cons:**
    *   **Low Clock Speeds:** Because signals must travel through programmable interconnects rather than hardened wires, FPGAs typically max out at 200–500 MHz, compared to the 1.0–2.0 GHz boost clocks of datacenter GPUs (H100/B200).
    *   **Routing Congestion & Timing Failures:** A design might mathematically fit on the chip (e.g., using 85% of available LUTs), but physical routing congestion may make it physically impossible to meet timing constraints, causing the design to fail compilation.
    *   **Abysmal Compilation Time:** "Compiling" an FPGA (synthesis and routing) takes hours, not seconds.
    *   **Development Friction:** Requires hardware engineering expertise (RTL/HLS) and months of effort to achieve timing closure, vs. days to deploy on a GPU.
    *   **Low Memory Capacity:** Extremely limited on-chip memory compared to GPU VRAM.


---

## 2. Universal Analytical Framework: The Roofline Model

### 2.1 Arithmetic Intensity

The roofline model is the primary analytical tool for predicting performance. Every operation has an **arithmetic intensity** (AI): floating-point operations performed per byte transferred from DRAM.

```
Peak performance = min(Peak TFLOPS, Peak BW × Arithmetic Intensity)
```

Below the roofline transition point, performance scales with bandwidth, not FLOPS. Above it, with compute.

**H100 SXM roofline parameters:**
- Peak BF16 throughput: 1,979 TFLOPS (sparse) / 989 TFLOPS (dense)
- HBM3 bandwidth: 3.35 TB/s
- **Transition point: ~590 FLOP/Byte (Sparse) or ~295 FLOP/Byte (Dense)** — below this the chip is memory-bound

| LLM Phase | Arithmetic Intensity | Regime |
| :--- | :--- | :--- |
| Prefill (prompt tokens in parallel) | 55–100 FLOP/Byte | Compute-bound |
| Decode, batch=1 | 1–10 FLOP/Byte | **Deeply memory-bound** |
| Decode, batch=256 | 200+ FLOP/Byte | Compute-bound |

A 7B-parameter FP16 model has 14 GB of weights. Loading all weights for one forward pass on H100 takes ~4.2 ms. The compute for one token at FP16 is ~14 GFLOP — under 0.01 ms at peak. At batch=1 the model is **~400× more memory-bound than compute-bound**. The 1,979 TFLOPS figure is nearly irrelevant for single-request inference.

This is why the H200 (same die, larger/faster HBM3e: 141 GB @ 4.8 TB/s) improved real-world LLM serving throughput by ~43% over H100 despite identical compute — and why the entire hardware landscape is evolving around moving compute closer to memory.

**FlashAttention** is the canonical algorithmic response: it tiles attention computation into SRAM-resident blocks, reducing HBM round-trips by 5–20×. It improves H100 attention throughput not by adding FLOPS, but by staying above the roofline transition point within each tile.

### 2.2 The KV-Cache Memory Wall

Model weights are only half of the memory bandwidth problem. For serving multiple concurrent users, the **KV-Cache** (stored attention keys and values for all tokens across all concurrent requests) often exceeds weight memory at production scale. 

A 70B parameter model serving 1,000 concurrent users at a 4K context window requires **~280 GB of KV-cache** at FP16—dwarfing the 140 GB required for the model weights themselves. This is why techniques like **PagedAttention** (vLLM) were revolutionary: the memory problem for serving is highly dynamic, fragmented, and scales with context length, whereas weight loading is static.

### 2.3 System Architecture: Prefill vs. Decode

Because the prefill phase is compute-bound and the decode phase is deeply memory-bound, they actively compete for the same resources in a shared serving system. 

If a new request with a 10K-token prompt arrives, the GPU will dedicate its compute array to the prefill. This blocks the memory-bound decode phase for all other requests currently in flight, ruining time-to-inter-token SLAs. This fundamental tension drives modern architectural decisions like **chunked prefill** (breaking long prompts into smaller pieces to interleave with decode steps) or **disaggregated serving** (routing prefill requests to compute-heavy GPU nodes, and decode requests to memory-heavy/latency-optimized nodes like TPUs or Groq).

---

## 3. Deep Dive 1: GPU — The SIMT Engine


### 3.2 Execution Model (SIMT)

> [!NOTE]
> **The Historical Twist: The GPU Accidental Empire (2012)**
> In the 2000s, NVIDIA was primarily a gaming company building chips to render triangles. However, Jensen Huang made a massively expensive, heavily criticized bet to make their GPUs general-purpose programmable via **CUDA**. For years, this was viewed as an academic niche. 
> 
> Then came 2012. Researchers training a neural network called **AlexNet** realized that the SIMD-parallel execution model GPUs use for vertex/fragment shading maps exceptionally well onto the batched GEMM operations of Convolutional Neural Networks (CNNs). They wrote `cuda-convnet` from scratch, trained a model that crushed the ImageNet competition, and kicked off the Deep Learning revolution. The GPU didn't win because it was designed for AI; it won because it already possessed the massive memory bandwidth and parallel execution model required, and CUDA made it accessible.

GPUs execute threads using a **SIMT** (Single Instruction, Multiple Threads) model. Threads are grouped into **warps** of 32 that share a single instruction fetch/decode unit. All 32 threads must execute the exact same instruction simultaneously, just on different data.

> [!TIP]
> **The SIMT Analogy:** Think of a CPU as a fleet of taxis—each driver (core) can independently navigate anywhere in the city. A GPU is a fleet of buses. The bus driver (the warp scheduler) dictates the route, and all 32 passengers (threads) must go to the same stop. If passengers need to go to different places (an `if/else` branch), the bus must drive to *both* locations sequentially, while the un-involved passengers sit idle. This is called **warp divergence** and it destroys hardware utilization.

The H100 Hopper die (TSMC 4N, 80B transistors, 814 mm²):

| Unit | H100 SXM |
| :--- | :--- |
| Streaming Multiprocessors (SMs) | 132 |
| CUDA cores per SM | 128 |
| 4th-gen Tensor Cores per SM | 4 |
| Registers per SM | 65,536 × 32-bit |
| L1 / Shared Memory per SM | 256 KB |
| L2 Cache (shared) | 50 MB |
| HBM3 capacity / bandwidth | 80 GB / 3.35 TB/s |

### 3.3 Latency Hiding via Warp Switching

HBM access latency is ~400–600 clock cycles. A single warp stalled on memory would waste those cycles. Instead, each SM maintains 64+ *active warps*. When one warp stalls, the scheduler dispatches a ready warp in zero cycles — no context switch overhead, because each warp's register file remains resident. This occupancy-based latency hiding is why GPUs achieve high throughput despite deep memory hierarchies — but it requires large batches to generate enough independent warps to hide latency. At batch=1, there are insufficient independent operations to overlap.

### 3.4 Tensor Cores

Tensor Cores are hardwired MMA (Matrix Multiply-Accumulate) units operating on fixed tile sizes:

| Generation | Chip | Formats | Notes |
| :--- | :--- | :--- | :--- |
| 3rd gen | Ampere (A100) | FP16, BF16, TF32, INT8, INT4 | 2:4 structured sparsity support |
| 4th gen | Hopper (H100) | + FP8 (E4M3/E5M2) | Transformer Engine with per-tensor dynamic FP8 scaling |
| 5th gen | Blackwell (B200) | + FP4 (NVFP4), FP6 | First native FP4 hardware |

Tensor Core throughput is only achievable on GEMM shapes aligned to hardware tile multiples. Misaligned shapes (e.g., odd vocab sizes, non-power-of-2 sequence lengths) cause partial tile utilization, reducing effective throughput below the listed peak.

**2:4 structured sparsity:** On Ampere+, if exactly 2 of every 4 consecutive weights are zero, the sparse tensor core skips zero-multiplications and doubles throughput. Measured impact on Llama FP8 sparse: ~1.27× throughput improvement, 30% lower latency vs dense FP16.

### 3.5 Memory Hierarchy

```
Registers (65,536 × 32-bit/SM, ~1 cycle)
   └── L1 / Shared Memory (256 KB/SM, ~5 cycles, SW-controlled)
       └── L2 Cache (50 MB total, ~100 cycles)
           └── HBM3 (80 GB, 3.35 TB/s, ~400-600 cycles)
               └── PCIe 5.0 Host CPU Memory (64 GB/s, ~1000+ cycles)
               └── (optional) NVLink peer GPU memory (~800 GB/s)
```

> [!WARNING]
> **The PCIe Bottleneck:** Notice the 50–125× gap between HBM bandwidth (3.35+ TB/s) and PCIe 5.0 (64 GB/s). Any workload that requires moving data between the host CPU and the accelerator at runtime will be violently bottlenecked by PCIe, completely negating the GPU's internal bandwidth advantage. This is why entire training datasets or models must be fully resident on the accelerator network.

Shared memory is a software-managed scratchpad — explicitly loaded by the programmer (or compiler). Fusing CUDA kernels into one eliminates intermediate HBM writes; FlashAttention and fused attention kernels exploit this to stay in shared memory for entire attention blocks.

### 3.6 Multi-GPU Interconnect

| Interconnect | Bandwidth | Scale |
| :--- | :--- | :--- |
| NVLink 4 (H100) | 900 GB/s bidirectional/GPU | 8 GPUs per NVSwitch node |
| NVLink 5 (B200) | 1.8 TB/s bidirectional/GPU | 72 GPUs in GB200 NVL72 |
| NVSwitch 3.0 (H100 HGX) | Non-blocking all-to-all, 8 GPUs | ~22 ms for 20 GB all-reduce |
| NVSwitch 4.0 (B200 NVL72) | Non-blocking all-to-all, 72 GPUs | 120 kW/rack power envelope |

The GB200 NVL72 rack (72 B200 GPUs + 36 Grace CPUs) draws ~120 kW. Standard data center racks are provisioned for 5–10 kW. Every GB200 NVL72 deployment requires liquid cooling infrastructure (rear-door exchangers or immersion).

### 3.7 The Ultimate Insight: The CUDA Software Moat

While we discuss hardware specs, the true reason the GPU archetype dominates is its software ecosystem. NVIDIA has spent 17 years building CUDA. As of 2025, ~89% of ML research papers reference CUDA-specific implementation details (like Triton kernels or custom memory tiling). 

Standard models (like a basic ResNet) run out-of-the-box on AMD ROCm or Google TPUs. But bleeding-edge performance relies on custom fused operators. Projects like FlashAttention or vLLM's paged attention are *hand-optimized* for NVIDIA's PTX architecture and memory hierarchy. Getting a newly released model to run at peak throughput on an AMD MI300X often requires waiting weeks for the community to port the custom CUDA kernels, whereas it is plug-and-play on NVIDIA on day one.

### 3.8 Multi-Instance GPU (MIG)

H100 and beyond support hardware partitioning into up to 7 isolated GPU instances (MIG). Each instance receives dedicated SM slices, HBM partition, and L2 cache slices — hardware isolation, not virtualization. A failure in one MIG instance cannot corrupt another's memory. Used for cloud multi-tenancy and predictable QoS in inference serving.

---

## 4. Deep Dive 2: TPU & ASICs — The Efficiency Play

### 4.1 Matrix Multiply Unit (MXU) Mechanics

The MXU is a 2D **systolic array** — a grid of processing elements (PEs), each performing a multiply-accumulate. Data flows through the array in a wave:

```
                ┌────┐ ┌────┐ ┌────┐
  activations → │ PE │→│ PE │→│ PE │→ ...   (row direction)
                └──┬─┘ └──┬─┘ └──┬─┘
                   ↓      ↓      ↓
  weights held  ┌────┐ ┌────┐ ┌────┐
  stationary →  │ PE │→│ PE │→│ PE │→ ...
                └────┘ └────┘ └────┘
```

**Weight-stationary dataflow**: model weights are loaded into the array once and held. Input activations stream through rows; partial sums accumulate vertically and exit as outputs. After the initial load, zero HBM accesses are needed until the next weight tile — entirely eliminating the weight-fetch latency that constrains GPUs at low batch sizes.

Array sizes across generations:

| TPU | MXU Array Size | MACs/cycle |
| :--- | :--- | :--- |
| v4, v5p | 128 × 128 | 16,384 |
| v7 (Ironwood) | 256 × 256 | 65,536 |

Each chip also has: vector unit (activation functions, layer norm), scalar unit (control flow), and in v7, dedicated **SparseCores** (4/chip) for embedding lookups and MoE expert routing — workloads with irregular, non-GEMM access patterns.

### 4.2 Inter-Chip Interconnect (ICI) and Topology

| TPU | ICI Bandwidth | Topology | Pod Size |
| :--- | :--- | :--- | :--- |
| v4 | 656 Gbps/chip | 3D torus | 4,096 chips |
| v5e | 1,600 Gbps/chip | 2D torus | 256 chips |
| v5p | 4,800 Gbps/chip | 3D torus | 8,960 chips |
| v6e (Trillium) | ~4,800 Gbps/chip | 2D torus | 256/pod |
| v7 (Ironwood) | ~4,800 Gbps/chip | 3D torus | 9,216 chips |

**3D torus vs 2D torus trade-off:** For an N-chip pod, maximum hop count is O(∛N) for 3D torus vs O(√N) for 2D torus. For 8,960 chips: 3D torus reduces max hops from ~190 to ~62 — directly reducing all-reduce latency for large-scale training. 2D torus (v5e, v6e) is cheaper to wire and sufficient for inference pods at smaller scale.

Comparison to NVLink: TPU ICI runs over a dedicated, low-latency custom network fabric, not PCIe. This eliminates PCIe contention and enables tighter coupling between chips than NVLink in multi-rack configurations.

> [!TIP]
> **Parallelism Strategies:** The topology dictates the parallelization strategy. NVLink's all-to-all switch hierarchy is highly optimized for **Data Parallelism** (where each GPU holds a full model replica, and gradients are synchronized via All-Reduce). The TPU 3D Torus is explicitly designed for **Model Parallelism** via tensor sharding (where layers are split across chips, requiring constant AllGather and ReduceScatter operations). This mechanistic difference is why Google's TPU pods scale so efficiently for massive models like Gemini without needing an NVSwitch equivalent.

### 4.3 What is XLA and Why Does It Matter?

> [!IMPORTANT]
> **The Key Insight:** A TPU is essentially a "dumb" arithmetic engine. It lacks the complex, dynamic schedulers of a GPU. It achieves extreme power efficiency by offloading all scheduling complexity to software—specifically, a compiler called **[XLA (Accelerated Linear Algebra)](https://openxla.org/)**. If XLA fails to optimize your workload, your TPU will perform far worse than a standard GPU.

If you use a standard PyTorch/CUDA workflow, operations execute sequentially. If you run a matrix multiply followed by an activation function, the GPU runs the matrix multiply kernel, writes the massive result out to HBM, reads it back from HBM, and then runs the activation kernel. This crashes headfirst into the Memory Wall.

XLA changes this paradigm via **Whole-Graph Optimization**. It refuses to execute anything until it sees the *entire* neural network graph:

```text
Framework (JAX / PyTorch-XLA / TensorFlow)
         ↓
    HLO graph (High-Level Operations)  <-- XLA evaluates the math, independently of hardware
         ↓ 
    Operator Fusion & Tiling           <-- XLA aggressively fuses operations to eliminate HBM reads/writes
         ↓ 
    Hardware Machine Code (LLO)        <-- XLA compiles a static binary directly for the TPU array
```

**The Power of Operator Fusion:** Because XLA sees the whole graph, it can fuse a matrix multiply, GELU, LayerNorm, and a residual add into a *single, custom machine-code kernel* that executes entirely within the TPU's ultra-fast SRAM. For a standard transformer block, this fusion reduces HBM memory traffic by 3–5× compared to standard eager execution.

> [!WARNING]
> **The Trade-off:** To achieve extreme fusion, XLA demands that the computation graph be **statically shaped** at compile time. Dynamic shapes (e.g., variable-length text sequences, data-dependent `if/else` branches) force XLA to trigger a JIT (Just-In-Time) recompilation during runtime. This is fine for massive, steady-state training runs, but catastrophic for highly dynamic, low-latency inference workloads.

### 4.4 ASIC / Cloud Hardware Progression

> [!NOTE]
> **The Historical Twist: The ASIC Panic (2015)**
> By 2013, Google realized a terrifying truth: if every Android user used voice search for just 3 minutes a day, the compute required for the neural network inference would force Google to *double* their global datacenter footprint. CPUs were too slow, and GPUs (at the time) were too power-hungry for hyperscale inference.
> 
> Faced with a capital expenditure crisis, Google secretly designed the **TPU v1** in just 15 months. By stripping away all the general-purpose logic of a CPU/GPU and building a rigid, single-purpose "Systolic Array" specifically for 8-bit matrix math, they achieved a 15–30× performance-per-watt advantage over contemporary silicon. The TPU v1 saved Google billions in datacenter costs and proved that **Domain-Specific Architectures (DSAs)** were the only viable path for hyperscale AI economics.

| Silicon | Compute Units | BF16 TFLOPS/chip | FP8 TOPS/chip | Memory Bandwidth | TDP (est.) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[Baseline] Server CPU** (EPYC 96c) | 96 Cores | ~3–5 | — | 0.46 TB/s (DDR5) | 360W |
| **[Baseline] GPU** (NVIDIA H100) | 132 SMs (528 TCs) | 1,979 | 3,958 | 3.35 TB/s (HBM3) | 700W |
| **[Baseline] GPU** (NVIDIA H200) | 132 SMs (528 TCs) | 1,979 | 3,958 | 4.80 TB/s (HBM3e) | 700W |
| **[Baseline] GPU** (NVIDIA B200) | 160 SMs (640 TCs) | 2,250 | 4,500 | 8.00 TB/s (HBM3e) | 1,000W |
| **[Baseline] GPU** (Huawei Ascend 910B) | ~300 DaVinci Cores | ~600 (FP16) | — | 1.20 TB/s (HBM2e) | ~350W |
| **[Baseline] GPU** (Huawei Ascend 910C) | ~600 DaVinci Cores | ~800 (FP16) | — | 1.80 TB/s (HBM2e) | ~400W |
| **Intel Gaudi 3** | 8 MMEs (Matrix Engines) | 1,835 | 3,670 | 3.70 TB/s | 600W |
| **AWS Trainium2** | 8 NeuronCores | ~667 | 1,299 | 2.90 TB/s | ~400W |
| **Google TPU v4** | 2 TensorCores (4 MXUs of 128²) | ~275 | — | ~1.2 TB/s | ~170W |
| **Google TPU v5e** | 1 TensorCore (4 MXUs of 128²) | ~197 | ~393 (INT8) | ~1.6 TB/s | ~150W |
| **Google TPU v5p** | 2 TensorCores (4 MXUs of 128²) | ~459 | — | ~2.8 TB/s | ~200W |
| **Google TPU v6e** (Trillium) | 1 TensorCore (Unconfirmed MXU layout) | ~918 | — | ~4.8 TB/s | ~250W |
| **Google TPU v7** (Ironwood) | 2 TensorCores (est. 4 MXUs of 256²) | ~2,300 | 4,614 | 7.37 TB/s | ~500W |

*Note: TPU power figures are not published directly; estimates are derived from rack-level disclosures. v7 Ironwood (available November 2025) is the first TPU generation with native FP8 hardware support, bringing it into direct comparison with the Hopper/Blackwell tensor core precision baseline.*

**Architectural Conclusion: Performance & Efficiency**
Based on the progression above, the TPU's positioning becomes clear:
*   **Vs. CPUs:** CPUs are entirely unviable for large-scale matrix math. A 96-core server CPU yields ~5 TFLOPS at 360W. A single TPU v7 is ~460× faster while drawing only 40% more power.
*   **Vs. GPUs (Raw Performance):** Google has successfully matched NVIDIA's bleeding-edge performance. The TPU v7 achieves parity with the NVIDIA B200 in both raw compute (~4,600 FP8 TOPS) and memory bandwidth (~7.4 TB/s).
*   **Vs. GPUs (Performance-per-Watt):** This is the Domain-Specific ASIC's true moat. By offloading scheduling to the XLA compiler and removing the general-purpose control logic required by GPUs, the TPU dedicates far more silicon to pure arithmetic. The TPU v7 hits its 2,300 TFLOPS at an estimated ~500W, compared to the B200's 1,000W. This gives the TPU roughly **2× the performance-per-watt** of a flagship GPU.

---

## 5. Deep Dive 3: FPGA — Spatial Compute

The fundamental distinction between instruction-driven processors (von Neumann architectures like CPUs and GPUs) and FPGAs lies in the computational paradigm. While GPUs map software instructions to a static, hardened datapath, FPGAs synthesize the algorithm directly into a custom physical datapath utilizing programmable logic.

This establishes the strict dichotomy between **Temporal** architectures and **Spatial** architectures.

### 5.1 The Core Thesis: Spatial vs. Temporal Execution

> [!NOTE]
> **The Historical Twist: The FPGA Lifeline (Project Catapult)**
> While Google built ASICs, Microsoft faced a different crisis. Their Bing search ranking algorithms were becoming too complex for CPUs, pushing search latency to unacceptable levels. However, search algorithms change weekly—a 24-month ASIC tape-out cycle was too rigid, and GPUs were too inefficient for the specific decision-tree logic required.
> 
> Microsoft's solution was **Project Catapult**. They strapped an Altera FPGA to every single server in the Bing datacenter. FPGAs provided the deterministic, hardware-level speed of an ASIC, but could be "re-wired" via a software bitstream update whenever the algorithm changed. This hybrid approach yielded a 50% throughput increase without adding servers, proving that spatial compute could survive in the hyperscale cloud.

A GPU possesses massive **Data Parallelism** (e.g., 10,000+ CUDA cores), but its execution of the algorithm remains **Temporal**. The entire compute array executes the instructions for Layer 1 across a massive batch of data. Once Layer 1 completes, the activations are written to memory, the GPU loads the instructions for Layer 2, and the compute array is repurposed for the next step. Time is the axis of algorithmic progression.

An FPGA utilizes **Pipeline (Spatial) Parallelism**. You instantiate Layer 1, Layer 2, and Layer 3 as physically separate, dedicated logic blocks residing simultaneously on different areas of the chip. They are connected directly by wires.

> [!TIP]
> **Data at Rest vs Data in Motion:** GPUs are built for "Data at Rest." You pull data from memory, compute on it, and put it back. FPGAs are built for "Data in Motion." You pipe a 100Gbps network stream directly into the chip, and the data flows continuously through the physical gates, emerging fully processed on the other side without ever touching DRAM.

```text
Temporal (GPU):    Input → [Layer 1] → mem → [Layer 2] → mem → [Layer 3] → Output
                           ← time →

Spatial (FPGA):    Input → [Layer 1] → wire → [Layer 2] → wire → [Layer 3] → Output
                           ← all active in parallel, pipelined →
```

**The consequence:** A spatial pipeline fires a result every single clock cycle. Batch size is irrelevant. Input tokens stream through the pipeline at line rate, and latency is deterministic (nanoseconds to low microseconds).

> [!WARNING]
> **The "Dark Silicon" Problem:** Because an FPGA instantiates the *entire* algorithm spatially, any logic block that is not currently processing a token is wasting silicon. If you deploy a 100-layer neural network on an FPGA, Layer 100 sits completely idle while the token flows through Layer 1. This is why GPUs easily beat FPGAs in maximum aggregate throughput.

### 5.2 The Anatomy of Programmable Logic

Instead of ALUs and registers, the FPGA fabric provides raw building blocks:

*   **LUTs (Look-Up Tables):** Programmable truth tables. Any Boolean function of 6 variables can be wired into a single LUT.
*   **Flip-Flops:** 1-bit registers for pipelining the logic.
*   **Hardened DSP Slices:** Dedicated 27×18-bit multiply-accumulate blocks (to avoid wasting thousands of LUTs on basic math).
*   **BRAM / URAM:** Scattered blocks of on-chip SRAM (usually <100 MB total).
*   **Routing Fabric:** A massive sea of programmable interconnect wires that consumes 60–70% of the die area.

When you write an HLS (C++) or RTL (Verilog) design, the compiler is quite literally routing physical paths through these components to create a custom, fixed circuit.

### 5.3 The Modern Reality: Heterogeneous SoCs

Modern FPGAs are no longer just "seas of logic gates." Because routing fabric is slow (maxing out at 300–500 MHz), vendors have moved to hybrid architectures to compete with ASICs:

*   **Hardened AI Engines (e.g., AMD Versal):** Instead of building matrix multipliers out of slow LUTs, modern chips drop hundreds of hardened, 1 GHz VLIW vector processors directly onto the silicon alongside the programmable logic.
*   **Advanced Interconnects (e.g., Intel Agilex with CXL):** To combat the memory wall, newer FPGAs integrate CXL 2.0. This allows the FPGA to address the host CPU's terabytes of DRAM coherently, bypassing the need to explicitly copy model weights across the PCIe bus entirely.

The goal is to provide the deterministic, spatial execution of an FPGA for the control logic, while using hardened, ASIC-like tiles for the heavy mathematical lifting.

### 5.4 Deterministic Latency

FPGA latency is a function of pipeline depth and clock frequency — neither changes at runtime:

```
Latency = pipeline_stages / f_clk
         = constant
```

For a CNN implemented as a spatial pipeline at 300 MHz with 200 pipeline stages:
- Latency: 200 / 300 MHz = **0.67 µs** — regardless of batch size, system load, or thermal state

GPU latency at batch=1 (H100, ResNet-50): 4–8 ms, governed by kernel launch overhead, warp scheduler startup, and HBM prefetch latency — not the computation itself. The pipeline startup cost is fixed and dominates single-request latency.

This determinism is why FPGAs are used in HFT and O-RAN: not just because they are fast, but because they are **predictably fast** — no jitter, no tail latency, no thermal throttling degrading SLAs.

### 5.5 HLS and Design Toolchains

| Tool | Input | Notes |
| :--- | :--- | :--- |
| Vitis HLS 2024.2 | C/C++ with `#pragma HLS` directives | `PIPELINE`, `UNROLL`, `DATAFLOW` guide micro-architecture |
| Intel HLS Compiler (oneAPI) | C++ | Integrates with SYCL cross-platform flow |
| ScaleHLS / SODA | MLIR IR | Research-grade; accepts TF/PyTorch → FPGA RTL via MLIR lowering |
| Vitis AI | PyTorch / ONNX → DPU | Standard model deployment; 100+ pre-optimized models |

HLS productivity vs RTL: 5–10× more lines of implementable code per engineer-day. However, timing closure (meeting target clock frequency) frequently requires dropping back to RTL-level tuning for critical paths. For novel designs, budget implementation + closure as a combined effort.

---

## 6. The Memory-Centric Challengers

The memory wall for LLM inference created space for architectures that eliminate the HBM bottleneck by integrating compute and memory at a fundamentally different scale.

### 6.1 Cerebras WSE-3: Wafer-Scale On-Chip Memory

| Spec | WSE-3 | H100 SXM |
| :--- | :--- | :--- |
| Die area | ~46,000 mm² | 814 mm² |
| Process | TSMC 5nm | TSMC 4N |
| Transistors | 4 trillion | 80 billion |
| Compute cores | 900,000 | 16,896 CUDA cores |
| On-chip SRAM | **44 GB** | ~26 MB (L1+L2) |
| On-chip bandwidth | **21 PB/s** | ~240 TB/s (L1 aggregate) |
| Off-chip memory | None (model on-chip) | 80 GB HBM3 @ 3.35 TB/s |

WSE-3 sidesteps the memory wall by making all model memory on-chip SRAM. For a 70B-parameter model in INT8 (70 GB), the model does not fit; for a 7B model in FP16 (14 GB) or a 40B+ model in INT4/INT8, it does, and every weight access takes ~5 cycles instead of 400–600 cycles. By shifting the memory bandwidth from 3.35 TB/s (HBM3) to 21 PB/s (SRAM), the WSE-3 effectively raises the Roofline bandwidth ceiling by ~6,000×, pushing almost all inference workloads into the compute-bound regime.

Architectural constraint: the 44 GB on-chip SRAM is the model size ceiling. Training very large models requires weight streaming from external MemoryX nodes (Cerebras's attached DRAM), which reintroduces bandwidth constraints at that boundary. For inference of models that fit on-chip, the performance envelope is structurally different from any HBM-based accelerator.

### 6.2 Groq LPU: Compiler-Scheduled Determinism

The LPU (Language Processing Unit) achieves low-latency LLM inference through a fundamentally different scheduling model:

| Property | LPU | GPU |
| :--- | :--- | :--- |
| Scheduling | Compile-time, fully static | Runtime, dynamic warp scheduler |
| Cache hierarchy | None (no cache misses) | L1 / L2 / HBM |
| Branch prediction | None | Speculative |
| Memory access | Fully deterministic (address pre-computed at compile time) | Non-deterministic (TLB, cache effects) |
| Execution model | SIMD, deterministic instruction stream | SIMT, dynamic warp dispatch |

The Groq compiler pre-computes every memory address and instruction slot for the entire inference pass. At runtime, the hardware executes this static schedule at maximum clock speed with zero scheduler overhead. No cache misses occur because accesses are pre-planned and pre-fetched.

Measured result: ~0.8 seconds for 100 output tokens on Llama 2 70B — vs. 3–8 seconds on H100 for the same model. The speed advantage narrows under heavy batching where GPU throughput catches up, but Groq's deterministic latency floor is a hard physical advantage for single-request, latency-sensitive serving. In Roofline terms, Groq eliminates the massive kernel-launch overhead latency floor that artificially depresses GPU performance at batch=1, allowing single-request inference to actually reach the theoretical hardware limits.

LPU constraints: no training capability, limited dynamic shapes support, model support catalog is curated (not arbitrary PyTorch).

### 6.3 SambaNova SN40L: Dataflow for MoE Models

The SN40L (Reconfigurable Dataflow Unit) addresses a specific problem: **Mixture-of-Experts (MoE) models with irregular weight access patterns**.

MoE inference activates only 2 of N experts per token. With 671B total parameters but only ~20B activated per token, the majority of weights sit unused in memory each inference step. On a GPU, all 671B parameters must reside in HBM to avoid slow PCIe transfers on demand — requiring ~320 H100 GPUs.

SN40L's three-tier memory hierarchy:
```
On-chip SRAM          — active expert weights (~fast)
HBM                   — model's "hot" expert pool
DRAM                  — model's full parameter set
```

The compiler maps the entire model as a dataflow graph. Inactive experts remain in DRAM; only activated experts are loaded to HBM/SRAM ahead of each forward pass based on expert routing predictions. 16 SN40L chips serve a 671B MoE model that otherwise requires ~320 H100s.

The mechanism is only efficient because MoE activation patterns are predictable over a short window — the compiler exploits this locality. For dense models, the DRAM tier adds latency rather than helping.

---

## 7. Engineering Trade-offs & System Lifecycles

### 7.1 Time to Production: A Problem-Driven View

The question "How long does it take?" is meaningless without defining the engineering problem. The development timeline is a direct function of whether you are using the *right tool for the problem*.

| The Engineering Problem | The Right Tool | The Wrong Tool | Why? |
| :--- | :--- | :--- | :--- |
| **Deploy a standard model** (e.g., LLaMA 3, YOLOv8) | **GPU (1–3 days)** | FPGA (2–4 weeks via DPU) | The CUDA ecosystem has pre-built, highly optimized binaries for standard matrix math. You `import torch` and run. FPGAs require compiling the model to a soft-core DPU, which adds friction. |
| **Implement a custom FP16/INT8 algorithm** (e.g., a novel attention mechanism) | **GPU (2–8 weeks)** | TPU (Months / XLA constraints) | GPUs provide CUDA/Triton. You can write custom software kernels to execute standard precision math very efficiently. TPUs require XLA compiler support, making custom ops difficult. |
| **Implement non-standard precision** (e.g., Ternary / 1.58-bit weights) | **FPGA (2–6 weeks)** | GPU (Months / Poor Perf) | GPUs possess fixed 8/16-bit ALUs. Emulating 1.58-bit math on a GPU requires complex software bit-shifting that destroys performance. FPGAs allow native wiring of 2-bit gates (`ap_int<2>`) in HLS. |
| **Zero-OS deterministic processing** (e.g., HFT market data, 100G O-RAN) | **FPGA (4–16 weeks)** | GPU (Not Viable) | GPUs require an OS, a PCIe bus transfer, and kernel launch overhead (~5 µs jitter). FPGAs terminate the network protocol directly in hardware with nano-second determinism. |
| **Massive-scale steady-state serving** (e.g., Google Search, ChatGPT) | **TPU / Custom ASIC (18–36 months)** | GPU (Too expensive at scale) | If the model is fixed and the volume is immense, the $20M+ NRE cost of designing an ASIC is quickly eclipsed by the millions saved in power and cooling over 3 years. |

> [!NOTE]
> **What is a DPU?**
> In the FPGA ecosystem, DPU stands for **Deep Learning Processor Unit** (not to be confused with Data Processing Units like NVIDIA BlueField). It is a programmable, soft-core inference engine provided by AMD/Xilinx that you instantiate onto the FPGA fabric. Instead of writing custom hardware logic (RTL) for a neural network, you configure the DPU, and the Vitis AI compiler translates your PyTorch/TensorFlow model into instructions the DPU executes. It effectively turns the FPGA into a customizable GPU. [Read more in the AMD Vitis AI DPU Product Guide](https://docs.amd.com/r/en-US/pg338-dpu/Deep-Learning-Processor-Unit).

The GPU advantage ("fast to develop for") holds only for software problems that map cleanly to standard precision (FP16/INT8) matrix multiplication. It collapses the moment the problem requires bit-level manipulation, non-standard data paths, or strict hardware determinism.

### 7.2 FPGA Development Phases (Novel Design)

| Phase | Duration |
| :--- | :--- |
| Architecture design, resource estimation | 2–6 months |
| RTL / HLS implementation | 3–12 months |
| Functional verification, timing closure | 3–9 months |
| Board bring-up and driver integration | 3–7 months |
| **Total** | **11–34 months** |

Timing closure is non-trivial: meeting a 300 MHz target after HLS synthesis often requires manual RTL tuning of critical paths identified from timing analysis reports.

**Is this timeline good or bad?** It depends entirely on the chosen methodology and the baseline of comparison:

| Methodology & Platform | Typical Time | Capital Cost (NRE) | Risk & Iteration Profile |
| :--- | :--- | :--- | :--- |
| **GPU (CUDA Software)** | **2–6 months** | ~$0 | **Low**. Bugs fixed via OTA update. Compilation and iteration take minutes. |
| **FPGA (HLS-Driven)** | **6–12 months** | ~$0 | **Medium**. C++ synthesized to gates. 5–10× faster to write than RTL, but timing closure often forces manual RTL fine-tuning on critical paths. |
| **FPGA (Pure RTL)** | **11–34+ months** | ~$0 | **Medium-High**. Verilog/VHDL. Total control over spatial layout, but verifying cycle-accurate logic takes immense labor. |
| **ASIC / Custom Silicon** | **18–36+ months** | **$10M–$50M+** | **Extreme**. Uses the same HLS/RTL workflows as FPGA, but a silicon bug requires a physical respin, costing millions and adding 6+ months. |

Compared to writing software for a GPU, hardware development (even using HLS) is incredibly slow. HLS dramatically accelerates the initial algorithmic implementation compared to pure RTL, but it is a "leaky abstraction" — engineers almost always have to drop down to RTL to fix timing violations. However, compared to designing a custom ASIC, FPGAs offer similar development workflows while completely eliminating the $20M+ tape-out risk. This makes FPGAs the defacto standard for prototyping ASICs and deploying low-volume hardware where an ASIC tape-out cannot be financially justified.

> [!WARNING]
> **The Production Lifecycle Constraint:** Synthesis time doesn't just impact initial development; it dictates production operations. A GPU can swap model weights in seconds. A TPU can JIT-recompile a graph in minutes. An FPGA requires hours of synthesis followed by a bitstream download. This means an FPGA system cannot dynamically hot-reload algorithms on the fly. Versioning, A/B testing, and emergency rollbacks must be architected at the hardware deployment level, drastically altering the system's operational lifecycle.

### 7.3 Software Ecosystem Depth

| Hardware Platform | High-Level Framework Support | Low-Level Compilers & Libraries | Ecosystem Maturity |
| :--- | :--- | :--- | :--- |
| **NVIDIA** | **PyTorch** (Native, optimal), TensorFlow, JAX, vLLM | **CUDA Toolkit**, cuBLAS, cuDNN, TensorRT, NCCL, Triton | ~17 years; the undisputed industry standard. |
| **AMD (ROCm)** | **PyTorch** (Good, via HIP), vLLM (Improving) | rocBLAS, MIOpen, RCCL, HIP | Growing. Historically fragile setup; closing the gap on standard ops. |
| **Google TPU** | **JAX** (Native, optimal), PyTorch (via PyTorch/XLA) | OpenXLA compiler, Pallas | Deep for Google tooling. Demands static computation graphs (no dynamic shapes). |
| **Intel (Gaudi/oneAPI)** | PyTorch (via IPEX), OpenVINO | oneMKL, SynapseAI | Maturing. PyTorch coverage is good but lacks the long tail of CUDA community fixes. |
| **FPGA (AMD Vitis AI)** | ONNX, PyTorch (via DPU compilation) | DPU soft-core, FINN (Quantization) | Niche. Requires quantizing models to INT8 and compiling to a static hardware block. |

**The CUDA Moat in Practice:** The practical constraint for AMD ROCm is not hardware capability — it is the software ecosystem flywheel. As of 2025, ~89% of ML research papers reference CUDA-specific implementation details. What does this mean for an engineering team? 
- Standard models via PyTorch (e.g., standard ResNet or BERT) run out-of-the-box on ROCm.
- However, bleeding-edge performance relies on custom fused operators. Projects like FlashAttention, vLLM's paged attention, and Triton kernels are initially hand-optimized for NVIDIA's memory hierarchy and PTX architecture.
- Getting a newly released model architecture to run *at peak theoretical throughput* on MI300X often requires waiting weeks for the open-source community to port and tune the custom CUDA kernels to AMD's HIP/ROCb API, whereas it is plug-and-play on NVIDIA on day one.

---

## 8. The Next Twist: The 1.58-bit Threat (Quantization & Precision)

### 8.1 Hardware Support Matrix

| Precision | Relative Throughput (vs BF16 baseline) | Standard GPU Paradigm | Bleeding-Edge GPU / ASIC | FPGA (Spatial Logic) | Hardware Mechanism & Trade-offs |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BF16 / FP16** | **1× (Baseline)** | Native (Tensor Cores) | Native (Tensor Cores / MXU) | Emulated (via DSP cascades) | Standard baseline. Uses ~500 gate equivalents per MAC. Excellent accuracy, highest memory bandwidth pressure. |
| **FP8 / INT8** | **~2×** | Native (Tensor Cores) | Native (Tensor Cores / MXU) | Native (Hardened DSPs) | Halves memory bandwidth pressure vs 16-bit. The de facto industry standard for high-throughput inference serving. |
| **INT4 / FP4** | **~4×** | Emulated (Poor efficiency) | **Native** (e.g., Blackwell FP4) | Native (via LUTs or DSP packing) | Doubles FP8 throughput, but the silicon ALU must be physically wired to support 4-bit instructions to actually see these gains. |
| **Ternary / 1.58-bit** | **~16×–32×** (Theoretical on custom silicon) | Not Viable (Fixed ALU) | Not Viable (Fixed ALU) | **Native (Custom synthesis)** | Only requires 2 AND gates + 1 Adder. Temporal architectures (GPU/TPU) must wait 36 months for a new silicon tape-out to support it natively. FPGAs adapt instantly via bitstream rewiring. |

**FP8 impact on H100 (measured):** With TensorRT-LLM FP8 + 2:4 sparsity: 30% lower latency, 20% higher throughput vs FP16 dense baseline.

### 8.2 BitNet b1.58 and Ternary Arithmetic

Microsoft's BitNet b1.58 (2025) natively trains LLMs with ternary weights {−1, 0, +1} (1.58 bits/weight). CPU performance is dramatically improved (2–6× speedup, 55–82% energy reduction) because ternary multiplication reduces to masking and sign operations.

GPU and TPU currently lack native ternary hardware. FP4 (B200) is the closest approximation but still executes a floating-point multiply internally. A ternary MAC on silicon requires:
- 2:1 MUX (if weight=0, output 0; if weight=+1, pass input)
- 1 conditional negation (if weight=−1, negate input)
- A standard integer accumulator

vs. an FP16 multiplier requiring ~500 gate equivalents. On FPGA, this maps directly. A custom Versal AIE program or RTL pipeline for BitNet b1.58 could achieve **10–50× better TOPS/W** vs an INT8 GPU implementation — the efficiency difference is physical, not algorithmic.

No current GPU or TPU vendor has announced native ternary hardware. This is an active gap.

## 9. Synthesis: Architecture Selection Matrix

| Criteria | GPU (H100/B200) | TPU (v5p/v7) | FPGA (Versal/Agilex) | Cerebras/Groq/SambaNova |
| :--- | :--- | :--- | :--- | :--- |
| Model training | **Best** | **Best** (JAX/XLA required) | Not viable | Cerebras: Yes; Groq: No |
| Large-batch throughput inference | **Excellent** | Excellent | Limited | Workload-specific |
| Single-request (batch=1) latency | Poor (4–8 ms) | Poor (5–20 ms) | **1.5–2 ms** | Groq: **<1 ms** |
| Deterministic latency | No | No | **Yes** | Groq: Yes |
| Non-standard precision (ternary, bitwise) | Not viable | Not viable | **Native** | Not applicable |
| Real-time protocol processing | Not viable | Not viable | **Native** | Not applicable |
| Safety certification (ISO 26262, DO-254) | Not viable | Not viable | **Achievable** | Not applicable |
| Model flexibility | Any PyTorch/TF model | XLA-compatible models | Model-specific design | Limited catalog |
| Time to first deployment | **Days** | Weeks–months | Months–years | Weeks–months |
| Power (TFLOPS/W, BF16) | 2.3–2.83 | ~3.7–4.6 | 3–10× better (matched workloads) | High (purpose-built) |
| MoE large-model inference | Good (multi-GPU) | Good (SparseCores v7) | Limited | SambaNova: **Optimal** |

### 9.1 Workload Analysis: Training vs Inference

#### 9.1.1 Training
Training is computationally dominated by large GEMM operations over full batches (batch size 32–8192 typical). Arithmetic intensity is high — frequently above the roofline transition point. The binding constraints are:
1. **Aggregate HBM bandwidth** for optimizer state updates (AdamW stores 3 copies of parameters: weight, momentum, variance)
2. **All-reduce bandwidth** for gradient synchronization across GPUs/chips
3. **Compute throughput** for the forward/backward GEMM operations

GPUs win here: CUDA's maturity means every training operation has a highly tuned kernel. NVLink all-reduce dominates PCIe. TPUs win at extreme scale (8,960+ chips) where 3D torus ICI outperforms NVLink topology for model-parallel gradient communication.
FPGAs are not viable for training: synthesis latency (hours to recompile for a changed model), inability to represent backpropagation natively in RTL, and insufficient on-chip memory for optimizer states.

#### 9.1.2 Single-Request Inference (Batch=1)
Workloads: Real-time voice assistants, agentic AI loops, coding assistants where time-to-first-token and ultra-low latency are paramount.

**The GPU struggles here.** At batch=1, the massive compute array is starved of work, and the execution is completely dominated by memory latency and kernel-launch overhead. The hardware is fundamentally mismatched for the workload.
**The Solutions:** 
- Groq's LPU eliminates the scheduler overhead entirely, providing deterministic, sub-millisecond execution.
- Cerebras WSE-3 eliminates the memory wall by keeping the entire model in SRAM, reducing fetch times from ~500 cycles to ~5 cycles.
- FPGAs provide single-request determinism by streaming data through a spatial pipeline, but lack the memory capacity for massive LLMs.

#### 9.1.3 Mixture of Experts (MoE) Large-Model Inference
Workloads: Serving 100B+ parameter models (like Grok, Mixtral, GPT-4 architecture) efficiently.

MoE models only activate a tiny fraction of their total parameters per token. This creates an extreme memory capacity requirement (you must store 600B+ parameters in HBM) but a low compute requirement (you only compute on 20B parameters per token). 
Deploying this on standard GPUs requires massive 8-node or 16-node clusters just to pool enough HBM, wasting the majority of the compute capability. Architectures like SambaNova's SN40L solve this via a tiered memory hierarchy, keeping inactive experts in cheap DRAM and only loading them to HBM/SRAM ahead of time based on routing predictions.

#### 9.1.4 Real-Time Protocol and Signal Processing
Workloads: O-RAN fronthaul (FFT/IFFT, channel estimation, LDPC/Polar decoding at 100G line rate), radar signal processing, network intrusion detection. *(For High-Frequency Trading specifics, see [Hardware Acceleration](hardware_acceleration.md)).*

**Only FPGAs are viable** for these workloads. Requirements:
- Deterministic sub-microsecond latency
- Zero OS/kernel involvement (network packets processed at FPGA NIC, not passed to CPU)
- Line-rate throughput at 25G/100G/400G without backpressure
- Custom protocol state machines not expressible as matrix math

GPU interrupt latency alone (~1–10 µs for kernel launch) disqualifies it. CPU kernel-bypass (DPDK) achieves ~1–5 µs; FPGA achieves 1–10 clock cycles at 300+ MHz.


### 9.2 Decision by Workload

**Use GPUs when:** training any large model; offline batch inference at scale with standard precision; rapid iteration on model architecture; standard quantization (INT8/FP8) deployment.

**Use TPUs when:** training at 1,000+ chip scale on JAX; steady-state inference of high-volume models with stable architecture; workload fits XLA's static graph requirement.

**Use FPGAs when:** deterministic sub-microsecond latency is required; processing involves custom bit widths or non-GEMM algorithms; workload is a network protocol, signal processing pipeline, or automotive safety function; field-reprogrammability of deployed hardware is needed.

**Use Cerebras/Groq/SambaNova when:** single-request LLM latency is the primary constraint (Groq); model fits on WSE-3 on-chip SRAM and eliminates HBM bottleneck entirely (Cerebras); serving a 100B+ MoE model without a 200+ GPU cluster (SambaNova).

---

## Sources

- [LLM Inference Unveiled: Roofline Model Insights | arXiv 2402.16363](https://arxiv.org/html/2402.16363v4)
- [GPU Architecture Fundamentals | BentoML LLM Inference Handbook](https://bentoml.com/llm/kernel-optimization/gpu-architecture-fundamentals)
- [NVIDIA H100/H200/B200 Specs | IntuitionLabs](https://intuitionlabs.ai/articles/nvidia-data-center-gpu-specs)
- [Nvidia Blackwell Perf TCO Analysis | SemiAnalysis](https://newsletter.semianalysis.com/p/nvidia-blackwell-perf-tco-analysis)
- [NVIDIA NVLink and NVSwitch Architecture | NVIDIA Developer Blog](https://developer.nvidia.com/blog/nvidia-nvlink-and-nvidia-nvswitch-supercharge-large-language-model-inference/)
- [TPU v5p Documentation | Google Cloud](https://docs.cloud.google.com/tpu/docs/v5p)
- [TPU v7 (Ironwood) Architecture | Google Cloud](https://docs.cloud.google.com/tpu/docs/tpu7x)
- [Google TPU Architecture: 7 Generations | Introl Blog](https://introl.com/blog/google-tpu-architecture-complete-guide-7-generations)
- [AMD Versal AI Core Series | AMD](https://www.amd.com/en/products/adaptive-socs-and-fpgas/versal/ai-core-series.html)
- [AMD Versal AI Edge Gen 2 | AMD](https://www.amd.com/en/products/adaptive-socs-and-fpgas/versal/gen2/ai-edge-series.html)
- [Intel Agilex 9 Product Overview | Intel](https://www.intel.com/content/www/us/en/products/details/fpga/agilex/9.html)
- [Chiplet-Based FPGA and CXL | Electronic Design](https://www.electronicdesign.com/technologies/embedded/digital-ics/fpga/article/21266629/electronic-design-chiplet-based-fpga-tackles-cxl)
- [Cerebras vs SambaNova vs Groq AI Chip Comparison | IntuitionLabs](https://intuitionlabs.ai/articles/cerebras-vs-sambanova-vs-groq-ai-chips)
- [AMD MI300X vs NVIDIA H100 Benchmarks | Tom's Hardware](https://www.tomshardware.com/pc-components/gpus/amd-mi300x-performance-compared-with-nvidia-h100)
- [MI300X vs H100 Training | SemiAnalysis](https://newsletter.semianalysis.com/p/mi300x-vs-h100-vs-h200-benchmark-part-1-training)
- [Intel Gaudi 3 vs H100 | Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/intel-launches-gaudi-3-accelerator-for-ai-slower-than-h100-but-also-cheaper)
- [2:4 Sparse Llama FP8 Benchmarks | Red Hat Developer](https://developers.redhat.com/articles/2024/12/18/24-sparse-llama-fp8-sota-performance-nvidia-hopper-gpus)
- [Faster Inference: FPGA vs GPU Benchmarks | InAccel](https://inaccel.medium.com/faster-inference-real-benchmarks-on-gpus-and-fpgas-fa3df04d51d7)
- [FPGA vs GPU for ML: Comparative Analysis | arXiv 2502.02304](https://arxiv.org/html/2502.02304v1)
- [FPGA HLS: Successes, Challenges, Opportunities | ACM TRETS](https://dl.acm.org/doi/10.1145/3530775)
- [Microsoft BitNet b1.58 | GitHub](https://github.com/microsoft/BitNet)
- [Mixture of Experts Explained | Hugging Face](https://huggingface.co/blog/moe)
- [MLPerf Inference v5.1 Results | HPCwire](https://www.hpcwire.com/2025/09/10/mlperf-inference-v5-1-results-land-with-new-benchmarks-and-record-participation/)
- [OpenXLA Project](https://openxla.org/)