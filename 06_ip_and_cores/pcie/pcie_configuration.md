[← 06 IP & Cores Home](../README.md) · [← PCIe Home](README.md) · [← Project Home](../../../README.md)

# PCIe IP Configuration — BARs, MSI-X, and Parameterization

Configuring a PCIe hard block is not just about setting link speed and lane count. The real work is defining the **address map** (BARs), the **interrupt delivery** (MSI/MSI-X), and the **performance parameters** that govern how the host sees your FPGA.

---

## BAR (Base Address Register) Setup

BARs are how the host CPU maps FPGA memory into its physical address space. The host enumerates BARs during PCIe enumeration and assigns physical addresses.

### BAR Types

| BAR Type | Size Encoding | Prefetchable | Common Use |
|---|---|---|---|
| **32-bit Memory** | 1 B to 2 GB | Optional | Register maps, control/status |
| **64-bit Memory** | 1 B to 2^64 (practical: to 256 GB) | Optional | Large DMA buffers, frame buffers |
| **I/O** | 1 B to 256 B | N/A | Legacy (deprecated; avoid in new designs) |
| **Expansion ROM** | Up to 16 MB | N/A | Pre-boot firmware for endpoint |

### BAR Size Determination

The host determines BAR size by writing all-1s to the BAR and reading back:

```
Write 0xFFFF_FFFF to BAR0
Read back BAR0 = 0xFFFF_0000
→ Lower 16 bits are read-only (hardwired to 0)
→ BAR0 size = 2^16 = 64 KB
→ BAR0 requires 64 KB of address space
```

**Practical BAR sizing:**

```tcl
# Xilinx PCIe4 IP: Configure BAR0 as 64-bit, 1 GB
set_property CONFIG.PF0_BAR0_64BIT {true} [get_bd_cells pcie_0]
set_property CONFIG.PF0_BAR0_SCALE {Gigabytes} [get_bd_cells pcie_0]
set_property CONFIG.PF0_BAR0_SIZE {1} [get_bd_cells pcie_0]
```

| FPGA Memory | Recommended BAR Size | BAR Type |
|---|---|---|
| Control/status registers | 64 KB – 1 MB | 32-bit, non-prefetchable |
| DMA descriptor rings | 4 KB – 64 KB | 32-bit, non-prefetchable |
| DMA data buffer (small) | 64 MB – 256 MB | 64-bit, prefetchable |
| DMA data buffer (large) | 1 GB – 4 GB | 64-bit, prefetchable |
| DDR memory passthrough | Up to total DDR size | 64-bit, prefetchable |

> [!WARNING]
> **Prefetchable BAR**: The host may read ahead from a prefetchable BAR even if no read was issued. Use only for memory with no read side-effects (i.e., buffers, not registers).

---

## MSI and MSI-X — Interrupt Delivery

### MSI (Message Signaled Interrupts)

MSI replaces the legacy INTx# wires with in-band Memory Write TLPs:

```
FPGA Endpoint:
  └── Writes MSI TLP to host's MSI address
      (pre-configured during enumeration)
      │
      ▼
  Host CPU: Interrupt controller decodes the write
            and triggers the interrupt handler
```

MSI supports up to 32 interrupt vectors per function. Each vector maps to a different address/data pair in the MSI capability structure.

### MSI-X (Extended MSI)

MSI-X supports **up to 2048 vectors** per function and adds a per-vector mask bit:

| Feature | MSI | MSI-X |
|---|---|---|
| **Max vectors** | 32 | 2048 |
| **Per-vector mask** | No (all-or-nothing) | Yes (individual mask) |
| **Address/data** | In capability structure | In external BAR table (BAR space) |
| **Use case** | Simple accelerator, ≤32 event types | Multi-queue NIC, NVMe, GPU |

```verilog
// Sending an MSI-X interrupt (simplified)
// The PCIe hard block internally translates vector → address + data
// User logic just asserts the vector:
assign cfg_msix_int_req = |interrupt_pending;  // OR of all pending vectors
```

> For most FPGA accelerators, **MSI (32 vectors) is sufficient**. Use MSI-X only if you need >32 distinct interrupt types or need per-vector masking.

---

## Configuration Space — What Matters for FPGA

The PCIe configuration space is 4 KB of registers (256 B legacy + extended). The hard block auto-generates most of it, but you control these key fields:

