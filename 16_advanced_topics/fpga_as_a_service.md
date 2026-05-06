[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# FPGA as a Service (FaaS): The Cloud Hardware Landscape

FPGA as a Service (FaaS) is a cloud computing model that allows developers to rent bare-metal or virtualized access to Field Programmable Gate Arrays by the hour. It abstracts away the massive upfront Capital Expenditure (CAPEX) of hardware procurement and allows hyperscale horizontal scaling of custom silicon logic. However, FaaS comes with extreme vendor lock-in, network latency overhead, and a custom SDLC that differs fundamentally from bare-metal FPGA development.

> [!NOTE]
> For hardware acceleration architecture patterns (streaming, SmartNIC, edge AI, HFT), see [Hardware Acceleration](hardware_acceleration.md). For FPGA vs GPU vs TPU compute comparison, see [FPGA vs GPU vs TPU](fpga_vs_gpu_vs_tpu.md).

---

## 1. The Genesis of Cloud FPGAs

Before 2016, FPGAs were largely confined to on-premises enterprise data centers, defense applications, and specialized high-frequency trading (HFT) collocation facilities.

**The Hyperscaler Precursors (2010–2015)**
The concept of FPGAs in the cloud began as internal hyperscaler infrastructure. 
*   **Microsoft's Project Catapult (2014):** Microsoft deployed Altera FPGAs across Bing servers to accelerate search ranking algorithms. By 2015, they integrated FPGAs into their SmartNICs (AccelNet) to offload Hyper-V network virtualization.
*   **IBM Supervessel (2015):** IBM offered an early proof-of-concept cloud allowing academic researchers to accelerate workloads on attached FPGAs via OpenPOWER architecture.

**The Public Cloud Explosion (2016–2018)**
The shift to public FaaS occurred rapidly:
*   **AWS F1 Instances (Nov 2016):** AWS shocked the industry at re:Invent 2016 by launching the EC2 F1 instance (Xilinx Virtex UltraScale+). For the first time, anyone with a credit card could rent an enterprise-grade FPGA for $1.65/hour.
*   **Alibaba Cloud F3 (May 2018):** Alibaba launched their "Shuntian" platform, heavily pushing FaaS for financial risk analysis and genomics.
*   **Azure Project Brainwave (May 2018):** Microsoft exposed their internal Intel Stratix 10 FPGA fleet for real-time AI inferencing through Azure Cognitive Services.

---

## 2. Current Hardware Landscape (2026)

Today, the major public cloud providers offer highly standardized FPGA instances.

| Provider & Instance | FPGA Hardware | Target Workloads | Pricing (On-Demand) | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **AWS EC2 F2** (`f2.12xlarge`) | 2× AMD Virtex UltraScale+ HBM | Genomics, Video Transcoding, Custom DSP | ~$3.96/hr (US-East) | Active. The legacy F1 instances reached End-of-Life in Dec 2025. |
| **Azure NP-Series** (`Standard_NP10s`) | 1× Xilinx Alveo U250 | Real-time AI scoring, Database Acceleration | ~$3.20/hr (East US) | **Retiring May 2027.** Microsoft ended reservations in April 2026. |
| **Alibaba Cloud F3** (`ecs.f3`) | Xilinx Virtex UltraScale+ VU9P | Genomics, Financial Risk, Video Processing | Varies by region | Active. Pay-As-You-Go or Subscription. |

### Instance Selection Guide

| Need | Recommended Instance | Why |
|---|---|---|
| Maximum FPGA resources (2× VU9P) | AWS F2 (`f2.12xlarge`) | Two FPGAs, HBM for memory-bound workloads |
| Cost-effective single FPGA | Alibaba F3 | Lowest hourly rate for single VU9P |
| AI inferencing only | Azure Cognitive Services | No FPGA programming required — use managed API |
| Legacy F1 designs | Migrate to F2 | F1 EOL Dec 2025; F2 uses same AMD architecture |

---

## 3. The Custom SDLC: Cloud Shells and Lock-in

Developing for a Cloud FPGA is fundamentally different from developing for a bare-metal FPGA on your desk. You cannot flash the raw silicon; you must integrate with the provider's **"Shell"** architecture.

### The Shell vs. Custom Logic
Cloud providers divide the FPGA die into two static regions:
1.  **The Shell (Provider Logic):** Takes up ~20% of the FPGA. This is locked, pre-synthesized logic provided by AWS/Azure. It handles PCIe enumeration, DMA transfers to the host CPU, DDR4 memory controllers, and chip health monitoring (thermal throttling).
2.  **Custom Logic (Your Design):** The remaining ~80% of the FPGA where your RTL or HLS design sits.

### The Development Stack (e.g., AWS FPGA HDK)
You do not use standard Vivado to generate a `.bit` file. Instead, the workflow is:
1.  **Develop:** Write your Custom Logic in Verilog/VHDL or High-Level Synthesis (C/C++ via Vitis/OpenCL).
2.  **Integrate:** Wrap your logic in the provider-specific AXI-bus interfaces required to talk to the Cloud Shell.
3.  **Synthesize:** Run Vivado (usually provided free on a provider's Developer VM) to synthesize against the specific Shell version.
4.  **DRC & Image Generation:** Submit your synthesized design via CLI. The cloud provider runs deep Design Rule Checks (DRC) to ensure your bitstream won't physically damage the server (e.g., thermal limits or malicious PCIe writes).
5.  **AFI Creation:** If passed, AWS generates an **Amazon FPGA Image (AFI)**. You load this AFI onto an EC2 instance dynamically using the `fpga-load-local-image` command.

> [!WARNING]
> **Extreme Vendor Lock-in:** An AFI compiled for AWS F2 cannot be deployed on Azure or Alibaba. The bitstream is physically bound to the AWS PCIe Shell. Migrating to another cloud provider requires rewriting your top-level AXI wrappers and entirely re-synthesizing the design (a process taking days to weeks).

### Shell Comparison Across Providers

| Feature | AWS F2 Shell | Azure NP Shell | Alibaba F3 Shell |
|---|---|---|---|
| Shell region | ~20% of FPGA | ~20% of FPGA | ~15% of FPGA |
| Custom logic region | ~80% | ~80% | ~85% |
| DMA engine | Provided (AXI DMA) | Provided | Provided |
| PCIe interface | Shell-managed | Shell-managed | Shell-managed |
| DDR access | Shell DDR controller | Shell DDR controller | Shell DDR controller |
| DRC checks | Mandatory (thermal, PCIe) | Mandatory | Mandatory |
| Image format | AFI (Amazon FPGA Image) | Custom bitstream | Custom bitstream |
| Shell source | Open-source (GitHub) | Limited | Limited |

---

## 4. Market Positioning: Why rent an FPGA?

Cloud providers market FaaS primarily for highly parallel, data-streaming workloads that cannot be effectively batched on GPUs:

| Workload | Why FPGA | Typical Speedup vs CPU |
|---|---|---|
| **Genomics (BWA-MEM, Smith-Waterman)** | Massive integer dynamic programming, custom scoring matrices | 30× |
| **Video Transcoding** | Hardware-encode 4K/8K (H.264/H.265) at line rate | 10–20× |
| **Cryptography & ZKP** | Custom hashing pipelines, MSM acceleration | 5–15× |
| **Financial Risk (Monte Carlo)** | Deep spatial pipelines for options pricing | 10–20× |
| **Database Acceleration** | Predicate pushdown, columnar scan offload | 3–8× |

---

## 5. Economic Analysis: FaaS vs. On-Premises Ownership

When architecting a solution, the decision between FaaS and buying on-premises hardware comes down to two major constraints: **Economics** and **I/O Latency**.

### The CAPEX vs. OPEX Break-Even
An AWS F2 instance (`f2.12xlarge` with 2 FPGAs) costs ~$3.96/hour. Running it 24/7/365 results in an OPEX of **~$34,600 per year**.

Purchasing an equivalent high-end PCIe FPGA board (like an AMD Alveo U250) costs roughly **$8,000 to $15,000** (CAPEX).

**The Conclusion:** If your workload runs 24/7, purchasing on-premises hardware pays for itself in less than 6 months. **FaaS is financially devastating for steady-state workloads.**

**When FaaS Wins:**
*   **Bursty Workloads:** You only need 1,000 FPGAs for 4 hours a month to process a massive batch of genomic data.
*   **Evaluation & CI/CD:** Renting an F2 instance to verify your RTL design before dropping $15,000 on a physical board.
*   **Hardware Lifecycle Avoidance:** Avoiding the depreciation and physical maintenance of PCIe cards.

### The Virtualization & Network Bottleneck
> [!IMPORTANT]
> **The I/O Reality:** Cloud FPGAs sit behind the cloud provider's network virtualization and hypervisor stack. If you send a network packet to an AWS F2 instance, it goes through the AWS Nitro VPC network -> Host CPU -> PCIe Bus -> FPGA Shell -> Your Logic.

This adds **100–500 µs of latency** before your FPGA even sees the data. For applications like High-Frequency Trading (HFT) or O-RAN fronthaul—which rely on FPGAs explicitly to achieve <100ns latency by terminating network optical links directly into the FPGA transceivers—FaaS is entirely useless. You cannot physically plug an SFP28 fiber cable into an AWS instance.

---

## 6. The Shift to Managed Services

Raw FaaS adoption has grown slower than GPU compute due to the steep learning curve of hardware design and the intense vendor lock-in of proprietary Cloud Shells.

Consequently, hyperscalers are pivoting from offering "Raw FaaS" to **Managed Accelerated Services**. Rather than renting an FPGA and struggling with Vivado synthesis, customers use APIs (like AWS MediaConvert or Alibaba Financial Risk endpoints). The hyperscaler routes the API call to a massive, internal fleet of FPGAs, entirely shielding the end-user from the hardware SDLC.

For developers who *do* need custom logic, FaaS remains an incredible tool for OPEX-based prototyping, provided the workload does not require bare-metal sub-microsecond networking.

---

## Best Practices

1. **Never use FaaS for 24/7 steady-state workloads** — the OPEX exceeds CAPEX in under 6 months; buy on-premises hardware instead
2. **Use FaaS for bursty, time-limited workloads** — genomics batch processing, CI/CD verification, and short-lived algorithm exploration
3. **Decouple your RTL from the Shell** — keep your core logic in a vendor-agnostic AXI4-Stream wrapper; only the top-level shell adapter needs to change between AWS/Azure/Alibaba
4. **Use the provider's free synthesis VM** — AWS provides a free Developer AMI with Vivado pre-installed; don't pay for your own synthesis license
5. **Test DRC locally before submitting** — use the AWS `drc_checks.tcl` script locally before submitting to the cloud; DRC failures waste time and may count against quotas

---

## Pitfalls

### 1. Shell Version Pinning
AWS and Azure update their Shell versions periodically. An AFI compiled against Shell v1.4 may not load on an instance running Shell v1.6. There is no backward compatibility guarantee.

**Fix:** Pin your Shell version in the HDK configuration, and re-synthesize when the provider announces a Shell update. Always test against the latest Shell before production deployment.

### 2. Partial Reconfiguration Not Supported
Most cloud FaaS providers do not allow partial reconfiguration of the FPGA. You must load a complete AFI for any change, even a minor RTL update.

**Fix:** Accept this limitation. If you need partial reconfiguration, use on-premises hardware with DFX (Dynamic Function eXchange).

### 3. Debug Access is Limited
You cannot attach Vivado Hardware Manager or SignalTap to a cloud FPGA. Debug visibility is limited to the Shell's built-in telemetry and your own printf-style logging via DMA to host memory.

**Fix:** Implement a comprehensive telemetry module in your custom logic that DMA-logs key internal states to host memory. Use the AWS FPGA Management Tools for Shell-level health checks.

---

## Sources

- [AWS EC2 F2 Instances and FPGA Developer Kit](https://aws.amazon.com/ec2/instance-types/f2/)
- [Azure NP-Series Retirement Notice | Microsoft](https://learn.microsoft.com/en-us/azure/virtual-machines/np-series-retirement)
- [Alibaba Cloud FPGA Instances (F3) | Alibaba Cloud](https://www.alibabacloud.com/help/en/ecs/user-guide/f3-instances)
- [Project Brainwave | Microsoft Research](https://www.microsoft.com/en-us/research/project/project-brainwave/)
- [Hardware Acceleration](hardware_acceleration.md) — Architecture patterns
- [FPGA vs GPU vs TPU](fpga_vs_gpu_vs_tpu.md) — Compute comparison
