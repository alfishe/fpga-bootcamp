[← Section Home](../README.md) · [← Project Home](../../README.md)

# 06-E — PCIe Blocks

PCI Express is the high-bandwidth link between FPGA and host system. This folder covers the integrated hard PCIe blocks found in modern FPGAs, from endpoint configuration to DMA engines.

## Index

| File | Topic |
|---|---|
| [pcie_hard_blocks.md](pcie_hard_blocks.md) | Integrated PCIe hard blocks: endpoint vs root port, Gen1–Gen5 comparison (Xilinx UltraScale+ 16G, Versal 32G; Intel Arria 10/Stratix 10/Agilex Gen4/Gen5; Microchip PolarFire Gen2) |
| [pcie_configuration.md](pcie_configuration.md) | PCIe IP configuration: BAR setup (32/64-bit, prefetchable, expansion ROM), MSI/MSI-X, max payload size, AER, AXI4/Avalon bridge interface |
| [pcie_dma.md](pcie_dma.md) | DMA for PCIe: XDMA (Xilinx), Intel DMA IP, descriptor rings, scatter-gather, host-to-card and card-to-host throughput, performance analysis |
