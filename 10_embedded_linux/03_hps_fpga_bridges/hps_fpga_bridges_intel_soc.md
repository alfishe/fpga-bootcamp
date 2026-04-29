[← Section Home](../README.md) · [← Common Overview](hps_fpga_bridges.md) · [← Project Home](../../README.md)

# Intel SoC FPGA — HPS-FPGA Bridge Programming

> [!NOTE]
> This article covers the **Linux software perspective** — bridge addresses, device tree bindings, and driver patterns for Intel SoC FPGAs. For hardware architecture (block diagrams, clock domains, signal-level detail), see [02_architecture/soc/hps_fpga_intel_soc.md](../02_architecture/soc/hps_fpga_intel_soc.md).

Intel SoC FPGAs (Cyclone V, Arria 10, Stratix 10, Agilex 5/7) use a fixed set of **four AXI bridges** between the Hard Processor System (HPS) and FPGA fabric. There is **no cache coherency** — FPGA masters bypass the CPU L2 cache entirely when accessing DDR.

---

## Bridge Inventory and Address Maps

```
                    ┌─────────────────────────────────────┐
                    │         Intel HPS Subsystem         │
                    │  ┌─────────┐    ┌───────────────┐   │
                    │  │ Dual/   │    │   L2 Cache    │   │
                    │  │ Quad    │◄──►│  (512K-1MB)   │   │
                    │  │ Cortex  │    └───────┬───────┘   │
                    │  │ -A9/A53 │            │           │
                    │  └────┬────┘            │           │
                    │       │                 │           │
                    │  ┌────▼─────────────────▼────┐      │
                    │  │   L3 Interconnect (NIC)   │      │
                    │  └────┬──────────┬─────┬─────┘      │
                    └───────┼──────────┼─────┼────────────┘
                            │          │     │
              ┌─────────────┼──────────┼─────┼─────────────┐
              │             ▼          ▼     ▼             │
              │  FPGA Fabric ───────────────────────────── │
              │   ┌─────┐  ┌─────┐  ┌─────┐  ┌──────────┐  │
              │   │H2F  │  │LWH2F│  │F2H  │  │  F2S     │  │
              │   └─────┘  └─────┘  └─────┘  └──────────┘  │
              └────────────────────────────────────────────┘
```

| Bridge | Direction | Width | Cyclone V / Arria 10 Base Address | Stratix 10 / Agilex Base Address | Linux Use |
|---|---|---|---|---|---|
| **H2F** | HPS → FPGA | 64-bit | `0xC000_0000` (960 MB window) | `0x0000_0000` (2 GB window) | `ioremap()` for FPGA peripherals |
| **LWH2F** | HPS → FPGA | 32-bit | `0xFF20_0000` (2 MB window) | `0xF900_0000` (2 MB) | Lightweight register access (lower latency) |
| **F2H** | FPGA → HPS | 64-bit | `0x0000_0000` (960 MB) | `0x0000_0000` (2 GB) | FPGA DMA writes to CPU-visible DDR |
| **F2S** | FPGA → SDRAM | 128/256-bit | 6× read + 4× write ports | 6× read + 4× write ports | FPGA direct DDR access (bypasses CPU) |

### Key Differences by Family

| Feature | Cyclone V | Arria 10 | Stratix 10 | Agilex 5/7 |
|---|---|---|---|---|
| **CPU cores** | Dual Cortex-A9 | Dual Cortex-A9 | Quad Cortex-A53 | Quad Cortex-A55/-A76 |
| **H2F base** | `0xC000_0000` | `0xC000_0000` | `0x0000_0000` | `0x0000_0000` |
| **LWH2F base** | `0xFF20_0000` | `0xFF20_0000` | `0xF900_0000` | `0xF900_0000` |
| **Cache coherency** | None | None | Optional CCU | Optional CCU |
| **ACP equivalent** | None | None | CCU (Cache Coherency Unit) | CCU |
| **FPGA IRQ count** | 64 | 64 | 128 | 128+ |
| **Example board** | DE10-Nano, MiSTer | Arria 10 SoC Dev Kit | Stratix 10 SoC Dev Kit | Agilex 7 SoC Dev Kit |

> **Important:** Stratix 10 and Agilex use **CCU (Cache Coherency Unit)**, not ACP, for hardware cache coherency. The CCU is an optional hard IP block that must be instantiated in the FPGA design. Most Intel designs omit it and operate non-coherently.

---

## Device Tree Bindings

### Cyclone V SoC — H2F Bridge Peripheral