| Field | Offset | Controlled By | Typical FPGA Value |
|---|---|---|---|
| **Vendor ID** | 0x00 | IP parameter | 0x10EE (Xilinx), 0x1172 (Intel), 0x11AA (Microchip) |
| **Device ID** | 0x02 | IP parameter | User-assigned |
| **Subsystem Vendor/Device ID** | 0x2C | IP parameter | User-assigned (your company's PCI-SIG ID) |
| **Max Payload Size** | 0x74[2:0] | IP parameter | 256 or 512 bytes |
| **Max Read Request Size** | 0x74[14:12] | IP parameter | 512 bytes (balance latency/throughput) |
| **MSI Capability** | 0x50 | IP parameter | Enabled, 1–32 vectors |
| **MSI-X Capability** | 0x70 (extended) | IP parameter | Enabled, table size, table BAR indicator |
| **BAR0–BAR5** | 0x10–0x24 | IP parameter | See BAR sizing above |

---

## AER (Advanced Error Reporting)

AER is a PCIe extended capability that provides detailed error logging:

```
┌── AER Registers ───────────────────────────────┐
│  Uncorrectable Error Status   (logs fatal errors)│
│  Uncorrectable Error Mask                         │
│  Correctable Error Status     (logs recoverable)  │
│  Header Log                   (TLP that caused it)│
│  Root Error Command/Status    (root port only)    │
└──────────────────────────────────────────────────┘
```

AER is **strongly recommended** for Gen3+. It provides the TLP header that triggered the error — invaluable for debugging.

---

## Performance Parameters

### Max Payload Size (MPS)

The largest TLP the endpoint can accept. Negotiated with the root complex:

| MPS | Effect |
|---|---|
| 128 B | High overhead (~20% of bandwidth lost to headers) |
| 256 B | Good compromise for mixed R/W workloads |
| 512 B | Maximum for many root complexes; best throughput |

### Max Read Request Size (MRRS)

The largest read request the endpoint can issue. Too large → higher latency for other traffic. Too small → many round-trips needed for large transfers.

**Recommended:** 512 bytes for most FPGA DMA engines.

### Completion Timeout

If a read request is not completed within this time, the requester may abort. Set to **range C or D** (50 ms to 20 seconds) for FPGA DMA — FPGA DMA engines can be slower than ASIC equivalents.

---

## Configuration Checklist

```
□ Vendor ID and Device ID assigned (use PCI-SIG assigned Vendor ID or FPGA vendor default)
□ Subsystem ID set (differentiates your card from reference designs)
□ BAR0: Control/status registers (32-bit, non-prefetchable, 64 KB)
□ BAR1: DMA buffer space (64-bit, prefetchable, size = max DMA transfer × 2 for double-buffering)
□ BAR2–BAR5: Optional additional address spaces
□ MSI enabled (≥1 vector) — without this, interrupts won't work
□ MSI-X enabled only if >32 vectors needed
□ MPS ≥ 256 bytes
□ MRRS = 512 bytes
□ AER enabled (for Gen3+)
□ Completion timeout ≥ range C
□ Lane reversal enabled if PCB routing requires it
□ PERST# timing verified: deassert AFTER FPGA configuration complete
□ REFCLK 100 MHz HCSL (not LVDS)
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **BAR size not power-of-2** | Host assigns wrong address range → access faults | Round BAR size up to nearest power-of-2 |
| **Prefetchable BAR used for registers** | Register reads return stale data (host cached) | Mark control/status BARs as non-prefetchable |
| **MSI not enabled** | `lspci -vv` shows "MSI: Enable-" | Check MSI capability enable bit in IP config |
| **MPS mismatch** | Throughput far below theoretical maximum | Check `lspci -vv` for negotiated MPS; set MPS ≥ 256 |
| **64-bit BAR not aligned** | BARs 0+1 form a pair (2 consecutive 32-bit BARs) | If using 64-bit BAR0, BAR1 is consumed — skip to BAR2 for next |
| **Missing PERST# hold time** | FPGA hard block never exits reset properly | Hold PERST# low ≥100 ms after power stable + FPGA configured |

---

## Further Reading

| Article | Topic |
|---|---|
| [pcie_hard_blocks.md](pcie_hard_blocks.md) | PCIe hard block architecture, endpoint vs root port |
| [pcie_dma.md](pcie_dma.md) | DMA engines, descriptor rings, scatter-gather throughput |
| Xilinx PG213 | UltraScale+ Devices Integrated Block for PCI Express |
| Intel AN 456 | PCI Express High Performance Reference Design |
