[← Home](../../README.md) · [Architecture](../README.md) · [Fabric](README.md)

# BRAM & URAM — On-Chip Memory Architecture

FPGA designs rarely use LUTs alone — real computation needs memory. Block RAM (BRAM) provides dedicated on-chip SRAM: fast, dual-ported, and organized in fixed-size tiles. URAM (Ultra RAM) extends this to deep storage (288 Kb per block) for UltraScale+ and Versal devices. This article covers the memory block architectures across all major vendors, their operating modes, and how to choose the right memory primitive for your design.

---

## Overview

Every FPGA includes hardened dual-port SRAM blocks — typically 9–40 Kb each — that can be configured as single-port RAM, true dual-port RAM, simple dual-port RAM, ROM, or FIFO. These blocks are physically distributed across the die alongside the logic fabric, minimizing the routing distance from LUTs to memory. The key dimensions that vary across vendors are: block size (impacts waste for small memories), port width flexibility (can you split 36 bits into 4×9?), write behavior (byte-write enables, read-first vs write-first), and whether hard FIFO logic is integrated (counters, flags, ECC). Unlike LUTs, BRAM blocks cannot be fractured arbitrarily small — a 9-bit-deep memory on a 9 Kb block wastes the remaining 8,991 bits. Understanding these constraints is essential for memory-efficient design.

---

## Vendor-by-Vendor Comparison

| Parameter | Xilinx BRAM36 | Xilinx URAM | Intel M20K | Intel MLAB | Lattice EBR | Lattice PDR | Gowin BSRAM | Microchip LSRAM |
|---|---|---|---|---|---|---|---|---|
| **Size** | 36 Kb | 288 Kb | 20 Kb | 640 bits | 9 Kb (ECP5), 18 Kb (iCE40) | 18 Kb | 18 Kb | 20 Kb |
| **Ports** | True dual-port | True dual-port | True dual-port | Simple dual-port | True dual-port | Pseudo dual-port | True dual-port | Dual-port |
| **Width range** | 32K×1 to 512×72 | 4K×72 fixed | 20K×1 to 512×40 | 32×20 | 8K×1 to 256×36 | 512×36 | 16K×1 to 512×36 | 512×40 to 16K×1 |
| **Byte-write** | Yes (×9/×18/×36) | No | Yes (×8/×16/×20) | No | Yes (×9/×18/×36) | Yes (×9/×18) | Yes | Yes |
| **Hard FIFO** | Yes (FIFO18/FIFO36) | No | Yes | No | Yes | Partial | Yes | No |
| **ECC** | Yes (×64+8) | Yes (×64+8) | Yes (×20+5) | No | No | No | No | Yes |
| **Cascade** | Yes (depth) | No (fixed 4K) | Yes (depth) | No (small) | Yes (depth) | Yes (depth) | Yes | Yes |
| **Power (static)** | ~0.5 mW per block | ~1.0 mW | ~0.3 mW | ~0.1 mW | ~0.2 mW | ~0.4 mW | ~0.2 mW | ~0.15 mW |

---

## Xilinx BRAM36 and URAM

### BRAM36 (36 Kb)

The BRAM36 is the universal Xilinx memory block from 7-series through Versal. It can be split into two independent 18 Kb blocks (BRAM18 mode):

```
┌────────────── BRAM36 (36 Kb) ──────────────┐
│ ┌── BRAM18 (18 Kb) ──┐ ┌── BRAM18 ──┐      │
│ │ Port A    Port B    │ │ Port A  B  │      │
│ │  ↓         ↓        │ │  ↓      ↓  │      │
│ │ [   18 Kb SRAM   ]  │ │ [18 Kb SRAM]│      │
│ └─────────────────────┘ └────────────┘      │
│  FIFO36 mode: ┌──────────────────────┐      │
│               │  36 Kb FIFO + Flags  │      │
│               └──────────────────────┘      │
└─────────────────────────────────────────────┘
```

