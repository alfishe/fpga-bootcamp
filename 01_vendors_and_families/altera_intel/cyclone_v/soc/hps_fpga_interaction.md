[← SoC Home](README.md) · [← Cyclone V Home](../README.md) · [← Project Home](../../../../README.md)

# HPS ↔ FPGA Interaction — Comprehensive Guide

Every Cyclone V SoC design faces a fundamental question: **which bridge should I use for this data?** This guide covers all 8 interaction methods with real bandwidth measurements, when-to-use/when-not-to-use analysis, best practices, and a catalog of common anti-patterns.

---

## All Methods at a Glance

| # | Method | Master | Data Width | Theoretical | Practical | Coherent? | Latency |
|---|--------|--------|-----------|------------|----------|-----------|--------|
| 1 | **Lightweight H2F (LWH2F)** | HPS → FPGA | 32-bit | 400 MB/s | 15–40 MB/s | No | ~10–20 cycles |
| 2 | **HPS-to-FPGA (H2F)** | HPS → FPGA | 64/128 bit | 800–1600 MB/s | 100–700 MB/s | No | ~15–30 cycles |
| 3 | **FPGA-to-HPS (F2H)** | FPGA → HPS | 64/128 bit | 800–1600 MB/s | 100–500 MB/s | Via ACP | ~20–40 cycles |
| 4 | **FPGA-to-SDRAM (F2S)** | FPGA → DDR | 6× 16–256 bit | 3.2–38.4 GB/s agg. | 1–15 GB/s | **Never** | ~30–100 cycles |
| 5 | **On-Chip RAM** | Shared | 64 KB | ~1.6 GB/s | 500–1200 MB/s | Configurable | ~3–8 cycles |
| 6 | **Loaned Peripherals** | HPS ↔ FPGA | Periph-specific | Periph-specific | Periph-specific | N/A | Periph-specific |
| 7 | **Interrupts** | Bidirectional | 64 signals | Signal only | ~1 µs | N/A | ~100 ns–1 µs |
| 8 | **HPS DMA Controller** | HPS → FPGA/DDR | 8 channels | ~1.6 GB/s | 400–800 MB/s | No | ~20–60 cycles |

