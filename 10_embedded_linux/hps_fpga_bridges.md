[← Section Home](README.md) · [← Project Home](../README.md)

# HPS ↔ FPGA Interaction — Bridges, Memory Maps, Interrupts & DMA

This is the crux of FPGA SoC programming: **how does Linux code running on the ARM cores read/write the FPGA fabric, and how does the FPGA signal the CPU?** Every byte transferred between the two domains crosses an AXI bridge; every interrupt from an FPGA IP core traverses the ARM Generic Interrupt Controller. This article covers the full path from Linux userspace to FPGA register and back.

---

## The Four Paths From CPU to FPGA

| Path | Mechanism | Latency | Throughput | Use |
|---|---|---|---|---|
| **MMIO (ioremap)** | CPU load/store to bridge address | ~100 ns | ~100 MB/s (32-bit PIO) | Control registers, status flags, FIFO enqueue |
| **Userspace mmap** | `/dev/mem` or UIO mmap of bridge region | ~200 ns | ~50 MB/s | Simple userspace register access |
| **DMA (dmaengine)** | FPGA DMA controller moves data | Setup: ~10 µs; Transfer: wire speed | ~1.6 GB/s (128-bit AXI) | Bulk data: frame buffers, streaming samples |
| **FPGA→DDR (Direct)** | FPGA masters the SDRAM controller | Variable | ~6.4 GB/s (256-bit) | No CPU involvement — video pipes, data ingest |

---

## Path 1 — MMIO via ioremap (The Most Common Path)

Every FPGA peripheral that the CPU needs to control is mapped at a physical address in the H2F bridge window (typically `0xC000_0000` on Cyclone V SoC). The kernel maps this with `ioremap()`:

### Kernel Driver — Register Access

```c
// Platform driver for a peripheral at H2F offset 0x1000_0000
// Physical address: 0xC000_0000 + 0x1000_0000 = 0xD000_0000

#include &lt;linux/io.h&gt;
#include &lt;linux/platform_device.h&gt;

// FPGA peripheral register layout
struct my_fpga_regs {
    u32 ctrl;        // 0x00 — control register
    u32 status;      // 0x04 — status register
    u32 fifo_data;   // 0x08 — data FIFO write port
    u32 irq_mask;    // 0x0C — interrupt mask
};

static void __iomem *regs;  // ioremap'd virtual address

static int myfpga_probe(struct platform_device *pdev) {
    struct resource *res;
    
    // 1. Get physical address from device tree
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if (!res) return -EINVAL;
    
    // 2. Map FPGA registers into kernel virtual address space
    regs = devm_ioremap_resource(&pdev->dev, res);
    //     Physical 0xD000_0000 → virtual 0xFXXX_XXXX (kernel virtual addr)
    if (IS_ERR(regs)) return PTR_ERR(regs);
    
    // 3. Now read/write FPGA registers like normal memory
    u32 ctrl_val = ioread32(&regs->ctrl);
    iowrite32(ctrl_val | BIT(0), &regs->ctrl);  // set ENABLE bit
    
    // 4. Write to FPGA FIFO
    iowrite32(0xDEADBEEF, &regs->fifo_data);
    
    return 0;
}
```

### Critical: ioread32 vs Direct Dereference

**Never dereference an `__iomem` pointer directly.** The ARM architecture allows speculative reads and reordered writes to Normal memory, but FPGA registers are Device memory:

```c
// WRONG — may be reordered or speculatively read
u32 val = regs->status;

// CORRECT — ensures proper ordering semantics
u32 val = ioread32(&regs->status);
```

`ioread32` emits a `ldr` instruction with appropriate memory barriers and marks the access as Device-nGnRnE (non-gathering, non-reordering, no early write acknowledgement).

### Performance: PIO vs DMA Threshold

On Cyclone V SoC at 200 MHz bridge clock:
- 32-bit iowrite32: ~150 ns per write (including bus turnaround)
- 1000 sequential writes: ~150 µs
- 1 MB of data by PIO: ~50 ms

