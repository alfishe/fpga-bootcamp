[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# USB and Storage Interfaces — USB 2.0/3.0/4, SATA, NVMe, SD/eMMC

Moving up from simple serial buses, these interfaces require dedicated PHYs, SerDes transceivers, or at minimum external bridge chips. They connect FPGAs to mass storage, host PCs, and removable media.

---

## Overview

| Interface | Speed | Pins | Voltage | FPGA Support |
|---|---|---|---|---|
| **USB 1.1 Full Speed** | 12 Mbps | 2 (D+, D-) | 3.3V | Soft core (e.g., USB-CDC) + external PHY or bit-banging |
| **USB 2.0 High Speed** | 480 Mbps | 2 (D+, D-) | 3.3V | ULPI external PHY (8-pin parallel) or hard IP on some SoCs |
| **USB 3.0 SuperSpeed** | 5 Gbps | 2 SSTX + 2 SSRX | 3.3V | Requires SerDes (GTP/GTX) or external USB3 PHY |
| **USB 3.1 Gen2** | 10 Gbps | Same as USB3 | 3.3V | GTY/GTH transceivers or external PHY |
| **USB4 / Thunderbolt 3** | 40 Gbps | 2 lanes diff | 3.3V | External controller (no FPGA direct PHY) |
| **SATA 1.5/3/6G** | 1.5/3/6 Gbps | 2 diff TX + 2 diff RX | 3.3V / 1.5V | GTP/GTX transceivers + soft SATA core |
| **NVMe** | 1–16 GB/s | 1–16 PCIe lanes | 3.3V / 1.8V | PCIe hard block + soft NVMe controller |
| **SD UHS-I** | 104 MB/s | 4 data + clk + cmd | 3.3V / 1.8V | Soft core; UHS-II requires transceivers |
| **SDIO / eMMC** | 200–400 MB/s | 4/8 data + clk + cmd | 3.3V / 1.8V | Soft core; eMMC common on SoC FPGAs |

---

## USB — Universal Serial Bus

### USB 1.1 / 2.0 — The FPGA-Friendly Generations

USB 2.0 is the practical limit for most FPGAs without dedicated SerDes. Implementation options:

**Option A: External USB-to-UART Bridge (Easiest)**
- FT232R, CP2102, CH340 — USB on one side, UART on the other
- FPGA sees a simple UART. No USB protocol knowledge needed.
- **Best for:** Bootloading, debug consoles, slow data logging

**Option B: ULPI External PHY (Moderate)**
- USB3320, USB3343 — ULPI interface to FPGA (8 data + 3 control pins)
- FPGA implements USB 2.0 MAC/controller in fabric (~500–1000 LUTs)
- **Best for:** USB device mode (MSC, CDC-ACM, HID) on any FPGA with enough IO

**Option C: Hard USB Controller (SoC FPGAs)**
| FPGA Family | Hard USB | Speed | Notes |
|---|---|---|---|
| Xilinx Zynq-7000 | 1× USB 2.0 OTG | HS (480 Mbps) | PS-side only, ULPI external PHY |
| Xilinx Zynq MPSoC | 1× USB 3.0 + 1× USB 2.0 | SS (5 Gbps) / HS | USB 3.0 requires external PHY |
| Intel Cyclone V SoC | 1× USB 2.0 OTG | HS | HPS-side, ULPI external PHY |
| Microchip PolarFire SoC | 1× USB 2.0 | HS | MSS-side |

**Option D: Soft USB 1.1 / 2.0 (No PHY)**
- Projects like `foboot` (ICE40), `softusb` use resistor-DAC + oversampling
- FPGA drives D+/D- directly with series resistors
- Very timing-critical, limited to Full Speed (12 Mbps)
- **Best for:** iCE40 UP5K and other ultra-low-cost FPGAs

### USB 3.0+ — SerDes Territory

USB 3.0 SuperSpeed requires differential signaling at 5 Gbps. This needs:
- **SerDes transceivers** (GTP/GTX/GTY) on the FPGA, OR
- **External USB 3.0 hub/controller chip** (e.g., VL805) with parallel FIFO interface

Very few FPGAs implement USB 3.0 MAC in hard silicon. The Zynq MPSoC USB 3.0 still requires an external PHY (e.g., TUSB1310A).

---

## SATA — Serial ATA

SATA is a point-to-point serial bus at 1.5/3/6 Gbps. It uses 8b/10b encoding and native command queuing (NCQ).

### FPGA Implementation

SATA is **not** commonly implemented on FPGAs because:
1. It requires 6 Gbps SerDes (GTP/GTX minimum)
2. The protocol stack (PHY, Link, Transport, Command) is complex
3. NVMe over PCIe is faster and better supported

**When SATA on FPGA makes sense:**
- Industrial data recorders with legacy SATA SSDs
- SATA protocol analyzers (capture SATA traffic)

| FPGA Family | Transceiver Speed | SATA Feasibility |
|---|---|---|
| Xilinx Artix-7 | GTP @ 6.6 Gbps | Possible with soft SATA core |
| Xilinx Kintex-7 | GTX @ 12.5 Gbps | Straightforward |
| Intel Cyclone V | No native 6G transceivers | External SATA bridge required |
| Lattice ECP5 | SERDES @ 5 Gbps | Marginal for SATA 3G |

**Soft SATA cores:** OpenCores has SATA 2/3 implementations, but they require significant LUT resources (~3000–5000 LUTs) and careful timing closure.

---

## NVMe — Non-Volatile Memory Express

NVMe is **not a physical interface** — it is a protocol that runs over PCIe. To implement NVMe on an FPGA:

1. **PCIe hard block** (Endpoint or Root Port mode)
2. **NVMe host controller** in fabric (soft core)
3. **PCIe DMA engine** for data movement

### FPGA Implementation Path

```
PCIe Root Port (hard) ──→ NVMe Host Controller (soft) ──→ AXI DMA ──→ DDR
         │                                              │
         └──→ PCIe lanes ──→ M.2 connector ──→ NVMe SSD
```

**Vendor IP:**
- Xilinx: XDMA + custom NVMe host (~$0 license for XDMA, NVMe host is custom)
- Intel: PCIe HIP + custom NVMe logic
- Open source: `nvme-fpga` project (Berkeley) implements NVMe host on RISC-V + FPGA

| FPGA Family | PCIe Gen | Max NVMe Speed | Notes |
|---|---|---|---|
| Xilinx Artix-7 | Gen2 x4 | 2 GB/s | Budget NVMe host |
| Xilinx Kintex UltraScale+ | Gen3 x8 | 8 GB/s | High-performance storage |
| Intel Stratix 10 DX | Gen3 x16 / Gen4 x8 | 16 GB/s | DCI-attached storage |
| AMD Versal | Gen4 x8 / Gen5 x4 | 16 GB/s | AI/ML training datasets |

---

## SD / SDIO / eMMC

### SD Card Interface

SD cards use a parallel bus (1, 4, or 8 data lines) with a command line and clock:
- **SDSC** — up to 25 MHz, 1-bit or 4-bit bus
- **SDHC** — up to 50 MHz, 4-bit bus
- **SDXC UHS-I** — up to 208 MHz, 4-bit bus, 1.8V signaling
- **UHS-II** — 1–2 Gbps, requires transceivers (not common on FPGAs)

### FPGA Implementation

SD host controllers are almost always **soft cores**:
- ~200–400 LUTs for basic SPI-mode SD
- ~500–800 LUTs for full SD mode (4-bit, DMA)
- Vendor IP available (Xilinx SDx, Intel SD Host)

**eMMC** is electrically identical to SD but soldered down (BGA package). SoC FPGAs often boot from eMMC.

| FPGA Family | Hard SD/eMMC | Notes |
|---|---|---|
| Xilinx Zynq-7000 | Yes (PS) | Boots from SD/eMMC |
| Xilinx Zynq MPSoC | Yes (PS) | SD 3.0 / eMMC 4.51 |
| Intel Cyclone V SoC | Yes (HPS) | SD/eMMC boot |
| Microchip PolarFire SoC | Yes (MSS) | eMMC boot |
| Lattice ECP5 | No | Soft core only |

---

## FPGA Family Support Summary

| Interface | SoC FPGA (Zynq, Cyclone V) | Mid-Range (Artix, ECP5) | High-End (Kintex, Stratix) |
|---|---|---|---|
| USB 2.0 Device | Hard + external PHY | Soft + external PHY | Hard + external PHY |
| USB 2.0 Host | Hard + external PHY | Soft + external PHY | Hard + external PHY |
| USB 3.0 | Hard on MPSoC + external PHY | External bridge only | External bridge or GTY |
| SATA | Not practical | Not practical | Soft core + GTX |
| NVMe | Hard PCIe + soft NVMe | Not practical (no PCIe) | Hard PCIe + soft NVMe |
| SD/SDIO | Hard controller | Soft core | Soft or hard |
| eMMC | Hard (boot) | Soft core | Soft or hard |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| USB 2.0 Specification | USB-IF | Full USB 2.0 protocol, electrical, timing |
| ULPI Specification | UTMI+ Working Group | ULPI PHY interface (8-bit parallel to USB) |
| SATA 3.2 Specification | SATA-IO | 6 Gbps signaling, power management, NCQ |
| NVMe 1.4 Specification | NVM Express Inc | NVMe command set, queues, admin commands |
| SD Physical Layer Simplified Spec | SD Association | SD/SDHC/SDXC signaling, timing, command set |
| [PCIe Hard Blocks](../pcie/README.md) | This KB | PCIe implementation details for NVMe |
