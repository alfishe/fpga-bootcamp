[← Zynq-7000 Home](../README.md) · [← 7-Series Home](../README.md) · [← Project Home](../../../../README.md)

# Zynq-7000 SoC — PS-PL Architecture Deep Dive

The Zynq-7000 is the Xilinx counterpart to Cyclone V SoC. Same dual Cortex-A9 ARM cores, same 28nm node, same vintage — but fundamentally different bridge topology and coherency model. This file covers the PS-PL integration: AXI port inventory, memory paths, cache coherency via ACP, interrupt routing, DMA, and the boot flow.

> For general Zynq-7000 family info (variants, dev boards, Cyclone V comparison table), see the [parent README](../README.md).

---

## PS Block Diagram — Processing System Internals

```
┌──────────────── Zynq-7000 PS (Processing System) ────────────────┐
│                                                                    │
│  ┌──────────┐  ┌──────────┐                                       │
│  │ Cortex-A9│  │ Cortex-A9│  667–866 MHz, 32 KB L1 I+D each       │
│  │  Core 0  │  │  Core 1  │  NEON SIMD, VFPv3                     │
│  └────┬─────┘  └────┬─────┘                                       │
│       │   SCU (Snoop Control Unit)  │   Maintains L1 coherency     │
│       └───────┬───────┘              │                              │
│               │                     │                              │
│       ┌───────▼───────┐             │                              │
│       │  L2 Cache      │  512 KB shared, 8-way set-associative    │
│       │  (PL310)       │  ECC optional                            │
│       └───────┬───────┘             │                              │
│               │                     │                              │
│  ┌────────────▼────────────────────▼────────────────────────────┐ │
│  │              Central Interconnect (OCM + DDR)                │ │
│  │  On-Chip Memory (OCM) 256 KB — low-latency scratchpad         │ │
│  │  DDR Controller — DDR2/DDR3/LPDDR2, up to 1 GB, 32-bit       │ │
│  │  DMA Controller (DMAC) — 8-channel, scatter-gather           │ │
│  └────────────┬────────────────────┬────────────────────────────┘ │
│               │                    │                               │
│  ┌────────────▼────────┐  ┌───────▼────────────────────────────┐ │
│  │   I/O Peripherals   │  │     PS↔PL AXI Interfaces           │ │
│  │  USB, GbE, SD, SPI, │  │  GP, HP, ACP (see below)          │ │
│  │  UART, I2C, CAN,    │  │                                    │ │
│  │  GPIO, QSPI, NAND   │  │                                    │ │
│  └─────────────────────┘  └────────────────────────────────────┘ │
│                                                                    │
│                     PS↔PL Interrupts: IRQ_F2P[15:0] + nIRQ        │
│                     Cross-trigger: CTI/CTM (CoreSight debug)      │
└────────────────────────────────────────────────────────────────────┘
```

---

## AXI Port Inventory — 9 Interfaces, 3 Categories

Zynq-7000 exposes **nine** AXI3 interfaces between PS and PL. This is more than Cyclone V's 3 bridges, and the categories map to fundamentally different use cases.

| Port | Direction | Width | Bandwidth (theoretical) | Coherent? | Primary Use |
|---|---|---|---|---|---|
| **S_AXI_GP0** | PS → PL master | 32-bit | 600 MB/s | No | General-purpose control — register access |
| **S_AXI_GP1** | PS → PL master | 32-bit | 600 MB/s | No | Second GP channel (independent) |
| **M_AXI_GP0** | PL → PS master | 32-bit | 600 MB/s | No | FPGA → PS peripheral access |
| **M_AXI_GP1** | PL → PS master | 32-bit | 600 MB/s | No | Second GP channel (independent) |
| **S_AXI_HP0** | PL → DDR slave | 64-bit | 1,200 MB/s | No | High-performance FPGA → DDR streaming |
| **S_AXI_HP1** | PL → DDR slave | 64-bit | 1,200 MB/s | No | HP port #2 |
| **S_AXI_HP2** | PL → DDR slave | 64-bit | 1,200 MB/s | No | HP port #3 |
| **S_AXI_HP3** | PL → DDR slave | 64-bit | 1,200 MB/s | No | HP port #4 |
| **S_AXI_ACP** | PL → SCU slave | 64-bit | 1,200 MB/s | **Yes — L1/L2 coherent** | Cache-coherent FPGA access |

