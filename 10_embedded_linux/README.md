[← Home](../README.md)

# 10 — Embedded Linux on FPGA SoCs

Running Linux on FPGA SoCs — Cyclone V SoC, Zynq, PolarFire SoC, Agilex SoC. Covers the full software stack: SoC architecture from Linux's perspective, boot flow, HPS↔FPGA interaction (bridges, interrupts, DMA), device trees and FPGA Manager overlays, kernel driver patterns (UIO/VFIO/platform), and build systems + OTA updates.

**This section is the software companion to Section 01.** Where Section 01 describes the hardware, here you learn how to use it from Linux.

## Articles

| Article | Topic |
|---|---|
| [soc_linux_architecture.md](soc_linux_architecture.md) | SoC FPGA architecture from Linux's view: HPS/PS vs PL domains, bridge topology, memory maps, cache coherency (ACP vs non-coherent), cross-cutting power/reset/clock concerns |
| [boot_flow.md](boot_flow.md) | Full boot sequence: Boot ROM → Preloader/SPL → U-Boot → Kernel → Userspace. When to configure FPGA at each stage. U-Boot FPGA commands, distro boot, MiSTer convention |
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | **★ The core of HPS↔FPGA interaction**: Four paths from CPU to FPGA (MMIO/ioremap, userspace mmap, IRQ, DMA). Complete kernel code examples for register access, interrupt handling, DMA setup. Cache coherency in practice, shared ring buffer patterns |
| [device_tree_and_overlays.md](device_tree_and_overlays.md) | Device tree for FPGA SoCs: static vs dynamic DT, reserved-memory carveouts, FPGA Manager configfs loading, device tree overlay compilation and application |
| [kernel_drivers_and_dma.md](kernel_drivers_and_dma.md) | Three driver patterns: UIO (30-line shim), platform driver (production), VFIO (userspace DMA via IOMMU). DMA Engine cyclic DMA, buffer type selection |
| [build_and_update.md](build_and_update.md) | Buildroot vs Yocto for FPGA SoCs: configuration examples, layer selection, SDK generation. OTA bitstream updates: A/B scheme with fallback, remote system update, secure boot integration |
