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

> **2024 Hardware Alternatives:** To address the rising cost of the official DE10-Nano, 2024 saw the successful release of "clone" boards such as the **MiSTer Pi** (spearheaded by Taki Udon). These boards offer exact 1:1 hardware compatibility with the DE10-Nano's Cyclone V SoC, allowing identical performance at a significantly lower price point (often under $100 for the main board).

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

| Category | Core | ALMs Used | Logic Utilization | Registers used | Register Utillization | Block Memory Bits | Block Memory Bits Utilization | RAM Blocks | RAM Block Utilization | DSP Blocks | DSP Block Utilization |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Computer | ao486 | 34052 | 81.25% | 30,478 | 18.36% | 3,428,235 | 60.54% |  | 0.00% | 33 | 29.46% |
| Console | SNES | 31551 | 75.28% | 26,983 | 16.25% | 3,987,891 | 70.42% |  | 0.00% | 65 | 58.04% |
| Console | TurboGrafx 16 / PC Engine | 23336 | 55.68% | 32,785 | 19.75% | 2,226,915 | 39.33% |  | 0.00% | 30 | 26.79% |
| Console | Turbo-Grafx (CD) + PC Engine (CD) | 19814 | 47.28% |  |  | 3,054,531 | 53.94% |  | 0.00% | 33 | 29.46% |
| Console | MegaCD | 19535 | 46.61% |  |  | 4,169,651 | 73.63% | 539 | 97.47% | 43 | 38.39% |
| Console | Genesis/Megadrive | 19194 | 45.80% | 25,174 | 15.16% | 2,649,427 | 46.79% |  | 0.00% | 41 | 36.61% |
| Console | NES | 18981 | 45.29% | 23,020 | 13.86% | 526,091 | 9.29% |  | 0.00% | 39 | 34.82% |
| Console | GBA | 18600 | 44.38% |  |  | 2,272,587 | 40.13% | 317 | 57.32% | 61 | 54.46% |
| Computer | Altair 8800 | 18499 | 44.14% | 29,268 | 17.63% | 3,544,636 | 62.60% |  | 0.00% | 34 | 30.36% |
| Computer | ZX Spectrum | 18333 | 43.74% | 19,595 | 11.80% | 1,408,593 | 24.87% |  | 0.00% | 35 | 31.25% |
| Computer | Commodore 64, Ultimax | 17441 | 41.62% | 20,464 | 12.33% | 2,233,103 | 39.44% |  | 0.00% | 52 | 46.43% |
| Console | NeoGeo | 15692 | 37.44% | 19,765 | 11.90% | 2,900,053 | 51.21% |  | 0.00% | 34 | 30.36% |
| Computer | TSConf | 15618 | 37.27% | 15,807 | 9.52% | 1,607,537 | 28.39% |  | 0.00% | 35 | 31.25% |
| Arcade | MoonPatrol | 15594 | 37.21% | 16,804 | 10.12% | 778,964 | 13.76% | 105 | 18.99% | 28 | 25.00% |
| Computer | MultiComp | 15159 | 36.17% | 22,036 | 13.27% | 2,480,344 | 43.80% |  | 0.00% | 31 | 27.68% |
| Computer | Amiga | 15012 | 35.82% | 18,806 | 11.33% | 613,187 | 10.83% |  | 0.00% | 37 | 33.04% |
| Console | Gameboy, Gameboy Color | 14962 | 35.70% | 17,618 | 10.61% | 2,299,779 | 40.61% |  | 0.00% | 33 | 29.46% |
| Arcade | Xevious | 14776 | 35.26% | 21,913 | 13.20% | 3,480,408 | 61.46% | 434 | 78.48% | 33 | 29.46% |
| Console | Master System, GameGear | 13547 | 32.32% | 18,778 | 11.31% | 1,079,669 | 19.07% |  | 0.00% | 33 | 29.46% |
| Arcade | Defender | 12859 | 30.68% | 20,322 | 12.24% | 1,361,752 | 24.05% |  | 0.00% | 31 | 27.68% |
| Computer | Acorn Archimedes | 12778 | 30.49% | 15,825 | 9.53% | 359,538 | 6.35% |  | 0.00% | 29 | 25.89% |
| Computer | BK0011M | 12731 | 30.38% | 19,817 | 11.94% | 1,704,355 | 30.10% |  | 0.00% | 29 | 25.89% |
| Arcade | MoonCresta | 12181 | 29.06% | 19,841 | 11.95% | 1,971,224 | 34.81% | 244 | 44.12% | 31 | 27.68% |
| Arcade | Centipede | 12047 | 28.74% | 18,749 | 11.29% | 2,710,516 | 47.87% | 348 | 62.93% | 28 | 25.00% |
| Computer | BBC Micro B,Master | 11959 | 28.53% | 13,042 | 7.85% | 3,979,747 | 70.28% |  | 0.00% | 29 | 25.89% |
| Computer | Atari 800XL | 11911 | 28.42% | 15,123 | 9.11% | 3,768,227 | 66.54% |  | 0.00% | 32 | 28.57% |
| Computer | Commodore 16, Plus/4 | 11897 | 28.39% | 14,546 | 8.76% | 2,299,635 | 40.61% |  | 0.00% | 40 | 35.71% |
| Arcade | 1943 | 11654 | 27.81% | 16,502 | 9.94% | 2,128,644 | 37.59% | 286 | 51.72% | 33 | 29.46% |
| Computer | MSX | 11506 | 27.45% | 13,377 | 8.06% | 394,205 | 6.96% |  | 0.00% | 36 | 32.14% |
| Computer | SAM Coupe | 11421 | 27.25% | 13,497 | 8.13% | 934,797 | 16.51% |  | 0.00% | 34 | 30.36% |
| Computer | Amstrad CPC 6128 | 11400 | 27.20% | 13,307 | 8.01% | 634,083 | 11.20% |  | 0.00% | 30 | 26.79% |
| Arcade | Galaga | 11123 | 26.54% | 12,420 | 7.48% | 2,806,580 | 49.56% | 360 | 65.10% | 30 | 26.79% |
| Computer | Vector 06C | 11061 | 26.39% | 12,530 | 7.55% | 3,834,627 | 67.72% |  | 0.00% | 29 | 25.89% |
| Computer | TI-99/4A | 11046 | 26.36% | 11,608 | 6.99% | 2,889,363 | 51.02% |  | 0.00% | 29 | 25.89% |
| Arcade | BurgerTime | 11039 | 26.34% | 11,039 | 6.65% | 2,790,756 | 49.28% | 351 | 63.47% | 32 | 28.57% |
| Console | Atari 5200 | 10930 | 26.08% | 14,314 | 8.62% | 1,160,003 | 20.48% |  | 0.00% | 32 | 28.57% |
| Computer | Commodore VIC-20 | 10784 | 25.73% | 12,785 | 7.70% | 1,435,691 | 25.35% |  | 0.00% | 30 | 26.79% |
| Console | Vectrex | 10641 | 25.39% | 10,845 | 6.53% | 3,814,767 | 67.37% |  | 0.00% | 36 | 32.14% |
| Computer | DEC PDP-1 | 10560 | 25.20% | 11,123 | 6.70% | 3,068,290 | 54.18% |  | 0.00% | 32 | 28.57% |
| Arcade | GnG | 10515 | 25.09% | 13,929 | 8.39% | 3,119,782 | 55.09% | 403 | 72.88% | 34 | 30.36% |
| Arcade | DigDug | 10418 | 24.86% | 11,717 | 7.06% | 2,474,036 | 43.69% | 323 | 58.41% | 29 | 25.89% |
| Arcade | BombJack | 10133 | 24.18% | 11,752 | 7.08% | 2,897,596 | 51.17% | 366 | 66.18% | 28 | 25.00% |
| Computer | Sinclair QL | 9954 | 23.75% | 11,745 | 7.07% | 2,893,283 | 51.09% |  | 0.00% | 29 | 25.89% |
| Arcade | TheEnd | 9936 | 23.71% | 11,677 | 7.03% | 1,674,832 | 29.58% | 219 | 39.60% | 30 | 26.79% |
| Arcade | 1942 | 9923 | 23.68% | 12,070 | 7.27% | 3,919,540 | 69.22% | 499 | 90.24% | 28 | 25.00% |
| Arcade | TimePilot | 9909 | 23.64% | 11,467 | 6.91% | 2,330,932 | 41.16% | 304 | 54.97% | 29 | 25.89% |
| Arcade | Amidar | 9855 | 23.51% | 11,581 | 6.97% | 2,004,752 | 35.40% | 256 | 46.29% | 30 | 26.79% |
| Arcade | Scramble | 9826 | 23.45% | 11,550 | 6.96% | 2,021,344 | 35.70% | 258 | 46.65% | 30 | 26.79% |
| Arcade | Pooyan | 9807 | 23.40% | 11,455 | 6.90% | 1,785,652 | 31.53% | 233 | 42.13% | 29 | 25.89% |
| Computer | Apple II+ | 9719 | 23.19% | 11,873 | 7.15% | 2,789,795 | 49.27% |  | 0.00% | 32 | 28.57% |
| Arcade | Frogger | 9618 | 22.95% | 11,330 | 6.82% | 2,021,344 | 35.70% | 258 | 46.65% | 30 | 26.79% |
| Computer | Apple Macintosh Plus | 9468 | 22.59% | 11,525 | 6.94% | 600,451 | 10.60% |  | 0.00% | 29 | 25.89% |
| Arcade | TraverseUSA | 9437 | 22.52% | 11,396 | 6.86% | 3,086,772 | 54.51% | 389 | 70.34% | 28 | 25.00% |
| Console | Astrocade | 9177 | 21.90% | 11,676 | 7.03% | 745,259 | 13.16% |  | 0.00% | 29 | 25.89% |
| Arcade | Stargate | 9013 | 21.51% | 11,038 | 6.65% | 1,467,508 | 25.92% | 190 | 34.36% | 28 | 25.00% |
| Computer | Specialist/MX | 8990 | 21.45% | 10,924 | 6.58% | 3,857,523 | 68.12% |  | 0.00% | 29 | 25.89% |
| Arcade | Victory | 8874 | 21.17% | 10,606 | 6.39% | 2,775,172 | 49.01% | 354 | 64.01% | 29 | 25.89% |
| Arcade | Uniwars | 8858 | 21.14% | 10,673 | 6.43% | 2,799,748 | 49.44% | 357 | 64.56% | 29 | 25.89% |
| Computer | ZX81 | 8854 | 21.13% | 10,575 | 6.37% | 1,268,067 | 22.39% |  | 0.00% | 29 | 25.89% |
| Arcade | Jin | 8841 | 21.10% | 10,604 | 6.39% | 2,166,116 | 38.25% | 276 | 49.91% | 28 | 25.00% |
| Arcade | Bagman | 8745 | 20.87% | 11,232 | 6.76% | 3,333,428 | 58.87% | 421 | 76.13% | 31 | 27.68% |
| Arcade | Galaxian | 8737 | 20.85% | 10,947 | 6.59% | 2,793,600 | 49.33% | 356 | 64.38% | 28 | 25.00% |
| Arcade | WarOfTheBugs | 8720 | 20.81% | 10,905 | 6.57% | 1,731,162 | 30.57% | 223 | 40.33% | 28 | 25.00% |
| Arcade | Pacman | 8688 | 20.73% | 10,712 | 6.45% | 1,761,979 | 31.12% | 234 | 42.31% | 30 | 26.79% |
| Arcade | AzurianAttack | 8684 | 20.72% | 10,701 | 6.44% | 2,793,600 | 49.33% | 356 | 64.38% | 28 | 25.00% |
| Arcade | Pickin | 8679 | 20.71% | 11,032 | 6.64% | 2,645,812 | 46.72% | 338 | 61.12% | 28 | 25.00% |
| Arcade | Pisces | 8679 | 20.71% | 10,811 | 6.51% | 1,735,788 | 30.65% | 224 | 40.51% | 28 | 25.00% |
| Arcade | Botanic | 8671 | 20.69% | 10,945 | 6.59% | 2,645,812 | 46.72% | 338 | 61.12% | 28 | 25.00% |
| Arcade | Catacomb | 8648 | 20.63% | 10,770 | 6.49% | 2,793,600 | 49.33% | 356 | 64.38% | 28 | 25.00% |
| Console | Atari 2600 | 8644 | 20.63% | 10,938 | 6.59% | 655,563 | 11.58% |  | 0.00% | 29 | 25.89% |
| Arcade | BlackHole | 8637 | 20.61% | 10,723 | 6.46% | 2,793,600 | 49.33% | 356 | 64.38% | 28 | 25.00% |
| Arcade | DonkeyKong | 8627 | 20.58% | 10,866 | 6.54% | 2,389,364 | 42.19% | 306 | 55.33% | 28 | 25.00% |
| Arcade | MrDoNightmare | 8612 | 20.55% | 10,689 | 6.44% | 1,649,242 | 29.12% | 213 | 38.52% | 28 | 25.00% |
| Arcade | Orbitron | 8597 | 20.51% | 10,654 | 6.42% | 1,731,162 | 30.57% | 223 | 40.33% | 28 | 25.00% |
| Arcade | ZigZag | 8537 | 20.37% | 10,907 | 6.57% | 1,632,052 | 28.82% | 213 | 38.52% | 28 | 25.00% |
| Arcade | CrazyKong | 8509 | 20.30% | 10,813 | 6.51% | 2,385,204 | 42.12% | 302 | 54.61% | 28 | 25.00% |
| Computer | Aquarius | 8502 | 20.29% | 10,773 | 6.49% | 1,550,819 | 27.39% |  | 0.00% | 29 | 25.89% |
| Arcade | BurningRubber | 8495 | 20.27% | 11,054 | 6.66% | 2,782,564 | 49.14% | 350 | 63.29% | 32 | 28.57% |
| Computer | Jupiter Ace | 8408 | 20.06% | 10,078 | 6.07% | 844,067 | 14.91% |  | 0.00% | 29 | 25.89% |
| Arcade | Pleiads | 8396 | 20.03% | 10,794 | 6.50% | 1,801,092 | 31.81% | 228 | 41.23% | 30 | 26.79% |
| Arcade | Arkanoid | 8392 | 20.02% | 10,736 | 6.47% | 3,148,372 | 55.60% | 398 | 71.97% | 28 | 25.00% |
| Arcade | Squash | 8388 | 20.01% | 10,725 | 6.46% | 810,804 | 14.32% | 114 | 20.61% | 28 | 25.00% |
| Arcade | Phoenix | 8374 | 19.98% | 10,855 | 6.54% | 1,801,092 | 31.81% | 228 | 41.23% | 30 | 26.79% |
| Computer | Apogee | 8346 | 19.91% | 11,203 | 6.75% | 1,006,979 | 17.78% |  | 0.00% | 30 | 26.79% |
| Arcade | Dorodon | 8342 | 19.90% | 10,837 | 6.53% | 1,302,324 | 23.00% | 169 | 30.56% | 28 | 25.00% |
| Arcade | LadyBug | 8325 | 19.86% | 10,807 | 6.51% | 1,300,276 | 22.96% | 168 | 30.38% | 28 | 25.00% |
| Arcade | Omega | 8272 | 19.74% | 10,851 | 6.54% | 1,731,162 | 30.57% | 223 | 40.33% | 28 | 25.00% |
| Arcade | DreamShopper | 8248 | 19.68% | 10,538 | 6.35% | 1,636,396 | 28.90% | 212 | 38.34% | 28 | 25.00% |
| Arcade | Eggor | 8245 | 19.67% | 10,161 | 6.12% | 1,630,640 | 28.80% | 215 | 38.88% | 30 | 26.79% |
| Arcade | MsPacman | 8216 | 19.60% | 10,393 | 6.26% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | VanVanCar | 8206 | 19.58% | 10,620 | 6.40% | 1,635,884 | 28.89% | 212 | 38.34% | 28 | 25.00% |
| Arcade | Splat | 8201 | 19.57% | 9,623 | 5.80% | 1,515,976 | 26.77% | 197 | 35.62% | 31 | 27.68% |
| Arcade | Frenzy | 8147 | 19.44% | 10,442 | 6.29% | 646,451 | 11.42% | 88 | 15.91% | 29 | 25.89% |
| Arcade | Pengo | 8146 | 19.44% | 10,364 | 6.24% | 1,822,252 | 32.18% | 238 | 43.04% | 29 | 25.89% |
| Arcade | CrushRoller | 8139 | 19.42% | 10,354 | 6.24% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | CrazyClimber | 8138 | 19.42% | 10,550 | 6.35% | 837,156 | 14.78% | 117 | 21.16% | 28 | 25.00% |
| Utility | Memtest | 8129 | 19.40% | 11,483 | 6.92% | 327,043 | 5.78% |  | 0.00% | 29 | 25.89% |
| Arcade | Eyes | 8121 | 19.38% | 10,140 | 6.11% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | Berzerk | 8119 | 19.37% | 10,461 | 6.30% | 630,068 | 11.13% | 86 | 15.55% | 29 | 25.89% |
| Arcade | SuperGlob | 8119 | 19.37% | 10,318 | 6.21% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | Alibaba | 8112 | 19.36% | 10,355 | 6.24% | 1,763,756 | 31.15% | 231 | 41.77% | 29 | 25.89% |
| Arcade | PacmanClub | 8107 | 19.34% | 10,333 | 6.22% | 1,755,564 | 31.00% | 230 | 41.59% | 29 | 25.89% |
| Arcade | Woodpecker | 8101 | 19.33% | 10,324 | 6.22% | 1,755,564 | 31.00% | 230 | 41.59% | 29 | 25.89% |
| Arcade | LizardWizard | 8098 | 19.32% | 10,341 | 6.23% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | MrTNT | 8095 | 19.32% | 10,375 | 6.25% | 1,781,492 | 31.46% | 232 | 41.95% | 29 | 25.89% |
| Arcade | SilverLand | 8093 | 19.31% | 10,470 | 6.31% | 771,620 | 13.63% | 109 | 19.71% | 28 | 25.00% |
| Arcade | SnapJack | 8093 | 19.31% | 10,537 | 6.35% | 747,316 | 13.20% | 100 | 18.08% | 28 | 25.00% |
| Arcade | PacmanPlus | 8092 | 19.31% | 10,332 | 6.22% | 1,755,564 | 31.00% | 230 | 41.59% | 29 | 25.89% |
| Arcade | RiverPatrol | 8085 | 19.29% | 10,440 | 6.29% | 771,620 | 13.63% | 109 | 19.71% | 28 | 25.00% |
| Arcade | Gorkans | 8080 | 19.28% | 10,328 | 6.22% | 1,755,564 | 31.00% | 230 | 41.59% | 29 | 25.89% |
| Arcade | CosmicAvenger | 8079 | 19.28% | 10,396 | 6.26% | 747,316 | 13.20% | 100 | 18.08% | 28 | 25.00% |
| Arcade | Eeekk | 8078 | 19.27% | 10,390 | 6.26% | 1,624,492 | 28.69% | 214 | 38.70% | 29 | 25.89% |
| Arcade | PacmanicMiner | 8077 | 19.27% | 10,367 | 6.24% | 1,619,636 | 28.60% | 212 | 38.34% | 29 | 25.89% |
| Arcade | Birdiy | 8076 | 19.27% | 10,409 | 6.27% | 1,650,804 | 29.15% | 216 | 39.06% | 29 | 25.89% |
| Arcade | RallyX | 8076 | 19.27% | 11,240 | 6.77% | 709,780 | 12.53% | 101 | 18.26% | 31 | 27.68% |
| Arcade | SuperBreakout | 8045 | 19.20% | 10,429 | 6.28% | 1,651,092 | 29.16% | 214 | 38.70% | 29 | 25.89% |
| Arcade | Sinistar | 7943 | 18.95% | 9,303 | 5.60% | 2,560,456 | 45.22% | 323 | 58.41% | 31 | 27.68% |
| Arcade | Sprint2 | 7925 | 18.91% | 10,360 | 6.24% | 442,772 | 7.82% | 66 | 11.93% | 30 | 26.79% |
| Computer | ht1080z / TRS-80 Model 1 clone | 7906 | 18.86% | 9,715 | 5.85% | 367,832 | 6.50% |  | 0.00% | 29 | 25.89% |
| Arcade | Robotron | 7887 | 18.82% | 9,273 | 5.58% | 1,515,976 | 26.77% | 197 | 35.62% | 31 | 27.68% |
| Computer | Commodore PET | 7867 | 18.77% | 10,375 | 6.25% | 959,971 | 16.95% |  | 0.00% | 29 | 25.89% |
| Arcade | Joust | 7860 | 18.75% | 9,268 | 5.58% | 1,515,976 | 26.77% | 197 | 35.62% | 31 | 27.68% |
| Arcade | Bubbles | 7828 | 18.68% | 9,294 | 5.60% | 1,515,976 | 26.77% | 197 | 35.62% | 28 | 25.00% |
| Arcade | Ponpoko | 7798 | 18.61% | 10,022 | 6.04% | 715,828 | 12.64% | 102 | 18.44% | 29 | 25.89% |
| Arcade | CanyonBomber | 7781 | 18.57% | 10,205 | 6.15% | 404,836 | 7.15% | 61 | 11.03% | 30 | 26.79% |
| Arcade | Sprint1 | 7762 | 18.52% | 10,268 | 6.18% | 442,772 | 7.82% | 66 | 11.93% | 29 | 25.89% |
| Console | Odyssey2 | 7559 | 18.04% | 9,449 | 5.69% | 570,712 | 10.08% |  | 0.00% | 31 | 27.68% |
| Arcade | Dominos | 7539 | 17.99% | 10,017 | 6.03% | 405,652 | 7.16% | 60 | 10.85% | 29 | 25.89% |
| Arcade | Mayday | 7441 | 17.75% | 7,780 | 4.69% | 1,094,984 | 19.34% | 145 | 26.22% | 31 | 27.68% |
| Arcade | Colony7 | 7268 | 17.34% | 7,780 | 4.69% | 2,170,184 | 38.32% | 275 | 49.73% | 31 | 27.68% |
| Arcade | ComputerSpace | 7086 | 16.91% | 9,786 | 5.89% | 320,760 | 5.66% | 45 | 8.14% | 30 | 26.79% |
| Arcade | Asteroids | 7081 | 16.90% | 9,807 | 5.91% | 2,507,988 | 44.29% | 311 | 56.24% | 29 | 25.89% |
| Computer | Apple I | 7002 | 16.71% | 9,271 | 5.58% | 1,422,552 | 25.12% |  | 0.00% | 29 | 25.89% |
| Arcade | LunarLander | 6982 | 16.66% | 9,639 | 5.81% | 2,551,028 | 45.05% | 318 | 57.50% | 28 | 25.00% |
| Arcade | Pong | 6951 | 16.59% | 9,477 | 5.71% | 366,204 | 6.47% | 51 | 9.22% | 28 | 25.00% |
| Arcade | AsteroidsDeluxe | 5879 | 14.03% | 7,965 | 4.80% | 2,540,744 | 44.87% | 315 | 56.96% | 31 | 27.68% |
| Computer | Orao | 5447 | 13.00% | 6,678 | 4.02% | 714,184 | 12.61% |  | 0.00% | 31 | 27.68% |
| Computer | Sharp MZ Series | 4779 | 11.40% | 4,158 | 2.50% | 3,529,344 | 62.33% |  | 0.00% | 6 | 5.36% |
| Computer | X68000 |  | 0.00% |  | 0.00% |  | 0.00% |  | 0.00% |  | 0.00% |
| Console | ColecoVision, SG-1000 |  | 0.00% |  | 0.00% |  | 0.00% |  | 0.00% |  | 0.00% |

> **The Limits of the Cyclone V:** The 110K LE limit of the 5CSEBA6 is the MiSTer's ultimate ceiling. Throughout 2023 and 2024, developers like *FPGAzumSpass* (N64) and *srg320* (Saturn) pushed this to the absolute brink, delivering highly playable, mature cores that were once thought impossible on this hardware. PlayStation, Saturn, and N64 represent the bleeding edge of the DE10-Nano's capabilities.

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
| MiSTer Core Utilization Spreadsheet | https://docs.google.com/spreadsheets/d/1wHetlC0RqFnBcqzGEZI8SWi6tlHFxl_ehpaokDwg7CU/edit#gid=0 |
