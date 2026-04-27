[← 06 IP & Cores Home](../README.md) · [← PCIe Home](README.md) · [← Project Home](../../../README.md)

# DMA for PCIe — XDMA, QDMA, Descriptor Rings, and Throughput

The PCIe hard block gives the host access to FPGA memory through BARs, but for bulk data transfer at line rate, you need a DMA (Direct Memory Access) engine. DMA offloads the CPU from copying data and allows the FPGA to read/write host memory directly.

---

## Why DMA Exists in PCIe

Without DMA, the host transfers data using **Programmed I/O (PIO)** — the CPU copies each word:

```
Host CPU (PIO write, no DMA):
  for (i = 0; i < 1_000_000; i++)
      *bar0_ptr++ = buffer[i];     // CPU copy → ~500 MB/s max, 100% CPU
```

With DMA, the FPGA pulls data directly from host memory:

```
Host CPU (DMA):
  dma_submit(desc);                // Submit descriptor → <1 µs CPU
  // FPGA reads 1 GB from host DRAM → ~10 GB/s, 0% CPU during transfer
  wait_for_completion();           // Poll or interrupt
```

---

## DMA Architecture

```
┌──────── Host ────────┐          ┌────── FPGA ────────────┐
│                       │          │                         │
│   Driver              │          │   DMA Engine            │
│   └── Descriptor Ring │          │   ├── Descriptor Fetcher│
│       (in host DRAM)  │◄─────────┼───┤   (reads from host) │
│                       │  PCIe    │   ├── Read Engine       │
│   Data Buffers        │◄─────────┼───┤   (H2C = Host→Card)│
│   (in host DRAM)      │──────────┼──►│   ├── Write Engine  │
│                       │          │   │   (C2H = Card→Host)│
│                       │          │   └── Interrupt Gen    │
│                       │          │                         │
└───────────────────────┘          └─────────────────────────┘
```

### Descriptor Ring

The descriptor ring is a circular buffer in host memory that the FPGA DMA engine polls:

```c
// Descriptor structure (simplified XDMA format)
struct dma_desc {
    uint32_t control;       // bit 0: start, bit 1: last, bits [7:4]: length
    uint32_t length;        // Transfer size in bytes
    uint32_t src_addr_lo;   // Source address (lower 32 bits)
    uint32_t src_addr_hi;   // Source address (upper 32 bits)
    uint32_t dst_addr_lo;   // Destination address
    uint32_t dst_addr_hi;
    uint32_t next_desc_lo;  // Next descriptor pointer (for scatter-gather)
    uint32_t next_desc_hi;
};
```

**Submission flow:**
1. Driver fills descriptor(s) in host DRAM
2. Driver writes the doorbell register (BAR0) → tells FPGA "new descriptor at index N"
3. FPGA DMA engine fetches the descriptor, executes the transfer
4. FPGA writes completion status to descriptor and (optionally) fires MSI-X interrupt

---

## Scatter-Gather DMA

Real data is rarely contiguous in physical memory. Scatter-gather chains multiple descriptors to handle fragmented buffers:

```
Descriptor 0: src=0x1000, len=4096  ─┐
Descriptor 1: src=0x3000, len=4096  ─┤  → Combined: 16 KB transfer
Descriptor 2: src=0xA000, len=4096  ─┤    from 3 non-contiguous pages
Descriptor 3: src=0xF000, len=4096  ─┘
```

The DMA engine follows the `next_desc` chain, executing each transfer and pausing on descriptors with `stop=1`.

---

## Xilinx XDMA vs QDMA

| Feature | XDMA (classic) | QDMA (queue-based) |
|---|---|---|
| **Channels** | Up to 4 H2C + 4 C2H | Up to 2048 queues |
| **Interface** | AXI4-MM per channel | AXI4-MM (bypass) or AXI4-Stream |
| **Descriptor format** | Fixed ring | Descriptor ring + completion ring |
| **Multi-queue** | No (fixed channels) | Yes (per-VF queues for SR-IOV) |
| **Throughput** | ~10 GB/s (Gen3 ×8) | ~100 GB/s (Gen5 ×16, 2k queues) |
| **Use case** | Simple accelerators | Multi-function, multi-queue, NVMe-like |
| **IP name** | `xdma` (Vivado) | `qdma` (Vivado 2018.3+) |

