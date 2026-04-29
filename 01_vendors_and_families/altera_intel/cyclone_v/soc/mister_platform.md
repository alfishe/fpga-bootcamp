[← SoC Home](README.md) · [← Cyclone V Home](../README.md) · [← Project Home](../../../../README.md)

# MiSTer Platform — DE10-Nano as a Retro Computing Powerhouse

The MiSTer project transformed the Terasic DE10-Nano from a general-purpose FPGA dev board into the world's most popular FPGA retro-computing platform. Understanding MiSTer means understanding both the Cyclone V SoC capabilities it exploits and the framework architecture that makes 100+ hardware-accurate cores possible.

---

## What Is MiSTer?

MiSTer is an open-source project that uses the DE10-Nano's Cyclone V SoC (5CSEBA6U23I7, 110K LEs) to implement hardware-accurate recreations of vintage computers, game consoles, and arcade boards. Unlike software emulation, MiSTer cores implement the actual digital logic at the gate/register level — the FPGA becomes the original hardware.

**Core principle:** The FPGA fabric implements the retro system's logic (CPU, GPU, sound chips, memory controllers), while the HPS ARM cores handle the Linux-based framework: file I/O, menu system, network, and core loading.

---

## Hardware Stack

```
┌──────────────────────────────────────────┐
│  DE10-Nano (Cyclone V SoC 5CSEBA6)       │
│                                          │
│  ┌─────────── HPS ───────────────┐       │
│  │  Linux (Buildroot-based)      │       │
│  │  MiSTer Main Binary           │       │
│  │  Menu, OSD, Networking, I/O   │       │
│  └────────────┬──────────────────┘       │
│               │ H2F/F2H/LWH2F bridges    │
│  ┌────────────▼──────────────────┐       │
│  │  FPGA Core (loaded at runtime)│       │
│  │  Retro system logic           │       │
│  └────────────┬──────────────────┘       │
│               │ GPIO 0/1                 │
│  ┌────────────▼──────────────────┐       │
│  │  SDRAM Add-On (optional)      │       │
│  │  32 MB or 128 MB SDR SDRAM    │       │
│  └───────────────────────────────┘       │
│                                          │
│  ┌────────────┬──────────────────┐       │
│  │  IO Board / USB Hub Board     │       │
│  │  HDMI, audio, USB, buttons    │       │
│  └───────────────────────────────┘       │
└──────────────────────────────────────────┘
```

### Required Components

| Component | Model / Spec | Purpose |
|---|---|---|
| **DE10-Nano** | Terasic P0496 | Main FPGA board with Cyclone V SoC |
| **MicroSD card** | ≥8 GB, Class 10 | Boot, Linux rootfs, cores, ROMs |
| **Power supply** | 5V DC, 2A minimum, 5.5×2.1mm barrel | Powers DE10-Nano + expansion boards |
| **Heat sink + fan** | 40mm fan, passive heat sink on FPGA | 110K LE core at 100+ MHz = 5–8W; throttles without cooling |

### Recommended Expansion

| Board | Connects via | Provides |
|---|---|---|
| **SDRAM Add-On** | GPIO 0/1 (40-pin) | 32 MB or 128 MB SDR SDRAM, 16-bit, needed by 90% of cores |
| **IO Board (Analog)** | GPIO 0/1 | VGA output, audio DAC (3.5mm jack + TOSLINK), user buttons, LEDs, SNAC port |
| **IO Board (Digital)** | GPIO 0/1 | Dual HDMI, audio DAC, user buttons, SNAC port (no VGA) |
| **USB Hub Board** | USB bridge connector | 7-port USB 2.0 hub, powers peripherals, bridges to IO board |

---

## SDRAM Add-On — The Unspoken Requirement

### Why SDRAM?

The Cyclone V SoC has only 6.8 Mb of on-chip M10K BRAM in the 5CSEBA6. That's plenty for small cores but nowhere near enough for:
- Neo Geo: 64 MB cartridge ROM + 64 KB VRAM
- SNES: 4–6 MB ROM + 256 KB WRAM + 64 KB VRAM
- Amiga AGA: 2 MB Chip RAM + 8 MB Fast RAM + 1.5 MB Kickstart
- PSX Core: 2 MB main RAM + 1 MB VRAM + 512 KB BIOS

The SDRAM add-on provides a large, low-latency memory pool the FPGA core can access at full speed.

### SDRAM Board Specifications

| Parameter | 32 MB Board | 128 MB Board |
|---|---|---|
| **Chip** | AS4C16M16SA (or similar) | AS4C32M16SA (or similar) |
| **Capacity** | 32 MB (256 Mbit) | 128 MB (1 Gbit) |
| **Data bus** | 16 bits | 16 bits |
| **Clock** | 48–167 MHz (from FPGA PLL) | 48–167 MHz |
| **Peak bandwidth** | ~333 MB/s at 167 MHz | ~333 MB/s at 167 MHz |
| **Latency** | ~20 ns (3 cycles at 150 MHz) | Same |
| **Interface** | Custom FPGA memory controller per core | Same |