### GP vs HP vs ACP — When to Use Which

```
┌────────────── PS ──────────────────────────────┐
│                                                 │
│   GP Ports (4×, 32-bit):                        │
│   ┌─────────────────────────────────┐           │
│   │ Low bandwidth, high flexibility │           │
│   │ • Access any PS peripheral       │           │
│   │ • Access OCM, DDR                │           │
│   │ • 8–12 cycle latency             │           │
│   │ Use: GPIO, I2C, UART, registers  │           │
│   └─────────────────────────────────┘           │
│                                                 │
│   HP Ports (4×, 64-bit):                        │
│   ┌─────────────────────────────────┐           │
│   │ High bandwidth, DDR only        │           │
│   │ • FIFO interfaces at PS side     │           │
│   │ • 16–30 cycle latency            │           │
│   │ • 1,200 MB/s each (peak)        │           │
│   │ Use: Video, DMA, bulk data       │           │
│   └─────────────────────────────────┘           │
│                                                 │
│   ACP (1×, 64-bit):                             │
│   ┌─────────────────────────────────┐           │
│   │ Coherent — FPGA sees cache state │           │
│   │ • Connected to SCU directly      │           │
│   │ • 24–40 cycle latency            │           │
│   │ • 2–3 cycle penalty vs HP        │           │
│   │ Use: Shared data structures,     │           │
│   │      semaphores, lock-free code  │           │
│   └─────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

**Critical sizing note**: The GP ports at 32-bit/150 MHz deliver ~600 MB/s theoretical but typically ~40–80 MB/s sustained due to PS interconnect arbitration. The HP ports at 64-bit/150 MHz are ~4× faster. If you're streaming data, use HP.

---

## ACP — The Crown Jewel of Zynq-7000

The **Accelerator Coherency Port** is Zynq-7000's architectural differentiator. No Cyclone V SoC has anything equivalent.

### How ACP Works

```
┌─────────── Cortex-A9 ───────────┐
│  Core 0        Core 1            │
│  L1 I/D        L1 I/D            │
│    └─────┬────────┘               │
│          ▼                        │
│    ┌───────────┐                  │
│    │    SCU    │ ◄── S_AXI_ACP ───┼── FPGA fabric issues coherent
│    │ Snoop     │     (64-bit)      │   read/write through ACP
│    │ Control   │                  │
│    │ Unit      │                  │
│    └─────┬─────┘                  │
│          ▼                        │
│    ┌───────────┐                  │
│    │ L2 Cache  │  512 KB           │
│    │ (PL310)   │                  │
│    └─────┬─────┘                  │
│          ▼                        │
│    ┌───────────┐                  │
│    │ DDR Ctrl  │ ─── DDR3 ────────┼── External DDR
│    └───────────┘                  │
└────────────────────────────────────┘

When FPGA issues a read through ACP:
1. SCU checks L1 caches of both cores for dirty data
2. If dirty → SCU copies modified line to L2, responds to FPGA
3. If clean in L2 → L2 responds directly
4. If miss → DDR fetch + L2 fill + respond to FPGA
```

### ACP vs Non-Coherent (HP)

| Operation | HP (Non-Coherent) | ACP (Coherent) |
|---|---|---|
| FPGA reads shared variable | Reads DDR directly — **stale data risk** | SCU snoops L1 — **always current** |
| CPU writes, FPGA reads | Must `flush_cache_range()` first | Automatic — no software intervention |
| FPGA writes, CPU reads | Must `invalidate_cache_range()` first | Automatic |
| Latency | ~20 cycles | ~24 cycles (~2 extra for snoop) |
| Bandwidth | ~700–900 MB/s | ~500–800 MB/s (snoop overhead) |

### When NOT to Use ACP

ACP adds ~2–4 cycles of snoop latency. For pure **bulk streaming** where CPU and FPGA never share data structures:
- Use HP ports — lower latency, slightly higher throughput
- ACP is for **shared data** (queues, buffers with metadata, lock-free rings)
- Classic pattern: HP for data buffers, ACP for control/status in shared memory

---

## PS↔PL Interrupt Routing

Zynq-7000 provides **16 PL-to-PS interrupts** (IRQ_F2P[15:0]) plus a shared peripheral interrupt (nIRQ):

```
PL (FPGA Fabric)                    PS (Processing System)
─────────────────                   ──────────────────────
irq_f2p[0]  ──────────────────────► Generic Interrupt Controller (GIC)
irq_f2p[1]  ──────────────────────►     │
    ...                                 ├─ nIRQ → CPU0
