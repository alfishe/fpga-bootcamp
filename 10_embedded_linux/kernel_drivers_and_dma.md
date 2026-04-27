[← Section Home](README.md) · [← Project Home](../README.md)

# Kernel Drivers for FPGA IP — UIO, VFIO & DMA Engine

When you place a custom IP core in the FPGA fabric, someone must write a Linux driver for it. The driver translates between the kernel's abstractions (file ops, mmap, read/write) and the FPGA's reality (memory-mapped registers, DMA descriptors, interrupt lines). This article covers the three driver patterns and how to choose between them.

---

## The Three Driver Patterns

| Pattern | Kernel Code | Userspace Access | Best For |
|---|---|---|---|
| **UIO** (Userspace I/O) | Minimal shim (~30 lines) | Direct mmap + IRQ via blocking read | Prototyping, custom DSP, one-off hardware |
| **Platform Driver** | Full kernel driver (100–500 lines) | Via /dev/mydevice + ioctl + sysfs | Production IP, shared resources, kernel subsystem integration |
| **VFIO** (Virtual Function I/O) | PCIe-style passthrough | Direct userspace DMA via IOMMU | High-perf DMA, userspace drivers, DPDK |

---

## UIO — Userspace Driver in 30 Lines

The kernel side is a thin shim that exposes FPGA registers and a single interrupt:

```c
// Kernel side — minimal UIO platform driver
#include <linux/uio_driver.h>
#include <linux/platform_device.h>

static int my_uio_probe(struct platform_device *pdev) {
    struct uio_info *info;
    struct resource *res;

    info = devm_kzalloc(&pdev->dev, sizeof(*info), GFP_KERNEL);
    info->name = "myfpga-uio";
    info->version = "1.0";

    // Map register region from device tree
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    info->mem[0].addr = res->start;
    info->mem[0].size = resource_size(res);
    info->mem[0].memtype = UIO_MEM_PHYS;

    // Map interrupt
    info->irq = platform_get_irq(pdev, 0);

    return uio_register_device(&pdev->dev, info);
}

static const struct of_device_id my_uio_match[] = {
    { .compatible = "mycorp,myfpga-uio" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, my_uio_match);

static struct platform_driver my_uio_driver = {
    .probe = my_uio_probe,
    .driver = {
        .name = "myfpga-uio",
        .of_match_table = my_uio_match,
    },
};
module_platform_driver(my_uio_driver);
```

```c
// Userspace side — direct hardware access, no more syscalls
int fd = open("/dev/uio0", O_RDWR);

// mmap FPGA registers
volatile uint32_t *regs = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

regs[0] = 0x01;  // Write control register directly

// Block until FPGA interrupt fires
uint32_t irq_count;
read(fd, &irq_count, sizeof(irq_count));  // blocks here
// => IRQ received, process data
```

### UIO Decision Guide

| Good for UIO | Not for UIO |
|---|---|
| Simple register read/write | Needs DMA (UIO has no kernel DMA API) |
| Single IRQ line | Multiple prioritized IRQs |
| Single user process | Shared resource with multiple clients |
| Quick prototype | Production driver needing kernel integration (V4L2, ALSA, network) |
| Zero-copy register access | Secure multi-user access (no IOMMU protection) |

---

## Platform Driver — Production Kernel Driver

For production drivers that integrate with kernel subsystems:

```c
static int myfpga_probe(struct platform_device *pdev) {
    struct myfpga_dev *dev;
    struct resource *res;

    dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);

    // 1. ioremap FPGA registers
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    dev->regs = devm_ioremap_resource(&pdev->dev, res);

    // 2. Request IRQ
    dev->irq = platform_get_irq(pdev, 0);
    devm_request_irq(&pdev->dev, dev->irq, myfpga_isr,
                     0, "myfpga", dev);

    // 3. Register character device
    alloc_chrdev_region(&dev->devt, 0, 1, "myfpga");
    cdev_init(&dev->cdev, &myfpga_fops);
    cdev_add(&dev->cdev, dev->devt, 1);

    platform_set_drvdata(pdev, dev);
    return 0;
}

// ioctl-based control interface
static long myfpga_ioctl(struct file *filp, unsigned int cmd,
                         unsigned long arg) {
    struct myfpga_dev *dev = filp->private_data;

    switch (cmd) {
    case MYFPGA_IOC_START:
        iowrite32(0x01, &dev->regs->ctrl);
        break;
    case MYFPGA_IOC_GET_STATUS:
        return ioread32(&dev->regs->status);
    }
    return 0;
}

static const struct file_operations myfpga_fops = {
    .owner = THIS_MODULE,
    .open = myfpga_open,
    .unlocked_ioctl = myfpga_ioctl,
    .mmap = myfpga_mmap,
};
```

---

## VFIO — Userspace DMA Without Kernel Copy

VFIO exposes FPGA DMA and MMIO directly to userspace through the IOMMU. Used for high-performance networking (DPDK), GPU passthrough, and workloads where kernel DMA overhead is unacceptable.

