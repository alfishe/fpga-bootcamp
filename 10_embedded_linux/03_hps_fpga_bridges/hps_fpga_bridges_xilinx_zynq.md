[← Section Home](../README.md) · [← Common Overview](hps_fpga_bridges.md) · [← Project Home](../../README.md)

# Xilinx Zynq / MPSoC / Versal — PS-PL Interface Programming

> [!NOTE]
> This article covers the **Linux software perspective** — AXI port addresses, device tree bindings, ACP coherency usage, and driver patterns. For hardware architecture (block diagrams, signal-level detail), see [02_architecture/soc/hps_fpga_xilinx_zynq.md](../02_architecture/soc/hps_fpga_xilinx_zynq.md).

Xilinx provides the richest set of PS-PL interfaces in the industry. Unlike Intel's fixed four-bridge model, Xilinx scales from 9 AXI interfaces on Zynq-7000 to a hard NoC mesh on Versal. Critically, Xilinx offers **optional cache coherency** through the ACP (Accelerator Coherency Port).

---

## Port Inventory and Address Maps

```
┌─────────────────────────────────────┐
│      Xilinx Processing System       │
│  ┌─────────┐    ┌───────────────┐   │
│  │ Dual/   │    │   L2 Cache    │   │
│  │ Quad    │◄──►│  (SCU/CCI)    │   │
│  │ Cortex  │    └───────┬───────┘   │
│  └────┬────┘            │           │
│       │                 │           │
│  ┌────▼─────────────────▼────┐      │
│  │  AXI Interconnect / NoC   │      │
│  └────┬────┬────┬────┬───────┘      │
└───────┼────┼────┼────┼──────────────┘
        │    │    │    │
┌───────┼────┼────┼────┼──────────────┐
│       ▼    ▼    ▼    ▼             │
│  PL (FPGA Fabric)                  │
│   M_AXI_GP    S_AXI_HP   S_AXI_ACP │
│   (PS→PL)     (PL→DDR)   (cache)   │
└────────────────────────────────────┘
```

### Zynq-7000 AXI Ports

| Port | Direction | Width | Address Range | Purpose | Linux Use |
|---|---|---|---|---|---|
| **M_AXI_GP0** | PS → PL | 32-bit | `0x4000_0000` – `0x7FFF_FFFF` | General-purpose control | `ioremap()` for FPGA registers |
| **M_AXI_GP1** | PS → PL | 32-bit | `0x8000_0000` – `0xBFFF_FFFF` | Second GP port | Additional register maps |
| **S_AXI_HP0–HP3** | PL → PS | 64-bit | DDR (0x0000_0000+) | High-performance PL→DDR | DMA destination buffers |
| **S_AXI_ACP** | PL → PS | 64-bit | Cache-coherent | Cache-coherent PL access | Shared data structures |

### Zynq UltraScale+ MPSoC AXI Ports

| Port | Direction | Width | Notes |
|---|---|---|---|
| **M_AXI_HPM0/HPM1** | PS → PL | 128-bit | Replaces GP ports on MPSoC; higher bandwidth |
| **S_AXI_HP0–HP3** | PL → PS | 128-bit | High-performance PL→DDR |
| **S_AXI_HPC0/HPC1** | PL → PS | 128-bit | High-Performance Coherent — same as HP but with ACP coherency |
| **S_AXI_ACE** | PL → PS | 128-bit | Full ACE-Lite coherency (for CPU-like masters) |

### Versal AXI Ports

Versal replaces the fixed AXI ports with a **programmable NoC (Network-on-Chip)**. PL masters connect to NoC Master Units (NMUs); PS slaves connect to NoC Slave Units (NSUs). The address map is defined at design time in the NoC compiler.

---

## Device Tree Bindings

### Zynq-7000 — Simple Register Peripheral (GP0)

```dts
// FPGA peripheral at GP0 offset 0x1000_0000
// PS physical address = 0x4000_0000 + 0x1000_0000 = 0x5000_0000

amba {
    myfpga: myfpga@50000000 {
        compatible = "mycompany,myfpga-core";
        reg = <0x50000000 0x10000>;
        interrupts = <0 29 IRQ_TYPE_LEVEL_HIGH>;  // PL→PS IRQ #0
        interrupt-parent = <&intc>;
    };
};
```

### MPSoC — HPM0 Peripheral

```dts
// MPSoC: FPGA peripheral connected to HPM0 at offset 0x2000_0000
// Example: HPM0 base is typically 0xA000_0000 or configurable

myfpga: myfpga@a2000000 {
    compatible = "mycompany,myfpga-core";
    reg = <0x0 0xa2000000 0x0 0x10000>;  // 64-bit addresses
    interrupts = <0 89 IRQ_TYPE_LEVEL_HIGH>;
};
```

