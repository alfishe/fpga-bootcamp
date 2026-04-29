[← Section Home](../README.md) · [← Project Home](../../README.md)

# HPS ↔ FPGA Interaction — Bridges, Memory Maps, Interrupts & DMA

> [!IMPORTANT]
> Every byte transferred between the CPU and FPGA fabric crosses an AXI bridge; every interrupt from an FPGA IP core traverses a Generic Interrupt Controller. Understanding the hardware paths is prerequisite to writing correct, performant drivers.

This article covers the **vendor-agnostic common concepts**: what HPS-FPGA bridges are, the four canonical interaction paths (MMIO, userspace map, interrupts, DMA), cache coherency fundamentals, and how to choose the right method for your data. For per-vendor bridge addresses, port inventories, and family-specific constraints, see the linked deep dives at the end.

---

## The Bridge Concept

A SoC FPGA integrates a hard processor system (HPS/PS/MSS) with FPGA fabric on one die. Communication between these two domains — different clock trees, different reset schemes, different internal buses — happens through **AXI bridges** built into the silicon.

Every SoC FPGA has at least these logical bridge classes:

```
┌───────────────────────────────────────┐
│        Processor System (CPU)         │
│  ┌─────┐  ┌─────┐  ┌──────────┐      │
│  │Core0│  │Core1│  │L2 Cache  │      │
│  └──┬──┘  └──┬──┘  └────┬─────┘      │
│     └────────┴───────────┘            │
│              │                        │
│    ┌─────────▼─────────┐              │
│    │  L3 Interconnect  │              │
│    └──┬──────┬────┬────┘              │
└───────┼──────┼────┼───────────────────┘
        │      │    │
   ┌────▼──┐ ┌▼───┐│┌──▼───┐
   │H2F    │ │F2H │││F2S   │
   │AXI-64 │ │AXI │││AXI   │
   │CPU→FP │ │FP→ │││FP→   │
   │(ctrl) │ │CPU │││DDR   │
   └───┬───┘ └──┬─┘│└──┬───┘
       │        │  │   │
┌──────┼────────┼──┼───┼────────────────┐
│      ▼        ▼  ▼   ▼               │
│          FPGA Fabric                  │
│    ┌──────┐  ┌────┐  ┌─────────┐    │
│    │Ctrl  │  │DMA │  │Video    │    │
│    │Regs  │  │Eng │  │FrameBuf │    │
│    └──────┘  └────┘  └─────────┘    │
└──────────────────────────────────────┘
```

| Bridge Direction | Role | Typical Throughput | Use Case |
|---|---|---|---|
| **H2F** (CPU→FPGA) | CPU reads/writes FPGA registers | ~100 MB/s (32-bit PIO) | Control registers, status flags |
| **F2H** (FPGA→CPU) | FPGA initiates reads/writes to CPU-visible memory | ~1.6 GB/s (128-bit AXI) | DMA engine destination, interrupt pulse |
| **F2S** (FPGA→DDR) | FPGA masters DRAM controller directly, **no CPU involvement** | ~6.4 GB/s (256-bit) | Video frames, streaming data ingest |
| **LWH2F** (lightweight) | Low-latency CPU→FPGA for register access | ~50 MB/s (32-bit) | GPIO-set, peripheral control |

Intel calls these H2F/LWH2F/F2H/F2S. Xilinx calls them M_AXI_GP/S_AXI_HP/S_AXI_HPC/S_AXI_ACP. Microchip calls them FIC0/FIC1/FIC2. The function is identical; the names and counts differ.

---

## The Four Paths From CPU to FPGA

| Path | Mechanism | Latency | Throughput | Best For |
|---|---|---|---|---|
| **MMIO (ioremap)** | CPU load/store to bridge address | ~100 ns | ~100 MB/s (32-bit) | Control registers, status flags, FIFO enqueue |
| **Userspace mmap** | `/dev/mem` or UIO mmap of bridge region | ~200 ns | ~50 MB/s | Simple userspace register access |
| **Interrupts (FPGA→CPU)** | FPGA asserts SPI line → GIC → Linux IRQ handler | ~3–10 µs | Event-driven | Notification on data ready, DMA complete |
| **DMA (dmaengine)** | FPGA DMA controller moves bulk data | Setup ~10 µs; wire speed | ~1.6 GB/s (128-bit) | Frame buffers, streaming samples, large transfers |

---

## Path 1 — MMIO via ioremap (Kernel Driver)

Every FPGA peripheral the CPU needs to control is mapped at a physical address in a bridge window. The kernel maps it with `ioremap()`:

```c
// Platform driver for a peripheral at H2F offset
// Physical address = bridge_base + peripheral_offset

#include <linux/io.h>
#include <linux/platform_device.h>

struct my_fpga_regs {
    u32 ctrl;        // 0x00 — control register
    u32 status;      // 0x04 — status register
    u32 fifo_data;   // 0x08 — data FIFO write port
    u32 irq_mask;    // 0x0C — interrupt mask
};

static void __iomem *regs;

static int myfpga_probe(struct platform_device *pdev) {
    struct resource *res;

    // 1. Get physical address from device tree
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if (!res) return -EINVAL;

    // 2. Map FPGA registers into kernel virtual address space
    regs = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(regs)) return PTR_ERR(regs);

    // 3. Read/write FPGA registers like IO memory
    u32 ctrl_val = ioread32(&regs->ctrl);
    iowrite32(ctrl_val | BIT(0), &regs->ctrl);  // set ENABLE bit

    // 4. Write to FPGA FIFO
    iowrite32(0xDEADBEEF, &regs->fifo_data);

    return 0;
}
```

### Critical: ioread32 vs Direct Dereference

**Never dereference an `__iomem` pointer directly.** ARM cores allow speculative reads and reordered writes to Normal memory, but FPGA registers are Device memory:

```c
// WRONG — may be reordered or speculatively read
u32 val = regs->status;

// CORRECT — ensures proper ordering semantics
u32 val = ioread32(&regs->status);
```

`ioread32()` emits a `ldr` instruction with appropriate memory barriers and marks the access as Device-nGnRnE (non-gathering, non-reordering, no early write acknowledgement).

### PIO vs DMA Threshold

On a typical SoC FPGA at 200 MHz bridge clock:
- 32-bit iowrite32: ~150 ns per write (including bus turnaround)
- 1000 sequential writes: ~150 µs
- 1 MB of data by PIO: ~50 ms

**Rule of thumb:** If moving >4 KB between CPU and FPGA, switch to DMA. Below that, PIO is simpler and often faster (DMA setup overhead is ~10 µs).

---

## Path 2 — Userspace mmap of FPGA Registers

### Method A — UIO (Proper Userspace IO)

UIO is a lightweight kernel driver that exposes FPGA registers to userspace. It handles resource allocation and interrupt forwarding.

**Device tree:**
```dts
myfpga@ff200000 {
    compatible = "generic-uio";
    reg = <0xff200000 0x1000>;
    interrupts = <0 40 IRQ_TYPE_LEVEL_HIGH>;
};
```

**Userspace:**
```c
int fd = open("/dev/uio0", O_RDWR);

// mmap FPGA registers
volatile void *fpga_regs = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

// Write to FPGA
*(volatile uint32_t *)(fpga_regs + 0x00) = 0x01;

// Wait for FPGA interrupt (blocking read)
uint32_t irq_count;
read(fd, &irq_count, sizeof(irq_count));  // blocks until IRQ
```

UIO is ideal for FPGA peripherals that don't fit cleanly into an existing kernel subsystem — custom DSP pipelines, proprietary register maps, research prototypes.

### Method B — /dev/mem (Quick Hack, Not For Production)

```c
int fd = open("/dev/mem", O_RDWR | O_SYNC);
volatile uint32_t *fpga_regs = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd,
    0xFF200000);  // physical FPGA address

fpga_regs[0] = 0x01;
uint32_t status = fpga_regs[1];
```

Drawbacks: no resource management (two apps can map the same registers), no interrupt support, `CONFIG_STRICT_DEVMEM` blocks it on many distributions, requires root.

---

## Path 3 — Interrupts: FPGA → CPU

An FPGA IP core signals the CPU by pulling a **Shared Peripheral Interrupt (SPI) line to the GIC** (Generic Interrupt Controller). The full path:

```
FPGA IP Core
    │  (asserts interrupt output, active-high level)
    ▼
FPGA Interrupt Controller (soft IP, optional)
    │  (aggregates interrupts when you have many IP cores)
    ▼
FPGA-to-HPS Bridge (F2H interrupt signals)
    │  (numbered FPGA→HPS IRQ lines, count varies by family)
    ▼
HPS System Manager / PS Interconnect
    │  (routes FPGA IRQ to GIC input)
    ▼
ARM GIC (Generic Interrupt Controller)
    │  (distributes to CPU cores)
    ▼
Linux IRQ subsystem → irq_handler
```

### Irq Latency

| Step | Typical Latency |
|---|---|
| FPGA asserts IRQ → GIC receives | ~20 ns |
| GIC → CPU IRQ exception entry | ~50 ns (12 cycles at 800 MHz) |
| Linux IRQ handler called | ~2–5 µs (context save, vector dispatch) |
| **Total FPGA→irq_handler** | **~3–10 µs** |

The dominant latency is Linux interrupt entry, not hardware. For sub-microsecond response, use an FPGA-side FIFO to absorb bursts and let the interrupt signal buffer readiness.

### Kernel Driver — Interrupt Handling

