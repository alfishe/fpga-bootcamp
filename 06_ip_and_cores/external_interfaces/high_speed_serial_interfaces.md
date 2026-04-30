[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# High-Speed Serial Interfaces — USB 1.1/2.0/3.0/4

USB is the most common high-speed serial interface connecting FPGAs to host PCs, storage, and peripherals. Unlike I2C or SPI, USB requires a **physical layer (PHY)** and a **protocol stack** that spans from signal-level differential pairs up to enumeration, endpoints, and transfer types. FPGAs implement USB in two fundamentally different ways: **soft IP in fabric** (using external PHYs or bit-banging) and **hardened USB controllers** (integrated silicon on SoC FPGAs).

---

## USB Generations at a Glance

| Generation | Speed | Signaling | PHY | FPGA Implementation |
|---|---|---|---|---|
| **USB 1.1 Full Speed** | 12 Mbps | Single-ended D+/D- | Internal or external | Soft core + external PHY; bit-banging on some FPGAs |
| **USB 2.0 High Speed** | 480 Mbps | Differential D+/D- | External ULPI PHY | Soft core + ULPI PHY; hard USB 2.0 OTG on SoC FPGAs |
| **USB 3.0 SuperSpeed** | 5 Gbps | Differential SSTX/SSRX | External or SerDes | Soft core + USB3 PHY; requires GT transceivers |
| **USB 3.1 Gen2** | 10 Gbps | Differential SSTX/SSRX | External or SerDes | GTY/GTH transceivers + external PHY |
| **USB4 / Thunderbolt 3** | 40 Gbps | Dual-lane differential | External controller only | No FPGA direct support; external bridge chip |

---

## Soft IP Implementations

When an FPGA has no hardened USB block, the entire USB protocol stack must be implemented in fabric logic.

### Option A: External USB-to-Serial Bridge (Simplest)

The FPGA does not implement USB at all. An external bridge handles the USB side.

| Bridge IC | USB Side | FPGA Side | Use Case |
|---|---|---|---|
| **FT232R/FT232H** | USB 2.0 FS/HS | UART / FIFO | Debug console, slow data logging |
| **CP2102/CP2104** | USB 2.0 FS | UART | Low-cost alternative to FTDI |
| **CH340/CH343** | USB 2.0 FS | UART | Ultra-low-cost Chinese option |
| **FT2232H** | USB 2.0 HS | Dual UART / JTAG / FIFO | Debug + JTAG in one chip |
| **CY7C68013A** | USB 2.0 HS | 8/16-bit parallel FIFO | Higher throughput, DMA-capable |

**Best for:** Any FPGA. No USB knowledge needed. The FPGA sees UART or FIFO.

### Option B: ULPI External PHY + Soft MAC

A **ULPI PHY** (e.g., USB3320, USB3343) converts USB 2.0 differential signals to a parallel 8-bit interface that the FPGA drives.

```
USB 2.0 Cable ──→ USB3320 ULPI PHY ──→ FPGA (8 data + 3 control pins)
                              │
                              └── 24 MHz ULPI clock
```

**FPGA fabric requirements:**
- **USB 2.0 Device MAC:** ~500–1000 LUTs (state machine + endpoint buffers)
- **USB 2.0 Host MAC:** ~1500–2500 LUTs (hub support, scheduling, TT)
- **External pins:** 8 data + DIR + NXT + STP + CLK = 12 pins

**Open-source USB 2.0 soft cores:**
- `tinyusb` (C library, runs on soft CPU + FPGA)
- `no2usb` — Verilog USB 2.0 device core (~800 LUTs)
- `ulpi_wrapper` — ULPI-to-fabric adapter in VHDL

### Option C: Bit-Banged USB (No PHY)

Some projects implement USB 1.1 Full Speed by directly driving D+/D- from FPGA pins through resistor DACs:

- **Project `foboot`** — USB bootloader for iCE40 UP5K
- **Project `softusb`** — USB 1.1 on Lattice iCE40
- **Principle:** FPGA pins + series resistors + oversampling at 48 MHz
- **Limitation:** Full Speed (12 Mbps) only; very timing-critical

**Resource cost:** ~200–300 LUTs for device-only, 1-bit DAC output.

### Option D: USB 3.0+ Soft MAC + External PHY

USB 3.0 requires **5 Gbps SerDes** or a dedicated USB 3.0 PHY chip:

- **TUSB1310A** — USB 3.0 PHY with parallel pipe interface
- **VL805/VL806** — USB 3.0 host controller with PCIe or parallel FIFO back-end
- **FPGA sees:** PIPE interface (16-bit @ 250 MHz) or FIFO interface

**Resource cost:** USB 3.0 device MAC ~3000–5000 LUTs; host MAC ~8000+ LUTs.

---

## Hardened USB Controllers — Where to Find Them

SoC FPGAs integrate ARM or RISC-V processors with hardened USB controllers on the processor subsystem. These are **not accessible from the FPGA fabric directly** — they live on the "PS" (Processing System) or "HPS" (Hard Processor System) side.

### Master Matrix: Hardened USB by FPGA Family

| FPGA Family | Hard USB | USB Version | Speed | PHY Interface | PS/HPS Access | Fabric Bridge |
|---|---|---|---|---|---|---|
| **Xilinx Zynq-7000** | Yes | 2.0 OTG | HS (480 Mbps) | ULPI external | Cortex-A9 PS | AXI via GP port |
| **Xilinx Zynq MPSoC** | Yes | 3.0 + 2.0 OTG | SS (5 Gbps) / HS | USB3 external + ULPI | Cortex-A53/R5 PS | AXI via NoC/GP |
| **Xilinx Zynq RFSoC** | Yes | 3.0 + 2.0 OTG | SS / HS | Same as MPSoC | Cortex-A53 PS | AXI via NoC |
| **Intel Cyclone V SoC** | Yes | 2.0 OTG | HS | ULPI external | ARM Cortex-A9 HPS | Avalon-MM bridge |
| **Intel Arria 10 SoC** | Yes | 2.0 OTG | HS | ULPI external | ARM Cortex-A9 HPS | Avalon-MM bridge |
| **Microchip PolarFire SoC** | Yes | 2.0 | HS | ULPI external | RISC-V MSS | AXI4 fabric bridge |
| **Lattice ECP5** | No | — | — | — | — | Soft core only |
| **Lattice CrossLink-NX** | No | — | — | — | — | Soft core only |
| **Lattice CertusPro-NX** | No | — | — | — | — | Soft core only |
| **Intel MAX 10** | No | — | — | — | — | Soft core only |
| **Gowin Arora-V** | No | — | — | — | — | Soft core only |
| **Microchip PolarFire (non-SoC)** | No | — | — | — | — | Soft core only |

### Key Insight: USB 3.0 is Rarely Hardened

Only the **Xilinx Zynq MPSoC/RFSoC** has a hardened USB 3.0 controller — and even then, it still requires an **external USB 3.0 PHY** (e.g., TUSB1310A). There is no FPGA (as of 2025) with a fully integrated USB 3.0 PHY.

```
Zynq MPSoC USB 3.0 block:
┌─────────────────────────────────────────┐
│  PS Side: USB 3.0 controller (hardened) │
│         └──→ PIPE interface             │
│                │                        │
│         External TUSB1310A PHY          │
│                │                        │
│         USB 3.0 SSTX/SSRX pins          │
└─────────────────────────────────────────┘
```

### Accessing Hardened USB from the FPGA Fabric

The hardened USB lives in the processor subsystem. To use it from FPGA logic:

**Xilinx Zynq-7000 path:**
```
FPGA fabric ──→ AXI GP port ──→ PS AXI interconnect ──→ USB 2.0 controller ──→ ULPI PHY
```

**Intel Cyclone V SoC path:**
```
FPGA fabric ──→ Avalon-MM bridge ──→ HPS L3 interconnect ──→ USB 2.0 OTG ──→ ULPI PHY
```

**Latency implication:** Every USB transaction from fabric goes through the PS/HPS interconnect. For high-throughput USB, use DMA (PL330 on Zynq, mSGDMA on Intel) rather than CPU-mediated transfers.

---

## USB 2.0: Soft vs. Hardened Decision Guide

| Criterion | Soft USB + ULPI PHY | Hardened USB (SoC FPGA) |
|---|---|---|
| **FPGA cost** | Any FPGA (~$5–$50) | SoC FPGA only (~$50–$500+) |
| **LUT cost** | 500–2500 LUTs | 0 LUTs (hardened) |
| **Development effort** | High — protocol stack in RTL or soft CPU | Low — Linux handles USB stack |
| **Linux support** | Must port tinyusb or write driver | Full Linux USB gadget/host support |
| **Throughput** | Up to ~40 MB/s (USB 2.0 HS bulk) | Up to ~40 MB/s (USB 2.0 HS bulk) |
| **Host vs Device** | Either (but host is more LUTs) | OTG — both (role switchable) |
| **Best for** | Standalone FPGA without processor | SoC designs running Linux |

---

## USB on Specific FPGA Families

### Xilinx Zynq-7000 — The Reference Implementation

```c
// Linux device tree snippet for Zynq-7000 USB 2.0
usb0: usb@e0002000 {
    compatible = "xlnx,zynq-usb-2.20a";
    clocks = <&clkc 28>;
    dr_mode = "otg";          // or "peripheral" or "host"
    phy_type = "ulpi";
    usb-phy = <&usb_phy0>;
};
```

- **Two USB 2.0 OTG controllers** in PS
- **ULPI external PHY required** (e.g., USB3320)
- Linux `g_mass_storage`, `g_ether`, `g_serial` gadget modules work out-of-the-box
- From PL: Use AXI GP port to trigger USB DMA, or use Linux on PS

### Intel Cyclone V SoC — HPS USB

- **One USB 2.0 OTG** in HPS
- **ULPI external PHY required**
- HPS runs Linux; FPGA fabric accesses USB indirectly via Avalon-MM
- Pre-built Yocto/PetaLinux images include USB gadget support

### Microchip PolarFire SoC — RISC-V USB

- **One USB 2.0 controller** in MSS
- **ULPI external PHY required**
- PolarFire SoC Linux BSP includes USB host and gadget drivers
- RISC-V core handles USB stack; FPGA fabric bridges via AXI

### Lattice iCE40 / ECP5 — Soft USB Only

- **No hardened USB anywhere**
- **iCE40:** `foboot` project implements USB 1.1 bootloader in ~300 LUTs using resistor DAC
- **ECP5:** Can implement ULPI + soft MAC for USB 2.0 device at ~800 LUTs
- **Trade-off:** Lowest cost, highest effort

---

## Power and Clocking Considerations

| USB Generation | Reference Clock | FPGA Clock Requirement | Power |
|---|---|---|---|
| USB 1.1 FS | 48 MHz (from PHY or FPGA) | 48 MHz ±0.25% | ~10 mW |
| USB 2.0 HS | 60 MHz ULPI clock | 60 MHz input + fabric @ 60 MHz | ~50–100 mW (PHY) |
| USB 3.0 SS | 100 MHz REFCLK | SerDes CPLL @ 5 Gbps | ~500 mW–1 W (PHY + SerDes) |

**Critical:** USB 2.0 High Speed requires a **±0.25% clock accuracy** (500 ppm). Use a crystal or precision oscillator — FPGA-derived clocks from internal oscillators are usually not accurate enough.

---

## FPGA Resource Summary

| Implementation | LUTs | FFs | BRAM | External Components |
|---|---|---|---|---|
| USB 1.1 FS device (bit-bang) | 200–300 | 100–200 | 0 | 2 resistors + Zener diodes |
| USB 2.0 FS device (soft) | 400–600 | 200–400 | 1–2 | ULPI PHY (USB3320) |
| USB 2.0 HS device (soft) | 800–1200 | 400–800 | 2–4 | ULPI PHY (USB3320) |
| USB 2.0 HS host (soft) | 2000–3500 | 1000–2000 | 4–8 | ULPI PHY + hub knowledge |
| USB 3.0 device (soft MAC) | 3000–5000 | 2000–3000 | 8–16 | USB3 PHY (TUSB1310A) |
| **Hardened USB 2.0** | **0** | **0** | **0** | ULPI PHY |
| **Hardened USB 3.0** | **0** | **0** | **0** | USB3 PHY |

---

## Best Practices

1. **Use hardened USB when available** — If your design uses a Zynq, Cyclone V SoC, or PolarFire SoC, let the processor handle USB. Run Linux and use existing gadget/host drivers.
2. **Use external USB-to-serial bridges for debug** — FT2232H gives you JTAG + UART + FIFO in one chip. No USB protocol development needed.
3. **Always use an external ULPI PHY for USB 2.0 HS** — Bit-banging USB 2.0 HS is not reliably achievable in FPGA fabric.
4. **Check USB 3.0 PHY availability before committing** — USB 3.0 PHYs are expensive (~$10–$20) and have long lead times. Consider USB 2.0 + external bridge instead.
5. **Ground the ID pin for OTG role detection** — If the PHY supports OTG, the ID pin state determines host vs device mode.

---

## Pitfalls

1. **"USB 2.0 is easy, I'll just bit-bang it"** — Full Speed (12 Mbps) is achievable. High Speed (480 Mbps) is NOT achievable via bit-banging. You need a ULPI PHY.
2. **Forgetting the 5V VBUS tolerance** — USB VBUS is 5V. USB connector shells and some PHY pins see 5V. Ensure your FPGA board can handle 5V on those pins (or use a PHY with built-in 5V tolerance).
3. **ULPI clock domain crossing** — The 60 MHz ULPI clock is asynchronous to your FPGA system clock. Use proper CDC (FIFO or handshake) between ULPI and fabric logic.
4. **USB enumeration timeout** — The host waits ~100 ms for a device to respond to SETUP packets. A slow FPGA configuration or a bug in the descriptor response causes "USB device not recognized."
5. **Confusing USB 3.0 PHY with USB 3.0 controller** — The Zynq MPSoC has a USB 3.0 controller but NO USB 3.0 PHY. You still need TUSB1310A or similar. The controller alone is useless.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| USB 2.0 Specification | USB-IF | Full protocol, descriptors, endpoints, electrical |
| ULPI Specification v1.1 | UTMI+ Working Group | ULPI pinout, register map, timing |
| USB 3.2 Specification | USB-IF | SuperSpeed protocol, LTSSM, power delivery |
| USB3320 Datasheet | Microchip | Common ULPI PHY pinout and configuration |
| TUSB1310A Datasheet | TI | USB 3.0 PHY with PIPE interface |
| `no2usb` Project | GitHub / im-tomu | Open-source Verilog USB 2.0 device core |
| `foboot` Project | GitHub / im-tomu | iCE40 USB 1.1 bootloader |
| [Storage Interfaces](usb_and_storage_interfaces.md) | This KB | SATA, NVMe, SD/eMMC (storage over USB or direct) |
| [Low-Speed Serial](low_speed_serial_interfaces.md) | This KB | I2C, SPI, UART for USB-PHY configuration and sideband |
