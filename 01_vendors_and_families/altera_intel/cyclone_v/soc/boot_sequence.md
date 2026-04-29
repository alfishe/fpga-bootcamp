[← SoC Home](README.md) · [← Cyclone V Home](../README.md) · [← Project Home](../../../../README.md)

# Cyclone V SoC — Boot Sequence Deep Dive

From cold power-on to a running Linux kernel with active FPGA bridges. The Cyclone V boot flow is multi-stage, strictly ordered, and full of vendor-specific gotchas. Understanding it is essential for debugging "why doesn't my FPGA bitstream load" and "why did the kernel hang."

---

## Overview: Who Boots First?

```
POWER-ON
   │
   ▼
HPS Boot ROM (64 KB mask ROM, immutable)          ← FPGA is NOT configured yet
   │
   ▼
Preloader (U-Boot SPL from SD/QSPI/NAND)          ← Configures SDRAM, clocks, pinmux
   │                                               ← Optionally configures FPGA
   ▼
U-Boot (SSBL from SD/QSPI/NAND)                   ← Loads kernel + device tree
   │                                               ← Can configure FPGA via FPGA Manager
   ▼
Linux Kernel                                       ← FPGA Manager driver initializes
   │                                               ← FPGA can be reconfigured via configfs
   ▼
Userspace                                          ← FPGA bridges active, bulk data flowing
```

The FPGA fabric is **always** a configurable peripheral — never the boot master. The HPS wakes up first, initializes the world, and then decides when to bring the FPGA online.

---

## Stage 1: Boot ROM (0xFFFD_0000)

| Property | Value |
|---|---|
| **Size** | 64 KB mask ROM |
| **Execution starts** | Immediately after POR de-assertion |
| **Clock** | Internal 25 MHz oscillator (before PLLs are configured) |
| **Stack** | On-Chip RAM (64 KB at 0xFFFF_0000) |
| **Role** | Minimal bootstrap: read BSEL pins, find preloader, validate header, jump |

**What the Boot ROM does:**

1. Reads BSEL[2:0] pins (strapped on PCB) to determine boot source
2. Initializes the selected boot peripheral (SD/MMC, QSPI, NAND, or FPGA)
3. Searches for a valid preloader image header at known offsets
4. Validates the header checksum
5. Copies the preloader to On-Chip RAM (max 60 KB)
6. Jumps to preloader entry point in OCRAM

**What the Boot ROM does NOT do:**
- Configure SDRAM (no DDR controller init)
- Configure PLLs (runs on internal oscillator)
- Configure pin muxing beyond the boot peripheral
- Touch the FPGA fabric at all

---

### BSEL Pin Decoding

| BSEL[2:0] | Boot Source | Typical Use |
|---|---|---|
| `000` | Reserved | — |
| `001` | FPGA (HPS-to-FPGA bridge) | FPGA provides preloader image directly |
| `010` | 1.8V NAND flash | Embedded systems |
| `011` | 3.3V NAND flash | Legacy designs |
| `100` | 1.8V SD/MMC | **DE10-Nano default** |
| `101` | 3.3V SD/MMC | Some custom boards |
| `110` | 1.8V QSPI | Fast boot from QSPI NOR |
| `111` | 3.3V QSPI | Common on industrial boards |

> **DE10-Nano:** BSEL = `100` (1.8V SD/MMC) — the microSD card slot is the boot source.

---

## Stage 2: Preloader (U-Boot SPL)

The preloader is a stripped-down U-Boot Secondary Program Loader (SPL). It's the first user-controlled code — and where most boot customization happens.

### Preloader Responsibilities

| Task | Why it matters |
|---|---|
| **Clock initialization** | Configure MPU PLL (800–925 MHz), L3/L4 PLLs, SDRAM PLL |
| **SDRAM calibration** | DDR3/DDR3L/LPDDR2: read/write leveling, DQS gating, VREF training |
| **Pin muxing** | Configure HPS I/O pins for UART, EMAC, I2C, etc. via System Manager |
| **FPGA configuration (optional)** | Load `.rbf` from SD/QSPI and pump it into FPGA via FPP ×16 |
| **Bridge enable (optional)** | Enable H2F/LWH2F/F2H bridges after FPGA configured |
| **Load next stage** | Find SSBL (U-Boot proper) on boot media, load to SDRAM, jump |

### Preloader Image Header

The preloader image must have a specific 512-byte header recognized by Boot ROM:

```
Offset 0x00:  0x00000000  (magic word 1)
Offset 0x04:  0x00000000  (magic word 2)
Offset 0x08:  0x00000000  (magic word 3)
Offset 0x0C:  0x00000000  (magic word 4)
Offset 0x40:  Entry point address (typically 0xFFFF0000, OCRAM base)
Offset 0x44:  Image size (in bytes)
Offset 0x48:  Header version
Offset 0x4C:  Checksum (32-bit sum of all previous words + entry + size + version)
```

The Boot ROM XOR-validates the four magic words, version, and checksum before executing.

### Preloader Size Limit

The Boot ROM only copies the preloader to On-Chip RAM (64 KB). The preloader image must fit within **60 KB** (4 KB reserved for Boot ROM data). This is tight — U-Boot SPL with DDR calibration, QSPI, and SD/MMC drivers fits, but not much more.

---

## Stage 3: U-Boot (SSBL)

Full U-Boot runs from SDRAM with full driver support. Key responsibilities:

| Action | Command / Mechanism |
|---|---|
| **Load kernel** | `fatload mmc 0:1 ${loadaddr} zImage` |
| **Load device tree** | `fatload mmc 0:1 ${fdtaddr} socfpga.dtb` |
| **Load FPGA bitstream (if not done in SPL)** | `fpga load 0 ${fpgadata} ${filesize}` via FPGA Manager |
| **Enable FPGA bridges** | `bridge enable` |
| **Boot kernel** | `bootz ${loadaddr} - ${fdtaddr}` |

