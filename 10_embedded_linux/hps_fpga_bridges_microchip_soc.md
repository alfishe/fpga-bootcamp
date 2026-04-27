[← Section Home](README.md) · [← Common Overview](hps_fpga_bridges.md) · [← Project Home](../README.md)

# Microchip SoC FPGA — MSS-Fabric Interface Programming

> [!NOTE]
> This article covers the **Linux software perspective** — FIC addresses, device tree bindings, and driver patterns for Microchip SoC FPGAs. For hardware architecture (block diagrams, coherent bus matrix details), see [02_architecture/soc/hps_fpga_microchip_soc.md](../02_architecture/soc/hps_fpga_microchip_soc.md).

Microchip's approach is architecturally distinct: **all CPU cores and the FPGA fabric share a unified coherent memory subsystem**. There is no optional coherency port — coherency is the default. The FPGA is a first-class citizen on the AXI4 bus matrix, not a peripheral that needs special ports.

---

## FIC Inventory and Address Maps

```
┌───────────────────────────────────────────────┐
│         PolarFire SoC MSS / Fabric            │
│  ┌─────────┐  ┌─────────┐  ┌───────────────┐ │
│  │  U54×4  │  │   E51   │  │    L2 Cache   │ │
│  │(Linux)  │  │(Monitor)│◄─┤  ( coherent   │ │
│  └────┬────┘  └────┬────┘  │   across all )│ │
│       │            │       └───────┬───────┘ │
│       └────────────┴───────────────┘         │
│                     │                        │
│              ┌──────▼──────┐                 │
│              │ Coherent    │                 │
│              │ AXI4 Bus    │                 │
│              │ Matrix      │                 │
│              └──────┬──────┘                 │
│    ┌────────────────┼────────────────┐      │
│    │  ┌─────────┐ ┌─────────┐ ┌────▼───┐  │
│    │  │  FIC0   │ │  FIC1   │ │  FIC2  │  │
│    │  │AXI4 64b │ │AXI4 64b │ │AXI4 64b│  │
│    │  │ Master  │ │Master/  │ │ Slave  │  │
│    │  │         │ │ Slave   │ │        │  │
│    │  └────┬────┘ └────┬────┘ └───┬────┘  │
│    └───────┼───────────┼─────────┼───────┘  │
└────────────┼───────────┼─────────┼──────────┘
             └───────────┴─────────┘
                         │
                  FPGA Fabric
```

### Fabric Interface Controllers

| FIC | Direction | Width | Address Range (Linux) | Purpose |
|---|---|---|---|---|
| **FIC0** | MSS → Fabric (Master) | 64-bit AXI4 | `0x2000_0000` – `0x2FFF_FFFF` (256 MB) | CPU-initiated FPGA register access, low-latency control |
| **FIC1** | Bidirectional | 64-bit AXI4 | `0x3000_0000` – `0x3FFF_FFFF` (256 MB) + LL DDR region | FPGA DMA to/from DDR, shared memory regions |
| **FIC2** | Fabric → MSS (Slave) | 64-bit AXI4 | MSS DDR space | FPGA masters reading/writing CPU-mapped DDR (limited use) |

> **FIC1 is the workhorse for DMA.** It operates as both master (CPU→FPGA) and slave (FPGA→DDR), making it the primary path for bulk data transfers.

### FIC1 Sub-Modes

| Mode | Route | Use Case |
|---|---|---|
| **FIC1 Master** | CPU initiates AXI transactions to FPGA | CPU writes commands; FPGA reads DDR via FIC1 slave |
| **FIC1 Slave (LL DDR)** | FPGA reads/writes the Low-Latency DDR region directly | FPGA DMA to dedicated uncached DDR region |
| **FIC1 Slave (Cacheable)** | FPGA accesses cacheable DDR through coherent bus | Shared data structures — **no cache maintenance needed** |

---

## Device Tree Bindings

### PolarFire SoC — FIC0 Peripheral

