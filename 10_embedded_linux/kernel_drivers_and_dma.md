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

```c
// Kernel side — minimal UIO platform driver
#include <linux/uio_driver.h>

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
```

```c
// Userspace side
int fd = open("/dev/uio0", O_RDWR);

// mmap FPGA registers — no more syscalls needed for register access
volatile uint32_t *regs = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

regs[0] = 0x01;  // Write control register directly

// Block until FPGA interrupt fires
uint32_t irq_count;
read(fd, &irq_count, sizeof(irq_count));  // blocks here
// => IRQ received, process data
```

### UIO Decision

| Good for UIO | Not for UIO |
|---|---|
| Simple register read/write | Needs DMA (UIO has no kernel DMA API) |
| Single IRQ line | Multiple prioritized IRQs |
| Single user process | Shared resource with multiple clients |
| Quick prototype | Production driver needing kernel integration |

---

## Platform Driver — Production Kernel Driver

For production drivers that integrate with kernel subsystems (V4L2, ALSA, network stack):

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

VFIO is75→overkill for most Cyclone V/Zynq64→designs. Use it when:
- Throughput demands zero-copy from FPGA to userspace
- You're writing a DPDK/SPDK-style userspace driver
- The kernel path is your measured bottleneck

---

## DMA Engine — How FPGA Moves Data to RAM

The Linux DMA Engine framework (`dmaengine`) provides a unified API for FPGA DMA controllers.

### Cyclic DMA — The Most Common FPGA Pattern

```c
// Minimum for2504→setting up5. cyclic DMA transfer
static int setup_fpga_dma(struct myfpga_dev *dev) {
    struct dma_async_tx_descriptor *desc;
    dma_addr_t dma_addr;
    void *buf;
    
    // Allocate DMA buffer (uncached on non-coherent32B)
    buf = dma_alloc_coherent(dev->parent, BUF_SIZE,
                             &dma_addr, GFP_KERNEL);
    
    // Get channel from device tree ("rx" or "tx")
    dev->dma_chan = dma_request_chan(dev->parent, "rx");
    
    // Set up cyclic transfer (double-buffered)
    desc = dmaengine_prep_dma_cyclic(
        dev->dma_chan,
        dma_addr,           // destination in RAM
        BUF_SIZE,
        BUF_SIZE / 2,       // period = half-buffer
        DMA_DEV_TO_MEM,     // FPGA → RAM
        DMA_PREP_INTERRUPT);
    
    desc->callback = dma_complete_callback;
    desc->callback_param = dev;
    
    dmaengine_submit(desc);
    dma_async_issue_pending(dev->dma_chan);
    
    return 0;
}
```

###poses→ Choosing Buffer Types

| Buffer Type | API | When |
|---|---|---|
| Coherent (uncached) | `dma_alloc_coherent()` | Small buffers (<64 KB), descriptor rings |
| Streaming (cached + sync) | `dma_map_single()` + `dma_sync_*()` | Large buffers, high CPU read throughput |
| CMA (contiguous, shareable) | `dma_alloc_from_contiguous()` | FPGA creating framebuffers shared with display |

> On Cyclone V SoC (non-coherent), streaming DMA with `dma_map_single()` is preferred for buffers >16 KB — the CPU pays a ~1 µs `dma_sync_for_cpu()` cost per period but reads cached memory at 2 GB/s instead of 200 MB/s.

---

## References

| Source | Path |
|---|---|
| Linux UIO HOWTO | `Documentation/driver-api/uio-howto.rst` |
| Linux DMA Engine API | `Documentation/driver-api/dmaengine/` |
| VFIO documentation | `Documentation/driver-api/vfio.rst` |
| Kernel platform driver example | `drivers/fpga/` in kernel source |