```dts
// Peripheral at H2F offset 0x1000_0000
// Physical address = 0xC000_0000 + 0x1000_0000 = 0xD000_0000

soc {
    #address-cells = <1>;
    #size-cells = <1>;

    h2f_bridge: bridge@ff200000 {
        compatible = "altr,socfpga-h2f-bridge";
        reg = <0xff200000 0x1000>;
        clocks = <&l4_main_clk>;
    };

    myfpga: myfpga@d0000000 {
        compatible = "mycompany,myfpga-core";
        reg = <0xd0000000 0x10000>;             // 64 KB of FPGA registers
        interrupts = <0 40 IRQ_TYPE_LEVEL_HIGH>; // FPGA IRQ 0 → GIC SPI 72
        clocks = <&h2f_user0_clk>;
    };
};
```

### Stratix 10 / Agilex — H2F Bridge

```dts
soc {
    myfpga: myfpga@400000000 {
        compatible = "mycompany,myfpga-core";
        reg = <0x4 0x00000000 0x0 0x10000>;  // 64-bit address space
        interrupts = <0 40 IRQ_TYPE_LEVEL_HIGH>;
    };
};
```

---

## FPGA Interrupt Numbers

### Cyclone V / Arria 10

| FPGA IRQ Line | GIC SPI ID | Notes |
|---|---|---|
| FPGA IRQ 0 | SPI 72 | Most commonly used |
| FPGA IRQ 1 | SPI 73 | |
| ... | SPI 74–135 | FPGA IRQ 2–63 |

### Stratix 10 / Agilex

| FPGA IRQ Line | GIC SPI ID | Notes |
|---|---|---|
| FPGA IRQ 0 | SPI 128 | |
| ... | SPI 129–255 | FPGA IRQ 1–127 |

---

## Driver Pattern: ioremap on Cyclone V

```c
#include <linux/io.h>
#include <linux/platform_device.h>

struct myfpga_dev {
    void __iomem *regs;
    int irq;
};

static int myfpga_probe(struct platform_device *pdev) {
    struct myfpga_dev *dev;
    struct resource *res;

    dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);

    // Map FPGA registers through H2F bridge
    // Physical: 0xD000_0000 (bridge_base + peripheral_offset)
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    dev->regs = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(dev->regs)) return PTR_ERR(dev->regs);

    // Register interrupt
    dev->irq = platform_get_irq(pdev, 0);
    return devm_request_irq(&pdev->dev, dev->irq,
                            myfpga_irq_handler, 0,
                            "myfpga", dev);
}

// Read FPGA FIFO status (using LWH2F for lower latency)
static inline u32 fpga_read_status(struct myfpga_dev *dev) {
    return ioread32(dev->regs + 0x04);
}
```

> **LWH2F vs H2F for register access:** The LWH2F bridge has lower latency for 32-bit PIO because it bypasses the 64-bit width conversion in the H2F bridge. Use LWH2F for control/status registers; use H2F only when you need 64-bit bursts.

---

## Non-Coherent DMA on Intel

Intel SoCs are **non-coherent by default**. CPU cache lines are invisible to FPGA fabric. When sharing DDR buffers:

```c
// Allocate uncached buffer for FPGA DMA
dma_addr_t dma_handle;
void *cpu_addr = dma_alloc_coherent(dev->dma_device,
                                     256 * 1024,      // 256 KB
                                     &dma_handle,
                                     GFP_KERNEL);

// CPU writes data → must flush before FPGA reads
memcpy(cpu_addr, source_data, data_size);
dma_sync_single_for_device(dev->dma_device, dma_handle,
                            data_size, DMA_TO_DEVICE);

// Tell FPGA the data is ready
iowrite32(READY_FLAG, dev->regs + FPGA_CTRL_REG);

// After FPGA processes and writes results → invalidate before CPU reads
dma_sync_single_for_cpu(dev->dma_device, dma_handle,
                         result_size, DMA_FROM_DEVICE);
memcpy(dest_data, cpu_addr, result_size);
```

For Stratix 10/Agilex with CCU instantiated, coherent DMA eliminates these sync calls — see the [architecture reference](../02_architecture/soc/hps_fpga_intel_soc.md) for CCU configuration.

---

## Further Reading

| Resource | Description |
|---|---|
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | Vendor-agnostic common overview |
| [../02_architecture/soc/hps_fpga_intel_soc.md](../02_architecture/soc/hps_fpga_intel_soc.md) | Hardware-level bridge architecture |
| [boot_flow_intel_soc.md](../02_boot_flow/boot_flow_intel_soc.md) | Intel boot flow deep dive |
| [Intel SoC FPGA Linux Documentation](https://rocketboards.org/) | Official Intel Linux for SoC FPGA |