```dts
// FPGA register peripheral at FIC0 offset 0x1000_0000
// Physical address = 0x2000_0000 + 0x1000_0000 = 0x3000_0000

soc {
    #address-cells = <2>;
    #size-cells = <2>;

    myfpga: myfpga@30000000 {
        compatible = "mycompany,myfpga-core";
        reg = <0x0 0x30000000 0x0 0x10000>;
        interrupts = <48>;   // Fabric IRQ (PLIC external interrupt)
        interrupt-parent = <&plic>;
    };
};
```

### FIC1 DMA Buffer

```dts
reserved-memory {
    #address-cells = <2>;
    #size-cells = <2>;

    fpga_dma_region: fpga-dma@c0000000 {
        reg = <0x0 0xc0000000 0x0 0x1000000>;  // 16 MB
        no-map;
    };
};
```

---

## Coherent by Default — Driver Implications

The unified coherent bus matrix means **no `dma_sync_*` calls are needed for FIC1 coherent mode**:

```c
// PolarFire SoC: shared ring buffer — NO cache maintenance needed

struct cmd_entry {
    u32 cmd;
    u32 param;
};

// Allocate in normal cacheable memory (kzalloc)
struct cmd_entry *ring = kzalloc(
    RING_SIZE * sizeof(*ring), GFP_KERNEL);

// CPU fills entry — immediately visible to FPGA
ring[tail].cmd = CMD_CONFIG;
ring[tail].param = 0x42;
tail = (tail + 1) % RING_SIZE;

// Update tail pointer in FPGA registers (via FIC0)
iowrite32(tail, fpga_regs + TAIL_PTR_OFFSET);

// FPGA reads ring[prev_tail] through FIC1 coherent slave
// → sees the same values CPU wrote — no dma_sync needed

// FPGA writes results; CPU reads:
if (ring[head].cmd == CMD_DONE) {
    // No cache invalidate needed — coherency is hardware-managed
    process_result(ring[head].param);
}
```

### Performance Consideration

The hardware coherency has a latency cost (snoop transactions on the bus). For bulk data:

| Approach | Throughput | When to Use |
|---|---|---|
| **FIC1 coherent (cacheable DDR)** | ~800 MB/s | Shared control structures, small payloads |
| **FIC1 LL DDR (uncached region)** | ~1.6 GB/s | Bulk DMA where CPU doesn't need to read the data |
| **FIC1 coherent + double buffer** | ~1.4 GB/s | CPU processes FPGA output in streaming fashion |

---

## RISC-V Interrupts

PolarFire SoC uses a **RISC-V PLIC** (Platform-Level Interrupt Controller), not ARM GIC:

```c
// RISC-V interrupt handler
static irqreturn_t myfpga_irq_handler(int irq, void *dev_id) {
    struct myfpga_dev *dev = dev_id;

    u32 status = ioread32(dev->regs + FPGA_STATUS);

    if (status & FPGA_IRQ_FLAG) {
        // Process FPGA data
        iowrite32(FPGA_IRQ_FLAG, dev->regs + FPGA_STATUS); // W1C
        return IRQ_HANDLED;
    }
    return IRQ_NONE;
}
```

### PLIC Fabric Interrupts

| Source | PLIC ID | Notes |
|---|---|---|
| Fabric IRQ 0–40 | 1–41 | Mapped from FPGA to PLIC inputs |
| MSS internal IRQs | 42+ | UART, SPI, I2C, etc. |

The Linux RISC-V kernel handles PLIC setup automatically through device tree. The driver API is identical to ARM — use `platform_get_irq()` and `devm_request_irq()`.

---

## Further Reading

| Resource | Description |
|---|---|
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | Vendor-agnostic common overview |
| [../02_architecture/soc/hps_fpga_microchip_soc.md](../02_architecture/soc/hps_fpga_microchip_soc.md) | Hardware-level MSS-Fabric interface architecture |
| [boot_flow_microchip_soc.md](boot_flow_microchip_soc.md) | Microchip boot flow deep dive |
| [PolarFire SoC documentation](https://www.microchip.com/en-us/products/fpgas-and-plds/system-on-chip-fpgas/polarfire-soc-fpgas) | Official Microchip docs |
