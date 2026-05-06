[← 06 Ip And Cores Home](../README.md) · [← Other Hard Ip Home](README.md) · [← Project Home](../../../README.md)

# Video & Audio IP Blocks — Vendor Comparison and Pipeline Integration

FPGA video and audio IP spans frame buffers, scalers, mixers, HDMI/DVI/DisplayPort PHY interfaces, and audio formatters. These IP blocks form the backbone of video processing pipelines in broadcast, medical imaging, automotive displays, and industrial machine vision. This article surveys the vendor IP landscape for A/V pipelines and provides integration patterns for the most common video and audio use cases.

> [!NOTE]
> For high-speed transceivers that carry HDMI/DisplayPort signals, see [Transceiver Basics](../transceivers/transceiver_basics.md). For display core catalog (open-source VGA/DVI/HDMI), see [Display Cores](../../12_open_source_open_hardware/video_display/display_cores.md).

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
| **Color Space Converter** | RGB ↔ YCrCb, full-range ↔ limited-range | ~200 LUTs | Fixed-point matrix multiply |
| **Gamma Correction** | Per-channel gamma LUT | 3 BRAM (10-bit) | Configurable gamma curve |

### HDMI Subsystem

| IP Block | Function | Max Resolution | Notes |
|---|---|---|---|
| **HDMI TX Subsystem** | HDMI 1.4/2.0 transmit | Up to 4K60 4:2:0 | Includes TMDS encoding, audio embedding, HDCP (optional). |
| **HDMI RX Subsystem** | HDMI 1.4/2.0 receive | Up to 4K60 | Includes TMDS decode, audio extraction, EDID management. |
| **DisplayPort TX Subsystem** | DP 1.2/1.4 transmit | Up to 4K60 | 1/2/4 lane. MST (daisy-chain) support. |
| **DisplayPort RX Subsystem** | DP 1.2/1.4 receive | Up to 4K60 | Link training, audio extraction. |

---

## Intel Video IP

Intel's video IP is less extensive — typically you'd use soft-IP or FPGA-to-HPS bridge with Linux DRM subsystem.

| IP Block | Function | Notes |
|---|---|---|
| **Video and Image Processing Suite** | Scaler, deinterlacer, color-space converter, alpha blender | Avalon-ST interfaces. Good for industrial machine vision. |
| **HDMI Intel FPGA IP** | HDMI 1.4/2.0 TX/RX | Up to 4K60. Requires transceiver for TMDS data rates. |
| **DisplayPort Intel FPGA IP** | DP 1.4 TX/RX | Arria 10 / Stratix 10. 1–4 lanes. |
| **CVI (Clocked Video Input)** | Parallel video → Avalon-ST | Intel's equivalent of Video In to AXI4-Stream |
| **CVO (Clocked Video Output)** | Avalon-ST → parallel video | Intel's equivalent of AXI4-Stream to Video Out |

---

## Lattice / Microchip / Gowin

| Vendor | Video IP | Notes |
|---|---|---|
| **Lattice** | MIPI D-PHY (hard on CrossLink-NX), DSI/CSI-2 IP | Primarily MIPI-oriented. No general-purpose HDMI IP. See [Lattice IP](../vendor_ip/lattice_ip.md). |
| **Microchip** | No dedicated video IP | Third-party or hand-coded. PolarFire has enough DSP for soft scaler/mixer. |
| **Gowin** | Limited DVI/LVDS output IP | Gowin EDA IP generator has basic TMDS output for DVI. See [Gowin IP](../vendor_ip/gowin_ip.md). |

---

## Audio IP

| Vendor | IP Block | Function | Interface |
|---|---|---|---|
| **Xilinx** | Audio Formatter | I2S ↔ AXI4-Stream bridge | Multi-channel (2–32), configurable sample width |
| **Xilinx** | SPDIF TX/RX | S/PDIF digital audio interface | Coaxial / optical |
| **Intel** | Audio core (part of HPS for SoC) | I2S via HPS peripheral | No dedicated FPGA audio IP |
| **Lattice/Gowin** | No audio IP | Hand-coded I2S toggles ~100 LUTs | Trivial to implement manually |

### Hand-Coded I2S (When No IP is Available)

For vendors without audio IP (Lattice, Gowin, Microchip), I2S is simple enough to implement in ~100 LUTs:

```verilog
// Minimal I2S transmitter — ~100 LUTs
// Produces left/right audio channels on I2S bus
module i2s_tx #(
    parameter DATA_WIDTH = 24
) (
    input  wire                    mclk,      // Master clock (256× sample rate)
    input  wire                    rst,
    output wire                    bclk,      // Bit clock (64× sample rate)
    output wire                    lrclk,     // Left/right select
    output wire                    sdata,     // Serial data out
    input  wire [DATA_WIDTH-1:0]   left_ch,   // Left channel sample
    input  wire [DATA_WIDTH-1:0]   right_ch,  // Right channel sample
    input  wire                    sample_valid
);
    // BCLK = MCLK / 4, LRCLK = MCLK / 256
    // Implementation: counter-based bit serializer
    // Full implementation left as exercise — see Xilinx PG286 for reference
endmodule
```

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

### DDR Bandwidth Budget for Video

Video is DDR-bandwidth-hungry. Calculate your DDR budget before committing to a pipeline:

| Resolution | Format | Frame Size | @ 30 fps | @ 60 fps |
|---|---|---|---|---|
| 1080p (1920×1080) | RGB 8-bit | 6.2 MB | 186 MB/s | 373 MB/s |
| 1080p | YUV422 8-bit | 4.1 MB | 124 MB/s | 249 MB/s |
| 4K (3840×2160) | RGB 8-bit | 24.9 MB | 746 MB/s | 1.49 GB/s |
| 4K | YUV422 10-bit | 20.7 MB | 620 MB/s | 1.24 GB/s |

**Rule of thumb:** Each frame buffer read+write costs 2× the frame rate bandwidth. A 4K60 pipeline with one frame buffer in and one out requires ~3 GB/s of DDR bandwidth — which is most of a Cyclone V SoC's DDR budget.

**Fix:** Use 4:2:0 chroma subsampling when color fidelity isn't critical — cuts bandwidth by 50%.

---

## Best Practices

1. **Use Xilinx TPG for bring-up** — generate known-good video without cameras or HDMI receivers
2. **Frame buffer is your bottleneck** — DDR bandwidth is precious. Use 4:2:0 chroma subsampling when color fidelity isn't critical
3. **Pipeline your AXI4-Stream passes** — video IP all uses streaming; chain them with zero buffering for best latency
4. **VTC (Video Timing Controller) is your clock reference** — all video IP syncs off VTC's generated timing signals
5. **Start with the Xilinx Video FMC design** — Xilinx provides reference designs (KV260, ZCU104) with complete video pipelines; modify these rather than starting from scratch
6. **Use VDMA, not MIG directly** — AXI VDMA handles frame buffer management, stride, and tiling automatically; direct MIG access requires manual address management

---

## Pitfalls

### 1. VDMA Lockup on Backpressure
If the downstream video sink (e.g., HDMI TX) stops accepting data, VDMA can lock up because the frame buffer write side keeps writing while the read side is stalled.

**Fix:** Always connect VDMA's `mm2s_fsync` and `s2mm_fsync` signals to VTC's vertical sync. This ensures VDMA resets its internal pointers at each frame boundary, preventing lockup.

### 2. Color Space Conversion Gamut Clipping
When converting from YCrCb to RGB, values outside the valid range (super-whites, negative chroma) get clipped, causing visible banding in highlights.

**Fix:** Use the Color Space Converter IP in "full range" mode, or clamp YCrCb to valid range before conversion. In broadcast applications, use "limited range" (16–235 for Y, 16–240 for Cb/Cr) per ITU-R BT.601.

### 3. HDMI TMDS Clock Rate Exceeds Fabric Limit
HDMI 1.4 1080p60 requires a TMDS clock of 148.5 MHz. This is within fabric limits. But HDMI 2.0 4K60 requires 594 MHz TMDS clock — far beyond fabric speed. You must use transceivers (GTH/GTY) for HDMI 2.0, not fabric IOs.

**Fix:** Use the Xilinx HDMI 2.0 Subsystem which uses transceivers in TMDS444 mode. Do not attempt to generate 594 MHz TMDS from fabric IOs.

---

## References

- Xilinx PG278: Video Timing Controller
- Xilinx PG235: HDMI TX Subsystem
- Xilinx PG236: HDMI RX Subsystem
- Xilinx PG286: Audio Formatter
- Xilinx PG020: AXI VDMA
- Intel Video and Image Processing Suite User Guide
- [Transceiver Basics](../transceivers/transceiver_basics.md) — SerDes for HDMI/DP
- [Display Cores](../../12_open_source_open_hardware/video_display/display_cores.md) — Open-source video cores
- [Lattice IP](../vendor_ip/lattice_ip.md) — MIPI bridging IP