**Configurations:**
| Mode | Depth × Width |
|---|---|
| 36 Kb SP RAM | 32K×1, 16K×2, 8K×4, 4K×9, 2K×18, 1K×36, 512×72 |
| 18 Kb SP RAM | 16K×1, 8K×2, 4K×4, 2K×9, 1K×18, 512×36 |
| True Dual-Port | Both ports can read/write simultaneously (address collision = undefined) |
| Simple Dual-Port | One read port, one write port (no collision) |
| ROM | Pre-loaded via bitstream; read-only at runtime |
| FIFO36/FIFO18 | Hard FIFO: built-in read/write counters, full/empty/almost flags |

**Byte-Write Enable:** BRAM36 supports byte-write at ×9, ×18, and ×36 widths. Each 8-bit byte + 1 parity bit can be independently written. This is critical for processor data memories and packet buffers.

**Read-First vs Write-First:** When read and write addresses collide in true dual-port mode, the output can be configured as READ_FIRST (output = old data), WRITE_FIRST (output = new data), or NO_CHANGE (output holds). Different ports can have different modes.

### URAM (288 Kb) — UltraScale+ and Versal

URAM provides 288 Kb blocks that can be cascaded for up to 4,096 entries deep (1.125 Mb per cascade chain). Unlike BRAM, URAM is:

| Feature | BRAM36 | URAM |
|---|---|---|
| Size per block | 36 Kb | 288 Kb |
| Port type | True dual-port | Simple dual-port only |
| Byte write | Yes | No (full-width only) |
| Width | Variable | Fixed 72-bit |
| FIFO mode | Yes (hard) | No |
| Cascade depth | Variable | Up to 4,096 entries |
| Recommended use | General memory, FIFOs, register files | Deep buffers, frame stores, LUT replacement |

**When URAM saves you:** A 256K × 72-bit frame buffer needs 512 BRAM36 blocks (18.4 Mb total) or just 64 URAM blocks. At 0.5 mW/BRAM vs 1.0 mW/URAM, URAM also wins on power: 256 mW vs 64 mW static.

---

## Intel M20K and MLAB

### M20K (20 Kb)

Intel's primary memory block across Cyclone V, Arria 10, Stratix 10, and Agilex:

| Configuration | Depth × Width |
|---|---|
| SP RAM | 20K×1, 10K×2, 5K×4, 2K×10, 1K×20, 512×40 |
| True Dual-Port | Both ports read/write |
| Simple Dual-Port | Independent read/write ports |
| FIFO | Hard FIFO control: read/write counters, full/empty/almost flags |
| ROM | Bitstream-initialized |

**Key difference from BRAM36:** M20K uses ×10/×20/×40 width options (not ×9/×18/×36). This means:
- ECC is ×20+5 encoding (vs ×64+8 for BRAM36)
- Port matching for processor buses (32-bit + parity) requires careful width selection

### MLAB (640 bits)

Each M20K block has an associated MLAB — 640 bits (32×20) of simple dual-port RAM. MLABs are Intel's "distributed RAM" equivalent. They're physically part of M20K blocks but can be used independently for small register files, delay lines, and shallow FIFOs.

| Feature | MLAB | M20K |
|---|---|---|
| Size | 640 bits | 20,480 bits |
| Depth × Width | 32×20 | 512×40 max |
| Ports | Simple dual-port | True dual-port |
| Hard FIFO | No | Yes |
| Byte-write | No | Yes |

---

## Lattice EBR, PDR, and LRAM

### EBR (9 Kb) — ECP5

ECP5 uses 9 Kb **Embedded Block RAM** blocks. Key characteristics:

| Configuration | Depth × Width |
|---|---|
| True Dual-Port | 8K×1, 4K×2, 2K×4, 1K×9, 512×18, 256×36 |
| Pseudo Dual-Port | One read port, one write port |
| FIFO | Hard FIFO16 mode with programmable flags |

