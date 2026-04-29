[<- Section Home](../README.md) · [<- Project Home](../../README.md)

# Commercial JTAG & Boundary Scan Tools

While open-source tools like OpenOCD are excellent for hobbyists and basic bring-up, the enterprise world relies on commercial JTAG solutions. These fall into two completely distinct categories that serve different purposes: **Production PCBA Testing (Boundary Scan)** and **High-End Hardware Debugging (Trace)**.

---

## 1. Production Boundary Scan (PCBA Testing)

These tools do not care about your C code or the Linux kernel. Their sole purpose is to use IEEE 1149.1 Boundary Scan (`EXTEST` and `SAMPLE`) to test the physical PCB for manufacturing defects (solder bridges, opens, missing passives) and to perform high-speed "gang programming" of flash memory on the assembly line.

### [XJTAG](https://www.xjtag.com/)
*   **Focus**: Ease of use, rapid test development, and seamless EDA integration (Altium, Mentor, Cadence).
*   **Hardware**: XJLink2 (USB-to-JTAG adapter).
*   **Software**: XJDeveloper (test creation), XJRunner (production line execution), XJAnalyser (visual pin toggling).
*   **Key Specs**: Up to 166 MHz TCK, supports up to 4 TAPs per XJLink2.
*   **Best For**: Medium-to-high volume manufacturing, automated detection of BGA shorts/opens, and companies that want engineers to generate test vectors quickly without writing custom scripts.
*   **Not Applicable To**: CPU code debugging, real-time instruction tracing.

### [Corelis](https://www.corelis.com/)
*   **Focus**: Enterprise-grade performance, high-throughput concurrent testing, and massive scalability for Automated Test Equipment (ATE) integration.
*   **Hardware**: NetUSB-1149.1, PCIe-1149.1, and PXIe-1149.1. Often paired with "ScanTAP" intelligent pods to support up to 8 independent TAPs concurrently.
*   **Software**: ScanExpress Suite (TPG for test generation, Runner for execution, JET for JTAG Embedded Test).
*   **Key Specs**: Sustained 80–100 MHz TCK frequencies. Advanced automatic signal delay compensation for long factory cables.
*   **Best For**: High-throughput factory lines, concurrent "gang" programming of multiple target boards simultaneously, and PXI-based test racks.

### [JTAG Technologies](https://www.jtag.com/)
*   **Focus**: Deep integration with legacy ATE setups (Teradyne, Spea) and pioneering structural testing methodologies.
*   **Hardware**: DataBlaster series (PCI, PCIe, PXI, USB).
*   **Software**: ProVision (development), JTAG Visualizer.
*   **Key Specs**: Highly modular hardware architecture capable of sustaining maximum throughput for massive flash programming operations.
*   **Best For**: Companies with existing Teradyne/Spea flying probe or bed-of-nails testers that want to augment physical probes with boundary scan.

### [Göpel electronic](https://www.goepel.com/)
*   **Focus**: Highly complex embedded system testing, combining JTAG with structural test and optical inspection.
*   **Hardware**: SCANFLEX II series (modular controllers).
*   **Software**: SYSTEM CASCON.
*   **Key Specs**: Highly synchronized multi-TAP control, embedded instrumentation capabilities (VarioTAP / ChipVORX).
*   **Best For**: Complex automotive and aerospace PCBs requiring rigorous validation combining boundary scan with processor emulation.

---

## 2. High-End CPU/SoC Debugging (Trace Tools)

These tools do not care about PCB solder joints. They use the JTAG interface purely as a physical transport layer to talk to the ARM CoreSight DAP or RISC-V Debug Module. They are designed to halt cores, inspect memory, and capture real-time instruction trace streams (ETM/PTM) to debug race conditions and kernel panics.

### [Lauterbach TRACE32](https://www.lauterbach.com/)
*   **Focus**: The absolute gold standard for embedded software debugging. If you are bringing up a custom Linux kernel or hypervisor on a new SoC, Lauterbach is the industry default.
*   **Hardware**: PowerDebug (basic JTAG/SWD), PowerTrace (captures high-speed parallel/serial trace data directly from the SoC).
*   **Software**: TRACE32 (infamous for its archaic UI, but unmatched in raw capability).
*   **Best For**: OS bring-up, debugging multi-core race conditions, analyzing Linux kernel panics, and non-intrusive real-time profiling.
*   **Not Applicable To**: PCBA boundary scan structural testing. Lauterbach is a software engineering tool, not a manufacturing tool.

### [ARM DSTREAM](https://developer.arm.com/Tools%20and%20Software/DSTREAM)
*   **Focus**: Official tooling from ARM. Highly optimized for ARM architectures.
*   **Hardware**: DSTREAM-ST (standard debug) and DSTREAM-PT (high-bandwidth parallel trace).
*   **Software**: Arm Development Studio (Arm DS).
*   **Key Specs**: Up to 180 MHz JTAG clock, massive internal trace buffers (up to 8GB on the PT model).
*   **Best For**: Pure ARM SoC bring-up and bare-metal firmware development on complex multi-core Cortex-A/R/M clusters.

---

## 3. Mid-Range & Development Tools

### [Segger J-Link](https://www.segger.com/products/debug-probes/j-link/)
*   **Focus**: The ubiquitous, cost-effective developer tool for microcontrollers and simple SoC debug.
*   **Hardware**: J-Link BASE, PLUS, PRO, and ULTRA+.
*   **Software**: Ozone (debugger), J-Flash (production programming).
*   **Best For**: Cortex-M development, flashing firmware, and basic GDB server capabilities for Zynq/Cyclone V.
*   **Not Applicable To**: Massive multi-core trace analysis or boundary scan structural testing.

### The Open Source Fallback: OpenOCD + FTDI
*   **Focus**: Zero-cost prototyping and CI/CD automation.
*   **Hardware**: Any FT2232-based adapter (e.g., Olimex ARM-USB-TINY-H, Digilent JTAG-HS3).
*   **Software**: [OpenOCD](https://openocd.org/).
*   **Best For**: Automated test runners (GitLab CI), hobbyist development, and scripting simple boundary scan SVF/XSVF playback.

---

## Quick Decision Matrix

| Goal | Recommended Tool Tier | Example Vendors |
|---|---|---|
| Detect solder shorts on BGA pins without booting the CPU | **PCBA Boundary Scan** | XJTAG, Corelis, JTAG Tech |
| Gang-program QSPI flash on 8 boards simultaneously on the assembly line | **PCBA Boundary Scan** | Corelis, Göpel |
| Debug a Linux kernel panic that occurs randomly every 4 hours | **High-End Trace** | Lauterbach, ARM DSTREAM |
| Flash a bare-metal RTOS onto a Cortex-M4 / Zynq-7000 | **Mid-Range Debug** | Segger J-Link |
| Automate bitstream loading in a Jenkins/GitLab pipeline | **Open Source** | OpenOCD + FTDI adapter |
