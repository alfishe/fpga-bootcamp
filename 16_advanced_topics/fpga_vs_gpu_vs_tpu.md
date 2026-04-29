[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Compute Architecture: FPGA vs GPU vs TPU

When designing a high-performance compute system, choosing the right silicon architecture is critical. The massive explosion of Artificial Intelligence has ignited a fierce "Silicon War," forcing engineers to fundamentally evaluate how they process data. 

Here is how FPGAs stack up against GPUs and Application-Specific ICs (ASICs) like Google's TPU.

---

## 1. History & Origins

To understand why these architectures differ so wildly today, we must look at what they were originally designed to do.

### The FPGA (Field Programmable Gate Array)
*   **Invented**: 1985 (Xilinx XC2064).
*   **Original Purpose**: FPGAs were invented as "glue logic" to connect different chips on a motherboard, and as a way to prototype ASICs before spending millions on a tape-out.
*   **Evolution**: As transistor density increased, FPGAs evolved from simple logic arrays into massive "System-on-Chips" (SoCs) containing hardened ARM processors, DSP slices, and high-speed transceivers.

### The GPU (Graphics Processing Unit)
*   **Invented**: Popularized in 1999 with the Nvidia GeForce 256.
*   **Original Purpose**: Pushing polygons and rendering 3D pixels for video games. Rendering a 4K screen requires doing the exact same math on 8 million pixels simultaneously.
*   **Evolution**: In 2006, Nvidia released **CUDA**, allowing developers to write general-purpose C++ code that ran on the GPU (GPGPU). This unlocked the GPU's massive parallelism for scientific compute and, eventually, neural networks.

### The TPU / ASIC (Tensor Processing Unit)
*   **Invented**: 2015 (Google TPU v1).
*   **Original Purpose**: While ASICs have existed forever (e.g., the chip inside your microwave), the AI-specific *TPU* was built by Google because running massive neural networks on standard CPUs was becoming mathematically impossible.
*   **Evolution**: TPUs sparked a wave of custom AI accelerators (AWS Inferentia, Groq) designed explicitly to multiply matrices as fast and efficiently as possible.

---

## 2. The AI Boom & Silicon Wars

In the late 2010s and early 2020s, the emergence of Large Language Models (LLMs) and Transformer architectures triggered a massive demand shock. 

*   **The Nvidia Monopoly**: Because researchers had been using CUDA for 15 years, Nvidia GPUs became the default hardware for *training* AI models. The world's largest companies bought hundreds of thousands of Hopper and Blackwell GPUs.
*   **The Power Crisis**: Modern GPUs can draw upwards of 700 to 1000 Watts *each*. Data centers physically cannot pull enough electricity from the grid to power them.
*   **The Inference Battleground**: While GPUs dominate *training* (creating the model), the industry is now shifting to *inference* (running the model for users). This is where the war is being fought. Companies are desperately seeking FPGA and TPU alternatives to escape Nvidia's pricing, reduce power consumption, and achieve lower latency.

---

## 3. Architectural Deep Dive

How do these chips actually process a neural network or a complex algorithm?

### The GPU: SIMD (Single Instruction, Multiple Data)
GPUs are masters of throughput. They have thousands of tiny cores. However, they rely on **SIMD**—they must execute the exact same instruction on a massive batch of data simultaneously. 
*   **The Flaw**: If you ask a GPU to process just *one* image or *one* token of text, it is terribly inefficient. It has high latency because it is waiting to build up a "batch" of 64 or 128 requests before it fires.

### The TPU: Systolic Arrays
TPUs use a hardwired "Systolic Array." Imagine a grid of calculators passing numbers to each other in a rhythmic, beating fashion (like a heart systole). 
*   **The Flaw**: It is mathematically rigid. It can multiply matrices with unmatched efficiency. But if AI researchers invent a new activation function or a completely new algorithm (like Spiking Neural Networks), the physical silicon of the TPU cannot adapt. It is a one-trick pony.

### The FPGA: Spatial Compute
FPGAs do not have "instructions." They do not run software. When you program an FPGA, you physically wire together logic gates to create a custom data path.
*   **The Advantage**: Data flows continuously from the input pin, through the logic gates, and out the output pin without ever hitting RAM or waiting for an OS interrupt. This is **Spatial Compute**.

---

## 4. Performance Matrix & Analysis

| Feature | GPU | TPU / ASIC | FPGA |
| :--- | :--- | :--- | :--- |
| **Flexibility** | High (Software programmable) | None (Fixed silicon) | High (Hardware reconfigurable) |
| **Latency** | Medium-High (Requires batching) | Low | **Ultra-Low (Deterministic)** |
| **Power Efficiency**| Poor (700W+) | **Ultimate** | Excellent |
| **Dev Time** | Days (Python/CUDA) | Years (Hardware Tape-out) | Months (RTL/HLS) |
| **Batch Size 1** | Terrible | Good | **Peak Efficiency** |

### The Batch Size Dilemma
This is the critical deciding factor in modern compute:
*   If you are training a model on billions of images, you want a **GPU**. You don't care if an individual image takes 500 milliseconds, as long as you process 10,000 images a second.
*   If you are an autonomous drone flying at 60mph, you cannot wait 500ms to identify a tree. You need a batch size of 1. You need the **FPGA**.

---

## 5. Conclusion: When to Use Which?

### Use the GPU When:
*   You are **training** massive foundation models.
*   Your ecosystem is heavily reliant on existing CUDA libraries.
*   You have workloads that easily parallelize into massive batches (e.g., rendering, offline video processing).

### Use the TPU / ASIC When:
*   You are deploying a massive, stable AI model (like Google Search) where the math will not change for years.
*   You have the massive capital required to justify fixed silicon development for the sake of long-term power efficiency.

### Use the FPGA When:
*   **High-Frequency Trading (HFT)**: You need to parse a network packet and execute a trade in under 500 *nanoseconds*.
*   **Evolving Algorithms**: You are deploying heavily quantized AI (e.g., 2-bit or 1-bit neural networks) that GPUs lack the hardware to process efficiently.
*   **Deterministic Latency**: You are building radar, medical imaging, or autonomous driving systems where a missed deadline means failure.
*   **Datacenter Interconnects**: You need a SmartNIC to parse custom protocols at 100Gbps line rate.
