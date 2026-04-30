[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# Display and Camera Interfaces — HDMI, DisplayPort, MIPI, LVDS

FPGAs are the backbone of video processing pipelines. They capture from cameras, process frames, and drive displays. The interface choices depend on bandwidth, cable length, and whether the FPGA has dedicated hardened video PHYs.

---

## Overview

| Interface | Speed per Lane | Lanes | Total Bandwidth | Voltage | FPGA Support |
|---|---|---|---|---|---|
| **DVI** | 1.65 Gbps | 3 data + clk | 4.95 Gbps | 3.3V TMDS | Soft TMDS encoder + external PHY |
| **HDMI 1.4** | 3.4 Gbps | 3 data + clk | 10.2 Gbps | 3.3V / 5V TMDS | Hard on Xilinx 7-series+; soft on others |
| **HDMI 2.0** | 6 Gbps | 3 data + clk | 18 Gbps | TMDS | Hard on UltraScale+; external chips for others |
| **HDMI 2.1** | 12 Gbps | 4 data (FRL) | 48 Gbps | TMDS/FRL | External retimer/PHY required |
| **DisplayPort 1.2** | 5.4 Gbps | 1–4 lanes | 21.6 Gbps | LVDS | Hard on high-end; external DP chips common |
| **DisplayPort 2.0** | 20 Gbps | 1–4 lanes | 80 Gbps | LVDS | External controller only |
| **MIPI D-PHY v1.2** | 1.5 Gbps | 1–4 data + clk | 6 Gbps | 1.2V | Hard on Lattice CrossLink-NX; soft on others |
| **MIPI D-PHY v2.1** | 2.5 Gbps | 1–4 data + clk | 10 Gbps | 1.2V | Hard on select devices |
| **MIPI C-PHY** | 2.28 Gbps/symbol | 3-wire | 6.84 Gbps | 1.2V | Very limited FPGA support |
| **LVDS Panel (24-bit)** | ~150 MHz pixel clk | 24 data + ctrl | ~5 Gbps | 2.5V / 3.3V LVDS | Almost all FPGAs support LVDS |

---

## HDMI — High-Definition Multimedia Interface

### TMDS Signaling

HDMI uses **TMDS (Transition Minimized Differential Signaling)** on three data channels plus a clock:
- Each TMDS channel carries 10 bits per pixel component (8b/10b encoded)
- 3.3V signaling on 7-series HR banks (TMDS_33 standard)
- Requires 50Ω termination to 3.3V

### FPGA Implementation Options

**Option A: Hard HDMI (Xilinx)**
| FPGA Family | Hard HDMI | Max Resolution | Notes |
|---|---|---|---|
| Xilinx 7-series (Artix/Kintex) | TX only (via VDMA) | 1080p60 | Requires external TMDS buffer (e.g., TMDS141) |
| Xilinx UltraScale+ | TX/RX | 4K60 (HDMI 2.0) | Integrated HDMI 2.0/DisplayPort subsystem |
| AMD Versal | TX/RX | 8K30 (HDMI 2.1) | Hard VDU (Video Decode Unit) + HDMI 2.1 |

**Option B: Soft TMDS (Any FPGA)**
- Implement TMDS encoder in fabric (~100 LUTs per channel)
- Use FPGA LVDS outputs with external level shift to TMDS voltages
- **DigiLED** project and others demonstrate this on iCE40 and ECP5
- Limited to lower resolutions (~720p30 on iCE40, 1080p30 on ECP5)

**Option C: External HDMI Transmitter (Most Flexible)**
- ADV7513 (HDMI 1.4), SiI9022A — parallel RGB in, HDMI out
- ADV7611 — HDMI in, parallel RGB out
- FPGA handles video timing; external chip handles TMDS

### Level Translation for HDMI

HDMI 5V DDC (I2C for EDID) is a common trap:
- The DDC lines (SCL/SDA) are pulled up to 5V on the sink side
- FPGA IO is 3.3V max
- **Solution:** PCA9306 or TXS0102 level translator on DDC lines
- TMDS lines themselves are current-mode differential — no level translation needed

---

## DisplayPort

DisplayPort uses **LVDS-like differential signaling** with link training:
- 1 to 4 main lanes + AUX channel (I2C-like, 1 Mbps)
- Link training establishes lane count, rate, and equalization
- Supports MST (Multi-Stream Transport) — multiple displays on one cable

### FPGA Implementation

DisplayPort is **significantly harder** than HDMI because:
1. Link training is mandatory and complex
2. AUX channel requires bidirectional communication
3. Higher speeds require GTY/GTX transceivers

| FPGA Family | DP Support | How |
|---|---|---|
| Xilinx UltraScale+ | DP 1.2 TX/RX | Hard DisplayPort subsystem + GTY |
| Intel Arria 10 | DP 1.2 TX/RX | Hard video IP + transceivers |
| Lattice CrossLink-NX | DP 1.2 TX | Hard ASSP + FPGA fabric |
| Low-end FPGAs | Not practical | External DP chip (e.g., Parade PS176) |

---

## MIPI — Mobile Industry Processor Interface

MIPI is the dominant camera and display interface in mobile/embedded. Two key specifications for FPGAs:

### MIPI D-PHY

D-PHY uses **1.2V differential pairs** with a unique DDR clocking scheme:
- Clock lane: continuous DDR clock
- Data lanes: DDR data, each bit sampled on both clock edges
- LP (Low Power) mode: single-ended 1.2V for control
- HS (High Speed) mode: differential 200 mV for data

### FPGA Implementation

**Hard MIPI D-PHY (Lattice CrossLink-NX / CertusPro-NX):**
- Lattice is the **only** FPGA vendor with hardened MIPI D-PHY in mid-range devices
- Supports 4 data lanes + 1 clock lane at 1.5 Gbps per lane
- Built-in CSI-2/DSI protocol layer

**Soft MIPI D-PHY (All Other FPGAs):**
- Xilinx 7-series: Use ISERDES/OSERDES with 1.2V HR banks + external resistor networks
- Intel: Similar approach with ALTLVDS + external components
- ECP5: Soft implementation possible but timing-critical

| FPGA Family | MIPI Support | Method | Max Speed |
|---|---|---|---|
| Lattice CrossLink-NX | Hard D-PHY | Hardened PHY + controller | 1.5 Gbps/lane |
| Lattice CertusPro-NX | Hard D-PHY | Same architecture | 1.5 Gbps/lane |
| Xilinx Zynq UltraScale+ | Soft D-PHY | ISERDES + external R-network | 1.0 Gbps/lane |
| Intel Arria 10 | Soft D-PHY | ALTLVDS + external components | 1.0 Gbps/lane |
| Gowin Arora-V | Soft D-PHY | Generic SerDes | ~800 Mbps/lane |

### MIPI CSI-2 vs. DSI

| Protocol | Direction | Use Case |
|---|---|---|
| **CSI-2** | Camera → FPGA | Image sensors, machine vision cameras |
| **DSI** | FPGA → Display | LCD panels, small OLEDs |

---

## LVDS Panel Interfaces

Industrial and automotive displays often use **parallel LVDS** (OpenLDI / FlatLink):
- 18-bit or 24-bit color (6 or 8 data pairs + clock pair)
- Pixel clock typically 25–150 MHz
- 2.5V or 3.3V LVDS signaling

### FPGA Implementation

Almost **every FPGA** can drive LVDS panels:
- Use FPGA LVDS outputs directly (no external PHY)
- Generate pixel clock with PLL/MMCM
- Drive R/G/B data + HSync/VSync/DE on LVDS pairs
- **Resource cost:** ~50 LUTs for timing generator + IOBs

| FPGA Family | LVDS Panel | Notes |
|---|---|---|
| All Xilinx 7-series | Yes | HR banks at 2.5V/3.3V |
| All Intel Cyclone/Arria | Yes | 2.5V/3.3V LVDS |
| Lattice ECP5 | Yes | Native LVDS support |
| Gowin LittleBee | Yes | Basic LVDS |

---

## FPGA Family Selection for Video

| Application | Recommended FPGA | Why |
|---|---|---|
| 4K60 HDMI capture | Xilinx Kintex UltraScale+ | Hard HDMI 2.0 + VDMA + high bandwidth |
| MIPI camera (machine vision) | Lattice CrossLink-NX | Hard MIPI D-PHY, low cost, low power |
| Multi-channel camera aggregator | AMD Versal | Multiple MIPI lanes + AI Engine preprocessing |
| LVDS industrial display | Intel MAX 10 / Lattice ECP5 | Simple, cheap, sufficient bandwidth |
| HDMI 2.1 / 8K | AMD Versal + external retimer | Only option for HDMI 2.1 FRL |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| HDMI 2.1 Specification | HDMI Forum | FRL mode, 8K, eARC, DSC |
| VESA DisplayPort 1.4 Standard | VESA | Link training, MST, DSC, HDR |
| MIPI D-PHY Specification v2.1 | MIPI Alliance | DDR clocking, LP/HS modes, 2.5 Gbps |
| MIPI CSI-2 Specification v3.0 | MIPI Alliance | Camera protocol, data types, virtual channels |
| Lattice TN1304 — CrossLink-NX MIPI | Lattice | Hard MIPI D-PHY usage, CSI-2/DSI configuration |
| Xilinx PG230 — HDMI 2.0/2.1 Subsystem | Xilinx | Hard HDMI subsystem for UltraScale+/Versal |
| [Video & Audio IP](../other_hard_ip/video_audio_ip.md) | This KB | Vendor video processing IP blocks |