```c
static irqreturn_t myfpga_irq_handler(int irq, void *dev_id) {
    struct myfpga_dev *dev = dev_id;

    // Read FPGA status register to identify the source
    u32 status = ioread32(&dev->regs->status);

    if (status & BIT(0)) {
        u32 data = ioread32(&dev->regs->fifo_data);
        // ... process data ...

        // Clear interrupt in FPGA (write-1-to-clear)
        iowrite32(BIT(0), &dev->regs->status);
        return IRQ_HANDLED;
    }

    return IRQ_NONE;  // not our interrupt
}

static int myfpga_probe(struct platform_device *pdev) {
    int irq = platform_get_irq(pdev, 0);
    return devm_request_irq(&pdev->dev, irq,
                            myfpga_irq_handler, 0,
                            "myfpga", dev);
}
```

---

## Path 4 — DMA Between FPGA and System RAM

AXI DMA moves bulk data without the CPU touching every byte:

```
FPGA IP → AXI4-Stream → AXI DMA Engine → AXI4-MM (F2H bridge) → System DRAM
                                                   or
                              AXI4-MM (F2S bridge) → System DRAM (bypasses CPU)
```

### Kernel-Side DMA — The Linux dmaengine API

```c
#include <linux/dmaengine.h>
#include <linux/dma-mapping.h>

struct my_dma_dev {
    struct dma_chan *rx_chan;
    dma_addr_t rx_dma_addr;       // Bus address for FPGA
    void *rx_buf_virt;            // Virtual address for CPU
    size_t buf_size;
    struct completion dma_done;
};

static void dma_callback(void *param) {
    struct my_dma_dev *dev = param;
    complete(&dev->dma_done);
}

static int setup_dma_transfer(struct my_dma_dev *dev) {
    struct dma_async_tx_descriptor *tx;
    enum dma_ctrl_flags flags = DMA_CTRL_ACK | DMA_PREP_INTERRUPT;

    // 1. Allocate coherent buffer (CPU + FPGA both access)
    dev->buf_size = 256 * 1024;
    dev->rx_buf_virt = dma_alloc_coherent(dev->parent_dev,
                                           dev->buf_size,
                                           &dev->rx_dma_addr,
                                           GFP_KERNEL);
    // rx_buf_virt = CPU virtual address (for memcpy)
    // rx_dma_addr = Bus address (tells FPGA where to write)

    // 2. Get DMA channel from device tree
    dev->rx_chan = dma_request_chan(dev->parent_dev, "rx");

    // 3. Prepare cyclic DMA transfer (double-buffered)
    tx = dmaengine_prep_dma_cyclic(
        dev->rx_chan,
        dev->rx_dma_addr,   // destination = DDR buffer
        dev->buf_size,
        dev->buf_size / 2,  // period = half buffer
        DMA_DEV_TO_MEM,     // direction: FPGA → Memory
        flags);

    tx->callback = dma_callback;
    tx->callback_param = dev;

    // 4. Submit and start
    dmaengine_submit(tx);
    dma_async_issue_pending(dev->rx_chan);

    return 0;
}
```

### Coherent vs Streaming DMA

| Type | Allocation | Cache Behavior | Best For |
|---|---|---|---|
| **Coherent** (`dma_alloc_coherent`) | Uncached, contiguous physical | Hardware-coherent or uncached | Control structures, descriptors, small buffers (<64 KB) |
| **Streaming** (`dma_map_single`) | Can be cached; explicit sync required | `dma_sync_for_device/cpu` needed | Large buffers, high throughput |

On **non-coherent platforms**, coherent DMA buffers are allocated as uncached pages. This eliminates cache maintenance but hurts CPU read bandwidth (~200 MB/s from uncached vs ~2 GB/s from cached).

**Production rule for non-coherent platforms:** Use streaming DMA with `dma_map_single()` for buffers >16 KB. The cost of `dma_sync_for_cpu()` (~1 µs per call) is far less than the throughput penalty of uncached memory.

---

## Cache Coherency in Practice

### The Fundamental Choice

When CPU and FPGA share the same DDR memory, you face a coherency question:

| Platform Type | Coherency Model | CPU→FPGA Data | FPGA→CPU Data | Example |
|---|---|---|---|---|
| **Non-coherent** | CPU cache invisible to FPGA; FPGA writes invisible to cache | CPU must flush cache before FPGA reads | CPU must invalidate cache before reading FPGA data | Intel SoCs (Cyclone V, Arria 10, Agilex without CCU) |
| **Coherent (ACP/CCU)** | FPGA participates in cache coherency protocol | No software flush needed | No software invalidate needed | Xilinx Zynq ACP, Stratix 10/Agilex CCU |
| **Fully coherent** | All masters share one coherent bus; no special ports | Transparent | Transparent | Microchip PolarFire SoC |

### Shared Ring Buffer (Non-Coherent Platform)