**XDMA for most FPGA designs.** QDMA is overkill unless you need SR-IOV with per-VF queuing.

---

## H2C vs C2H Throughput

| Direction | Mechanism | Bottleneck |
|---|---|---|
| **H2C** (Host → Card) | Host writes TLP → FPGA receives → DMA engine writes to FPGA DDR | FPGA DDR bandwidth (write side) |
| **C2H** (Card → Host) | FPGA reads FPGA DDR → DMA engine issues Memory Write TLP → host DRAM | PCIe link bandwidth (typically < DDR) |

### Performance Tuning

```c
// Linux XDMA driver: tune for high throughput
// Increase descriptor fetch burst
echo 16 > /sys/module/xdma/parameters/desc_blk_size    // Fetch 16 descriptors at once

// Enable write-combining on BAR
// Host side: mark BAR as write-combining in MTRR/PAT
// Makes PCIe writes faster (combines multiple writes into one TLP)

// Increase TLP payload size
// Set Max Payload Size = 256 or 512 in IP config
// Each TLP carries 256/512 bytes → fewer TLPs → less overhead
```

---

## Intel DMA for PCIe

Intel's DMA approach differs from Xilinx:

| IP | Interface | Use Case |
|---|---|---|
| **Intel DMA IP for PCIe** | Avalon-MM (Memory-Mapped) | Simple bulk transfer, descriptor-based |
| **MSI-X DMA** (Agilex) | Avalon-ST + Avalon-MM | High-performance, multi-queue, SR-IOV |
| **BAM (Bus Access Module)** | Avalon-MM | Low-level BAR access from user logic |

Intel's DMA IP is separate from the PCIe hard block (unlike Xilinx QDMA which integrates them). You instantiate the PCIe HIP, then add the DMA IP, then wire them together in Platform Designer.

```verilog
// Intel DMA IP: Simple descriptor-based transfer
// Descriptor layout (simplified):
// [63:32] Transfer Length (bytes)
// [31:0]  Source/Destination Address (32-bit address)
// Control: bit 0 = Go, bit 1 = Interrupt on Done
```

---

## Measuring DMA Throughput

```bash
# Linux: Test DMA throughput
# XDMA kernel module provides /dev/xdma0_h2c_0 and /dev/xdma0_c2h_0
# H2C: host writes to card
dd if=/dev/zero of=/dev/xdma0_h2c_0 bs=1M count=1000 oflag=direct
# → 1000+0 records in, 1000+0 records out, ~8.2 GB/s

# C2H: card sends to host
dd if=/dev/xdma0_c2h_0 of=/dev/null bs=1M count=1000 iflag=direct
# → 1000+0 records in, 1000+0 records out, ~7.8 GB/s
```

> **Expect 80–90% of theoretical link bandwidth** for bulk DMA. The remaining 10–20% is TLP headers, DLLP overhead, and link management.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Descriptor count mismatch** | DMA stops mid-transfer | Driver writes descriptor count; FPGA fetches N descriptors; verify count matches |
| **Doorbell write race** | DMA ignores new descriptors | Ensure doorbell write is flushed (PCIe write is posted; use read-back to force flush) |
| **Address translation missing** | DMA reads wrong host memory | Enable IOMMU bypass or use physical addresses (not virtual) in descriptors |
| **Completion ring overflow** | Completed transfers never reported to driver | Size completion ring = descriptor ring × 2 |
| **TLP size too small** | Only 25% of PCIe bandwidth used | Set MPS=256 or 512; check `lspci -vv` for negotiated value |
| **No interrupt after DMA** | Driver polls forever, wastes CPU | Enable interrupt-on-completion in descriptor control bit |
| **Cache coherence** | DMA reads stale data from host cache | Flush host CPU cache before DMA (e.g., `clflush` or use coherent DMA allocation) |

---

## Further Reading

| Article | Topic |
|---|---|
| [pcie_hard_blocks.md](pcie_hard_blocks.md) | PCIe hard block architecture, generations |
| [pcie_configuration.md](pcie_configuration.md) | BAR setup, MSI/MSI-X, performance parameters |
| Xilinx PG195 | DMA/Bridge Subsystem for PCI Express (XDMA) |
| Xilinx PG302 | QDMA Subsystem for PCI Express |
| Intel UG-20080 | Intel DMA IP for PCI Express |