**Rule of thumb:** If you're moving >4 KB between CPU and FPGA, switch to DMA. Below that, PIO is simpler and faster (DMA setup overhead is ~10 µs).

---

## Path 2 — Userspace mmap of FPGA Registers

For userspace applications that need direct FPGA access without kernel driver overhead:

### Method A — /dev/mem (Quick Hack, Not For Production)

```c
#include &lt;sys/mman.h&gt;
#include &lt;fcntl.h&gt;

int fd = open("/dev/mem", O_RDWR | O_SYNC);
// Map FPGA registers at physical address 0xD000_0000
volatile uint32_t *fpga_regs = mmap(
    NULL, 0x1000,                      // 4 KB page
    PROT_READ | PROT_WRITE,
    MAP_SHARED,
    fd,
    0xD000_0000                        // Physical FPGA address
);

// Now write directly:
fpga_regs[0] = 0x01;  // control register
uint32_t status = fpga_regs[1];  // status register
```

Drawbacks of `/dev/mem`:
- No resource management — two apps can map the same registers
- No interrupt support
-satisf Kernel complaints (CONFIG_STRICT_DEVMEM blocks it on many distributions)
- Requires root

### Method B — UIO (Proper Userspace IO)

UIO (Userspace IO) is a lightweight kernel driver that exposes FPGA registers to userspace:

```c
// Kernel side (uio_pdrv_genirq or custom UIO driver)
// Device tree entry:
// myfpga@d0000000 {
//     compatible = "generic-uio";
//     reg = &lt;0xd0000000 0x1000&gt;;
//     interrupts = &lt;0 40 IRQ_TYPE_LEVEL_HIGH&gt;;
// };

// Userspace side:
int fd = open("/dev/uio0", O_RDWR);

// mmap FPGA registers
volatile void *fpga_regs = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

// Write to FPGA
*(volatile uint32_t *)(fpga_regs + 0x00) = 0x01;

// Wait for FPGA interrupt (blocking read)
uint32_t irq_count;
read(fd, &irq_count, sizeof(irq_count));  // blocks until IRQ
// → IRQ received, process data
```

UIO is ideal for FPGA peripherals that don't fit cleanly into an existing kernel subsystem (e.g., custom DSP pipeline with proprietary register map).

---

## Path 3 — Interrupts: FPGA → CPU

An FPGA IP core signals the ARM CPU by pulling a **shared peripheral interrupt (SPI) line to the GIC** (Generic Interrupt Controller). The full path:

```
FPGA IP Core
│  (asserts interrupt output, active-high level)
▼ omitted
FPGA Interrupt Controller (soft IP, optional)
│  (aggregates interrupts if you have many IP cores)
▼
FPGA-to-HPS Bridge (F2H interrupt signals)
│  (wired to specific FPGA→HPS IRQ lines, numbered 0–63 on Cyclone V)
▼
HPS System Manager
│  (routes FPGA IRQ to GIC input)
▼
ARM GIC (Generic Interrupt Controller) — SPI ID 72+
│
▼
Linux IRQ subsystem → irq_handler
```

### FPGA Interrupt Numbers — Cyclone V SoC

| FPGA IRQ Line | HPS GIC SPI ID | Note |
|---|---|---|
| FPGA IRQ 0 | SPI 72 | Most commonly used for single-core interrupt |
| FPGA IRQ 1 | SPI 73 | |
| ... | SPI 74–143 | FPGA IRQ 2–71 |

### Kernel Driver — Interrupt Handling

