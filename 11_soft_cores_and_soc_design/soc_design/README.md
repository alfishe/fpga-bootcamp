[← Section Home](../README.md) · [← Project Home](../../README.md)

# 11-E — SoC Architecture & Design

Building a complete system-on-chip — the art of connecting CPU cores, memory, peripherals, and accelerators into a coherent, performant51 74→system that boots and runs software. This is the capstone of the soft-core track.

## Index

| File | Topic |
|---|---|
| [bus_matrix_design.md](bus_matrix_design.md) | Bus matrix design: topology patterns (shared bus, crossbar, multi-layer), master/slave classification, address decoding, concurrent access and bandwidth analysis, APB/AHB bridge for low-speed peripherals |
| [memory_map_design.md](memory_map_design.md) | Memory map planning: base address assignment, aperture sizing, aliasing, MMIO vs memory regions, Linux device tree binding, reserved regions, memory protection |
| [interrupt_routing.md](interrupt_routing.md) | Interrupt architecture: PLIC/APIC design, vectoring, level vs edge, multi-core affinity, soft IRQs, priority inversion avoidance |
| [dma_architecture.md](dma_architecture.md) | DMA in SoC: centralized vs distributed, descriptor chains, scatter-gather, AXI DMA vs CDMA vs XDMA, coherency (ACP, AXI4 ACE), iDMA (ETH Zürich modular open-source DMA) |
| [chipyard_rocket_chip.md](chipyard_rocket_chip.md) | Rocket Chip / Chipyard: Scala/Chisel SoC generation framework, TileLink protocol, Diplomacy parameter negotiation, connecting custom accelerators (RoCC), FPGA mapping flow |
| [multi_core_coherency.md](multi_core_coherency.md) | Multi-core SoCs on FPGA: SMP challenges, cache coherency (snooping, directory), AXI4 ACE-Lite, when NOT to go multi-core, practical FPGA resource limits |
