[← PolarFire Home](../README.md) · [← Project Home](../../../../README.md)

# PolarFire SoC — RISC-V Hard-SoC Architecture Deep Dive

PolarFire SoC is unique in the FPGA industry: the **only** FPGA with hardened RISC-V application processors. Five 64-bit cores (4× U54 + 1× E51), a coherent AXI4 matrix, flash-based instant-on fabric, and SEU immunity make it architecturally distinct from every ARM-based SoC FPGA.

> For general PolarFire family info (FPGA-only variants, dev boards, Cyclone V comparison), see the [parent README](../README.md).

---

## PS Block Diagram — MSS (Microprocessor SubSystem)

```
┌──────────── PolarFire SoC MSS ────────────────────────────────────┐
│                                                                     │
│  ┌─────────── CPU Cluster ────────────────────────────────────┐    │
│  │                                                            │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │  U54_1   │  │  U54_2   │  │  U54_3   │  │  U54_4   │  │    │
│  │  │RV64IMAFDC│  │RV64IMAFDC│  │RV64IMAFDC│  │RV64IMAFDC│  │    │
│  │  │ 667 MHz  │  │ 667 MHz  │  │ 667 MHz  │  │ 667 MHz  │  │    │
│  │  │32KB L1I+D│  │32KB L1I+D│  │32KB L1I+D│  │32KB L1I+D│  │    │
│  │  │FPU, MMU  │  │FPU, MMU  │  │FPU, MMU  │  │FPU, MMU  │  │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │    │
│  │       └──────────────┼──────────────┼──────────────┘       │    │
│  │                      │              │                      │    │
│  │  ┌───────────────────▼──────────────▼──────────────────┐  │    │
│  │  │          Coherent AXI4 Switch (128-bit)              │  │    │
│  │  │          • All U54 + fabric ports coherent           │  │    │
│  │  │          • 2 MB L2 Cache (shared, 16-way)            │  │    │
│  │  │          • DDR4/LPDDR4 Controller (72-bit, ECC)      │  │    │
│  │  └───────────────────┬─────────────────────────────────┘  │    │
│  │                      │                                    │    │
│  └──────────────────────┼────────────────────────────────────┘    │
│                         │                                         │
│  ┌──────────┐  ┌───────▼────────┐  ┌─────────────────────────┐   │
│  │ E51 Mon. │  │  Fabric IF     │  │  Peripheral Bus          │   │
│  │RV64IMAC  │  │  Controllers   │  │  (AHB/APB)              │   │
│  │ Boot +   │  │  FIC0, FIC1,   │  │  QSPI, eMMC/SD, USB,    │   │
│  │ Monitor  │  │  FIC2          │  │  GbE, SPI, I2C, UART,   │   │
│  │667 MHz   │  │                │  │  CAN, GPIO, Timer        │   │
│  └──────────┘  └────────────────┘  └─────────────────────────┘   │
│                                                                     │
│  MSS → PL Interrupts: 41 lines (PLIC-managed)                      │
│  PL → MSS Interrupts: 6 lines                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The 5-Core RISC-V Cluster

| Core | ISA | Role | OS | Notes |
|---|---|---|---|---|
| **U54_1** | RV64IMAFDC | Application | Linux (SMP with U54_2–4) | Core 0 in Linux — runs kernel init |
| **U54_2** | RV64IMAFDC | Application | Linux (SMP) | Usually idle until scheduled |
| **U54_3** | RV64IMAFDC | Application | Linux, RTOS, or bare-metal | Can be AMP (asymmetric: different OS per core) |
| **U54_4** | RV64IMAFDC | Application | Linux, RTOS, or bare-metal | Can be AMP |
| **E51** | RV64IMAC | Monitor | Bare-metal (HSS) | Boots first, initializes system, monitors U54s |

### ISA Extension Breakdown

| Extension | Meaning | Available on |
|---|---|---|
| **RV64I** | 64-bit base integer | All 5 cores |
| **M** | Integer multiply/divide | All 5 cores |
| **A** | Atomic instructions (LR/SC, AMO) | All 5 cores |
| **C** | Compressed instructions (16-bit) | All 5 cores |
| **F** | Single-precision FPU | U54 only |
| **D** | Double-precision FPU | U54 only |
| **MMU** | Sv39 virtual memory | U54 only |

**Key difference**: The E51 has no FPU and no MMU — it's a pure monitor core, not a Linux target. U54 cores run Linux with full MMU and FPU.

---

## The Coherent Fabric — Everyone Is Coherent

**This is PolarFire SoC's defining architectural characteristic.** Unlike Intel (non-coherent HPS bridges) and Xilinx (coherent only via ACP/HPC ports), PolarFire SoC's AXI4 switch is **coherent by default** for all masters:

```
┌────────────────── Coherent AXI4 Switch ──────────────────────┐
│                                                               │
│   Masters (all coherent):                    Slaves:          │
│   ┌──────────┐                              ┌──────────────┐ │
│   │ U54_1    │──┐                           │ L2 Cache     │ │
│   │ (I/O coh)│  │                           │ 2 MB, 16-way │ │
│   └──────────┘  │   ┌─────────────────┐     └──────────────┘ │
│                 │   │                 │                       │
│   ┌──────────┐  ├──►│  Coherent       │     ┌──────────────┐ │
│   │ U54_2    │──┘   │  AXI4 Switch    │────►│ DDR Ctrl     │ │
│   └──────────┘      │  (128-bit)      │     │ 72-bit + ECC │ │
│                     │                 │     └──────────────┘ │
│   ┌──────────┐      │  FIC0: coherent │                       │
│   │ FPGA DMA │─────►│  FIC1: coherent │     ┌──────────────┐ │
│   │ (FIC0)   │      │  FIC2: non-coh  │────►│ Peripherals  │ │
│   └──────────┘      └─────────────────┘     └──────────────┘ │
│                                                               │
│   No flush/invalidate needed — FPGA sees same memory as CPU   │
└───────────────────────────────────────────────────────────────┘
```

### What "Coherent by Default" Means in Practice

| Operation | Intel Cyclone V SoC | Xilinx Zynq-7000 | Microchip PolarFire SoC |
|---|---|---|---|
| FPGA reads DDR after CPU write | Stale data (must flush) | Stale unless via ACP | **Always coherent** |
| FPGA writes DDR before CPU read | CPU sees stale (must invalidate) | Stale unless via ACP | **Always coherent** |
| Software cache management | Mandatory | Optional (ACP avoids it) | **Not needed** |
| Performance penalty for coherence | N/A (not available) | +2–4 cycles (ACP) | **Zero** — built into switch |

The tradeoff: PolarFire SoC's coherent switch has lower peak bandwidth than Intel's dedicated F2S ports (3.2 GB/s vs 38.4 GB/s aggregate on Cyclone V). But for shared-data applications, **eliminating software cache flushes eliminates an entire class of bugs**.

---

## Fabric Interface Controllers (FIC0, FIC1, FIC2)

Three independent paths from FPGA fabric into the MSS:

| Interface | Bus | Width | Coherent? | Latency | Primary Use |
|---|---|---|---|---|---|
| **FIC0** | AXI4 | 64-bit | **Yes** | ~15 cycles | FPGA ↔ DDR, FPGA ↔ L2 cache. The main data path. |
| **FIC1** | AXI4 | 64-bit | **Yes** | ~15 cycles | Second independent coherent port. Parallel streaming. |
| **FIC2** | AHB-Lite | 32-bit | No | ~8 cycles | Low-latency register access, GPIO, peripheral control |

### FIC Bandwidth Budget

```
FIC0 (64-bit, 200 MHz)  = 1,600 MB/s theoretical
FIC1 (64-bit, 200 MHz)  = 1,600 MB/s theoretical
FIC2 (32-bit, 150 MHz)  = 600 MB/s theoretical