irq_f2p[15] ──────────────────────►     ├─ nIRQ → CPU1
                                        └─ Priority, masking, nesting
```

Each IRQ_F2P line is level-sensitive active-high. In the device tree:

```dts
interrupt-parent = <&intc>;
interrupts = <0 29 4>;  /* SPI 29, level high */
```

The 16 lines share the GIC's SPI (Shared Peripheral Interrupt) range 61–68 and 84–91. Consult UG585 Table 7-4 for the exact mapping.

---

## DMA Architecture

Zynq-7000 has two independent DMA engines:

| DMA | Channels | Data Width | Connected To | Use Case |
|---|---|---|---|---|
| **PS DMAC** (DMAC 330) | 8 | 32-bit | PS interconnect (DDR, OCM, peripherals, PL via GP/HP) | CPU-initiated memory-to-memory or peripheral DMA |
| **PL AXI DMA** (fabric IP) | Configurable | 32–1,024 bit | HP ports, ACP | FPGA-initiated scatter-gather DMA |

### PS DMAC → PL Data Path

```
CPU programs DMAC with descriptor chain
  │
  ▼
DMAC reads from DDR (via PS interconnect)
  │
  ▼
DMAC writes to S_AXI_GP0 → PL (AXI4-Lite, limited bandwidth)
  or
DMAC writes to S_AXI_HP0 → PL (AXI4, high bandwidth, but HP is PL-to-PS only!)
```

**Important restriction**: HP ports are **PL-to-PS only** (FPGA is the AXI master). The PS cannot initiate transactions to HP ports. To send data from PS to FPGA at high bandwidth, the FPGA must DMA-pull from DDR (via HP) or the PS must push through GP0/1 (slow) or through a shared BRAM FIFO in PL.

### Preferred High-Bandwidth Pattern

For CPU→FPGA data transfer at speed:
1. CPU writes data to DDR buffer
2. CPU notifies FPGA (register write via GP0)
3. FPGA's AXI DMA reads DDR through S_AXI_HP0 (FPGA is master)
4. FPGA processes data
5. FPGA's AXI DMA writes results to DDR through S_AXI_HP1

This keeps the FPGA as the DMA master on HP ports, which is what they're designed for.

---

## Boot Flow — PS First, Then PL

```
   Power-On Reset
        │
        ▼
