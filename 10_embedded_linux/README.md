[← Home](../README.md)

# 10 — Embedded Linux on FPGA SoCs

Running Linux on FPGA SoCs — Cyclone V SoC, Zynq, PolarFire SoC, Agilex SoC. Covers the full software stack: SoC architecture from Linux's perspective, boot flow, HPS↔FPGA interaction (bridges, interrupts, DMA), device trees and FPGA Manager overlays, kernel driver patterns (UIO/VFIO/platform), and build systems + OTA updates.

**This section is the software companion to Section 01.** Where Section 01 describes the hardware, here you learn how to use it from Linux.

## Index

| Folder / Article | Topic |
|---|---|
| [overview.md](overview.md) | **Architecture Overview**: The "why" of Linux on FPGA, build systems (Yocto vs Buildroot), vendor distributions, CPU architectures, and common pitfalls |
| **[01_architecture/](01_architecture/)** | |
| └ [soc_linux_architecture.md](01_architecture/soc_linux_architecture.md) | SoC FPGA architecture from Linux's view: HPS/PS vs PL domains, bridge topology, memory maps, cache coherency (ACP vs non-coherent), cross-cutting power/reset/clock concerns |
| **[02_boot_flow/](02_boot_flow/)** | |
| └ [boot_flow.md](02_boot_flow/boot_flow.md) | **Common overview**: Universal boot sequence, boot media matrix, SD card formatting, FPGA config decision framework, secure boot fundamentals, common failures |
| └ [uboot.md](02_boot_flow/uboot.md) | **U-Boot deep dive**: SSBL role, SPL vs full U-Boot, FPGA configuration from U-Boot, device tree handoff, environment scripting, board-specific setup, cross-vendor comparison |
| └ [boot_flow_intel_soc.md](02_boot_flow/boot_flow_intel_soc.md) | Intel/Altera deep dive: Cyclone V, Arria 10, Agilex, MAX 10. BSEL pins, preloader/mkpimage, FPP config, per-board specifics (DE10-Nano, MiSTer) |
| └ [boot_flow_xilinx_zynq.md](02_boot_flow/boot_flow_xilinx_zynq.md) | Xilinx deep dive: Zynq-7000, Zynq MPSoC, Versal. CSU/PMC boot, PCAP config, bootgen/BOOT.BIN, ATF/PMUFW, per-board specifics (ZedBoard, ZCU102) |
| └ [boot_flow_microchip_soc.md](02_boot_flow/boot_flow_microchip_soc.md) | Microchip deep dive: PolarFire SoC (RISC-V), SmartFusion2/IGLOO2. System Controller, HSS, OpenSBI, Flash-based FPGA config, Icicle Kit specifics |
| **[03_hps_fpga_bridges/](03_hps_fpga_bridges/)** | |
| └ [hps_fpga_bridges.md](03_hps_fpga_bridges/hps_fpga_bridges.md) | **★ Common overview**: Four paths from CPU to FPGA (MMIO/ioremap, userspace mmap, IRQ, DMA). Bridge concept, cache coherency fundamentals, kernel code examples, shared ring buffer patterns |
| └ [hps_fpga_bridges_intel_soc.md](03_hps_fpga_bridges/hps_fpga_bridges_intel_soc.md) | Intel deep dive: Cyclone V/Arria 10/Stratix 10/Agilex bridge addresses, device tree bindings, non-coherent DMA patterns, LWH2F vs H2F, FPGA interrupt numbers |
| └ [hps_fpga_bridges_xilinx_zynq.md](03_hps_fpga_bridges/hps_fpga_bridges_xilinx_zynq.md) | Xilinx deep dive: Zynq-7000/MPSoC/Versal AXI port inventory, ACP cache coherency programming, GP vs HP vs HPC, device tree, worked example (DMA + ACP) |
| └ [hps_fpga_bridges_microchip_soc.md](03_hps_fpga_bridges/hps_fpga_bridges_microchip_soc.md) | Microchip deep dive: PolarFire SoC FIC0/FIC1/FIC2, coherent-by-default model, RISC-V PLIC interrupts, no-maintenance shared memory patterns |
| **[04_drivers_and_dma/](04_drivers_and_dma/)** | |
| └ [device_tree_and_overlays.md](04_drivers_and_dma/device_tree_and_overlays.md) | Device tree for FPGA SoCs: static vs dynamic DT, reserved-memory carveouts, FPGA Manager configfs loading, device tree overlay compilation and application |
| └ [fpga_driver_patterns.md](04_drivers_and_dma/fpga_driver_patterns.md) | The definitive guide to FPGA IP drivers. Covers `/dev/mem`, UIO, VFIO, Kernel Platform Drivers, and the Linux DMA Engine API, with pros/cons and decision matrix. |
| **[05_build_systems/](05_build_systems/)** | |
| └ [build_and_update.md](05_build_systems/build_and_update.md) | OTA bitstream updates: A/B scheme with fallback, remote system update, secure boot integration |
| └ [yocto_petalinux_deep_dive.md](05_build_systems/yocto_petalinux_deep_dive.md) | Yocto bitbake internals, meta-user layers, and PetaLinux wrappers |
| └ [buildroot_deep_dive.md](05_build_systems/buildroot_deep_dive.md) | Buildroot BR2_EXTERNAL trees for minimal SoC deployments |