DDR4-2133 (72-bit)      = 19.2 GB/s theoretical (shared by all)

FIC0 + FIC1 cannot saturate DDR — FPGA fabric, not DDR,
is the bandwidth bottleneck for large transfers.
```

---

## Boot Flow — HSS-Orchestrated, No DDR Training

PolarFire SoC's flash-based fabric means **no external bitstream** to load. The FPGA config is stored in internal SONOS flash. The boot flow is:

```
Power-On (<1 ms to fabric live)
      │
      ▼
┌──────────────────────┐
│ System Controller     │  Boots from internal non-volatile memory
│ (dedicated hard IP)   │  • Reads MSS config from SPI flash
│ • Releases MSS reset  │  • FPGA fabric already live (instant-on flash)
│ • Loads HSS image     │  • No bitstream to load — fabric is configured
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ E51 Monitor Core      │  First RISC-V core to execute
│ • Boots Hart Software │  • Runs HSS (Hart Software Services)
│   Services (HSS)      │  • Initializes DDR (no training needed —
│ • Sets up U54 cores   │    calibration stored in flash)
│ • Loads U-Boot        │  • Starts U54 application cores
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ U-Boot (on U54_1)     │  Standard U-Boot, RISC-V build
│ • Filesystem access   │  • No FPGA config command needed
│ • Loads kernel + DTB  │  • Fabric is already live
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Linux (SMP on 4× U54) │  All 4 U54 cores boot into Linux SMP
│ • FPGA bridges ready   │  • FIC0/FIC1/FIC2 enumerated
│ • No FPGA Manager      │  • Fabric is static (flash-based)
└──────────────────────┘
```

**Critical difference from Intel/Xilinx**: There is **no FPGA configuration step** in the boot flow. The fabric is live at power-on (<1 ms). There is no `fpga load` command, no `/sys/class/fpga_manager/`, no partial reconfiguration. The FPGA bitstream is burned into internal flash during programming (Libero SoC "Run PROGRAM Action").

---

## Interrupt Architecture — RISC-V PLIC

PolarFire SoC uses the RISC-V **Platform-Level Interrupt Controller (PLIC)**:

```
PL (FPGA Fabric)                  MSS (CPU SubSystem)
─────────────────                 ────────────────────
41 PL-to-MSS interrupts           ┌──────────────┐
    GPIO, DMA done,                │   PLIC       │
    UART, timer, custom       ───► │ (Platform-   │
    ─────────────────────          │  Level       │──► U54_1 M-mode
                                   │  Interrupt   │──► U54_2
6 MSS-to-PL interrupts             │  Controller) │──► U54_3
    ◄──────────────────            │              │──► U54_4
    (CPU notification)             └──────────────┘