### FPGA Configuration via FPGA Manager

```
U-Boot > fatload mmc 0:1 0x1000000 soc_system.rbf
U-Boot > fpga load 0 0x1000000 ${filesize}
```

The FPGA Manager writes the raw `.rbf` bitstream into the FPGA configuration controller, which pumps data into the fabric via the FPP ×16 interface at ~100 MHz. A full 110K LE bitstream (~15–20 Mb compressed) takes **~80–150 ms** from the HPS side.

**Critical timing:** FPGA I/O pins are tri-stated during configuration and only driven after the `CONF_DONE` signal asserts. If Linux drivers probe FPGA-attached peripherals before `CONF_DONE`, they hang. Use `bridge enable` after `fpga load` in U-Boot, or rely on kernel FPGA Manager sequencing.

---

## Stage 4: Linux Kernel

### FPGA Manager Driver

The kernel's `fpga-mgr` subsystem loads after the `socfpga` platform driver:

```
[    1.234567] fpga_manager fpga0: Altera SOCFPGA FPGA Manager registered
```

At this point:
1. The `fpga-manager` device exposes `/sys/class/fpga_manager/fpga0/`
2. FPGA bridge drivers (`altera_hps2fpga_bridge`) expose bridge control
3. Device tree overlays can be applied to bring FPGA peripherals online post-boot

### Post-Boot FPGA Reconfiguration (configfs)

```bash
# Load a new bitstream at runtime
mkdir -p /config/device-tree/overlays/fpga
cat soc_system.rbf > /config/device-tree/overlays/fpga/firmware
echo 1 > /sys/class/fpga_manager/fpga0/load
```

This reconfigures the FPGA **without rebooting**. All FPGA bridges are automatically gated during reconfiguration and re-enabled after `CONF_DONE`.

---

## Stage 5: Userspace — FPGA Bridges Active

After all stages complete, userspace can access FPGA fabric through:
- `/dev/mem` with `mmap()` at H2F/LWH2F addresses
- UIO or kernel drivers for FPGA peripherals
- DMA Engine API for FPGA-to-SDRAM datapaths (F2S ports)

---

## Boot Timing (DE10-Nano Typical)

| Stage | Duration | Notes |
|---|---|---|
| Power-on to Boot ROM start | ~1 ms | POR ramp + internal oscillator lock |
| Boot ROM → Preloader | ~100 ms | SD card init, header search, copy to OCRAM |
| Preloader execution | ~200–500 ms | SDRAM calibration dominates |
| Preloader FPGA config (optional) | ~80–150 ms | FPP ×16 at 100 MHz, for 20 Mb bitstream |
| U-Boot → Kernel handoff | ~2–5 s | Kernel decompression, DT parse, driver init |
| **Total to Linux login** | **~5–10 s** | SD card speed is usually the bottleneck |

---

## Common Boot Problems

| Symptom | Root Cause | Fix |
|---|---|---|
| **No UART output at all** | Wrong BSEL pins, or Boot ROM can't read SD | Check BSEL strapping; verify SD card is FAT16/FAT32 with MBR |
| **"Checksum mismatch" in Boot ROM** | Corrupted preloader header | Regenerate preloader with `mkpimage` from U-Boot tools |
| **Hangs after "reading preloader"** | Preloader too large (>60 KB) | Strip unnecessary drivers from SPL config |
| **Preloader loads but hangs** | SDRAM calibration failed | Check DDR3 routing, VREF voltage, termination |
| **Kernel boots but FPGA bridge hangs** | FPGA not configured before bridge enable | Enable bridges only after `CONF_DONE` in U-Boot or kernel |
| **FPGA I/O contention during boot** | FPGA I/Os driving before HPS boot complete | Add weak pull-ups to FPGA I/O constraints; use `CONFIG_SEL` pin to gate |
| **U-Boot can't find kernel on SD** | Wrong partition table or FS type | Ensure SD has MBR partition 1 as FAT32 with `zImage` + `socfpga.dtb` |

---

## Reference Configuration: DE10-Nano Default Boot Flow

```
BSEL = 100 (SD/MMC 1.8V)
  │
  ▼
Boot ROM reads MBR → Partition 1 (FAT32, type 0x0B/0x0C)
  │  Searches for preloader-mkpimage.bin at offset 0 (raw partition)
  │  Or: preloader image at fixed offsets in bare-metal SD layout
  ▼
Preloader (U-Boot SPL):
  - Configures MPU to 800 MHz, L3 to 400 MHz
  - Calibrates 1 GB DDR3 on 32-bit bus
  - Does NOT configure FPGA (deferred to U-Boot or kernel for MiSTer)
  - Loads U-Boot from SD FAT partition
  ▼
U-Boot:
  - Loads kernel zImage + socfpga_cyclone5_de10_nano.dtb from /boot/
  - Enables HPS bridges
  - bootz → kernel
  ▼
Linux:
  - FPGA Manager driver probes
  - Userspace (MiSTer main binary) configures FPGA core via configfs
```

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS TRM, Chapter 7: Boot | Intel FPGA Documentation |
| Cyclone V Device Handbook Vol. 3: Appendix A (BSEL) | Intel FPGA Documentation |
| U-Boot SPL for SoCFPGA | `arch/arm/mach-socfpga/spl_gen5.c` in U-Boot source |
| U-Boot preloader image tool | `tools/mkpimage.c` in U-Boot source |
| Linux FPGA Manager | `drivers/fpga/socfpga.c` in Linux kernel |
| RocketBoards.org: Boot Flow | https://rocketboards.org/ |