```c
// CPU writes commands to a ring buffer in DDR, FPGA reads them

struct cmd_entry {
    u32 cmd;
    u32 param;
};

// 1. CPU fills entry
cmd_ring[tail].cmd = CMD_CONFIG;
cmd_ring[tail].param = 0x42;
tail = (tail + 1) % RING_SIZE;

// 2. Flush cache — FPGA won't see stale L1/L2 data
dma_sync_single_for_device(dev->dma_dev,
    dev->ring_dma_addr + (prev_tail * sizeof(struct cmd_entry)),
    sizeof(struct cmd_entry),
    DMA_TO_DEVICE);

// 3. Update tail pointer (FPGA-visible register)
iowrite32(tail, &fpga_regs->tail_ptr);
// Now FPGA sees both the new cmd_entry AND the updated tail
```

### Best Practices for Non-Coherent Platforms

1. **Double-buffer with F2S exclusive-access regions** — FPGA writes region A via F2S while CPU reads region B, then swap. No coherency overhead.
2. **Keep control structures small and uncached** — use coherent DMA for structures <1 KB that see frequent CPU/FPGA access.
3. **Batch cache operations** — `dma_sync_for_device()` invalidates entire cache lines (typically 64 bytes). Group shared fields to minimize flushes.

---

## Choosing Your Interaction Method

| You Want To... | Use | Notes |
|---|---|---|
| Read/write FPGA registers from kernel driver | `ioremap()` + `ioread32`/`iowrite32` | Device memory semantics, ordered access |
| Read/write FPGA registers from userspace | UIO `mmap()` | Handles interrupts, resource isolation |
| FPGA needs to alert CPU on event | `request_irq()` + FPGA SPI line | ~3–10 µs latency; use FPGA FIFO for sub-µs |
| Transfer bulk data FPGA→RAM | AXI DMA + streaming DMA + double-buffering | >1 GB/s throughput possible |
| FPGA needs uncached DDR region | `reserved-memory` DT + `dma_alloc_coherent` | Avoids cache thrashing |
| CPU & FPGA heavily share a buffer | Use ACP/CCU platform or double-buffer swap | Prefer ACP on Zynq; double-buffer on non-coherent |
| Multiple FPGA cores need interrupts | FPGA-side soft interrupt controller → single SPI line | Conserves GIC SPI lines |
| Debug a bus hang | Add read-back registers; check bridge transaction count | Ensure bridge is not in dead-loop state |

---

## Vendor-Specific Deep Dives

This article covers what is invariant across all FPGA SoCs. For per-vendor bridge addresses, port inventories, family-specific constraints, and worked examples:

| Platform | Deep Dive | Key Differences |
|---|---|---|
| **Intel / Altera** | [hps_fpga_bridges_intel_soc.md](hps_fpga_bridges_intel_soc.md) | Non-coherent by default; 4 fixed bridges (H2F, LWH2F, F2H, F2S); Cyclone V / Arria 10 / Stratix 10 / Agilex address maps |
| **Xilinx** | [hps_fpga_bridges_xilinx_zynq.md](hps_fpga_bridges_xilinx_zynq.md) | Optional ACP coherency; rich port inventory (GP, HP, HPC, ACP); Zynq-7000 / MPSoC / Versal topology |
| **Microchip** | [hps_fpga_bridges_microchip_soc.md](hps_fpga_bridges_microchip_soc.md) | Coherent by default; unified AXI4 bus matrix; FIC0/FIC1/FIC2; PolarFire SoC RISC-V specifics |

For hardware-level bridge architecture (block diagrams, signal-level details, clock domain behavior):
| Platform | Architecture Reference |
|---|---|
| Intel | [02_architecture/soc/hps_fpga_intel_soc.md](../02_architecture/soc/hps_fpga_intel_soc.md) |
| Xilinx | [02_architecture/soc/hps_fpga_xilinx_zynq.md](../02_architecture/soc/hps_fpga_xilinx_zynq.md) |
| Microchip | [02_architecture/soc/hps_fpga_microchip_soc.md](../02_architecture/soc/hps_fpga_microchip_soc.md) |

---

## Further Reading

| Resource | Description |
|---|---|
| Linux DMA Engine API | `Documentation/driver-api/dmaengine/` |
| Linux IRQ subsystem | `Documentation/core-api/irq/` |
| `ioremap` semantics | `Documentation/driver-api/io-mapping.rst` |
| [soc_linux_architecture.md](../01_architecture/soc_linux_architecture.md) | SoC FPGA architecture from Linux's view |
| [kernel_drivers_and_dma.md](../04_drivers_and_dma/kernel_drivers_and_dma.md) | Driver patterns and DMA buffer strategies |
| [device_tree_and_overlays.md](../04_drivers_and_dma/device_tree_and_overlays.md) | Device tree for FPGA SoCs |