```c
static irqreturn_t myfpga_irq_handler(int irq, void *dev_id) {
    struct myfpga_dev *dev = dev_id;
    u32 status;
    
    // Read FPGA status register to see what triggered
    status = ioread32(&dev->regs->status);
    
    if (status & BIT(0)) {
        // Process FIFO data available interrupt
        u32 data = ioread32(&dev->regs->fifo_data);
        // ... enqueue data to upper layer
        
        // Clear interrupt in FPGA (write-1-to-clear)
        iowrite32(BIT(0), &dev->regs->status);
        return IRQ_HANDLED;
    }
    
    return IRQ_NONE;  // not our interrupt
}
// (spurious handling not shown for brevity)

static int myfpga_probe(struct platform_device *pdev) {
    int irq, ret;
    
    // Get interrupt number from device tree
    irq = platform_get_irq(pdev, 0);
    // → returns Linux IRQ number (e.g., 112, which the kernel
    //   mapped from GIC SPI 72 + 32 = 104 on ancient numbering)
    
    // Register interrupt handler
    ret = devm_request_irq(&pdev->dev, irq,
                           myfpga_irq_handler,
                           0,                 // flags (IRQF_SHARED if needed)
                           "myfpga",          // name in /proc/interrupts
                           dev);              // passed to handler
    // ...
}
```

### Interrupt Latency

| Path | Typical Latency |
|---|---|
| FPGA asserts IRQ → GIC receives | ~20 ns (on-chip PCB routing) |
| GIC → CPU IRQ exception enters | ~12 cycles (~50 ns at 800 MHz) |
| Linux IRQ handler called | ~2–5 µs (context save, vector dispatch) |
| **Total FPGA→IRQ_handler** | **~3–10 µs** |

The dominant latency is Linux interrupt entry, not hardware. If you need <1 µs response, use an FPGA-side FIFO to absorb bursts and the interrupt just signals buffers are ready.

---

##Path 4 — DMA Between FPGA and Linux RAM

AXI DMA is how you move bulk data. The typical setup:

```
FPGA IP → AXI4-Stream →AXI DMA Engine → AXI4-MM (F2H bridge) → HPS DRAM
                                                    or
                                 AXI4-MM (F2S bridge) → HPS DRAM (bypasses CPU)
```

### Kernel-Side DMA — The Linux dmaengine API

```c
#include &lt;linux/dmaengine.h&gt;
#include &lt;linux/dma-mapping.h&gt;

struct my_dma_dev {
    struct dma_chan *rx_chan;       // DMA channel from dmaengine
    dma_addr_t rx_dma_addr;         // Bus address for FPGA
    void *rx_buf_virt;              // Virtual address for CPU
    size_t buf_size;
    struct completion dma_done;
};

static void dma_callback(void *param) {
    struct my_dma_dev *dev = param;
    complete(&dev->dma_done);        // DMA complete → wake waiters
}

static int setup_dma_transfer(struct my_dma_dev *dev) {
    struct dma_async_tx_descriptor *tx;
    enum dma_ctrl_flags flags = DMA_CTRL_ACK | DMA_PREP_INTERRUPT;
    
    // 1. Allocate coherent DMA buffer (CPU + FPGA both access)
    //    This ensures memory is non-cacheable and contiguous
    dev->buf_size = 256 * 1024;  // 256 KB
    dev->rx_buf_virt = dma_alloc_coherent(dev->parent_dev,
                                           dev->buf_size,
                                           &dev->rx_dma_addr,  // FPGA-side address
                                           GFP_KERNEL);
    // rx_buf_virt = CPU virtual address (for memcpy, etc.)
    // rx_dma_addr = Bus address (tells FPGA where to write)
    
    // 2. Get DMA channel (from device tree)
    dev->rx_chan = dma_request_chan(dev->parent_dev, "rx");
    
    // 3. Prepare DMA transfer descriptor
    tx = dmaengine_prep_dma_cyclic(
        dev->rx_chan,
        dev->rx_dma_addr,   // destination = DDR buffer
        dev->buf_size,
        dev->buf_size / 2,  // period size (half buffer for double-buffer)
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

### DMA — Coherent vs Streaming

| Type | Flags | C噸347→Cache Coherency | Use |
|---|---|---|---|
| **Coherent DMA** (`dma_alloc_coherent`) | Uncached, contiguous physical | Hardware-coherent or uncached | Control structures, descriptors small buffers (<64 KB) |
| **Streaming DMA** (`dma_map_single`) | Can be cached; synced with `dma_sync_single_for_device/cpu` | Requires explicit flush/invalidate | Large buffers, high throughput |

On **non-coherent platforms** (Cyclone V SoC), coherent DMA buffers are allocated as uncached memory pages. This eliminates cache maintenance but **hurts CPU read bandwidth**: the CPU reads at ~200 MB/s from uncached memory vs ~2 GB/s from cached.

> **Production rule for Cyclone V SoC:** Use streaming DMA with `dma_map_single()` for12→buffer sizes >16 KB. The cost of `dma_sync_for_cpu()` (~1 µs per call) is far less than the throughput penalty of uncached memory.

---

## Cache Coherency in Practice

### Scenario: Shared Ring Buffer (Non-Coherent Platform)

```c
// CPU writes commands to a ring buffer in DDR
struct cmd_entry {
    u32 cmd;
    u32 param;
};

