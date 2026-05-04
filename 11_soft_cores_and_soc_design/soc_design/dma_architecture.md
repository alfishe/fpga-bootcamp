[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# DMA Architecture — Data Movement in FPGA SoCs

DMA engines are the unsung heroes of FPGA SoC performance — offloading bulk data movement from the CPU, which is often 10–100× slower at memory copies than dedicated DMA. A well-designed DMA subsystem is the difference between a Zynq that processes frames at 60 fps and one that stalls at 5 fps.

This article covers DMA topologies, descriptor formats, the Xilinx AXI DMA register map, scatter-gather operation, coherency, and the Linux dmaengine API.

---

## DMA Topologies

| Architecture | Description | Best For | LUT Cost |
|---|---|---|---|
| **Centralized DMA** | One DMA engine serves all peripherals | Simple SoCs, <4 data streams | ~2,000 LUTs |
| **Distributed DMA** | Each peripheral has its own DMA | High-throughput, independent streams | ~1,000 LUTs per instance |
| **Scatter-Gather DMA** | Descriptor chain in memory → DMA follows linked list | Complex buffer management, network stacks | ~3,000 LUTs |
| **AXI CDMA** (Central DMA) | Xilinx IP: memory-to-memory copy | Memory remapping, frame buffer copy | Vendor IP |
| **AXI DMA** | Xilinx IP: AXI4-Stream ↔ AXI4 memory-mapped | Streaming IP to/from DDR (most common) | Vendor IP |
| **AXI XDMA** (PCIe DMA) | PCIe → AXI bridge with DMA | FPGA-as-PCIe-accelerator | Vendor IP |

### Simple DMA vs Scatter-Gather

```
Simple DMA:
  CPU writes: src_addr, dst_addr, length → DMA copies one contiguous block

Scatter-Gather DMA:
  CPU writes: pointer to descriptor chain → DMA follows linked list
  Each descriptor: src_addr, dst_addr, length, next_descriptor_ptr
  → DMA copies many non-contiguous blocks autonomously
```

Scatter-gather is essential for:
- Network packets (skb fragments are non-contiguous)
- Video frames (multi-planar buffers: Y, Cb, Cr in separate allocations)
- Zero-copy I/O (application buffers directly from userspace)

---

## Descriptor Formats

### Simple DMA Descriptor (MM2S / S2MM)

The CPU writes a single descriptor to the DMA register map:

```
┌──────────────────────────────────────┐
│ Source Address     [63:0]            │  ← Where to read from
├──────────────────────────────────────┤
│ Destination Address [63:0]           │  ← Where to write to
├──────────────────────────────────────┤
│ Transfer Length    [31:0]            │  ← Bytes to transfer
├──────────────────────────────────────┤
│ Control Flags      [31:0]            │  ← IRQ enable, etc.
└──────────────────────────────────────┘
```

### Scatter-Gather Descriptor (AXI DMA SG)

Each descriptor is a 64-byte structure in DDR, linked by pointers:

```
Offset  Field                Description
──────  ──────────────────── ──────────────────────────────────
0x00    NXTDESC_PTR[31:0]    Next descriptor address (low)
0x04    NXTDESC_PTR[63:32]   Next descriptor address (high)
0x08    RESERVED
0x0C    RESERVED
0x10    BUFFER_ADDR[31:0]    Source/dest buffer address (low)
0x14    BUFFER_ADDR[63:32]   Source/dest buffer address (high)
0x18    RESERVED
0x1C    RESERVED
0x20    CONTROL              [26:0]=length, [27]=EOF, [28]=IRQ
0x24    STATUS               Written by DMA after transfer
0x28-0x3C RESERVED / APP fields
```

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Descriptor 0 │────►│ Descriptor 1 │────►│ Descriptor 2 │
│ src: 0x1000  │     │ src: 0x2000  │     │ src: 0x3000  │
│ len: 1024    │     │ len: 2048    │     │ len: 512     │
│ IRQ: yes     │     │ IRQ: no      │     │ IRQ: yes     │
│ EOF: no      │     │ EOF: no      │     │ EOF: yes     │
│ next: 0x400  │     │ next: 0x500  │     │ next: NULL   │
└──────────────┘     └──────────────┘     └──────────────┘
```

The CPU writes descriptors to shared memory, then kicks the DMA engine. The DMA follows the linked list autonomously — zero CPU involvement per transfer.

**Key flags:**
- **EOF (End of Frame):** Marks the last descriptor of a frame/packet. The DMA asserts `tlast` on the AXI-Stream for this descriptor.
- **IRQ:** Generate an interrupt after this descriptor completes.

---

## Xilinx AXI DMA — Register Map (PG021)

The [AXI DMA](https://docs.amd.com/r/en-US/pg021_axi_dma/AXI-DMA-Register-Address-Map) is the most widely-used DMA IP in FPGA SoC designs. It has two independent channels: **MM2S** (memory-mapped → streaming) and **S2MM** (streaming → memory-mapped).

### MM2S Channel (Memory → Stream)

| Offset | Register | Reset | Description |
|---|---|---|---|
| 0x00 | MM2S_DMACR | 0x10001 | DMA control: Run/Stop (bit 0), IRQ_en (bit 12), Cyclic (bit 4) |
| 0x04 | MM2S_DMASR | 0x0 | DMA status: Halted (bit 0), Idle (bit 1), SGInc (bit 3), IRQ (bit 1) |
| 0x18 | MM2S_SA (low) | 0x0 | Source address [31:0] (simple mode) |
| 0x1C | MM2S_SA (high) | 0x0 | Source address [63:32] |
| 0x28 | MM2S_LENGTH | 0x0 | Transfer length in bytes (1–8,388,607) |
| 0x40 | MM2S_CUR_DESC | 0x0 | Current descriptor pointer (SG mode) |
| 0x48 | MM2S_TAIL_DESC | 0x0 | Tail descriptor pointer (SG mode) |

### S2MM Channel (Stream → Memory)

| Offset | Register | Reset | Description |
|---|---|---|---|
| 0x30 | S2MM_DMACR | 0x10001 | DMA control (same bit layout as MM2S) |
| 0x34 | S2MM_DMASR | 0x0 | DMA status |
| 0x48 | S2MM_DA (low) | 0x0 | Destination address [31:0] (simple mode) |
| 0x4C | S2MM_DA (high) | 0x0 | Destination address [63:32] |
| 0x58 | S2MM_LENGTH | 0x0 | Max transfer length (buffer size) |
| 0x70 | S2MM_CUR_DESC | 0x0 | Current descriptor pointer (SG mode) |
| 0x78 | S2MM_TAIL_DESC | 0x0 | Tail descriptor pointer (SG mode) |

### Programming Sequence (Simple Mode — MM2S)

```c
// 1. Reset the DMA
*((volatile uint32_t *)(DMA_BASE + 0x00)) = 0x00010004;  // DMACR: reset
while (*((volatile uint32_t *)(DMA_BASE + 0x04)) & 0x01); // Wait for reset done

// 2. Set source address
*((volatile uint32_t *)(DMA_BASE + 0x18)) = src_addr_low;
*((volatile uint32_t *)(DMA_BASE + 0x1C)) = src_addr_high;

// 3. Enable IRQs
*((volatile uint32_t *)(DMA_BASE + 0x00)) = 0x00011001;  // DMACR: run + IOC_IRQ_en

// 4. Start transfer (writing LENGTH starts the DMA)
*((volatile uint32_t *)(DMA_BASE + 0x28)) = length;
// DMA reads from src_addr and outputs on AXI-Stream
```

### Programming Sequence (Scatter-Gather Mode)

```c
// 1. Reset + enable SG
*((volatile uint32_t *)(DMA_BASE + 0x00)) = 0x00010004;  // Reset
while (*((volatile uint32_t *)(DMA_BASE + 0x04)) & 0x01);

// 2. Write CUR_DESC pointer (head of descriptor chain)
*((volatile uint32_t *)(DMA_BASE + 0x40)) = desc_chain_phys_addr;

// 3. Start DMA
*((volatile uint32_t *)(DMA_BASE + 0x00)) = 0x00011001;  // Run + IRQ

// 4. Write TAIL_DESC pointer (tail of new descriptors)
//    DMA fetches and processes descriptors from CUR to TAIL
*((volatile uint32_t *)(DMA_BASE + 0x48)) = tail_desc_phys_addr;

// DMA autonomously follows the linked list.
// When it hits TAIL, it pauses and waits for the CPU to update TAIL.
```

---

## Linux DMA Driver (dmaengine API)

Linux provides a generic DMA framework (`dmaengine`) that abstracts vendor-specific DMA hardware. The Xilinx AXI DMA has a kernel driver: `xilinx_dma`.

### Device Tree Binding

```dts
// Zynq Ultrascale+ device tree
axi_dma_0: dma@a0000000 {
    compatible = "xlnx,axi-dma-1.00.a";
    reg = <0x0 0xa0000000 0x0 0x1000>;
    #dma-cells = <1>;
    clocks = <&clk 71>, <&clk 71>;
    clock-names = "dma_clk", "m_axi_sg_aclk";
    interrupts = <0 89 4>, <0 90 4>;  // MM2S, S2MM
    interrupt-parent = <&gic>;

    dma-channel@a0000000 {
        compatible = "xlnx,axi-dma-mm2s-channel";
        xlnx,device-id = <0>;
        xlnx,datawidth = <0x20>;    // 512-bit data width
    };

    dma-channel@a0000030 {
        compatible = "xlnx,axi-dma-s2mm-channel";
        xlnx,device-id = <1>;
        xlnx,datawidth = <0x20>;
    };
};
```

### Kernel Driver: Submit a DMA Transfer

```c
#include <linux/dmaengine.h>
#include <linux/dma-mapping.h>

struct dma_chan *chan;
struct dma_async_tx_descriptor *tx;
dma_addr_t src_buf, dst_buf;
enum dma_status status;

// 1. Request DMA channel
chan = dma_request_chan(dev, "tx");  // "tx" matches DT label

// 2. Allocate coherent buffers
src_buf = dma_map_single(dev, src_virt, SIZE, DMA_TO_DEVICE);
dst_buf = dma_map_single(dev, dst_virt, SIZE, DMA_FROM_DEVICE);

// 3. Prepare DMA descriptor
tx = dmaengine_prep_dma_memcpy(chan, dst_buf, src_buf, SIZE,
                                 DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
if (!tx) return -ENOMEM;

// 4. Set completion callback
tx->callback = dma_complete_cb;
tx->callback_param = &comp;

// 5. Submit and issue
dmaengine_submit(tx);
dma_async_issue_pending(chan);

// 6. Wait for completion
wait_for_completion(&comp);

// 7. Cleanup
dma_unmap_single(dev, src_buf, SIZE, DMA_TO_DEVICE);
dma_unmap_single(dev, dst_buf, SIZE, DMA_FROM_DEVICE);
dma_release_channel(chan);
```

### Userspace DMA with UIO

For low-latency FPGA applications, bypass the kernel DMA driver and program the DMA registers directly from userspace:

```c
#include <sys/mman.h>
#include <fcntl.h>

// Map DMA registers via UIO
int fd = open("/dev/uio0", O_RDWR);
volatile uint32_t *dma = mmap(NULL, 0x1000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

// Map DMA buffer via hugepages or UIO
volatile void *buffer = mmap(NULL, BUF_SIZE,
    PROT_READ | PROT_WRITE, MAP_SHARED, mem_fd, phys_addr);

// Program DMA directly (same sequence as bare-metal)
dma[0x00 >> 2] = 0x10001;          // DMACR: run
dma[0x18 >> 2] = buffer_phys_low;  // Source address
dma[0x1C >> 2] = buffer_phys_high;
dma[0x28 >> 2] = SIZE;             // Start transfer

// Wait for IRQ via read() on UIO fd
uint32_t irq_count;
read(fd, &irq_count, sizeof(irq_count));
```

---

## Coherency Considerations

| DMA Type | Coherency | When to Use |
|---|---|---|
| **Non-coherent DMA** | CPU must flush/invalidate caches before/after | Default on most FPGA SoCs; simplest |
| **ACP-coherent DMA** (Zynq-7000) | FPGA accesses CPU cache via Snoop Control Unit | Shared data structures between CPU and FPGA |
| **AXI4 ACE-Lite** (Zynq UltraScale+) | Coherent transactions at CCI level | Multi-core SoCs with FPGA accelerators |

### Non-Coherent DMA — Manual Cache Management

```c
// Before DMA reads from buffer (CPU → FPGA):
dma_sync_single_for_device(dev, dma_handle, size, DMA_TO_DEVICE);
// This flushes CPU cache → data is visible to DMA in DDR

// After DMA writes to buffer (FPGA → CPU):
dma_sync_single_for_cpu(dev, dma_handle, size, DMA_FROM_DEVICE);
// This invalidates CPU cache → CPU reads fresh data from DDR
```

**If you skip cache maintenance, the CPU may read stale cached data instead of what the DMA wrote.** This is the #1 DMA bug in FPGA SoC designs.

### ACP (Accelerator Coherency Port) — Zynq-7000

ACP allows the FPGA to access the CPU's L2 cache directly. When the DMA reads an address through ACP, the SCU (Snoop Control Unit) checks if the data is in L2 — if so, it returns cached data without going to DDR.

```
FPGA DMA ──► ACP port ──► SCU ──► L2 Cache ──► DDR
                                 ↑ Snoop hit: return cached data
```

- **Pros:** Zero cache maintenance overhead; coherent by default
- **Cons:** Only on Zynq-7000 (not UltraScale+); limited bandwidth (~1/4 of HP ports); only 1 ACP port

### CCI (Cache Coherent Interconnect) — Zynq UltraScale+

Zynq UltraScale+ uses ARM CCI-400 for hardware coherency. The FPGA connects via ACE-Lite (coherent slave) ports.

```
A53 L2 ──► CCI-400 ──► DDR4
               ▲
FPGA PL ───────┘ ACE-Lite coherent slave
```

- **Pros:** Full hardware coherency with all CPU cores; multiple coherent ports
- **Cons:** ACE-Lite adds latency vs non-coherent HP ports; coherent transactions are more complex

---

## Common DMA Design Patterns

### Pattern 1: Streaming IP → DDR (S2MM)

```
ADC / Sensor ──► AXI-Stream ──► AXI DMA (S2MM) ──► DDR
                                    │
                                    └── IRQ → CPU processes buffer
```

Used for: video capture, ADC data acquisition, network RX.

### Pattern 2: DDR → Streaming IP (MM2S)

```
DDR ──► AXI DMA (MM2S) ──► AXI-Stream ──► DAC / TX
              │
              └── CPU fills buffer, kicks DMA
```

Used for: video display, DAC output, network TX.

### Pattern 3: Zero-Copy Network Stack

```
Ethernet MAC ──► AXI DMA (S2MM) ──► DDR (skb fragments)
                                         │
                                         └── CPU processes without copy
DDR (skb fragments) ──► AXI DMA (MM2S) ──► Ethernet MAC
```

Both directions use scatter-gather DMA to map directly to socket buffer fragments — no intermediate copy.

### Pattern 4: Bidirectional Accelerator

```
DDR ──► MM2S ──► FPGA Accelerator ──► S2MM ──► DDR
                  (e.g., ML inference)
                  │
                  └── CTRL registers via AXI-Lite
```

CPU sets up both MM2S and S2MM descriptors, then starts both channels. The accelerator reads input stream, processes, and outputs result stream.

---

## iDMA — Open-Source Modular DMA

ETH Zürich's [iDMA](https://github.com/pulp-platform/idma) is a modular, open-source DMA engine:
- Backend-agnostic (AXI, TileLink, custom interconnect)
- 1D/2D transfers with configurable burst size
- Written in SystemVerilog, FPGA-proven on PULP platform
- Supports address translation (for virtual memory systems)
- No vendor IP dependency — works on any FPGA

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Forgetting cache maintenance** | CPU reads stale data after DMA write | Call `dma_sync_single_for_cpu()` after S2MM |
| **Buffer not DMA-allocated** | Kernel oops or IOMMU fault | Use `dma_alloc_coherent()` or `dma_map_single()` |
| **SG TAILDESC not updated** | DMA stops after first chain | CPU must update TAILDESC after adding new descriptors |
| **AXI-Stream backpressure** | DMA stalls, no data flow | Ensure S2MM has buffer ready before streaming IP sends data |
| **Wrong byte ordering** | Data appears byte-swapped | Check AXI data width and byte-lane mapping; AXI DMA is little-endian |
| **Descriptor alignment** | DMA reads garbage | Descriptors must be 64-byte aligned (AXI DMA requirement) |
| **Length = 0 on S2MM** | DMA hangs | S2MM LENGTH is the *maximum* buffer size, never write 0 |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [PG021 — AXI DMA Product Guide](https://docs.amd.com/r/en-US/pg021_axi_dma/AXI-DMA-Register-Address-Map) | AMD/Xilinx | Complete register map, SG descriptor format, timing diagrams |
| [Linux DMA Engine Client API](https://docs.kernel.org/6.2/driver-api/dmaengine/client.html) | kernel.org | Kernel DMA API reference |
| [HPS-FPGA Bridges (Zynq)](../../10_embedded_linux/03_hps_fpga_bridges/hps_fpga_bridges_xilinx_zynq.md) | This KB | AXI port selection (HP vs ACP vs HPC), address translation |
| [Multi-Core Coherency](multi_core_coherency.md) | This KB | ACP vs CCI vs ACE, cache stashing |
| [Memory Map Design](memory_map_design.md) | This KB | Address decoder patterns, AXI address filtering |
| [Interrupt Routing](interrupt_routing.md) | This KB | GIC, PLIC, NVIC, FPGA IRQ mapping |