```

| Feature | RISC-V PLIC | ARM GIC (Zynq-7000) |
|---|---|---|
| Interrupt lines | 41 (PL→MSS) + 6 (MSS→PL) | 16 (PL→PS) |
| Priority levels | Configurable per-source | Configurable |
| Multi-core routing | Yes — any interrupt to any hart (core) | Yes — any interrupt to any core |
| Edge/level | Level-sensitive only | Level or edge |

---

## PolarFire SoC vs ARM SoCs — Unique Advantages

| Feature | PolarFire SoC | ARM SoCs (Cyclone V, Zynq) |
|---|---|---|
| **Coherency** | Native — all fabric masters coherent | Optional — ACP/HPC ports only |
| **Boot time to fabric live** | <1 ms | 50–500 ms (bitstream load) |
| **SEU immunity** | Immune (flash cells) | Prone (SRAM cells) |
| **FPGA reconfig at runtime** | No (flash-based, 500–1000 cycles) | Yes (SRAM, unlimited reconfigs) |
| **DDR training at boot** | Pre-calibrated in flash | Performed every boot |
| **Power (standby)** | Near-zero | SRAM leakage current |
| **Bitstream security** | Inherent — no external bitstream | Requires encryption |
| **CPU ISA** | RISC-V (open) | ARM (proprietary) |
| **Toolchain** | Libero SoC (free for SoC) | Quartus Lite (free) / Vivado Standard (free) |

---

## Best Practices

1. **FIC0 for data, FIC2 for control** — coherent 64-bit AXI4 for bulk transfers, low-latency 32-bit AHB for registers.
2. **No cache flush calls needed** — if you find `flush_cache_range()` in your PolarFire SoC driver, it's copied from an ARM driver and it's doing nothing useful.
3. **Plan around flash endurance** — 500–1000 programming cycles. Verify your design in simulation/Libero before committing to flash.
4. **E51 boots you, U54 runs your app** — don't try to bypass HSS. The E51→U54 handoff is required for correct initialization.
5. **Use AMP for mixed-criticality** — run Linux on U54_1–2, bare-metal RTOS on U54_3–4. The coherent fabric handles shared memory without partition headaches.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Flash endurance exceeded | Programming fails after ~500 cycles | Use external SPI flash for development iteration; burn internal flash only for production |
| Assuming non-coherent behavior | Cache flush calls in driver | Remove them — fabric is coherent by default |
| FIC2 bandwidth insufficient | Register access too slow | FIC2 is 32-bit AHB. Move bulk data to FIC0/FIC1 |
| Libero SoC licensing | Can't program device | Libero SoC is free for PolarFire SoC; register at Microchip.com |
| DDR not working after FPGA reconfig | System hangs | DDR calibration is stored in flash. After flash reprogram, re-run DDR training in Libero |

---

## References

| Source | Link |
|---|---|
| PolarFire SoC Data Sheet (DS0146) | [Microchip Docs](https://www.microchip.com/en-us/product/MPFS250T) |
| PolarFire SoC User Guide (UG0820) | Microchip documentation |
| PolarFire SoC MSS Technical Reference Manual | Microchip documentation |
| Hart Software Services (HSS) GitHub | [polarfire-soc/hart-software-services](https://github.com/polarfire-soc/hart-software-services) |
| Mi-V RISC-V Ecosystem | [Microchip Mi-V](https://www.microchip.com/en-us/products/fpgas-and-plds/ip-cores/miv-risc-v) |
| RISC-V Privileged Specification | [riscv.org](https://riscv.org/technical/specifications/) |

> **Related:** [Zynq-7000 SoC Deep Dive](../../../xilinx/7series/soc/README.md) | [Zynq MPSoC Deep Dive](../../../xilinx/ultrascale_plus/soc/README.md) | [SoC Architecture Overview](../../../../02_architecture/soc/README.md)
