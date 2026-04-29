[← SoC Home](README.md) · [← Cyclone V Home](../README.md) · [← Project Home](../../../../README.md)

# Cyclone V SoC — HPS Address Map Deep Dive

Every byte the HPS can touch lives in a flat 4 GB physical address space. Understanding what lives where — and which bridge a given address region traverses — is essential for writing device tree entries, debugging `/dev/mem` access, and designing FPGA slaves that respond to the right address ranges.

---

## The 4 GB Physical Address Space

```
0x0000_0000 ┌───────────────────────────────────────┐
            │  SDRAM (HPS DDR Controller)           │  ← Mapped via L3 NIC-301
            │  0–4 GB (populated: 256 MB–4 GB)      │
            │  Linux kernel, userspace, DMA buffers │
0xC000_0000 ├───────────────────────────────────────┤
            │  FPGA Slaves (H2F Bridge)             │  960 MB aperture
            │  HPS reads/writes FPGA AXI slaves     │
0xFC00_0000 ├───────────────────────────────────────┤
            │  RESERVED                             │
0xFF20_0000 ├───────────────────────────────────────┤
            │  FPGA Slaves (LWH2F Bridge)           │  2 MB aperture
            │  Lightweight control/status           │
0xFF40_0000 ├───────────────────────────────────────┤
            │  HPS Peripherals                      │
            │  UART, SPI, I2C, EMAC, etc.           │
0xFFD0_0000 ├───────────────────────────────────────┤
            │  System Manager / Clocks              │
            │  Reset Manager, Clock Manager         │
0xFFE0_0000 ├───────────────────────────────────────┤
            │  L3 Interconnect Config               │
            │  NIC-301 registers, QoS               │
0xFFFD_0000 ├───────────────────────────────────────┤
            │  Boot ROM (64 KB)                     │
            │  Read-only, maps at reset             │
0xFFFE_0000 ├───────────────────────────────────────┤
            │  On-Chip RAM (64 KB)                  │
            │  HPS + FPGA accessible via F2H        │
0xFFFF_FFFF └───────────────────────────────────────┘
```

---

## SDRAM Region (`0x0000_0000` – `0xBFFF_FFFF`)

| Property | Value |
|---|---|
| **Physical range** | `0x0000_0000` – `0xBFFF_FFFF` (up to 3 GB) |
| **DE10-Nano populated** | `0x0000_0000` – `0x3FFF_FFFF` (1 GB) |
| **Bus** | L3 NIC-301, 64-bit AXI |
| **Bandwidth** | Up to 3.2 GB/s (DDR3-400, 32-bit) |
| **Linux** | Kernel + userspace live here; loaded by U-Boot |
| **FPGA access** | Via F2S ports (not directly mapped to HPS address space) |

The HPS DDR controller handles all SDRAM access. FPGA masters reach SDRAM through the six F2S ports, which connect to the SDRAM controller via the L3 interconnect — **not** through the H2F/F2H bridges.

---

## FPGA Slaves — H2F Bridge (`0xC000_0000` – `0xFBFF_FFFF`)

| Property | Value |
|---|---|
| **Physical range** | `0xC000_0000` – `0xFBFF_FFFF` |
| **Size** | 960 MB |
| **Data width** | Configurable: 32, 64, or 128 bits |
| **Bus protocol** | AXI-3 (with WID write interleaving) |
| **Linux access** | `ioremap()` or `/dev/mem` from kernel space |
| **Typical use** | Bulk data transfer HPS→FPGA: framebuffers, lookup tables, DMA descriptor rings |

**Sub-region allocation (example from DE10-Nano Linux DT):**

| Region | Start | Size | Typical Assignment |
|---|---|---|---|
| FPGA AXI slaves | `0xC000_0000` | 256 MB | Memory-mapped FPGA IP, FIFOs, registers |
| Reserved | `0xD000_0000` | 704 MB | Unused in typical DE10-Nano config |

> The full 960 MB is configurable in Platform Designer (Qsys). You can map multiple FPGA AXI slaves at different offsets within this window.

