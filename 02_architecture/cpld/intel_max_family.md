[← CPLD Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# Intel MAX Family: MAX V and MAX 10

Intel (formerly Altera) offers two product lines under the MAX brand. **MAX V** is a true CPLD. **MAX 10** is marketed as an FPGA but inherits CPLD-like characteristics: on-chip flash, instant-on, and single-chip operation.

---

## MAX V: The True CPLD

MAX V is Intel's last dedicated CPLD family, built on a 1.8V core process with on-chip flash storage. It is the direct descendant of the MAX 7000 and MAX II families.

### Architecture

- **Logic Element (LE):** Each LE contains a 4-input LUT-equivalent implemented via AND-OR macrocell logic
- **User Flash Memory (UFM):** 8 Kb–54 Kb of on-chip flash for constant storage or soft-core MCU code
- **Internal Oscillator:** Eliminates need for external clock source for simple designs
- **Single 1.8V supply:** Simplifies power design; I/O banks support 1.5V–3.3V

### MAX V Density Range

| Device | LEs | Equivalent Macrocells | UFM | Pins | Pin-to-Pin Delay |
|---|---|---|---|---|---|
| **5M40Z** | 40 | 32 | 8 Kb | 44–64 | 7.5 ns |
| **5M80Z** | 80 | 64 | 8 Kb | 44–100 | 7.5 ns |
| **5M160Z** | 160 | 128 | 8 Kb | 44–100 | 7.5 ns |
| **5M240Z** | 240 | 192 | 8 Kb | 80–128 | 7.5 ns |
| **5M570Z** | 570 | 440 | 32 Kb | 80–144 | 7.5 ns |
| **5M1270Z** | 1,270 | 980 | 54 Kb | 144–208 | 7.5 ns |

### Key Features

- **50% lower power** than competing CPLDs (Intel claim, typical standby ~25–50 µA)
- **Instant-on:** Configuration loaded from internal flash in < 1 ms
- **Security:** No external configuration interface to probe
- **Programmable via JTAG** or in-system via ISP

### Development Boards

| Board | Vendor | Price | Features |
|---|---|---|---|
| **BeMicro MAX 10** | Arrow / Intel | ~$30–$50 | MAX 10 (not MAX V), 8 MB SDRAM |
| **BeMicro CV** | Arrow | ~$50 | Cyclone V, not MAX |

True MAX V dev boards are rare; most designers prototype on MAX 10 or use generic TQFP breakout boards.

---

## MAX 10: Flash-Based FPGA

MAX 10 is Intel's **non-volatile FPGA** family. It is not a CPLD architecturally (it uses LUTs and an FPGA fabric), but it fills the same market niche: single-chip, instant-on, low-cost programmable logic.

### MAX 10 vs MAX V

| Feature | MAX V (CPLD) | MAX 10 (FPGA) |
|---|---|---|
| **Core architecture** | AND-OR macrocell | LUT-based FPGA |
| **Density** | 40–1,270 LEs | 2,000–50,000 LEs |
| **Internal oscillator** | Yes (one) | Yes (multiple frequencies) |
| **User flash memory** | 8–54 Kb | Up to 1,888 Kb |
| **ADC** | No | **Yes** (1 MSPS, 12-bit, dual supply devices) |
| **Dual configuration** | No | **Yes** (two independent images in flash) |
| **External RAM support** | No | Yes (SDR/DDR SDRAM, soft controller) |
| **Nios II soft core** | Possible but tight | Comfortable at 10K+ LEs |
| **DSP blocks** | No | Yes (hard 18×18 multipliers) |
| **PLLs** | No | Yes (up to 4 per device) |
| **Packages** | TQFP, BGA | TQFP, BGA, WLCSP |

### MAX 10 Key Innovations

1. **Dual Configuration Flash:** Two independent configuration images stored internally. Image A can update Image B remotely, enabling fail-safe field upgrades.

2. **Integrated ADC:** The only Intel FPGA family with a built-in analog-to-digital converter (available on dual-supply devices only). Supports 1 MSPS sampling across 10+ channels.

3. **Single or Dual Supply:**
   - **Single supply:** 3.3V only — simplest power design
   - **Dual supply:** 1.2V core + 3.3V I/O — lower core power, enables ADC

4. **Instant-on:** Like CPLDs, MAX 10 boots from internal flash in milliseconds. No external config device needed for the primary image.

### MAX 10 Density Range

| Device | LEs | UFM (Kb) | ADC | PLLs | Packages |
|---|---|---|---|---|---|
| **10M02** | 2,000 | 1,376 | No | 1 | TQFP, BGA |
| **10M04** | 4,000 | 1,888 | No | 2 | TQFP, BGA |
| **10M08** | 8,000 | 1,888 | No | 2 | TQFP, BGA, WLCSP |
| **10M16** | 16,000 | 3,456 | No | 3 | TQFP, BGA |
| **10M25** | 25,000 | 3,456 | No | 3 | TQFP, BGA |
| **10M40** | 40,000 | 3,456 | No | 4 | BGA |
| **10M50** | 50,000 | 3,456 | No | 4 | BGA |
| **10M08D** | 8,000 | 1,888 | **Yes** | 2 | TQFP, BGA |
| **10M16D** | 16,000 | 3,456 | **Yes** | 3 | TQFP, BGA |
| **10M25D** | 25,000 | 3,456 | **Yes** | 3 | TQFP, BGA |
| **10M40D** | 40,000 | 3,456 | **Yes** | 4 | BGA |
| **10M50D** | 50,000 | 3,456 | **Yes** | 4 | BGA |

> **D suffix:** Dual-supply devices with integrated ADC. Single-supply devices (no D suffix) lack the ADC.

### Development Boards

| Board | Vendor | Price (USD) | MAX 10 Device | Key Features | Status |
|---|---|---|---|---|---|
| **DE10-Lite** | Terasic | $150 ($82 academic) | 10M50DAF484C7G | 64 MB SDRAM, Arduino headers, ADC, hex displays, VGA | Active |
| **BeMicro MAX 10** | Arrow | ~$30 | 10M08DAF484C8G | 8 MB SDRAM, Pmod, accelerometer, DAC, temp sensor | Active |
| **MAX 10 Evaluation Kit** | Intel / Altera | $53 | 10M08SAE144C8G | 144-EQFP, power measurement, Arduino, ADC, NOR flash | Active |

> **Current as of: 2026-04.** DE10-Lite price verified via DigiKey (P0466, $150); academic pricing direct from Terasic ($82). MAX 10 Evaluation Kit price verified via DigiKey (EK-10M08E144, $53.08). BeMicro MAX 10 price approximate from Arrow historical listing.

---

## Programming and Configuration

### MAX V
- **JTAG ISP:** In-system programming via USB-Blaster
- **No external config device:** Flash is on-chip
- **Security bit:** Prevents readback of configuration

### MAX 10
- **JTAG:** Standard programming
- **Dual Config:** Image 0 and Image 1 stored in internal flash
- **Remote System Update:** Image 0 can load Image 1; if Image 1 fails, watchdog reverts to Image 0
- **UFM access:** User Flash Memory accessible from Nios II or fabric logic
- **AES bitstream encryption:** Supported on larger devices

---

## Migration Path: MAX V to MAX 10

Intel does not offer a direct pin-compatible migration from MAX V to MAX 10, but the Quartus Prime software supports both families. Designers hitting MAX V density limits (1,270 LEs) typically migrate to:

1. **MAX 10** (same single-chip flash concept, up to 50K LEs)
2. **Cyclone V or Cyclone 10 LP** (if external config is acceptable and higher density needed)
3. **Lattice MachXO3** (if Intel supply chain is a concern)

---

## Further Reading

| Document | Intel Doc ID |
|---|---|
| MAX V Device Handbook | M5014 |
| MAX 10 FPGA Device Overview | 683658 |
| MAX 10 FPGA Configuration User Guide | UG-M10CONFIG |
| Quartus Prime Handbook Volume 1 | — |
