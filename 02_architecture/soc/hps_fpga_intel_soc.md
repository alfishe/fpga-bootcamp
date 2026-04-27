[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Intel SoC FPGA — HPS-FPGA Bridge Architecture

How the Intel Hard Processor System (HPS) communicates with FPGA fabric across Cyclone V SoC, Arria 10 SoC, Stratix 10 SoC, Agilex 5 SoC, and Agilex 7 SoC families. Covers bridge topology, memory maps, bandwidth budgets, and the fundamental non-coherency model that defines Intel's approach.

---

## The Intel Bridge Model: Four Bridges, No Coherency

Intel SoC FPGAs use a fixed set of AXI bridges between the HPS and FPGA fabric. Unlike Xilinx Zynq, **there is no cache coherency** — FPGA masters bypass the CPU L2 cache entirely when accessing DDR.

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
                    │  │    ARM NIC-301 / CoreLink │      │
                    │  └────┬──────────┬─────┬─────┘      │
                    │       │          │     │            │
                    └───────┼──────────┼─────┼────────────┘
                            │          │     │
              ┌─────────────┼──────────┼─────┼─────────────┐
              │             ▼          ▼     ▼             │
              │  FPGA Fabric ───────────────────────────── │
              │                                            │
              │   ┌─────┐  ┌─────┐  ┌─────┐  ┌──────────┐  │
              │   │H2F  │  │LWH2F│  │F2H  │  │  F2S     │  │
              │   │64-b │  │32-b │  │64-b │  │6× cmd    │  │
              │   │AXI  │  │AXI  │  │AXI  │  │4R/4W data│  │
              │   └─────┘  └─────┘  └─────┘  └──────────┘  │
              │                                            │
              └────────────────────────────────────────────┘
```

**Key architectural principle:** The HPS and FPGA fabric are **independent clock domains**. The bridges contain asynchronous FIFOs that tolerate large frequency mismatches (e.g., HPS at 800 MHz, FPGA at 150 MHz for a retro-computing core). This is why Intel SoCs are popular for MiSTer and other FPGA-computing projects — the CPU and fabric clocks are decoupled.

---

## Bridge Inventory by Family

| Bridge | Direction | Width | Protocol | Cyclone V / Arria 10 | Stratix 10 | Agilex 5 / 7 |
|---|---|---|---|---|---|---|
| **H2F** | HPS → FPGA | 64-bit | AXI-3 | ✓ | ✓ AXI-4 | ✓ AXI-4 |
| **LWH2F** | HPS → FPGA | 32-bit | AXI-3 | ✓ | ✓ AXI-4 | ✓ AXI-4 |
| **F2H** | FPGA → HPS | 64-bit | AXI-3 | ✓ | ✓ AXI-4 | ✓ AXI-4 |
| **F2S** | FPGA → DDR | 16-256 bit | AXI-3 | 6 cmd + 4R/4W | — | — |

> **Note:** Stratix 10 and Agilex families do **not** expose dedicated F2S ports. Instead, the FPGA fabric accesses DDR through the HPS SDRAM scheduler via the F2H bridge or through a dedicated FPGA DDR controller (hard memory controller in the fabric). The F2S bridge is unique to Cyclone V and Arria 10 SoC.

### AXI-3 vs AXI-4: The WID Problem

Cyclone V and Arria 10 use AXI-3, which includes the **WID** signal for write interleaving. AXI-4 (Stratix 10, Agilex) removes WID and relies on in-order write data. If you connect third-party AXI-4 IP to a Cyclone V H2F bridge:

1. The IP expects no WID and sends write data in AWID order
2. The bridge still accepts WID but the IP doesn't drive it
3. **Result:** Write reordering bugs, data corruption in burst writes

**Fix:** Insert an AXI-4 to AXI-3 protocol converter (available in Intel Platform Designer / Qsys) between the IP and the bridge.

---

## H2F — HPS-to-FPGA Bridge

The primary control path. The Linux kernel, U-Boot, or bare-metal code on the HPS uses this bridge to read/write registers in the FPGA fabric.

### Properties

| Property | Value |
|---|---|
| Data width | 64-bit |
| Address width | 32-bit (4 GB space) |
| Protocol | AXI-3 (CV/Arria 10), AXI-4 (Stratix 10/Agilex) |
| Clock | HPS clock (async FIFO to fabric) |
| Burst support | Up to 16 beats |
| Typical use | MMIO register banks, on-chip RAM, DMA descriptors |

### Memory Map (Cyclone V SoC Example)

The H2F bridge is mapped into the HPS address space at a fixed base address. FPGA peripherals appear as memory-mapped devices:

```
HPS Address Space (Cyclone V):
0x0000_0000 ──► 0xBFFF_FFFF   DDR SDRAM (3 GB)
0xC000_0000 ──► 0xCFFF_FFFF   On-chip RAM (256 KB)
0xFC00_0000 ──► 0xFFFF_FFFF   HPS peripherals (L3, timers, UART)

H2F Windows:
0xC000_0000 ──► 0xC003_FFFF   LWH2F (lightweight, 256 KB)
0xC000_0000 ──► 0xDFFF_FFFF   H2F (960 MB window)
```

In Linux, these regions appear under `/sys/class/fpga_manager/` or are mmap'd via `/dev/mem`. Device trees for Intel SoC declare the `hps_0_bridges` node with `ranges` that map H2F/LWH2F windows.

### Linux Access Example

```c
// mmap the H2F bridge region (simplified)
int fd = open("/dev/mem", O_RDWR | O_SYNC);
volatile uint32_t *fpga_regs = mmap(NULL, 0x10000,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0xC0000000);

// Write to a custom peripheral at offset 0x1000
fpga_regs[0x1000 / 4] = 0xDEADBEEF;

// Read back status
uint32_t status = fpga_regs[0x1004 / 4];
```

> **Best practice:** Use UIO (Userspace I/O) kernel driver instead of `/dev/mem` for production. UIO maps the bridge window through a proper device node and handles interrupts.

---

## LWH2F — Lightweight HPS-to-FPGA Bridge

A 32-bit, lower-latency version of H2F optimized for small control transactions.

### Why It Exists

The full H2F bridge has deep FIFOs and wide datapaths optimized for burst DMA. For simple register peeks and pokes (e.g., toggling an LED, checking a FIFO empty flag), this adds unnecessary latency. LWH2F is **cut-through** — transactions propagate faster because the bridge logic is simpler.

| Property | LWH2F | H2F |
|---|---|---|
| Data width | 32-bit | 64-bit |
| Burst support | Single beat only | Up to 16 beats |
| Latency | ~3-4 cycles | ~6-10 cycles |
| Address space | 2 MB | 960 MB |
| Use case | GPIO, simple control regs | DMA, framebuffers, bulk data |

### Typical RTL Connection

```verilog
// In Platform Designer, LWH2F appears as an Avalon-MM or AXI master
// Connect to a simple register bank:

module ctrl_regs (
    input         clk,
    input         reset,
    // LWH2F interface (Avalon-MM slave)
    input  [15:0] avs_address,
    input         avs_read,
    output [31:0] avs_readdata,
    input         avs_write,
    input  [31:0] avs_writedata,
    output        avs_waitrequest
);
    reg [31:0] regs [0:15];
    assign avs_readdata = regs[avs_address[5:2]];
    always @(posedge clk) begin
        if (avs_write) regs[avs_address[5:2]] <= avs_writedata;
    end
    assign avs_waitrequest = 1'b0; // Combinatorial response
endmodule
```

---

## F2H — FPGA-to-HPS Bridge

The reverse path: FPGA logic acts as AXI master, the HPS acts as slave. This lets the FPGA push data into HPS memory or interrupt the CPU.

### Properties

| Property | Value |
|---|---|
| Data width | 64-bit |
| Address width | 32-bit |
| Target | HPS DDR (via L3), on-chip RAM, HPS peripherals |
| Protocol | AXI-3 / AXI-4 |

### Typical Use Cases

1. **DMA completion notification:** FPGA DMA engine writes a completion flag into HPS DDR
2. **Mailbox / command queue:** FPGA writes command structures that the HPS polls
3. **Interrupt generation:** Write to the HPS GIC (Generic Interrupt Controller) distributor via memory-mapped access

### Address Translation

When the FPGA issues an AXI transaction through F2H, the bridge forwards it to the HPS L3 interconnect. The address is decoded by the NIC-301 to route to DDR, on-chip RAM, or peripherals. **No address translation occurs** — the FPGA must use HPS physical addresses. If Linux is running with virtual memory, the FPGA cannot directly access userspace buffers unless they are pinned and the physical address is passed to the FPGA.

```
FPGA AXI Master ──► F2H Bridge ──► NIC-301 ──► DDR Controller
         │                            │
         │    Physical address        │
         │    (no MMU in path)        │
         ▼                            ▼
   Must use HPS-                   Linux kernel
   visible phys addr               manages page tables
```

---

## F2S — FPGA-to-SDRAM (Cyclone V / Arria 10 Only)

The highest-bandwidth path. Six independent command ports with configurable read/write data widths give the FPGA direct access to external DDR without involving the HPS CPU complex.

### Architecture

```
FPGA Fabric
    │
    ├──► F2S Port 0 ──┐
    ├──► F2S Port 1   │
    ├──► F2S Port 2   ├──► SDRAM Scheduler ──► DDR Controller ──► DDR3/4
    ├──► F2S Port 3   │    (arbitrates 6:1)
    ├──► F2S Port 4   │
    └──► F2S Port 5 ──┘
```

| Parameter | Value |
|---|---|
| Command ports | 6 (independent read/write command channels) |
| Read data ports | 4 (64-bit each, configurable) |
| Write data ports | 4 (64-bit each, configurable) |
| Data width | 16, 32, 64, 128, or 256 bits per port |
| Clock | Fabric clock (async to HPS) |

### Bandwidth Math

At 64-bit width × 400 MHz DDR clock (Cyclone V typical):
- Peak per-port: 64 × 400M = 25.6 Gb/s = 3.2 GB/s (theoretical)
- With 6 ports: ~19.2 GB/s aggregate theoretical
- Realistic (70% efficiency): ~13.4 GB/s

This exceeds the DDR3-800 bandwidth (~6.4 GB/s for 16-bit interface, ~12.8 GB/s for 32-bit). **The F2S ports are over-provisioned** — the bottleneck is the DDR controller, not the bridges.

### The Starvation Problem

The SDRAM scheduler arbitrates between F2S ports and the HPS L3 with **no QoS**. A greedy FPGA DMA loop on one F2S port can starve the Linux kernel of DDR bandwidth, causing watchdog timeouts or audio dropouts.

**Mitigation strategies:**
1. **Rate-limit FPGA bursts:** Insert FIFOs in the FPGA that accumulate data, then burst at controlled intervals
2. **Use on-chip RAM as buffer:** Stage data in FPGA BRAM, then transfer to DDR in large bursts during CPU idle periods
3. **Reduce F2S port count:** Use fewer ports at higher width rather than many narrow ports

---

## NIC-301 Interconnect

The ARM CoreLink NIC-301 is the L3 crossbar inside the HPS. It routes transactions between CPU cores, DMA, bridges, DDR, and peripherals.

### Master Ports (Initiators)

| Master | Description |
|---|---|
| CPU0 / CPU1 | Cortex-A9 cores (or A53 on Stratix 10) |
| DMAC | DMA controller (8 channels) |
| H2F / LWH2F | HPS-to-FPGA bridges |

### Slave Ports (Targets)

| Slave | Description |
|---|---|
| DDR | SDRAM controller |
| OCRAM | On-chip RAM (64-256 KB) |
| F2H | FPGA-to-HPS bridge slave |
| Peripherals | UART, SPI, timers, etc. |
| STM | System Trace Macrocell |

### Arbitration

NIC-301 uses round-robin arbitration by default. There is **no programmable QoS** on Cyclone V — you cannot prioritize CPU transactions over FPGA transactions. Stratix 10 and Agilex upgrade to a more advanced interconnect with QoS support.

---

## Memory Map: HPS-FPGA Address Space

### Cyclone V SoC

| Region | HPS Address | Size | Description |
|---|---|---|---|
| SDRAM | 0x0000_0000 | 3 GB | DDR3 via hard controller |
| FPGA slaves (H2F) | 0xC000_0000 | 960 MB | FPGA Avalon-MM/AXI slaves |
| FPGA slaves (LWH2F) | 0xFF20_0000 | 2 MB | Lightweight control |
| HPS peripherals | 0xFC00_0000 | 64 MB | UART, timers, GPIO |
| Boot ROM | 0xFFFF_0000 | 64 KB | On-chip boot ROM |

### Agilex 7 SoC

Agilex uses a newer address map with larger windows and NoC integration:

| Region | HPS Address | Size | Description |
|---|---|---|---|
| SDRAM | 0x0000_0000 | 64 GB | DDR4/5 via hard controller |
| FPGA fabric (H2F) | 0x4000_0000_0000 | 512 GB | 64-bit addressing to fabric |
| PCIe | 0x1000_0000_0000 | 1 TB | PCIe root complex |
| HPS peripherals | 0xF900_0000 | 128 MB | Peripheral region |

The shift to 64-bit addressing in Agilex allows the HPS to address much larger FPGA fabric and external PCIe spaces.

---

## Cache Coherency: Explicitly Absent

Intel SoC FPGAs offer **no hardware cache coherency** between the CPU and FPGA fabric. This is the single biggest architectural difference from Xilinx Zynq.

### What This Means

When the FPGA writes data to DDR via F2S:
1. Data goes directly to DDR, bypassing the CPU L2 cache
2. If the CPU recently read that address, the L2 cache holds a stale copy
3. The CPU reads stale data from cache instead of fresh data from DDR

### Software Workaround: Cache Maintenance

Linux provides the `dma_sync_*` API and `flush_cache_all()` for explicit cache management:

```c
// HPS prepares a buffer for FPGA processing
void *buffer = dma_alloc_coherent(dev, size, &dma_handle, GFP_KERNEL);

// HPS writes commands to buffer
strcpy(buffer, "process_this");

// CRITICAL: Flush CPU cache so FPGA sees the data
__cpuc_flush_dcache_area(buffer, size);
outer_flush_range(__pa(buffer), __pa(buffer) + size);

// Trigger FPGA via H2F register
iowrite32(1, fpga_cmd_reg);

// Wait for FPGA done interrupt
wait_for_completion(&fpga_done);

// CRITICAL: Invalidate CPU cache before reading results
__cpuc_flush_dcache_area(buffer, size);
outer_inv_range(__pa(buffer), __pa(buffer) + size);

// Now safe to read results
printk("Result: %s\n", (char *)buffer);
```

> **Note:** `dma_alloc_coherent()` on Intel SoC allocates **non-cacheable** memory by default. If you use this, no flush/invalidate is needed — but CPU access to the buffer is slower.

---

## Platform Designer / Qsys Integration

Intel's system integration tool (formerly Qsys, now Platform Designer in Quartus Prime) generates the interconnect fabric between HPS bridges and your custom IP.

### Typical System Layout

```
┌───────────────────────────────────────────┐
│         Platform Designer System          │
│                                           │
│  ┌─────────┐      ┌────────────────────┐  │
│  │  HPS    │──────► AXI Interconnect   │  │
│  │  IP     │      │  (auto-generated)  │  │
│  │         │◄─────│                    │  │
│  └─────────┘      └──┬─────┬─────┬─────┘  │
│                      │     │     │        │
│                   ┌──▼──┐ ┌▼───┐ ┌▼────┐  │
│                   │DMA  │ │UART│ │Video│  │
│                   │Eng  │ │    │ │Proc │  │
│                   └─────┘ └────┘ └─────┘  │
│                                           │
└───────────────────────────────────────────┘
```

When you instantiate the `cyclone5_hps` or `agilex_hps` IP, Platform Designer automatically exposes the bridge interfaces. You connect your custom IP to the `h2f` and `f2h` Avalon-MM/AXI interfaces. The tool generates the arbitration, address decoding, and clock-crossing logic.

### Clock Domains

| Domain | Typical Frequency | Source |
|---|---|---|
| HPS CPU | 800-925 MHz (CV), 1.2 GHz (S10), 1.5 GHz (Agilex 7) | HPS PLL |
| HPS buses | 400 MHz | Derived from CPU clock |
| FPGA fabric | 50-400 MHz | Fabric PLLs |
| DDR | 400-800 MHz (800-1600 MT/s) | DDR PLL |

Bridge FIFOs handle the asynchronous crossing. Platform Designer inserts `altclkctrl` and `altera_avalon_mm_clock_crossing_bridge` automatically.

---

## Per-Family Comparison

| Feature | Cyclone V SoC | Arria 10 SoC | Stratix 10 SoC | Agilex 7 SoC | Agilex 5 SoC |
|---|---|---|---|---|---|
| CPU | Dual A9 | Dual A9 @ 1.2 GHz | Quad A53 | Quad A53 | Dual A76 + Dual A55 |
| CPU arch | ARMv7 | ARMv7 | ARMv8 | ARMv8 | ARMv8.2 |
| Max DDR | 4 GB DDR3 | 8 GB DDR3/4 | 64 GB DDR4 | 128 GB DDR4/5 | 64 GB DDR4/5/LPDDR5 |
| H2F width | 64-bit AXI-3 | 64-bit AXI-3 | 64-bit AXI-4 | 64-bit AXI-4 | 64-bit AXI-4 |
| F2S ports | 6 | 6 | None | None | None |
| FPGA DDR ctrl | No | No | Yes (hard) | Yes (hard) | Yes (hard) |
| Coherency | None | None | None | None | None |
| Interconnect | NIC-301 | NIC-301 | CoreLink CCN | NoC + AXI | NoC + AXI |
| PCIe | Gen2 x4 | Gen3 x8 | Gen3 x16 | Gen5 x16 | Gen4 x8 |

---

## Common Pitfalls

| Problem | Symptom | Fix |
|---|---|---|
| AXI-4 IP on AXI-3 bridge | Write data corruption | Insert protocol converter in Platform Designer |
| Cache stale data | FPGA results invisible to CPU | Use `dma_alloc_coherent()` or explicit flush/inv |
| F2S starvation | Linux watchdog reboots | Rate-limit FPGA DMA bursts, use BRAM buffers |
| LWH2F burst access | Bus hang, timeout | LWH2F only supports single-beat transactions |
| Wrong physical address | FPGA writes to wrong DDR region | Pass `dma_handle` (bus address) to FPGA, not CPU virtual addr |
| HPS not released from reset | FPGA configured but bridges dead | U-Boot must run `bridge_enable_handoff` before Linux boots |

---

## Further Reading

| Document | Intel Doc ID |
|---|---|
| Cyclone V HPS TRM | 683126 |
| Arria 10 HPS TRM | 683126 (shared) |
| Stratix 10 HPS TRM | 683222 |
| Agilex 7 HPS TRM | 683567 |
| Agilex 5 HPS TRM | 814346 |
| Embedded Peripherals IP User Guide | Various |
