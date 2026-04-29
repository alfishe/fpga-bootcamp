[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# Configuration Interfaces — Flash, Strapping, and Boot Strategy

Every FPGA needs to load its bitstream from somewhere. The choice of configuration memory — QSPI flash, eMMC, NAND, SD card, or JTAG-only — determines boot time, reliability, field-update capability, and bill-of-materials cost. This article covers the electrical interface selection, pin strapping, multi-boot schemes, and remote update strategies.

---

## Configuration Memory Options

| Memory Type | Capacity | Read Speed | Write Speed | Endurance | Cost (2026) | FPGA Families |
|---|---|---|---|---|---|---|
| **QSPI NOR Flash** | 16–256 Mb | 50–100 MB/s (Quad) | 0.5–2 MB/s | 100K cycles | $0.50–3 | All SRAM-based FPGAs |
| **Octal SPI (x8)** | 128 Mb–2 Gb | 200–400 MB/s | 1–5 MB/s | 100K cycles | $2–15 | Ultrascale+, Agilex, Versal |
| **eMMC** | 4–64 GB | 100–250 MB/s | 50–100 MB/s | 3K–10K cycles | $3–20 | Zynq, Cyclone V SoC, Versal |
| **NAND Flash (raw)** | 1–64 Gb | 20–40 MB/s | 5–20 MB/s | 100K cycles (SLC) | $2–15 | Rare — needs ECC, mostly via eMMC |
| **SD Card** | 1–64 GB | 10–50 MB/s | 10–50 MB/s | 10K+ (wear-leveled) | $5–30 | Zynq (boot), dev boards |
| **JTAG only** (no flash) | N/A | N/A | N/A | ∞ (volatile) | $0 | All FPGAs — dev/debug only |
| **Internal Flash (NV FPGA)** | 64Kb–2 Mb (UEB) | Instant | Self-contained | 10K cycles | Included | MAX 10, SmartFusion2, iCE40, GW1N |

---

## Configuration Modes by Vendor

### Xilinx 7-Series / UltraScale+

| Mode | Pins | Bus Width | Max Rate | Notes |
|---|---|---|---|---|
| **Master SPI (x1/x2/x4)** | M[2:0] = 001 | 1/2/4-bit | ~100 MB/s (x4) | Default for most designs |
| **Master BPI (x8/x16)** | M[2:0] = 010 | 8/16-bit | ~800 MB/s (x16) | Parallel NOR flash. Faster, more pins. |
| **Master SPI x8** | M[2:0] = 001 + extended | 8-bit | ~200 MB/s | UltraScale+ only. Octal SPI. |
| **Slave SelectMAP (x8/x16/x32)** | M[2:0] = 110 | 8/16/32-bit | Up to 3.2 GB/s (x32) | External master (MCU, CPU) controls config |
| **Slave Serial** | M[2:0] = 111 | 1-bit | ~100 MHz (12.5 MB/s) | Slowest. Legacy. |
| **JTAG** | M[2:0] = 101 | 1-bit | 30–66 MHz | Always available regardless of M[2:0] |

**M[2:0] strapping:** Set via external pull-up/pull-down resistors on dedicated config pins. Read at power-on only — not dynamically changeable.

### Intel (Altera) Cyclone V / Arria 10 / Stratix 10

| Mode | MSEL Pins | Bus Width | Max Rate | Notes |
|---|---|---|---|---|
| **Active Serial (AS) x1/x4** | MSEL[4:0] | 1/4-bit | ~100 MB/s (x4) | EPCS/EPCQ flash. x4 = "AS x4" mode. |
| **AS x4 (Fast)** | MSEL[4:0] | 4-bit | ~400 MB/s | DDR-capable EPCQ-L flash |
| **AS x4 (Octal)** | MSEL[4:0] + extended | 8-bit | ~800 MB/s | Stratix 10/Agilex with MT25Q flash |
| **Passive Serial (PS)** | MSEL[4:0] | 1-bit | ~125 MHz | External host. Slow. |
| **FPP (Fast Passive Parallel) x8/x16/x32** | MSEL[4:0] | 8/16/32-bit | Up to 3.2 GB/s (x32) | External host with parallel bus |
| **JTAG** | Always available | 1-bit | 30–66 MHz | Always available |

**MSEL pins on Cyclone V SoC:** MSEL is shared between HPS and FPGA configuration. Some MSEL values enable HPS boot (HPS boots first, then HPS configures FPGA).

### Lattice ECP5 / CrossLink-NX

| Mode | CFG Pins | Notes |
|---|---|---|
| **Master SPI** | CFG[1:0] = 00 | Default. Standard QSPI flash. |
| **Slave SPI** | CFG[1:0] = 01 | External MCU sends bitstream over SPI |
| **SD Card** | CFG[1:0] = 10 | ECP5 only (not CrossLink-NX) |
| **JTAG/SV** | CFG[1:0] = 11 | Program via JTAG or direct slave parallel |

---

## Flash Selection Guidelines

### When to Use QSPI NOR
- **Nearly always the correct answer** for SRAM-based FPGAs
- Bitstream fits in 16–256 Mb (most Artix-7 through Kintex-7 designs)
- Boot time < 200 ms from power-on

### When to Use Octal SPI
- UltraScale+ or Agilex with bitstream > 128 Mb
- Need < 100 ms boot (multiboot with fallback)
- Higher bandwidth allows partial reconfiguration between images

### When to Use eMMC / SD Card
- Zynq / Cyclone V SoC / Versal — Linux rootfs + bitstream on same device
- Bitstream > 256 Mb (Virtex UltraScale+ with large designs)
- Field-update friendly: users can swap SD cards

### When to Use JTAG Only
- Development / debug only
- Bitstream loaded each power cycle from host PC
- Zero BOM cost for configuration memory

---

## Multi-Boot and Fallback

Most modern FPGAs support storing multiple bitstreams in flash and selecting at boot.

| Vendor | Feature Name | How It Works |
|---|---|---|
| **Xilinx** | MultiBoot / Fallback | Flash has header + golden image + multiboot image(s). IPROG command triggers warm-boot to alternate address. If CRC fails, falls back to golden. |
| **Intel** | Remote System Upgrade (RSU) | Factory image at address 0, application image(s) at higher offsets. If application fails config, FPGA reverts to factory. |
| **Lattice** | Dual Boot | Two bitstreams in SPI flash. CFG pin or soft-register selects which to load. |
| **Microchip** | Auto-Update | SmartFusion2 stores bitstream in internal eNVM. Golden + update slot for field upgrade. |

**Critical design rule:** Never overwrite the golden/factory image during a field update. Always write the new image first, verify, then update the pointer.

```
┌─────────────────────────┐
│ Flash Address Space      │
├─────────────────────────┤
│ 0x000000: Golden Image   │ ← NEVER overwrite in field
│ 0x100000: App Image v1   │ ← Currently running
│ 0x200000: App Image v2   │ ← New version being written
│ 0x300000: Scratch/Data   │
└─────────────────────────┘
```

---

## Remote Update Architecture

For deployed systems that must update without physical access:

```
Cloud/Build Server
    │
    ▼ HTTPS
Device Linux (Zynq/Cyclone V SoC)
    │
    ├─ Download new bitstream → verify SHA-256
    ├─ Write to flash (NOT golden region)
    ├─ Set next-boot pointer
    └─ Reboot
    │
    ▼
Boot ROM → Golden Image checks pointer → loads new image
    │
    ├─ If new image times out (watchdog) → fallback to golden
    └─ If new image boots successfully → commit pointer permanently
```

| Vendor | Remote Update Tooling |
|---|---|
| **Xilinx** | FPGA Manager (Linux kernel), xdevcfg driver, U-Boot `fpga` command |
| **Intel** | FPGA Manager, Mailbox Client driver (Arria 10+), U-Boot `fpga` command |
| **Lattice** | No built-in remote update. Custom MCU must manage SPI flash writes. |

---

## SoC Boot vs FPGA-Only Configuration

| Aspect | FPGA-Only (Artix-7, ECP5) | SoC (Zynq, Cyclone V SoC) |
|---|---|---|
| Who boots first | FPGA (loads from flash on power-up) | CPU (Boot ROM → FSBL/SPL → then configures FPGA) |
| Flash contents | Single .bit / .sof file | FSBL + U-Boot + Linux kernel + rootfs + bitstream |
| Config time | 50–200 ms (FPGA loads itself) | 1–10 seconds (Linux boots first, then FPGA) |
| Flash type | QSPI NOR (simple) | QSPI + eMMC (complex partitioning) |
| Tool | Vivado/Quartus writes .mcs directly | Petalinux/Yocto builds BOOT.BIN with all partitions |

---

## Pin Strapping Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **M[2:0] wrong** | FPGA doesn't configure on power-up; JTAG works | Verify MSEL/M[2:0] against desired config mode in datasheet |
| **INIT_B stuck low** | FPGA tries to configure but CRC fails | Flash image corrupted. Re-program flash. Check flash voltage. |
| **DONE not going high** | Configuration completed but DONE pin stuck | DONE requires external pull-up (330 Ω to VCCO). Don't rely on internal pull. |
| **PROGRAM_B floating** | FPGA randomly reconfigures | External pull-up (4.7 kΩ to VCCO). Never leave floating. |
| **Shared JTAG chain issues** | Multiple FPGAs in JTAG chain — one won't configure | Verify TDI→TDO daisy chain order. Xilinx: set correct device index in `program_hw_devices`. |

---

## Best Practices

1. **Always include a JTAG header** — even on production boards. The 6-pin (TCK, TMS, TDI, TDO, GND, VREF) header costs $0.10 and saves days of debug.
2. **Golden image at flash address 0** — immutable, tested, never field-updated. Your insurance policy against bricked devices.
3. **Verify flash write before reboot** — read-back + SHA-256 check after every flash write. Power loss during write is the #1 cause of field bricking.
4. **Watchdog-based fallback** — if new bitstream doesn't toggle a heartbeat within 30 seconds, reset to golden.
5. **Don't multiplex config pins as user I/O** — even if the datasheet says you can after configuration. Multiplexed config pins cause debug nightmares.

---

## References

- Xilinx UG470: 7 Series FPGAs Configuration User Guide
- Xilinx UG570: UltraScale Architecture Configuration
- Intel AN 777: Configuration and Remote System Upgrades in Cyclone V Devices
- Lattice TN1260: ECP5 Configuration and Programming Guide
- Microchip UG0663: SmartFusion2 Configuration Guide