ECP5 EBRs can be cascaded for deeper memories. At 9 Kb, they're half the size of Xilinx BRAM18 and Intel M20K — this means ECP5 uses more blocks for equivalent memory depth but wastes less for shallow memories.

### PDR (18 Kb) — CertusPro-NX

CertusPro-NX upgrades to 18 Kb **Programmable Dual-port RAM** blocks with similar port configurations to EBR but doubled capacity.

### LRAM (Large RAM) — CrossLink-NX

CrossLink-NX uses 18 Kb RAM blocks with single-port and dual-port modes, including byte-write enables for efficient processor memory mapping.

---

## Gowin BSRAM (18 Kb)

Gowin's 18 Kb block SRAM supports:
- True dual-port (2 read/write ports)
- Simple dual-port (1 read, 1 write)
- Semi-dual-port (1 read/write + 1 read)
- ROM mode
- FIFO mode with sync/async flags

Gowin BSRAM lacks ECC and byte-write at narrower widths than ×36. This is consistent with Gowin's cost-optimized positioning.

---

## Microchip LSRAM and uSRAM

### LSRAM (20 Kb) — PolarFire

20 Kb **Large SRAM** blocks with:
- True dual-port (2RW)
- Two independent 10 Kb blocks
- ECC (×20+5)
- Byte-write at ×40 width

### uSRAM (1 Kb) — PolarFire

1 Kb **micro SRAM** blocks for small distributed memories — PolarFire's equivalent of Intel MLAB or Xilinx distributed RAM. 64×18 maximum configuration.

---

## When to Use / When NOT to Use

### Choosing the Right Memory

| Scenario | Best Primitive | Why |
|---|---|---|
| FIFO ≤ 512 deep | BRAM36 FIFO36 mode (Xilinx) or M20K FIFO (Intel) | Hard FIFO logic (counter, flags) consumes zero LUTs |
| FIFO ≤ 32 deep | Distributed RAM / SRL32 (Xilinx) or MLAB (Intel) | Save BRAM blocks; shallow depth wastes BRAM capacity |
| Large buffer (>1 Mb) | URAM (Xilinx UltraScale+) | Fewer blocks, lower static power than BRAM chains |
| Processor data memory | BRAM36 ×18 mode (Xilinx) or M20K ×10 (Intel) | Byte-write enables for narrow stores |
| Frame buffer | URAM (Xilinx) or multiple M20K (Intel) | URAM wins on density and power; Intel uses M20K cascades |
| ROM / LUT replacement | BRAM36 ROM mode (any vendor) | Pre-initialized via bitstream, zero-latency read |
| ECC-protected memory | BRAM36 ×64+8 (Xilinx) or M20K ×20+5 (Intel) | On-chip ECC encoder/decoder, no LUT cost |
| Cross-vendor portable | Vendor-agnostic inference (always @(posedge clk) reg [...] mem) | Let synthesis choose; add vendor pragmas if specific mode needed |

### When NOT to Use BRAM

| Situation | Alternative |
|---|---|
| Depth < 16 on Xilinx | Use distributed RAM (LUT-based) — saves BRAM for deeper storage |
| Depth < 32 on Intel | Use MLAB — saves M20K blocks |
| Latency-sensitive read (1 cycle) | BRAM has 1-cycle read latency; if this is acceptable, BRAM is fine. If you need zero-cycle (combinational), use LUT-based memory |
| Large LUT-only design running out of LUTs | Move register arrays and small memories to BRAM to free LUTs |

---

## Best Practices & Antipatterns

### Best Practices
1. **Use vendor inference templates** — Each vendor has recommended RTL patterns for BRAM inference. Follow them or the tool may infer registers instead
2. **Enable output registers** — BRAMs have optional output registers that add 1 cycle of latency but dramatically improve fMAX (aligns BRAM output with fabric timing)
3. **Plan for port collisions** — In true dual-port mode, simultaneous read/write to the same address produces undefined data. Use simple dual-port if you don't need two write ports
4. **Check ECC if using BRAM for critical data** — SEU-induced bit flips in BRAM are real. Use ECC mode for configuration, critical state, and processor code storage

