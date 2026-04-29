[← 06 Ip And Cores Home](../README.md) · [← Other Hard Ip Home](README.md) · [← Project Home](../../../README.md)

# Video & Audio IP Blocks

FPGA video and audio IP spans frame buffers, scalers, mixers, HDMI/DVI/DisplayPort PHY interfaces, and audio formatters. This article surveys the vendor IP landscape for A/V pipelines.

---

## Xilinx Video IP Suite

Xilinx has the most mature video IP ecosystem. All IP uses AXI4-Stream for pixel data and AXI4-Lite for register control.

| IP Block | Function | Resource (typical) | Notes |
|---|---|---|---|
| **Video In to AXI4-Stream** | Captures parallel video (HSYNC/VSYNC/DE) → AXI4-Stream | ~500 LUTs | Bridge from camera sensor / HDMI receiver |
| **AXI4-Stream to Video Out** | AXI4-Stream → parallel video output | ~500 LUTs | Bridge to HDMI transmitter / display |
| **Video Timing Controller** | Generates HSYNC/VSYNC/DE timing | ~300 LUTs | Supports CEA-861 and VESA standards |
| **Video Scaler** | Up/down scale (bilinear, bicubic) | 8–16 DSP48 + 5 BRAM | 1–4 pixels/clock throughput |
| **Video Mixer** | Alpha-blend up to 8 layers | 20–40 DSP48 + 15 BRAM | Each layer: position, alpha, color-key |
| **Test Pattern Generator (TPG)** | Color bars, zone plate, ramp | ~400 LUTs | Invaluable for bring-up — test without camera |
| **Frame Buffer Write / Read** | Video ↔ DDR memory | 2–4 HP ports + VDMA | Uses AXI4 VDMA for memory access |

### HDMI Subsystem

| IP Block | Function | Notes |
|---|---|---|
| **HDMI TX Subsystem** | HDMI 1.4/2.0 transmit | Up to 4K60 4:2:0. Includes TMDS encoding, audio embedding, HDCP (optional). |
| **HDMI RX Subsystem** | HDMI 1.4/2.0 receive | Up to 4K60. Includes TMDS decode, audio extraction, EDID management. |
| **DisplayPort TX Subsystem** | DP 1.2/1.4 transmit | Up to 4K60. 1/2/4 lane. MST (daisy-chain) support. |

---

## Intel Video IP

Intel's video IP is less extensive — typically you'd use soft-IP or FPGA-to-HPS bridge with Linux DRM subsystem.

| IP Block | Function | Notes |
|---|---|---|
| **Video and Image Processing Suite** | Scaler, deinterlacer, color-space converter, alpha blender | Avalon-ST interfaces. Good for industrial machine vision. |
| **HDMI Intel FPGA IP** | HDMI 1.4/2.0 TX/RX | Up to 4K60. Requires transceiver for TMDS data rates. |
| **DisplayPort Intel FPGA IP** | DP 1.4 TX/RX | Arria 10 / Stratix 10. 1–4 lanes. |

---

## Lattice / Microchip / Gowin

| Vendor | Video IP | Notes |
|---|---|---|
| **Lattice** | MIPI D-PHY (hard on CrossLink-NX), DSI/CSI-2 IP | Primarily MIPI-oriented. No general-purpose HDMI IP. |
| **Microchip** | No dedicated video IP | Third-party or hand-coded. PolarFire has enough DSP for soft scaler/mixer. |
| **Gowin** | Limited DVI/LVDS output IP | Gowin EDA IP generator has basic TMDS output for DVI. |

---

## Audio IP

| Vendor | IP Block | Function |
|---|---|---|
| **Xilinx** | Audio Formatter | I2S ↔ AXI4-Stream bridge. Multi-channel (2–32). Configurable sample width. |
| **Xilinx** | SPDIF TX/RX | S/PDIF digital audio interface |
| **Intel** | Audio core (part of HPS for SoC) | I2S via HPS peripheral. No dedicated FPGA audio IP. |
| **Lattice/Gowin** | No audio IP | Hand-coded I2S toggles ~100 LUTs. Trivial to implement manually. |

---

## Typical Video Pipeline (Xilinx)

```
Camera (MIPI/Parallel)
    │
    ▼
MIPI CSI-2 RX or Video In to AXI4-Stream
    │
    ▼
Video Scaler (optional: downscale for processing)
    │
    ▼
Your processing pipeline (AXI4-Stream)
    │
    ▼
Frame Buffer Write → DDR (VDMA)
    │
    ▼
Frame Buffer Read ← DDR (VDMA)
    │
    ▼
Video Mixer (overlay OSD, alpha blend)
    │
    ▼
AXI4-Stream to Video Out → HDMI TX
    │
    ▼
Monitor
```

---

## Best Practices

1. **Use Xilinx TPG for bring-up** — generate known-good video without cameras or HDMI receivers
2. **Frame buffer is your bottleneck** — DDR bandwidth is precious. Use 4:2:0 chroma subsampling when color fidelity isn't critical
3. **Pipeline your AXI4-Stream passes** — video IP all uses streaming; chain them with zero buffering for best latency
4. **VTC (Video Timing Controller) is your clock reference** — all video IP axes off VTC's generated timing signals

---

## References

- Xilinx PG278: Video Timing Controller
- Xilinx PG235: HDMI TX Subsystem
- Xilinx PG236: HDMI RX Subsystem
- Intel Video and Image Processing Suite User Guide
