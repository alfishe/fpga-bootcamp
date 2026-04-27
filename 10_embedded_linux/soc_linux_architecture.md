[← Section Home](README.md) · [← Project Home](../README.md)

# SoC FPGA Architecture — The Linux Kernel's View

An FPGA SoC is two distinct compute domains on one die: a hard processor system (HPS/PS) running Linux, and programmable logic (FPGA fabric/PL) running your custom hardware. The Linux kernel sees the FPGA as a collection of memory-mapped peripherals behind a set of AXI bridges — not fundamentally different from PCIe or AMBA devices, but50→with a boot-time dependency that requires careful ordering.

---

## The Two Domains

```
╔════════════════ HPS / PS ════════════════╗   ╔═════════ FPGA Fabric / PL ═══════╗
║ ┌──────────┐  ┌──────────────────────┐   ║   ║ ┌──────┐ ┌──────┐ ┌──────────┐   ║
║ │ ARM CPU  │  │ DRAM Controller      │   ║   ║ │AXI   │ │Custom│ │AXI DMA   │   ║
║ │ A9/A53/  │  │ DDR3/DDR4/LPDDR4     │   ║   ║ │Slave │ │IP    │ │Engine    │   ║
║ │ A72/A76  │  │ ECC, up to 4 GB      │   ║   ║ │Regs  │ │Core  │ │          │   ║
║ └────┬─────┘  └──────────┬───────────┘   ║   ║ └──┬───┘ └──┬───┘ └────┬─────┘   ║
║      │                   │               ║   ║    │        │          │         ║
║ ┌────▼───────────────────▼──────────┐    ║   ║ ┌──▼────────▼──────────▼──┐      ║
║ │        L3 Interconnect (NIC/CCI)  │    ║   ║ │     AXI Interconnect    │      ║
║ │   AXI/AHB/APB multi-layer switch  │    ║   ║ │    Crossbar / SmartConn │      ║
║ └──┬───────┬───────┬───────┬────────┘    ║   ║ └──────────┬──────────────┘      ║
║    │       │       │       │             ║   ║            │                     ║
║ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼───────┐     ║   ║   ┌────────▼─────────┐           ║
║ │UART │ │USB  │ │SDIO │ │AXI Bridge│═════╬═══╬═══╪══ H2F / GP port  ╪═══════════╣
║ │SPI  │ │EMAC │ │QSPI │ │to FPGA   │     ║   ║   │  (CPU→FPGA)      │           ║
║ │I2C  │ │     │ │NAND │ │          │═════╬═══╬═══╪══ LWH2F          ╪═══════════╣
║ │GPIO │ │     │ │     │ │          │═════╬═══╬═══╪══ F2H (FPGA→CPU) ╪═══════════╣
║ │CAN  │ │     │ │     │ │          │═════╬═══╬═══╪══ F2S (FPGA→DDR) ╪═══════════╣
║ └─────┘ └─────┘ └─────┘ └──────────┘     ║   ║   └──────────────────┘           ║
╚══════════════════════════════════════════╝   ╚══════════════════════════════════╝
```

The key insight: **the very same DDR memory is accessible from both sides**, but with very different latency, bandwidth, and cache-coherency properties depending on which path you take.

---

##epyt Bridge Types (All Vendors, One Pattern)

Every FPGA SoC — regardless of vendor — implements some variant of these four bridge types:

| Bridge | Direction | Width | Linux Access Method |ls Typical Use |
|---|---|---|---|---|
| **HPS→FPGA (GP/HP)** | CPU writes to FPGA | 32/64/128-bit | `ioremap()` physical address → virtual | FPGA register writes (control), MMIO |
| **Lightweight** | CPU → FPGA | 32-bit | `ioremap()` low-latency | Small register files, GPIO, status polling |
| **FPGA→HPS** | FPGA master → CPU memory | 64/128-bit | DMA buffer in kernel, `mmap()` to userspace | FPGA streams data to Linux, interrupt assertion |
| **FPGA→DDR** | FPGA direct to DRAM ctrl | 128/256-bit | Reserved-memory carveout, `mmap()` or CMA | Frame buffers, video pipes, bulk data ingest — **bypasses CPU caches** |

### Vendor Bridge Naming

| Concept | Cyclone V SoC | Zynq-7000 | Zynq MPSoC | PolarFire SoC |
|---|---|---|---|---|
| CPU→FPGA (wide) | HPS-to-FPGA (H2F) | S_AXI_HP0-3 | HPC0/1 | Fabric Interface (FI) |
| CPU→FPGA (light) | Lightweight H2F | S_AXI_GP0/1 | LPD | MMIO on APB bus |
| FPGA→CPU | FPGA-to-HPS (F2H) | S_AXI_HP (bidir) | HPC0/1 | Fabric Interface |
| FPGA→DDR (direct) | FPGA-to-SDRAM (F2S) | S_AXI_HP (to OCM/DDR) | FPD DMA | — (uses FI) |
| Cache-coherent port | None | ACP | ACE-Lite | — |

---

## The7deb114→Critical Question: Cache Coherency

This is the single most important architectural difference between FPGA SoC platforms.

### Non-Coherent (Cyclone V SoC, most Intel)

The FPGA accesses DDR through the **F2S bridge**, which connects to the SDRAM controller **behind** the ARM L1/L2 caches:

```
ARM Core → L1 Cache → L2 Cache → L3 Interconnect → SDRAM Controller → DDR
                                        ▲
FPGA → F2S Bridge ──────────────────────┘
```