### Antipatterns

| Antipattern | The Problem | The Fix |
|---|---|---|
| **"The BRAM Hoarder"** | Using BRAM for every small memory | Use distributed RAM/MLAB for shallow depths; BRAM waste at <50% utilization per block |
| **"The Async Read Wish"** | Expecting combinational (0-cycle) read from BRAM | BRAM reads are always synchronous (1 cycle). Use output register for fMAX; accept the latency or use LUT-based memory |
| **"The Dual-Port Collision"** | Writing and reading the same address on both ports of true dual-port BRAM | Use simple dual-port (1W+1R) if you need safe simultaneous access; or add address comparison logic |
| **"The Width Mismatch"** | Mapping 32-bit data to ×36 BRAM without using parity bits | Enable parity bits or use ×32 configuration if supported; wasted bits add up across hundreds of blocks |

---

## Pitfalls & Common Mistakes

### 1. Read-First / Write-First Confusion at Port Collision

**The mistake:** In true dual-port BRAM, port A writes address 100 while port B reads address 100 in the same cycle.

**Why it fails:** The read data is undefined per the vendor spec. Read-first mode outputs old data; write-first outputs new data. But these aren't guaranteed across vendors and may differ between ports.

**The fix:** Use simple dual-port (1W+1R) when possible. If true dual-port is needed, add address comparison logic to prevent collisions or pipeline the design to avoid them.

### 2. Underestimating Block Count for Wide Memories

**The mistake:** A 256×128-bit memory on ECP5 (9 Kb blocks): 256 × 128 = 32,768 bits. "That's only 4 EBRs of 9 Kb." 

**Why it fails:** ECP5 EBRs max out at 36-bit width. A 128-bit-wide memory needs 4 EBRs in parallel at each depth level (128/36 = 4 columns). But 256 depth requires only 1 block per column. Total: 4 blocks. Actually, this works — but double-check: 256 deep × 128 wide = 32,768 bits = 4 EBRs. However, 256 deep × 144 wide (e.g., 128 data + 16 ECC) = 36,864 bits. EBR at 36 bits wide: 128/36 = 4 columns × 256 deep = 36,864 / 9,216 bits per EBR = 4 blocks. It fits.

**The fix:** Calculate as **ceil(width / max_port_width) × ceil(depth / max_depth_per_block)**. Always verify with vendor memory planner.

### 3. Ignoring BRAM Power in Sleep States

**The mistake:** A design powers down most logic but leaves BRAMs enabled, expecting near-zero power.

**Why it fails:** BRAM static power (~0.5 mW/block) is small per block but scales with count. 500 BRAMs × 0.5 mW = 250 mW — significant in a 1 W power budget.

**The fix:** Use BRAM enable signals to gate reads/writes during idle periods. Cascade enable to reduce dynamic power. For deep sleep, consider designs that can lose BRAM contents (reload from external memory on wake).

---

## References

| Source | Document |
|---|---|
| Xilinx UG473 — 7-Series Memory Resources | https://docs.xilinx.com/r/en-US/ug473_7Series_Memory_Resources |
| Xilinx UG573 — UltraScale Architecture Memory Resources | https://docs.xilinx.com/ |
| Intel CV-5V2 — Cyclone V M10K and MLAB | Intel FPGA Documentation |
| Lattice TN1263 — ECP5 Memory Usage Guide | Lattice Tech Docs |
| Gowin UG286 — BSRAM User Guide | Gowin Docs |
| Microchip DS50002812 — PolarFire Memory | Microchip Docs |
| [LUTs and CLBs](luts_and_clbs.md) | Previous article — distributed vs block memory |
| [DSP Slices](dsp_slices.md) | Next article — DSP48/DSP58 blocks |
