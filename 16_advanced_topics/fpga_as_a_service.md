[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# FPGA as a Service (FaaS) & Cloud FPGAs

Hardware acceleration is increasingly moving to the cloud, allowing developers to rent massive FPGA compute power by the hour.

## The Cloud FPGA Landscape (2026)

### AWS EC2 F2 Instances
*   **Hardware**: AMD Virtex UltraScale+ HBM FPGAs paired with 3rd-gen AMD EPYC CPUs.
*   **Pricing (April 2026)**: ~$3.96/hr for On-Demand `f2.12xlarge` (2 FPGAs).
*   **Note**: The original F1 instances reached End-of-Life in December 2025. All new development targets the F2 platform.

### Global Provider Matrix (April 2026)

| Provider & Instance | FPGA Hardware | Target Workloads | Pricing (On-Demand) | Status / Notes |
|---|---|---|---|---|
| **AWS EC2 `f2.12xlarge`** | 2x AMD Virtex UltraScale+ HBM | Genomics, Video Transcoding, High-Bandwidth DSP | **~$3.96 / hr** (US-East) | Active. The legacy F1 instances reached End-of-Life in Dec 2025. All new AWS development targets F2. |
| **Azure `Standard_NP10s`** | 1x Xilinx Alveo U250 | Real-time AI scoring (Azure ML), Database Acceleration | **~$3.20 / hr** (East US) | **Retiring May 2027.** Microsoft ended reservations in April 2026 and recommends migrating to NDv2 or NC-series GPUs. |
| **Alibaba Cloud `ecs.f3`** | Xilinx Virtex UltraScale+ VU9P | Genomics, Financial Risk Analysis, Video Processing | **Varies by region** | Active. Available via Pay-As-You-Go or Subscription. Pricing underwent global adjustments in March 2026. |

> [!WARNING]
> **Vendor Lock-in:** Developing for Cloud FPGAs introduces massive vendor lock-in. An Amazon FPGA Image (AFI) compiled for AWS F2 cannot be deployed on Azure or Alibaba. You are locked into the provider's specific PCIe shell, DMA drivers, and SDK (e.g., AWS FPGA HDK).

*(This is a stub. Expand with a guide on using the AWS FPGA Developer AMI and generating AFI images.)*