┌────────────────────┐
│ Stage 0: Boot ROM  │  Mask ROM in PS — ~128 KB
│                    │  Reads boot mode pins (5 bits)
│                    │  Loads FSBL from SD/QSPI/NAND/NOR/JTAG
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Stage 1: FSBL      │  First Stage Boot Loader
│ (First Stage       │  • Initializes PS: DDR, clocks, PLLs, MIO
│  Boot Loader)      │  • MAY configure PL with bitstream
│                    │  • Loads U-Boot (or bare-metal app)
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Stage 2: U-Boot    │  Second Stage Boot Loader
│                    │  • Filesystem access (FAT/ext4)
│                    │  • MAY configure PL (if not done in FSBL)
│                    │  • Loads Linux kernel + device tree
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Stage 3: Linux     │  Kernel boots
│                    │  • PL may still be unconfigured!
│                    │  • FPGA Manager (/sys/class/fpga_manager/)
│                    │    configures PL post-boot
└────────────────────┘
```

| Boot Mode | Mode Pins | Media | Notes |
|---|---|---|---|
| SD Card | 0b00000 | SD/SDHC/SDXC | Most common for development |
| QSPI | 0b00100 | Single/dual QSPI flash | Production, fast boot |
| NAND | 0b01000 | 8/16-bit NAND | Larger capacity |
| NOR | 0b00110 | Parallel NOR | Fast random access |
| JTAG | — | — | Debug only, no media needed |

### PL Power Domain — NOT Automatic

**Critical gotcha**: The PL (FPGA fabric) power domain is **off** after PS boot. Unlike Cyclone V where fabric configuration is part of the HPS boot flow, Zynq-7000 requires explicit PL configuration:

```bash
# Linux: configure PL via FPGA Manager
echo soc_system.bit > /sys/class/fpga_manager/fpga0/firmware
# or via device tree overlay + configfs
mkdir /configfs/device-tree/overlays/my_fpga
cat my_overlay.dtbo > /configfs/device-tree/overlays/my_fpga/dtbo
```

Until PL is configured, AXI bridges appear "not ready" and any driver touching them will fail. Common workaround: configure PL in FSBL so bridges are ready when kernel probes.

---

## Zynq-7000 vs Cyclone V SoC — Decision Matrix

| Criterion | Choose Cyclone V SoC When... | Choose Zynq-7000 When... |
|---|---|---|
| Cache coherency | Not needed (streaming data) | **ACP needed** — shared data structures between CPU and FPGA |
| Toolchain cost | Free (Quartus Lite) | Free (Vivado Standard) for most devices |
| Dev board cost | DE10-Nano ~$108 | Cora Z7 ~$99 or Zybo ~$199 |
| FPGA density | 301K LEs max | 444K LEs max |
| Transceivers | 3.125 Gbps (E variant: none) | 12.5 Gbps |
| Open-source tools | None | Project X-Ray + SymbiFlow (partial) |
| Linux ecosystem | Yocto/Buildroot, Intel SoC EDS | PetaLinux, Yocto, PYNQ |
| Boot simplicity | HPS boot ROM → Preloader → U-Boot | Boot ROM → FSBL → U-Boot (extra stage) |
| FPGA config flexibility | U-Boot or Linux FPGA Manager | FSBL, U-Boot, or Linux FPGA Manager |

---

## Best Practices

1. **Use ACP for shared control structures, HP for data** — separate coherency-critical metadata from bandwidth-critical payloads.
2. **Configure PL in FSBL, not post-boot** — unless you have a specific hot-plug requirement. Drivers that probe before PL is ready are a debugging nightmare.
3. **Use 64-bit HP ports, not 32-bit GP ports for data** — GP ports are for register access and low-speed peripherals.
4. **OCM (256 KB) is faster than DDR** — use it for low-latency PS↔PL shared memory when your working set fits.
5. **Don't use all 4 HP ports simultaneously at max bandwidth** — the PS DDR controller has a single 32-bit interface. Aggregate HP bandwidth is capped by DDR throughput.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| PL not configured before driver probe | Bridge driver -ENODEV | Configure PL in FSBL or U-Boot |
| FPGA reads stale DDR via HP | Wrong data in FPGA after CPU write | Use ACP or `flush_cache_range()` before HP access |
| ACP bandwidth insufficient | Lower throughput than expected | ACP is for coherency, not max bandwidth. Use HP for bulk streaming |
| GP port bandwidth too low | Register access takes >100 µs | GP ports are 32-bit; burst access to DDR is penalized. Use HP + DMA |
| FSBL too large for OCM | Boot ROM can't load FSBL | OCM is 256 KB; FSBL must fit. Minimize FSBL features |

---

## References

| Source | Link |
|---|---|
| Zynq-7000 SoC Technical Reference Manual (UG585) | [AMD Docs](https://docs.amd.com/r/en-US/ug585-zynq-7000-trm) |
| Zynq-7000 SoC Data Sheet (DS190) | AMD/Xilinx documentation |
| Zynq-7000 AXI Reference Guide | Chapter 23 of UG585 |
| Vivado Design Suite: Embedded Processor Hardware Design (UG898) | AMD/Xilinx documentation |
| PetaLinux Tools Documentation | AMD/Xilinx documentation |

> **Next:** [Zynq MPSoC SoC Deep Dive](../../ultrascale_plus/soc/README.md) — quad Cortex-A53, CCI-400 coherency, dual R5F real-time cores, GPU, and VCU.
