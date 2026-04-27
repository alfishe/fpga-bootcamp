[← Home](../README.md)

# 10 — Embedded Linux on FPGA SoCs

Running Linux on FPGA SoCs — Cyclone V SoC, Zynq, PolarFire SoC, Agilex SoC. Covers the full software stack: SoC architecture from Linux's perspective, boot flow, HPS↔FPGA interaction (bridges, interrupts, DMA), device trees and FPGA Manager overlays, kernel driver patterns (UIO/VFIO/platform), and build systems + OTA updates.

**This section is the software companion to Section 01.** Where Section 01 describes the hardware, here you learn how to use it from Linux.

## Articles

| Article | Topic |
|---|---|
| [soc_linux_architecture.md](soc_linux_architecture.md) | SoC FPGA architecture from Linux's view: HPS/PS vs PL domains, bridge topology, memory maps, cache coherency (ACP vs non-coherent), cross-cutting power/reset/clock concerns |
| [boot_flow.md](boot_flow.md) | **Common overview**: Universal boot sequence, boot media matrix, SD card formatting, FPGA config decision framework, secure boot fundamentals, common failures |
| [boot_flow_intel_soc.md](boot_flow_intel_soc.md) | Intel/Altera deep dive: Cyclone V, Arria 10, Agilex, MAX 10. BSEL pins, preloader/mkpimage, FPP config, per-board specifics (DE10-Nano, MiSTer) |
| [boot_flow_xilinx_zynq.md](boot_flow_xilinx_zynq.md) | Xilinx deep dive: Zynq-7000, Zynq MPSoC, Versal. CSU/PMC boot, PCAP config, bootgen/BOOT.BIN, ATF/PMUFW, per-board specifics (ZedBoard, ZCU102) |
| [boot_flow_microchip_soc.md](boot_flow_microchip_soc.md) | Microchip deep dive: PolarFire SoC (RISC-V), SmartFusion2/IGLOO2. System Controller, HSS, OpenSBI, Flash-based FPGA config, Icicle Kit specifics |
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | **★ Common overview**: Four paths from CPU to FPGA (MMIO/ioremap, userspace mmap, IRQ, DMA). Bridge concept, cache coherency fundamentals, kernel code examples, shared ring buffer patterns |
| [hps_fpga_bridges_intel_soc.md](hps_fpga_bridges_intel_soc.md) | Intel deep dive: Cyclone V/Arria 10/Stratix 10/Agilex bridge addresses, device tree bindings, non-coherent DMA patterns, LWH2F vs H2F, FPGA interrupt numbers |
| [hps_fpga_bridges_xilinx_zynq.md](hps_fpga_bridges_xilinx_zynq.md) | Xilinx deep dive: Zynq-7000/MPSoC/Versal AXI port inventory, ACP cache coherency programming, GP vs HP vs HPC, device tree, worked example (DMA + ACP) |
| [hps_fpga_bridges_microchip_soc.md](hps_fpga_bridges_microchip_soc.md) | Microchip deep dive: PolarFire SoC FIC0/FIC1/FIC2, coherent-by-default model, RISC-V PLIC interrupts, no-maintenance shared memory patterns |
| [device_tree_and_overlays.md](device_tree_and_overlays.md) | Device tree for FPGA SoCs: static vs dynamic DT, reserved-memory carveouts, FPGA Manager configfs loading, device tree overlay compilation and application |
| [kernel_drivers_and_dma.md](kernel_drivers_and_dma.md) | Three driver patterns: UIO (30-line shim), platform driver (production), VFIO (userspace DMA via IOMMU). DMA Engine cyclic DMA, buffer type selection |
| [build_and_update.md](build_and_update.md) | Buildroot vs Yocto for FPGA SoCs: configuration examples, layer selection, SDK generation. OTA bitstream updates: A/B scheme with fallback, remote system update, secure boot integration |