> **Measured benchmarks source:** [UviDTE-FPSoC / CycloneVSoC-time-measurements](https://github.com/UviDTE-FPSoC/CycloneVSoC-time-measurements) — University of Vigo. Paper: *"Design Guidelines for Efficient Processor-FPGA Communication in Cyclone V FPSoCs"* (IEEE Access, 2021).

---

## 1. Lightweight HPS-to-FPGA (LWH2F)

```
CPU → L1 cache → SCU → L2 → NIC-301 → L3 Slave Peripheral Switch → LWH2F → FPGA fabric
```

The **LWH2F bridge** is designed for control registers — it's a 32-bit AXI-3 bus connected through the L3 Slave Peripheral Switch, the same path used by HPS UARTs, timers, I2C, and spi controllers.

| Property | Value |
|---|---|
| **Bus protocol** | AXI-3, 32-bit data, single transaction ID |
| **Address range** | `0xFF20_0000` – `0xFF3F_FFFF` (2 MB window) |
| **Max fabric clock** | l3_mp_clk / 2 or l4_mp_clk (typ. 50–100 MHz) |
| **Theoretical peak** | 32-bit × 100 MHz = 400 MB/s |
| **Measured baremetal read** | ~25–40 MB/s (memcpy, 64 KB) |
| **Measured baremetal write** | ~20–35 MB/s |
| **Measured Linux read** | ~15–25 MB/s (TLB misses, kernel overhead) |
| **Measured Linux write** | ~10–20 MB/s |

### Why It's Slow

The LWH2F path crosses the **L3 Slave Peripheral Switch** — a shared bus that arbitrates between the CPU, DMA engine, and all low-speed peripherals. Every kernel timer tick, UART debug print, and I2C sensor poll contends for this switch. The bridge also lacks the write buffer depth of the main H2F bridge.

### When to Use LWH2F

| Scenario | Verdict |
|---|---|
| Control/status registers, configuration, GPIO | **Use this.** It's exactly what it was designed for. |
| Command queues (<1 KB fifos) | Good — small, infrequent writes. |
| Streaming data (>4 KB) | **Use H2F** instead — 10× bandwidth. |
| Reading FPGA status registers in a tight loop | **Do not poll.** Use F2H to push status to DDR + interrupt. |
| High-frequency polling (>1 KHz) | Each read crosses the peripheral switch. Batch reads. |

### Best Practices

1. **Group all control registers into one address range** — consecutive addresses minimize AXI transaction overhead.
2. **Use 32-bit word-aligned accesses only** — unaligned or byte accesses trigger multiple bus transactions.
3. **Write, don't read** — LWH2F writes are posted (non-blocking); reads stall the CPU until FPGA responds. If you need FPGA→CPU status, use F2H to DDR instead.
4. **Keep register banks in FPGA BRAM** — BRAM read latency (~2 cycles) keeps the bridge from stalling.

### Anti-Patterns

| Anti-Pattern | Why It Hurts |
|---|---|
| **Streaming video frames through LWH2F** | 32-bit × 25 MB/s real. 640×480 @ 8 bpp = ~8 fps max. Use F2S. |
| **Tight polling loop on FPGA status bit** | Each iteration = full round-trip through peripheral switch. Deliver status via F2H→DDR→interrupt. |
| **Mixing control and data on LWH2F** | Data traffic starves control register access. Keep LWH2F for control only. |

---

## 2. HPS-to-FPGA (H2F)

```
CPU → L1 cache → SCU → L2 → NIC-301 L3 Main Switch → H2F bridge → FPGA fabric
```

The **H2F bridge** connects through the L3 Main Switch (not the peripheral switch), giving it much higher bandwidth. Configurable to 32-, 64-, or 128-bit data width. It's bidirectional — HPS can read from and write to FPGA resources.

| Property | Value |
|---|---|
| **Bus protocol** | AXI-3, configurable 32/64/128-bit data |
| **Address range** | `0xC000_0000` – `0xFBFF_FFFF` (960 MB window) |
| **Max fabric clock** | h2f_user_clk, up to l3_main_clk (typ. 100–150 MHz) |
| **Write buffer** | Yes (depth: ~4 bursts) |
| **Read buffer** | No — reads stall until FPGA responds |

### Bandwidth by Configuration

| Config | Width | Bus Clock | Theoretical | Measured (memcpy, 1 MB, baremetal) |
|---|---|---|---|---|
| **H2F32** | 32-bit | 100 MHz | 400 MB/s | ~140–180 MB/s |
| **H2F64** | 64-bit | 100 MHz | 800 MB/s | ~280–380 MB/s |
| **H2F128** | 128-bit | 100 MHz | 1.6 GB/s | ~550–700 MB/s |

> Source: UviDTE-FPSoC benchmarks. The gap between theoretical and measured comes from AXI protocol overhead (address phase, response phase), NIC-301 arbitration delay, and FPGA-side BRAM/register response latency.

### When to Use H2F

| Scenario | Verdict |
|---|---|
| CPU writes bulk data to FPGA (DMA descriptors, lookup tables) | **Use H2F64 or H2F128.** |
| CPU reads processed results from FPGA | Use H2F, but prefer F2H→DDR→CPU for large results. |
| Control registers when LWH2F window (2 MB) is too small | H2F gives 960 MB — huge register maps. |
| FPGA needs data from CPU DDR | **Don't proxy.** Use F2S — let FPGA pull directly from DDR. |
| Shared data structures requiring coherency | Cyclone V has no ACP on H2F. Use on-chip RAM or F2H+ACP. |

### Best Practices

1. **Use 128-bit when available** — 128-bit × 100 MHz = 1.6 GB/s, nearly doubles 64-bit throughput. Costs ~20 extra FPGA pins.
2. **Align to AXI burst boundaries** — 64-bit: 4-beat burst = 32 bytes. Misalignment can halve throughput.
3. **Preferred direction: CPU writes, FPGA consumes** — H2F write buffer absorbs bursts. H2F reads block the bus.
4. **irq-nc Use memcpy for cache-line-aligned data** — NEON linefills can saturate H2F bandwidth.
5. **Consider DMA for large transfers** — CPU memcpy to H2F ties up the core. DMA frees CPU for computation.

---

## 3. FPGA-to-HPS (F2H)

```
FPGA fabric → F2H bridge → NIC-301 L3 Main Switch → SDRAM Controller or ACP
```

The **F2H bridge** lets FPGA fabric act as an AXI master to HPS resources — SDRAM, on-chip RAM, peripherals, and (via ACP) cache-coherent memory.

| Property | Value |
|---|---|
| **Bus protocol** | AXI-3, 32/64/128-bit, up to 8 transaction IDs |
| **Accessible targets** | SDRAM, on-chip RAM, peripheral registers, DMA controller |
| **Max fabric clock** | f2h_user_clk (typ. 100–150 MHz) |
| **Theoretical peak (64-bit)** | 64-bit × 100 MHz = 800 MB/s |
| **Theoretical peak (128-bit)** | 128-bit × 100 MHz = 1.6 GB/s |
| **Measured to SDRAM write (64-bit)** | ~200–450 MB/s |
| **Measured to SDRAM read (64-bit)** | ~150–300 MB/s |

### ACP — The Coherent Path

The F2H bridge can be routed through the **Accelerator Coherency Port (ACP)** instead of going directly to SDRAM:

```
Without ACP: FPGA → F2H → NIC-301 → SDRAMC        (bypasses L2, always non-coherent)
With ACP:    FPGA → F2H → ACP → SCU → L2 → SDRAMC  (snoops, maintains coherency)
```

When ACP is enabled:
1. FPGA reads snoop L1 and L2 caches before going to DDR
2. FPGA writes invalidate stale cache lines in L1/L2
3. The FPGA sees the same memory state as the CPUs

> **Cost of coherency:** ACP adds ~2–4 cycles of latency vs direct F2H-to-SDRAM. For pure streaming (video, SDR samples), bypass ACP. For shared data structures, enable ACP.

### When to Use F2H

| Scenario | Verdict |
|---|---|
| FPGA writes results into HPS DDR for CPU to consume | **Use F2H to SDRAM.** Most common pattern. |
| FPGA and CPU share data structures (queues, ring buffers) | **Use F2H via ACP** — only coherent path. |
| FPGA accesses HPS peripherals (UART, SPI registers) | Use F2H to peripheral region if needed. |
| High-bandwidth streaming ingest (raw sensor→DDR) | **Use F2S instead** — dedicated bandwidth, no L3 contention. |

### Interrupt Delivery via F2H

A common pattern: FPGA writes completion status to a ring buffer in DDR via F2H, then triggers an F2H interrupt (f2h_irq). The CPU ISR reads the ring buffer from DDR — zero LWH2F or H2F reads needed.

---

## 4. FPGA-to-SDRAM (F2S)

```
FPGA fabric → F2S port → SDRAM Controller (direct, bypasses NIC-301 entirely)
```

The **highest bandwidth path** from FPGA to memory. F2S bypasses the L3 interconnect and talks directly to the SDRAM controller. Six independent ports, each with separate command, read, and write channels.

| Property | Value |
|---|---|
| **Number of ports** | 6 independent AXI-3 ports |
| **Port width** | Configurable 16–256 bits per port |
| **Max fabric clock** | f2s_sdram_clk (typ. 100–200 MHz, from FPGA PLL) |
| **Per-port theoretical (128-bit)** | 128-bit × 200 MHz = 3.2 GB/s |
| **Per-port theoretical (256-bit)** | 256-bit × 200 MHz = 6.4 GB/s |
| **HPS SDRAM controller total** | 400 MHz DDR, 32-bit data = 3.2 GB/s hard ceiling |
| **Coherency** | **None.** No snooping, no cache awareness. |

### Port Architecture Detail

```
F2S Port 0: CMD port 0 + can use R-port 0–3 + W-port 0–3
F2S Port 1: CMD port 1 + can use R-port 0–3 + W-port 0–3
...
F2S Port 5: CMD port 5 + can use R-port 0–3 + W-port 0–3

6 command ports share 4 read data ports + 4 write data ports
```

A single read transaction: command goes through command port N, data returns through one of the 4 read data ports. Reads and writes are independent — a blocked write on W-port 0 doesn't block reads using R-port 0.

### The Critical Mismatch

```
F2S Port 0 (3.2 GB/s theoretical) ──┐
F2S Port 1 (3.2 GB/s)              ──┤
F2S Port 2 (3.2 GB/s)              ──┤
F2S Port 3 (3.2 GB/s)              ──┼──► SDRAMC (3.2 GB/s MAX) ──► DDR3
F2S Port 4 (3.2 GB/s)              ──┤
F2S Port 5 (3.2 GB/s)              ──┤
Cortex-A9 cores + DMA              ──┘
```

6 × 3.2 GB/s = 19.2 GB/s aggregate theoretical vs. 3.2 GB/s controller ceiling. **No QoS arbitration.** If F2S Port 0 issues a tight read loop, Cortex-A9 Linux can stall for milliseconds.

| Consumer | Recommended Share |
|---|---|
| HPS SDRAM Controller total | **3.2 GB/s (100%)** |
| CPU bare minimum (Linux kernel) | ~0.5 GB/s (15%) |
| Available for ALL F2S ports | ~2.7 GB/s max, ~1.5–2.0 GB/s sustainable |
| Per F2S port (safe budget) | 300–500 MB/s |

### When to Use F2S

| Scenario | Verdict |
|---|---|
| Video framebuffer (FPGA → display memory) | **Primary use case.** High bandwidth, no coherency needed. |
| SDR/DSP sample ingest (ADC → DDR) | High bandwidth streaming. Route through one F2S port. |
| Bulk DMA source/sink for FPGA engines |map F2S buffer as source in FPGA-side DMA engine. |
| Shared memory between CPU and FPGA | **No coherency.** CPU must manually flush/invalidate. Use F2H+ACP. |
| Low-latency control-path data | F2S = ~30–100 SDRAM cycles. Use on-chip RAM instead. |

### Best Practices

1. **Rate-limit each F2S port in FPGA logic** — credit-based throttling. Target 300–500 MB/s per port max.
2. **Use FIFOs as burst buffers** — buffer 2–4 AXI bursts (512–1024 bytes at 128-bit) in FPGA BRAM before F2S. Smooths bursty traffic.
3. **Monitor SDRAM controller efficiency** — read SDRAMC status registers from HPS. If efficiency drops below 40%, add FPGA-side FIFOs.
4. **Align bursts to DDR row boundaries** — 1 KB aligned (DDR3 row size). Row misses cost ~30% bandwidth from precharge/activate penalties.
5. **Use one F2S port per data stream** — don't multiplex unrelated streams on one port. Each port has independent command queue; use that parallelism.

### Anti-Patterns

| Anti-Pattern | Damage |
|---|---|
| **All six F2S ports active without throttling** | CPU starvation, kernel panics, random watchdog timeouts. |
| **Using F2S for CPU-FPGA handshaking (mutex)** | F2S bypasses cache. Every flag read = DDR access (~80 ns), not L2 (~4 ns). |
| **Tight read-after-write on same F2S port** | AXI ordering serializes transactions. Distribute across ports. |

---

## 5. On-Chip RAM (64 KB Shared Scratchpad)

| Property | Value |
|---|---|
| **Size** | 64 KB single contiguous block |
| **HPS address** | `0xFFFF_0000` |
| **FPGA access** | Via F2H bridge |
| **HPS latency** | ~3–8 L3 clock cycles |
| **FPGA latency (via F2H)** | ~20–40 cycles (F2H bridge dominates) |
| **Coherency** | Configurable via MPU page table attributes (TEX/C/B bits) |

### When to Use OCR

| Scenario | Verdict |
|---|---|
| Software/hardware semaphores, atomic flags | **Extremely low latency.** ~5 cycle round trip. |
| Mailbox command/response (CPU↔FPGA) | 64 KB enough for cmd queue + response buffer. |
| Download FPGA configuration tables | Load from CPU, consume from FPGA. |
| Performance-critical shared buffers | Lowest latency shared memory. |
| Buffers >64 KB | Overflow — use F2H/F2S to DDR. |

---

## 6. Loaned Peripherals — HPS I/O via FPGA Pins

HPS peripherals can be routed through FPGA fabric pins instead of dedicated HPS pins. Configured in Platform Designer by setting peripheral pin mux to "FPGA" mode.

| Peripheral | Signals Routable to FPGA | Use Case |
|---|---|---|
| **UART** | TX, RX, CTS, RTS | Debug UART from FPGA logic |
| **SPI** | SCLK, MOSI, MISO, SS0–SS3 | FPGA-driven SPI flash or sensor |
| **I2C** | SCL, SDA | FPGA sensor I2C mux |
| **GPIO** | 67 pins across banks 0–2 | Any bit-banged protocol from fabric |
| **CAN** | TX, RX | FPGA CAN bus controller access |

> The loaned peripheral still uses HPS driver software. The FPGA is just in the pin path — it can tap, mux, or pass-through those signals.

---

## 7. Interrupts

| Property | Value |
|---|---|
| **FPGA-to-HPS** | 64 independent signals (f2h_irq[63:0]), edge/level configurable |
| **HPS-to-FPGA** | 4 general-purpose + 1 FPGA manager interrupt |
| **Baremetal latency** | ~100–500 ns |
| **Linux latency** | ~1–10 µs (softirq scheduling, scheduler) |

### Bon Usage Pattern

The right way: FPGA writes completions status to a ring buffer in DDR via F2H/F2S, then fires **one interrupt** to signal "there's new data." The CPU ISR drains the ring buffer, processes N entries, returns. **One interrupt per batch, not per event.**

---

## 8. HPS DMA Controller

| Property | Value |
|---|---|
| **Channels** | 8 independent DMA channels |
| **Max transfer** | 4 GB per descriptor chain |
| **Descriptor format** | Linked list, scatter-gather |
| **Source/dest combos** | SDRAM↔FPGA (via H2F/F2H), SDRAM↔SDRAM, SDRAM↔peripheral |
| **Max aggregate BW** | ~1.6 GB/s (L3 interconnect limit) |
| **Measured (256 KB block)** | ~400–800 MB/s per channel |
| **Trigger types** | Hardware (peripheral flow control) + software |

### When to Use DMA

| Scenario | Verdict |
|---|---|
| Offload CPU from memcpy to/from FPGA | **Use DMA** — frees CPU for computation. |
| Scatter-gather from non-contiguous pages | Hardware sg list traversal, no CPU involvement. |
| Cyclic/periodic transfers | Auto-restart mode, timed to FPGA data cycle. |
| Transfer <1 KB | DMA setup (~5–10 µs) exceeds memcpy time. Use CPU memcpy. |

---

## No ACP on H2F — Contrast with Zynq-7000

| Feature | Cyclone V SoC | Zynq-7000 |
|---|---|---|
| FPGA coherent read of L2 cache | F2H+ACP only | ACP port (direct SCU injection) |
| CPU coherent access to FPGA memory | **Not available** | Not available (ACP direction: FPGA→CPU) |
| F2S / S_AXI_HP coherency | Never coherent | Never coherent |
| On-chip RAM coherency | MPU configurable | MPU configurable |
| Multiple coherent FPGA masters | F2H can have 8 IDs through ACP | ACP 3 IDs |

> If your accelerator needs cache-coherent access to CPU data: use F2H+ACP on Cyclone V. If you need bidirectional coherency (CPU↔FPGA both ways), Zynq-7000 is stronger.

---

## Bandwidth Budget — Complete Picture

```
Resource                            Peak (MB/s)    Realistic (MB/s)   Notes
────────────────────────────────────────────────────────────────────────────
LWH2F (32-bit × 100 MHz)                  400           15–40        Control registers only
H2F 32-bit (32 × 100 MHz)                 400          140–180       Low-end CPU→FPGA
H2F 64-bit (64 × 100 MHz)                 800          280–380       Standard CPU→FPGA
H2F 128-bit (128 × 100 MHz)             1,600          550–700       Max CPU→FPGA
F2H 64-bit (64 × 100 MHz)                 800          200–450       FPGA→DDR or ACP
F2H 128-bit (128 × 100 MHz)             1,600          400–700       Max F2H non-F2S
F2S per port (128 × 200 MHz)            3,200        1,000–2,000     Single port
F2S per port (256 × 200 MHz)            6,400        2,000–3,000     Saturates controller
HPS SDRAM controller TOTAL              3,200         ~2,500         ALL masters share
On-Chip RAM (HPS access)                1,600          500–1,200     Low-latency, small
On-Chip RAM (FPGA via F2H)               ~500          100–300       Bridge overhead dominates
HPS DMAC aggregate                      1,600          400–800       8 channels sharing
FPGA Manager (FPP ×16 @100MHz)            200          150–200       Bitstream only
```

---

## Decision Matrix

| You want to... | Use | Reason |
|---|---|---|
| Configure FPGA peripheral registers from Linux | **LWH2F** | Designed for control registers |
| Send 1 MB data from CPU to FPGA | **H2F 128-bit** | High bandwidth, CPU as master |
| FPGA streams raw ADC samples to memory | **F2S (one port, 128-bit)** | Max BW, bypasses L3 |
| FPGA and CPU share lock-free ring buffer | **F2H + ACP** | Only coherent path |
| CPU triggers FPGA start; FPGA signals done | **LWH2F write then f2h_irq** | Minimum latency protocol |
| Low-latency handshake (mutex, flag) | **On-Chip RAM** | ~5 cycle round trip |
| Large CPU↔FPGA table transfer (lookup tables) | **H2F 128-bit write; F2H read** | Directional DMA-like pattern |
| Load FPGA bitstream at runtime | **FPGA Manager (FPP ×16)** | Dedicated reconfig path |

---

## Best Practices Summary

1. **One bridge per data type** — control registers on LWH2F, bulk data on F2S/F2H, handshakes in OCR. Never mix.
2. **Write more, read less** — H2F writes are posted; reads stall CPU. Design FPGA→CPU status pushes via F2H.
3. **FIFO everything** — FPGA BRAM FIFOs decouple bursty CPU access from steady FPGA flow. 4–8 KB sweet spot.
4. **ACP for shared, F2S for streaming** — coherency penalty (~2–4 cycles) worth it for shared data. Pure streaming doesn't need it.
5. **Reserve DDR bandwidth at design time** — CPU needs ~20% minimum. Budget remaining 80% across F2S/F2H ports explicitly.
6. **Lock FPGA PLLs to HPS reference** — eliminates CDC FIFOs. Same clock source for h2f_clk, f2h_clk, f2s_clk.
7. **One interrupt per batch** — FPGA accumulates events in DDR ring buffer, interrupts once per batch. Not per event.
8. **DMA for medium/large, memcpy for small** — threshold ~4–8 KB. Below that, DMA setup overhead dominates.

---

## Anti-Patterns Catalog

| Anti-Pattern | Symptom | Fix |
|---|---|---|
| **F2S without throttle** | Random kernel panics, watchdog timeouts | Rate-limit each port to 300–500 MB/s |
| **Tight polling ready bit on LWH2F** | 100% CPU doing nothing | F2H push to DDR + interrupt |
| **memcpy bulk data to LWH2F** | 10 MB/s when expecting 100+ | LWH2F is for registers. Use H2F for data. |
| **FPGA reads shared structs via F2S** | Stale data (CPU wrote to cache, not DDR) | ACP or manual cache flush |
| **All F2H traffic via ACP** | 30–40% BW hit on streaming data | Direct F2H for streaming; ACP for shared only |
| **Reading FPGA results via H2F** | 2–5× slower than F2H write to DDR | FPGA pushes results to DDR; CPU reads locally |
| **HPS DMA for <1 KB transfers** | Higher latency than memcpy | Setup overhead ~5–10 µs. memcpy wins. |
| **Uncontrolled F2S burst length** | Controller thrashing, low efficiency | 16-beat bursts (256 B) optimal for 128-bit F2S |
| **No SDRAM bandwidth reservation** | One master starves others intermittently | Hard-partition via FPGA logic: max bytes/period per port |
| **Using /dev/mem with wrong cache attributes** | Unpredictable, reload-dependent correctness | Use `ioremap` mapped-nocache or kernel FPGA Manager framework |

---

## Official Documentation References

| Source | URL |
|---|---|
| Cyclone V HPS Technical Reference Manual | https://www.intel.com/programmable/technical-pdfs/683126.pdf |
| Cyclone V Device Overview (cv_51001)r | https://www.intel.com/programmable/technical-pdfs/683740.pdf |
| SoC FPGA Design Guidelines (AN-796)d | https://www.intel.com/content/dam/www/programmable/us/en/pdfs/literature/an/an796.pdf |
| *Design Guidelines for Efficient Processor-FPGA Communication in Cyclone V FPSoCs* (Fariña et al., 2021) | doi:10.1109/ACCESS.2021.3068637 |
| UviDTE-FPSoC Benchmarks (GitHub) | https://github.com/UviDTE-FPSoC/CycloneVSoC-time-measurements |
| ARM CoreLink NIC-301 TRM (DDI 0397) | https://developer.arm.com/documentation/ddi0397/latest/ |
| AMBA AXI-3 Protocol Spec (IHI 0022D) | https://developer.arm.com/documentation/ihi0022/d/ |
| ARM Cortex-A9 MPCore TRM (DDI 0407I) | https://developer.arm.com/documentation/ddi0407/i |
| RocketBoards Forum — HPS-FPGA Bridges | https://forum.rocketboards.org/t/guide-hps-fpga-bridges-documentation/796 |
| Intel FPGA SoC EDS User Guide | https://www.intel.com/content/www/us/en/docs/programmable/683130/ |