---

## FPGA Slaves — LWH2F Bridge (`0xFF20_0000` – `0xFF3F_FFFF`)

| Property | Value |
|---|---|
| **Physical range** | `0xFF20_0000` – `0xFF3F_FFFF` |
| **Size** | 2 MB |
| **Data width** | 32-bit fixed |
| **Bus protocol** | AXI-3 (but effectively AXI-4 since no WID needed for 32-bit) |
| **Linux access** | `ioremap()` — small, ideal for control/status |
| **Typical use** | Control registers, GPIO banks, status readback, interrupt acknowledgements |

**Why a separate 32-bit bridge?**

The LWH2F bridge bypasses the HPS L3 NIC-301 for register access, giving lower latency (~10–20 cycles vs ~15–30 for H2F). It shares the HPS-to-FPGA physical path with the H2F bridge, so concurrent H2F bulk DMA can stall LWH2F reads (see [hps_fpga_interaction.md](hps_fpga_interaction.md) §1).

---

## HPS Peripheral Region (`0xFF40_0000` – `0xFFCF_FFFF`)

| Peripheral | Base Address | Size | Notes |
|---|---|---|---|
| **UART0** | `0xFFC0_2000` | 256 B | 16550-compatible, Linux console on DE10-Nano |
| **UART1** | `0xFFC0_3000` | 256 B | Secondary |
| **SPI0** | `0xFFE0_1000` | 256 B | Master/slave, up to 100 MHz |
| **SPI1** | `0xFFE0_2000` | 256 B | |
| **I2C0** | `0xFFC0_4000` | 256 B | Standard/Fast/Fast+ (100/400/1000 kHz) |
| **I2C1** | `0xFFC0_5000` | 256 B | |
| **I2C2** | `0xFFC0_6000` | 256 B | |
| **I2C3** | `0xFFC0_7000` | 256 B | |
| **EMAC0** | `0xFF70_0000` | 4 KB | 10/100/1000, RGMII/GMII/MII |
| **EMAC1** | `0xFF70_2000` | 4 KB | |
| **USB0 (OTG)** | `0xFFB0_0000` | 64 KB | USB 2.0 HS, ULPI PHY |
| **USB1 (OTG)** | `0xFFB4_0000` | 64 KB | |
| **SD/MMC** | `0xFF70_4000` | 4 KB | SD 3.0, eMMC 4.5, boot-capable |
| **QSPI** | `0xFF70_5000` | 4 KB | Quad-SPI flash controller, boot-capable |
| **NAND** | `0xFF90_0000` | 64 KB | ONFI 1.0, 8-bit, ECC |
| **CAN0** | `0xFFC0_0000` | 256 B | CAN 2.0B |
| **CAN1** | `0xFFC0_1000` | 256 B | |
| **GPIO0** | `0xFF70_8000` | 256 B | 29 I/O pins |
| **GPIO1** | `0xFF70_9000` | 256 B | 29 I/O pins |
| **GPIO2** | `0xFF70_A000` | 256 B` | 9 I/O pins (57 total in GPIO0+1+2) |
| **Timer0 (SP Timer)** | `0xFFC0_8000` | 256 B | OS tick |
| **Timer1–3 (SP)** | `0xFFC0_9000` – `0xFFC0_B000` | 256 B each | General-purpose |
| **Watchdog0** | `0xFFD0_0200` | 256 B | |
| **Watchdog1** | `0xFFD0_0300` | 256 B | |
| **DMA Controller** | `0xFFE0_0000` | 4 KB | 8-channel, scatter-gather, descriptor-based |

---

## System Manager (`0xFFD0_0000` – `0xFFDF_FFFF`)

| Block | Base Address | Notes |
|---|---|---|
| **System Manager** | `0xFFD0_8000` | Pin muxing, IO configuration, FPGA bridge control, ECC status |
| **Clock Manager** | `0xFFD0_4000` | MPU, L3/L4, SDRAM, peripheral clock configuration |
| **Reset Manager** | `0xFFD0_5000` | HPS + FPGA bridge reset control |
| **FPGA Manager** | `0xFFD0_6000` | Controls FPGA configuration from HPS (FPP ×16 data pump) |
| **Scan Manager** | `0xFFD0_9000` | JTAG scan chain control |
| **FPGA Bridge Control** | System Manager offset `0x50` | Enable/disable H2F, LWH2F, F2H bridges |

---

## L3 Interconnect (NIC-301) Configuration (`0xFFE0_0000` – `0xFFEC_FFFF`)

The ARM CoreLink NIC-301 is the central bus matrix. Its registers control QoS, remap, and security (TrustZone) for all master/slave ports.

---

## Boot ROM (`0xFFFD_0000` – `0xFFFD_FFFF`)

| Property | Value |
|---|---|
| **Size** | 64 KB |
| **Type** | Mask ROM, read-only |
| **Maps at** | Reset vector (`0x0000_0000` remapped to here on cold boot) |
| **Role** | First code executed. Reads BSEL pins, loads preloader from selected boot source |

---

## On-Chip RAM (`0xFFFF_0000` – `0xFFFF_FFFF`)

| Property | Value |
|---|---|
| **Size** | 64 KB |
| **Access** | HPS (all masters), FPGA (via F2H bridge configured to hit this range) |
| **ECC** | Supported (single-error correction, double-error detection) |
| **Typical use** | Shared mailbox between HPS and FPGA, preloader scratchpad, inter-processor communication |
| **Bandwidth** | ~1.6 GB/s theoretical; 500–1200 MB/s practical |

---

## FPGA View of HPS

From the FPGA fabric's perspective, the HPS address map is irrelevant. FPGA masters use:

| Access | How |
|---|---|
| **Read/write SDRAM** | F2S ports → L3 → SDRAM controller (FPGA sees SDRAM as sequential address space) |
| **Read/write On-Chip RAM** | F2H bridge → L3 → OCRAM (FPGA must drive correct HPS physical address) |
| **Read/write HPS peripherals** | F2H bridge → L3 → peripheral bus (rare; usually HPS owns peripherals) |
| **Signal interrupt to HPS** | Dedicated 64 FPGA-to-HPS interrupt lines → HPS GIC |

---

## Linux Device Tree Correlation

**From the Linux device tree (`socfpga.dtsi`):**

```dts
hps2fpga-bridge@0 {
    compatible = "altr,socfpga-hps2fpga-bridge";
    reg = <0xC0000000 0x20000000>;  /* 512 MB */
};