---

## ACP: Cache-Coherent FPGA Access

The **Accelerator Coherency Port (ACP)** is Xilinx's killer feature: it lets the FPGA participate in the CPU's cache coherency protocol. When the FPGA reads or writes through ACP, it sees the same data as the CPU — no explicit cache flushes needed.

```c
// With ACP: CPU writes data, FPGA reads it — no dma_sync needed

struct shared_data {
    u32 cmd;
    u32 param;
    u32 result;
    u8  payload[4096];
};

// Allocate in normal cacheable memory
struct shared_data *shared = kzalloc(sizeof(*shared), GFP_KERNEL);

// CPU fills command
shared->cmd = CMD_PROCESS;
shared->param = 0x42;

// ACP ensures FPGA sees this immediately — no cache flush

// Tell FPGA to start
iowrite32(START_FLAG, fpga_regs + CTRL_REG);

// Wait for FPGA to finish (interrupt or polling)
wait_for_completion(&fpga_done);

// ACP ensures CPU sees FPGA's writes — no cache invalidate
// shared->result and shared->payload are immediately visible
if (shared->result == SUCCESS) {
    process_payload(shared->payload);
}
```

### ACP vs HP for DMA

| Port | Coherency | Throughput | Best For |
|---|---|---|---|
| **S_AXI_ACP** | Cache-coherent | ~1.2 GB/s (lower than HP due to snoop overhead) | Small control structures (<4 KB), shared flags, ring buffer metadata |
| **S_AXI_HP** | Non-coherent | ~2.4 GB/s (64-bit) | Bulk data — video frames, streaming samples |
| **S_AXI_HPC** (MPSoC) | Cache-coherent | ~2.0 GB/s (128-bit) | Large shared buffers where coherency matters |

**Rule of thumb:** Use ACP for control structures and small shared data. Use HP for bulk DMA. On MPSoC, HPC bridges both worlds.

---

## PL Interrupt Numbers

### Zynq-7000

| PL Interrupt | GIC SPI ID | Notes |
|---|---|---|
| PL PS IRQ 0 (IRQF2P[0]) | SPI 61 | |
| PL PS IRQ 1–7 (IRQF2P[1:7]) | SPI 62–68 | |
| PL PS IRQ 8–15 (IRQF2P[8:15]) | SPI 84–91 | |

### MPSoC

| PL Interrupt | GIC SPI ID | Notes |
|---|---|---|
| PL PS IRQ 0–7 (pl_ps_irq0[0:7]) | SPI 121–128 | |
| PL PS IRQ 8–15 (pl_ps_irq1[0:7]) | SPI 136–143 | |

---

## Worked Example: Zynq-7000 AXI DMA + ACP

```c
// FPGA streams video frames to DDR via AXI DMA
// Frame metadata (pointer, size) goes through ACP
// Frame pixels go through HP for max throughput

struct video_frame {
    u32 frame_num;
    u32 width;
    u32 height;
    u32 data_offset;   // offset into the HP DMA buffer
};

// Allocate metadata in cacheable memory (ACP-visible)
struct video_frame *metadata = kzalloc(
    MAX_FRAMES * sizeof(*metadata), GFP_KERNEL);

// Allocate pixel buffer NON-cached (via HP)
dma_addr_t pixel_dma;
void *pixels = dma_alloc_coherent(dev->dma_device,
                                    1920 * 1080 * 4,  // RGBA
                                    &pixel_dma,
                                    GFP_KERNEL);

// Configure AXI DMA to write pixels to pixel_dma (HP)
// Configure FPGA to write metadata via ACP

// CPU reads metadata (ACP ensures visibility):
for (int i = 0; i < MAX_FRAMES; i++) {
    if (metadata[i].frame_num == expected_frame) {
        // Process pixels: need invalidate since HP is non-coherent
        dma_sync_single_for_cpu(dev->dma_device,
            pixel_dma + metadata[i].data_offset,
            metadata[i].width * metadata[i].height * 4,
            DMA_FROM_DEVICE);
        display_frame(pixels + metadata[i].data_offset);
    }
}
```

---

## Further Reading

| Resource | Description |
|---|---|
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | Vendor-agnostic common overview |
| [../02_architecture/soc/hps_fpga_xilinx_zynq.md](../02_architecture/soc/hps_fpga_xilinx_zynq.md) | Hardware-level PS-PL interface architecture |
| [boot_flow_xilinx_zynq.md](../02_boot_flow/boot_flow_xilinx_zynq.md) | Xilinx boot flow deep dive |
| [Xilinx UG585](https://docs.amd.com/) | Zynq-7000 Technical Reference Manual |
| [Xilinx UG1085](https://docs.amd.com/) | Zynq UltraScale+ MPSoC TRM |