```c
// Userspace VFIO for FPGA
int container = open("/dev/vfio/vfio", O_RDWR);
int group = open("/dev/vfio/12", O_RDWR);  // FPGA IOMMU group

ioctl(group, VFIO_GROUP_SET_CONTAINER, &container);
ioctl(container, VFIO_SET_IOMMU, VFIO_TYPE1_IOMMU);
int device = ioctl(group, VFIO_GROUP_GET_DEVICE_FD, "fpga:00:03.0");

// mmap BAR regions for direct register access
volatile void *bar0 = mmap(NULL, bar_size, PROT_READ | PROT_WRITE,
                            MAP_SHARED, device, bar_offset);

// DMA from userspace via VFIO_IOMMU_MAP_DMA
```

**VFIO is overkill for most Cyclone V / Zynq designs.** Use it when:
- Throughput demands zero-copy from FPGA to userspace
- You're writing a DPDK/SPDK-style userspace driver
- The kernel path is your measured bottleneck
- You need IOMMU-based isolation between multiple userspace drivers

---

## DMA Engine — How FPGA Moves Data to RAM

The Linux DMA Engine framework (`dmaengine`) provides a unified API for FPGA DMA controllers. The most common FPGA pattern is **cyclic DMA** with double-buffering:

```c
// Setting up cyclic DMA transfer (the standard FPGA pattern)
static int setup_fpga_dma(struct myfpga_dev *dev) {
    struct dma_async_tx_descriptor *desc;
    dma_addr_t dma_addr;
    void *buf;

    // Allocate DMA buffer (uncached on non-coherent platforms)
    buf = dma_alloc_coherent(dev->parent, BUF_SIZE,
                             &dma_addr, GFP_KERNEL);

    // Get channel from device tree ("rx" or "tx")
    dev->dma_chan = dma_request_chan(dev->parent, "rx");

    // Set up cyclic transfer (double-buffered)
    // Buffer is divided into two periods: CPU processes one half
    // while FPGA fills the other
    desc = dmaengine_prep_dma_cyclic(
        dev->dma_chan,
        dma_addr,           // destination in RAM
        BUF_SIZE,
        BUF_SIZE / 2,       // period = half-buffer
        DMA_DEV_TO_MEM,     // FPGA -> RAM
        DMA_PREP_INTERRUPT);

    desc->callback = dma_complete_callback;
    desc->callback_param = dev;

    dmaengine_submit(desc);
    dma_async_issue_pending(dev->dma_chan);

    return 0;
}

// Callback fires when each period (half-buffer) completes
static void dma_complete_callback(void *param) {
    struct myfpga_dev *dev = param;
    // Process the completed half-buffer
    // The other half is still being filled by FPGA DMA
    wake_up_interruptible(&dev->dma_wait);
}
```

---

## Choosing Buffer Types

| Buffer Type | API | Coherency | When to Use |
|---|---|---|---|
| **Coherent (uncached)** | `dma_alloc_coherent()` | Hardware-coherent or uncached | Small buffers (<64 KB), descriptor rings, control structures |
| **Streaming (cached + sync)** | `dma_map_single()` + `dma_sync_*()` | Manually synchronized | Large buffers (>64 KB), high CPU read throughput after DMA |
| **CMA (contiguous, shareable)** | `dma_alloc_from_contiguous()` | Depends on platform | FPGA frame buffers shared with display subsystem |
| **Reserved (no-map)** | `dma_declare_coherent_memory()` | FPGA-direct (no CPU) | FPGA-exclusive memory: F2S bridge, video pipes |

> **On Cyclone V SoC (non-coherent):** streaming DMA with `dma_map_single()` is preferred for buffers >16 KB. The CPU pays a ~1 µs `dma_sync_for_cpu()` cost per period but reads cached memory at ~2 GB/s instead of ~200 MB/s (uncached). On coherent platforms (Zynq ACP, PolarFire SoC), `dma_alloc_coherent()` has no performance penalty.

---

## Driver Pattern Decision Flowchart

```
┌─ Need DMA? ─Yes──┬─ Userspace driver? ─Yes──► VFIO (IOMMU DMA)
│                  │                              or UIO + kernel DMA thread
│                  └─ Kernel driver ──────────► Platform Driver + DMA Engine
│
└─ Register access only? ─┬─ Single user, simple IRQ? ─► UIO
                          │
                          └─ Multiple users, kernel integration? ─► Platform Driver
```

---

## References

| Source | Path / URL |
|---|---|
| Linux UIO HOWTO | `Documentation/driver-api/uio-howto.rst` |
| Linux DMA Engine API | `Documentation/driver-api/dmaengine/` |
| VFIO documentation | `Documentation/driver-api/vfio.rst` |
| Kernel platform driver template | `drivers/fpga/` in kernel source for FPGA Manager examples |
| [device_tree_and_overlays.md](device_tree_and_overlays.md) | Writing DT nodes that bind to these driver patterns |
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | Bridge programming — the hardware side of DMA |
