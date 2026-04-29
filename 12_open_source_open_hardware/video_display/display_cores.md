[← 12 Open Source Open Hardware Home](../README.md) · [← Video Display Home](README.md) · [← Project Home](../../../README.md)

# Open Display Cores

FPGA display controller cores — VGA, DVI, HDMI TX implementations, from simple VGA framebuffers to full HDMI with audio.

---

## Core Comparison

| Core | Output | Resolution | Color Depth | Audio | FPGA Verified | Repository |
|---|---|---|---|---|---|---|
| **Project F Display** | VGA | Up to 1920×1080 | 12–24 bit | No | iCE40, ECP5, Artix-7 | projf/projf-explore |
| **hdl-util/hdmi** | HDMI/DVI | Up to 1920×1080 | 24 bit | ✅ I²S audio embedding | ECP5, Artix-7, Cyclone V | hdl-util/hdmi |
| **Simple VGA** | VGA | 640×480 | 12 bit | No | iCE40, ECP5 | Various |
| **LiteVideo** | HDMI | 720p/1080p | 24 bit | Via LiteX | ECP5, Artix-7 | enjoy-digital/litevideo |

## Display Interface Comparison

| Interface | Pins | FPGA IO | Max Resolution (FPGA practical) | Notes |
|---|---|---|---|---|
| **VGA** (analog) | 5–12 (R,G,B,HS,VS) | GPIO with resistor DAC | 1920×1080 @ 60 Hz | Simplest, needs VGA monitor |
| **DVI** (digital) | 4 diff pairs (TMDS) | LVDS or true TMDS IO | 1920×1080 @ 60 Hz | Digital, no audio standard |
| **HDMI** (digital) | 4 diff pairs (TMDS) | LVDS or true TMDS IO | 1920×1080 @ 60 Hz | DVI + audio + EDID, ubiquitous |
| **DisplayPort** | 1–4 lanes | High-speed transceiver | 4K+ | Complex, needs SERDES, rare in open FPGA |

## TMDS on FPGA: The Key Challenge

HDMI/DVI uses **TMDS** (Transition Minimized Differential Signaling) — a DC-balanced serial protocol at 5× pixel clock. For 1080p@60, that's 148.5 MHz pixel clock × 5 = 742.5 Mbps per lane.

- **ECP5**: Has hard TMDS-capable IO (LVDS25E), can directly drive HDMI up to 1080p
- **Artix-7**: Needs OSERDES2 + appropriate IO standard — supported, well-documented
- **iCE40**: No TMDS IO, max ~480p via bit-banged LVDS

---

## Original Stub Description

**Project F** display controller (VGA/DVI/HDMI, Verilog), **hdl-util/hdmi** (audio/video over HDMI), open HDMI/DVI TX core survey, DVI/HDMI/DVI-D differences

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