lwhps2fpga-bridge@0 {
    compatible = "altr,socfpga-lwhps2fpga-bridge";
    reg = <0xFF200000 0x00200000>;  /* 2 MB */
};

fpga2hps-bridge@0 {
    compatible = "altr,socfpga-fpga2hps-bridge";
};
```

Custom FPGA slaves appear as children of the bridge nodes with `reg` offsets within the bridge aperture.

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Accessing `0xFF20_0000` with 64-bit LDRD instruction | Data abort / unaligned access | LWH2F is 32-bit only; use 32-bit reads |
| Trying to access FPGA slaves before bridge is enabled in System Manager | Bus hang / data abort | Enable bridges via `sysmgr` register writes in U-Boot |
| Mapping more than bridge aperture in DT | Silent truncation | Verify `ranges` property matches Platform Designer address width |
| Accessing HPS peripherals from FPGA via wrong F2H address | No response / bus error | FPGA must use HPS physical addresses exactly |

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS TRM, Chapter 1: Introduction to the HPS | Intel FPGA Documentation |
| Cyclone V HPS TRM, Chapter 4: HPS Address Map | Intel FPGA Documentation |
| Cyclone V Device Handbook Vol. 3: Hard Processor System | Intel FPGA Documentation |
| ARM CoreLink NIC-301 TRM | ARM DDI 0397 |
| Linux `socfpga.dtsi` | Linux kernel source: `arch/arm/boot/dts/socfpga.dtsi` |