> **128 MB is now standard** — most cores targeting 32 MB have been patched. If buying new, get 128 MB (v3.0+).

### SDRAM Pinout (GPIO 0/1)

The SDRAM board uses both 40-pin GPIO headers. GPIO 0 provides data pins, GPIO 1 provides address and control. This is why the MiSTer IO board "passes through" GPIO signals — the SDRAM and IO board share the same physical connector.

---

## Core Architecture

Every MiSTer core follows the same HPS-FPGA split:

### FPGA Side (the "Core")

The FPGA fabric is fully reprogrammed when a core loads. A typical core contains:
- The retro system's CPU(s) (e.g., 68000, Z80, 6502, 65816)
- GPU / video pipeline (scan-doubled to HDMI timing)
- Sound chip(s) (YM2612, SID, Paula, SPC700 + DSP)
- Memory controller for SDRAM and on-chip BRAM
- Input handling (USB HID via HPS bridge or native gamepad via SNAC)

### HPS Side (the "Framework")

The HPS runs a minimal Buildroot-based Linux with the MiSTer "Main" binary. It's always running, even when a core is loaded:

| Component | Role |
|---|---|
| **MiSTer Main** | Core selection (menu), core loading, OSD overlay, input mapping, file I/O |
| **Linux kernel** | USB HID stack, network (FTP/SMB for ROMs), SD card filesystem, framebuffer for menu |
| **HPS-FPGA bridges** | Core upload via H2F, status readback via LWH2F, input events via F2H interrupts |
| **FPGA Manager** | Reconfigures FPGA fabric when a new core is loaded (`.rbf` written via configfs) |

### Core Loading Sequence

```
1. User selects core from OSD menu
2. MiSTer Main reads core .rbf from /media/fat/_Computer/ or /media/fat/_Console/
3. FPGA Manager stops current core (tri-states FPGA I/Os)
4. New .rbf written to FPGA via configfs → FPP ×16 (~100 ms for 15–20 Mb core)
5. FPGA bridges re-enabled
6. Core runs its initialization (PLL lock, SDRAM calibration, video sync)
7. MiSTer Main detects core type, shows appropriate menu options
```

---

## Video Pipeline

```
┌──────────┐    ┌───────────┐    ┌──────────────┐
│ Retro    │    │ Scanline  │    │ Scan Doubler │
│ Core     │───→│ Buffer    │───→│ (line ×N)    │
│ (native  │    │ (BRAM)    │    │              │
│  timing) │    └───────────┘    └──────┬───────┘
└──────────┘                            │
                              ┌────────▼───────┐
                              │  Scaler (AScal) │
                              │  Crop, rotation,│
                              │  filters,       │
                              │  shadow masks   │
                              └────────┬───────┘
                                       │
                              ┌────────▼───────┐
                              │  HDMI TX        │
                              │  ADV7513        │
                              │  1080p/1440p    │
                              └────────────────┘
```

The ADV7513 HDMI transmitter is driven by the FPGA fabric at up to 148.5 MHz pixel clock (1080p60). Analog video (VGA, component, composite) is generated by the IO Board's DAC from the same FPGA video signals.

### Scaler (AScal)