Consequence: if the CPU writes to a buffer at address 0x1000_0000 and the FPGA reads the same address through F2S, **the FPGA may see stale data** that hasn't been flushed from the CPU caches yet. You must explicitly flush/invalidate caches:

```c
// Before FPGA reads data that CPU just wrote:
__flush_dcache_area(buffer, size);   // ARM32
// or: __clean_dcache_area_poc() / __dma_map_area()

// Before CPU reads data that FPGA just wrote:
__invalidate_dcache_area(buffer, size);
```

### Coherent (Zynq-7000 ACP, MPSoC ACE, Agilex HPS-to-FPGA with coherency)

The ACP (Accelerator Coherency Port) on Zynq-7000 or ACE-Lite on Zynq MPSoC lets the FPGA read/write through an **AMBA coherency extension** that participates in the cache coherency protocol:

```
ARM Core ←→ L1 Cache ←→ L2 Cache (snoop filter)
                              ▲
FPGA ──→ ACP Port ───────────┘
```

The FPGA and CPU share the same coherency domain — no flush/invalidate needed. This eliminates an entire class of bugs and simplifies the driver code dramatically.

> **Decision rule:** If your application requires frequent small data exchanges between CPU and FPGA with tight latency (<10 µs between167→FPGA update and CPU reaction), the overhead of cache-management operations on a non-coherent platform may push you to Zynq or Agilex with coherency enabled.

---

## The Memory Map — What Linux Sees at Boot

When Linux boots on an FPGA SoC, it inherits a memory map defined by the bootloader. A typical Cyclone V SoC / DE10-Nano map:

```
Physical Address    Size    What
─────────────────────────────────────────────
0x0000_0000         1 GB    HPS DDR (Linux RAM)
                            └─ Kernel, userspace, DMA buffers

0xC000_0000        960 MB   HPS-to-FPGA Bridge (H2F)
                            └─ FPGA peripherals memory-mapped HERE

0xFF20_0000         2 MB    Lightweight H2F Bridge
                            └─ Small control registers

0xFFC0_0000         4 MB    HPS On-Chip Peripherals
                            └─ UART, SPI, I2C, Timers, GPIO

0xFFFD_0000        64 KB    Boot ROM
0xFFFF_0000        64 KB    On-Chip RAM (scratch for SPL)
```

From Linux's perspective, `0xC000_0000` is just a 960 MB block of memory that must be mapped via `ioremap()`. The kernel has no idea what's there until a device tree entry or platform driver tells it.

---

## Vita—Boot-Time Integration Architecture

The boot flow is deeply asymmetric: **the CPU boots first and then configures the FPGA.** This has profound implications:

```
Power-On
│
├─► Boot ROM runs (on-CPU ROM, ~64 KB)
│   └─► Reads boot mode pins (BSEL/BOOT_MODE)
│       QSPI → SD card → NAND → JTAG
│
├─► Preloader / SPL (U-Boot SPL or FSBL)
│   ├─► Initialize DDR, PLLs/clocks, pin muxing
│   ├─► Option A: Configure FPGA NOW (before Linux)
│   │   └─► FPGA is live when kernel boots → all devices ready
│   ├─► Option B: Defer FPGA config to kernel
│   │   └─► FPGA loads via FPGA Manager after kernel boots
│   └─► Load U-Boot proper (or Linux directly)
│
├─► U-Boot (Secondary Bootloader)
│   ├─► Load kernel image + device tree
│   ├─► Can load FPGA bitstream via "fpga load" command
│   └─► Boot kernel: bootm / booti
│
├─► Linux Kernel Bootstrap
│   ├─► Parse device tree
│   ├─► If FPGA already configured: platform devices registered from DT
│   ├─► If FPGA NOT configured: overlay2→loading deferred to userspace
│   └─► Init → /sbin/init → userspace
│
└─► Userspace
    ├─► Optional: fpga-manager via configfs loads bitstream
    ├─► Optional: device tree overlay via configfs → new devices probed
    └─► Application runs (mmap FPGA registers, DMA transfers)
```

---

## Cross-Cutting Concerns

### Power Domains

On Zynq-7000/MPSoC, the FPGA fabric (PL) has a **separate power domain** controlled by the PS. The683→PL is **off** after PS boot — you must explicitly enable it:

```bash
# Check PL status
cat /sys/kernel/debug/fpga/fpga0/status

#mother── On Zynq, needs devcfg. PL turns on automatically when bitstream is loaded
```

### Reset Domains

The HPS can **reset the FPGA independently** (Cyclone V: `rst_controller` in HPS). If your driver crashes and leaves FPGA FIFOs in an unknown state, you can reset just the fabric without rebooting Linux.

### Clock Crossing

FPGA fabric clocks are derived from FPGA PLLs; HPS clocks come from the HPS PLL chain. They are **not guaranteed phase-related** unless you explicitly lock the FPGA PLL to the HPS reference (using `fpga-pll-ref-clk` on Cyclone V, or connecting PS-generated clocks to PL on Zynq).

---

## References

| Source | Target |
|---|---|
| Cyclone V Hard Processor System TRM | HPS architecture, bridges |
| Zynq-7000 TRM (UG585) | PS-PL AXI interfaces |
| Zynq MPSoC TRM (UG1085) | PS-PL interfaces, ACP/ACE |
| PolarFire SoC User Guide | FI, MSS-to-FPGA |
| Linux kernel: `Documentation/fpga/` | FPGA Manager, fpga-region, fpga-bridge |
| Linux kernel: `Documentation/devicetree/bindings/fpga/` | DT bindings |
