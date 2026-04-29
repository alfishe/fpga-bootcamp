[← 12 Open Source Open Hardware Home](../README.md) · [← Video Display Home](README.md) · [← Project Home](../../../README.md)

# RetroTINK & Open Scaler Projects

A survey of video scalers and converters — from the commercial RetroTINK line (which influences open FPGA designs) to open-source alternatives like GBS-Control and RGBtoHDMI.

---

## RetroTINK Line

| Product | Hardware | Key Features | FPGA Involvement |
|---|---|---|---|
| **RetroTINK 2X-Pro** | MCU + Video ADC | 480p output, smoothing filter, comb filter | No FPGA (dedicated ASIC) |
| **RetroTINK 5X-Pro** | Xilinx FPGA | 1080p/1440p output, motion-adaptive deinterlacing, CRT simulation, crop/zoom | Yes — FPGA-based scaling engine |
| **RetroTINK 4K** | Xilinx FPGA (larger) | 4K output, HDR, BFI, CRT beam simulation, advanced polyphase scaling | Yes — biggest FPGA scaler |

## Open-Source Alternatives

| Project | Hardware | Inputs | Output | FPGA/CPLD | Key Trait |
|---|---|---|---|---|---|
| **GBS-Control** | GBS-8200 board (TV5725 scaler) + ESP8266 | VGA, Component, RGBS | VGA (640×480 – 1920×1080) | No FPGA (TV5725 is an ASIC scaler, ESP8266 replaces MCU) | Open firmware on $20 hardware |
| **RGBtoHDMI** | Pi Zero + CPLD | RGB (analog, TTL) via GPIO | HDMI (via Pi GPU) | Lattice CPLD (XC9572XL or ATF1508) — signal capture only | Retro computer HDMI output, auto-calibrating ADC |

## How RGBtoHDMI Works

```
Retro Computer (RGB + CSYNC, 15–50 kHz)
    │
    ▼
CPLD — samples analog levels, derives pixel clock via PLL
    │
    ▼
Pi Zero — frame reconstruction, scaling, HDMI output
```

The CPLD doesn't scale — it's a **high-speed sampler** that captures analog video levels and passes raw samples to the Pi. The Pi Zero's GPU does the actual upscaling to HDMI. This architecture is clever: it pairs a $5 CPLD (fast, deterministic sampling) with a $5 Pi (cheap HDMI output, powerful GPU for scaling).

## FPGA in Scalers: Why?

| Task | Why FPGA/CPLD |
|---|---|
| **Analog sampling** | Deterministic capture at exact pixel clock — no jitter |
| **Line multiplication** | Line-by-line processing eliminates frame buffer latency |
| **Deinterlacing** | Motion-adaptive algorithms need parallel pixel processing |
| **CRT simulation** | Beam simulation, phosphor decay, mask patterns — per-pixel compute |

---

## Original Stub Description

**RetroTINK** line comparison (2X/5X/4K), **GBS-Control** (ESP8266 + TV5725, open firmware), **RGBtoHDMI** (Pi Zero + CPLD) — relationship with FPGA/CPLD technology

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