The MiSTer scaler is a pure-FPGA video processor supporting:
- Integer and non-integer scaling
- Custom aspect ratios and cropping
- Video filters (scanlines, LCD grid, CRT shadow masks, phosphor decay)
- Rotation (for arcade cores with vertical monitors)
- Adaptive sync (VSync_adjust=2 — matches output to core's exact refresh rate, even 57.3 Hz)

---

## Input Handling — USB vs SNAC

### USB (Default)

All USB controllers (keyboards, gamepads, arcade sticks) connect to the HPS USB OTG port via a USB hub. The HPS Linux HID stack processes events and forwards them to the FPGA core via the H2F bridge.

**Latency:** ~1–2 ms (USB polling at 1 kHz + HPS-to-FPGA bridge). Good enough for everything except competitive speedrunning on original hardware timings.

### SNAC (Serial Native Accessory Converter)

SNAC bypasses USB entirely. A level-shifter adapter connects original console controllers directly to FPGA GPIO pins. The core communicates natively (e.g., NES shift register protocol, SNES parallel latch).

**Latency:** ~0.01 ms (a few FPGA clock cycles). Required for light guns (NES Zapper, GunCon), which depend on beam-position timing.

---

## MiSTer Stack (MicroSD Layout)

```
/media/fat/
├── MiSTer                    # Main binary (HPS ARM executable)
├── MiSTer.ini                # Global config (video mode, vsync, volume, etc.)
├── menu.rbf                  # Menu core (FPGA bitstream)
├── linux/                    # Kernel + initramfs
├── _Computer/                # Computer cores (.rbf)
│   ├── Minimig.rbf           # Amiga AGA/ECS/OCS
│   ├── ao486.rbf             # 486 PC
│   ├── X68000.rbf            # Sharp X68000
│   └── ...
├── _Console/                 # Console cores (.rbf)
│   ├── NES.rbf
│   ├── SNES.rbf
│   ├── MegaDrive.rbf
│   └── ...
├── _Arcade/                  # Arcade cores (.rbf + .mra)
│   ├── cores/                # .rbf files
│   ├── _alternatives/        # Alt .mra files
│   └── ...
├── games/                    # ROM storage
│   ├── NES/
│   ├── SNES/
│   ├── MegaDrive/
│   └── ...
├── saves/                    # Save states, battery RAM
├── savestates/               # Save states (core-dependent)
└── config/                   # Per-core config overrides
```

---

## Key Cores & FPGA Utilization

| Core | FPGA LE Usage | SDRAM Required | Notes |
|---|---|---|---|
| **Menu** | ~5K | No | Always available |
| **NES** | ~12K | No | Fits in BRAM (small ROMs) |
| **SNES** | ~25K | Yes (24+ MB) | DSP-1/2/3/4 chips emulated |
| **Genesis/MegaDrive** | ~30K | Yes (32+ MB) | Virtua Racing needs SVP chip |
| **Neo Geo** | ~45K | Yes (128 MB) | Largest console core |
| **TurboGrafx-16/PCE** | ~15K | Yes (CD-ROM BIOS) | CD-ROM support via SD |
| **Minimig (Amiga AGA)** | ~35K | Yes (32+ MB) | AGA + RTG + HDD support |
| **ao486 (PC 486)** | ~60K | Yes (128 MB) | 486SX ~90 MHz equivalent; VESA VGA, Sound Blaster |
| **PlayStation** | ~90K | Yes (128 MB) | Near-full speed, dual SDRAM recommended |
| **Sega Saturn** | ~95K | Yes (128 MB dual) | In development, very tight on 110K LEs |
| **Arcade (CPS1/CPS2)** | ~20–40K | Yes (32+ MB) | Jotego's JTCPS cores |

> The 110K LE limit of the 5CSEBA6 is the MiSTer's ultimate ceiling. PlayStation already uses ~80% of the FPGA. Saturn pushes it to the absolute limit.

---

## MiSTer vs. Software Emulation

| Aspect | MiSTer (FPGA) | Software Emulation (RetroArch, etc.) |
|---|---|---|
| **Latency** | ~1 frame (HDMI at native refresh) | 2–8 frames (OS + GPU pipeline + USB stack) |
| **Timing accuracy** | Cycle-exact (hardware-level) | Approximate (timer callbacks, dynamic recompilation) |
| **Glitches** | Faithful to original (including bugs) | Variable — hacks to work around timing issues |
| **Input lag** | < 1 ms (SNAC), 1–2 ms (USB) | 8–16 ms typical, 1 frame+ |
| **Cost** | ~$225–400 (full setup) | $0 (any PC) – $200 (Raspberry Pi) |
| **Portability** | Fixed hardware (DE10-Nano) | Any device |
| **Core development** | VHDL/Verilog — steep learning curve | C/C++ — wider developer pool |

---

## Community & Resources

| Resource | URL |
|---|---|
| **MiSTer FPGA Wiki** | https://github.com/MiSTer-devel/Wiki_MiSTer |
| **MiSTer-devel GitHub** | https://github.com/MiSTer-devel |
| **MiSTer FPGA Forum** | https://misterfpga.org/ |
| **MiSTer Addons (SDRAM, IO boards)** | https://misteraddons.com/ |
| **Jotego (JTCORES, arcade)** | https://github.com/jotego |
| **MiSTer Discord** | Invite link on misterfpga.org |

---

## References

| Source | Path |
|---|---|
| DE10-Nano User Manual | Terasic |
| MiSTer Wiki — Main | https://github.com/MiSTer-devel/Wiki_MiSTer |
| MiSTer Framework Source | https://github.com/MiSTer-devel/Main_MiSTer |
| MiSTer SDRAM Controller Spec | https://github.com/MiSTer-devel/Main_MiSTer/wiki/SDRAM-Board |
| ADV7513 Datasheet | Analog Devices |
| Cyclone V Device Handbook | Intel FPGA Documentation |
| LTC2308 ADC Datasheet | Linear Technology (Analog Devices) |