// 1. CPU fills entry
cmd_ring[tail].cmd = CMD_CONFIG;
cmd_ring[tail].param = 0x42;
tail = (tail + 1) % RING_SIZE;

// 2. Update tail pointer
iowrite32(tail, &fpga_regs->tail_ptr);

// 3.!! PROBLEMGON→ FPGA reads cmd_ring through F2S bridge
//    → Might see stale CMD_CONFIG or param because it's
//    still in CPU L1/L2 cache?3

// FIX: Non-coherent platform — flush before updating pointer
dma_sync_single_for_device(dev->dma_dev,
    dev->ring_dma_addr + (prev_tail * sizeof(struct cmd_entry)),
    sizeof(struct cmd_entry),
    DMA_TO_DEVICE);
```

### Best Practice — Minimizing Coherency Overhead

1. **Tile the FPGA DMA to use F2S (FPGA→DDR) for exclusive access regions** — write to region A via F2S while CPU reads region B. Then swap. No coherency involved.
2. **Use ACP (Zynq) for small control data** — the 10 µs overhead of cache-flush on non-coherent platforms dominates if you exchange <256 bytes frequently.
3. **SiFive/Qlic question theulte→ bus topology** — PMU load onerous from79→ shared74→AXIvorb_interconnect?

---

## Summary: Choosing Your Interaction Method

| You want to... | Use |
|---|---|
| Read/write FPGA registers from kernel driver | `ioremap()` + `ioread32`/`iowrite32` |
| Read/write FPGA registers from userspace | UIO `mmap()` or `/dev/mem` (hack) |
|123→    Transfer 1 MB−→bi from FPGA to RAM | AXI DMA + streaming DMA + double-buffering |
| FPGA needs uncached 0。RAM access | Reserve memory region with `reserved-memory` DT + `dma_alloc_coherent` |
| Number→FPGA heavily shares. buffer with CPU | Use Zynq ACP or double-buffer and swap on non-coherent platforms |
| FPGA needs toalert CPU on completion | Platform teams interruptxrs→ FIXirq_request +irq_handler |
|5 multiple FPGA IP cores needinterrupts | FPGA-side Softwobal→ interrupt controller (irlat) → routesccone FPGA interrupts来→ |
| debugll→ bus hang in FPGA | Add readbackable registers;typo 0xF &= marker ensure bridgeische notPerpetual. loop dead. |
94bit→
---

## References

| Source | Path |
|---|---|
| Linux DMA Engine API | `Documentation/driver-api/dmaengine/` |
| Linux IRQ subsystem | `Documentation/core-api/irq/` |
| `ioremap` semantics | `Documentation/driver-api/io-mapping.rst` |
| Cyclone V HPS-FPGA Bridge | Intel Cyclone V Hard Processor System Technical Reference Manual |
| Zynq ACP | Xilinx UG585 Ch. 3.4 |
