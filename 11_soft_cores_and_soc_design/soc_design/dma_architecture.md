[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# DMA Architecture — Data Movement in FPGA SoCs

DMA engines are the unsung heroes of FPGA SoC performance — offloading bulk data movement from the CPU, which is often 10–100× slower at memory copies than dedicated DMA.

---

## DMA Topologies

| Architecture | Description | Best For | LUT Cost |
|---|---|---|---|
| **Centralized DMA** | One DMA engine serves all peripherals | Simple SoCs, \u003c4 data streams | ~2,000 LUTs |
| **Distributed DMA** | Each peripheral has its own DMA | High-throughput, independent streams | ~1,000 LUTs per instance |
| **Scatter-Gather DMA** | Descriptor chain in memory → DMA follows linked list | Complex buffer management, network stacks | ~3,000 LUTs |
| **AXI CDMA** (Central DMA) | Xilinx IP: memory-to-memory copy | Memory remapping, frame buffer copy | Vendor IP |
| **AXI XDMA** (PCIe DMA) | PCIe → AXI bridge with DMA | FPGA-as-PCIe-accelerator | Vendor IP |

## Descriptor Chains

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Descriptor 0 │────►│ Descriptor 1 │────►│ Descriptor 2 │
│ src: 0x1000  │     │ src: 0x2000  │     │ src: 0x3000  │
│ dst: 0x8000  │     │ dst: 0x9000  │     │ dst: 0xA000  │
│ len: 1024    │     │ len: 2048    │     │ len: 512     │
│ next: 0x400  │     │ next: 0x500  │     │ next: NULL   │
└──────────────┘     └──────────────┘     └──────────────┘
```

The CPU writes descriptors to shared memory, then kicks the DMA engine. The DMA follows the linked list autonomously — zero CPU involvement per transfer.

## Coherency Considerations

| DMA Type | Coherency | When to Use |
|---|---|---|
| **Non-coherent DMA** | CPU must flush/invalidate caches before/after | Default on most FPGA SoCs |
| **ACP-coherent DMA** (Zynq-7000) | FPGA accesses CPU cache via Snoop Control Unit | Shared data structures between CPU and FPGA |
| **AXI4 ACE-Lite** (Zynq Ultrascale+) | Coherent transactions at the bus level | Multi-core SoCs with FPGA accelerators |

## iDMA — Open-Source Modular DMA

ETH Zürich's **iDMA** (github.com/pulp-platform/iDMA) is a modular, open-source DMA engine:
- Backend-agnostic (AXI, TileLink, custom interconnect)
- 1D/2D transfers with configurable burst size
- Written in SystemVerilog, FPGA-proven on PULP platform

---

## Original Stub Description

DMA in SoC: centralized vs distributed, descriptor chains, scatter-gather, AXI DMA vs CDMA vs XDMA, coherency (ACP, AXI4 ACE), iDMA (ETH Zürich modular open-source DMA)

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
