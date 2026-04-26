[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel MAX 10 — Instant-On Non-Volatile FPGA

The MAX 10 is Intel's entry-level non-volatile FPGA. Configuration is stored in **internal flash** — no external config chip needed — and the device boots in milliseconds. It's the spiritual successor to the CPLD use-case (glue logic, power sequencing, simple controllers) but with enough density to run a Nios II soft processor.

---

## Key Specifications

| Feature | Specification |
|---|---|
| **Process** | 55nm NOR Flash |
| **LEs** | 2K–50K (10M02 to 10M50) |
| **On-chip Flash** | 128 KB–1,376 KB (stores 2 config images) |
| **Configuration** | Internal flash, instant-on (< 10 ms from power-good) |
| **Dual Configuration** | Store 2 images, remote-selected |
| **ADC** | 2× 12-bit SAR, 1 MSPS (10M04+) |
| **Memory** | M9K blocks, 108–1,638 Kb |
| **DSP** | 18×18 multipliers, 16–144 blocks |
| **PLLs** | 1–4 per device |
| **User IOs** | 26–360 |
| **Package** | TQFP, BGA, WLCSP |

---

## MAX 10 vs Cyclone V

| Criterion | MAX 10 | Cyclone V |
|---|---|---|
| **Boot time** | ~2 ms (instant-on) | ~100 ms+ (from external flash) |
| **External config chip** | None required | Requires QSPI flash or HPS SD |
| **Board complexity** | 1 power rail (core 1.2V or 3.3V) | 4+ rails |
| **SoC option** | No | Yes (dual ARM A9) |
| **Density ceiling** | 50K LEs | 301K LEs |
| **Device price (approx)** | $3–30 | $20–200 |

MAX 10 is ideal for glue logic, power management, and simple controllers where an external configuration flash would add BOM cost. Its **dual-configuration** feature enables safe remote firmware update: load new image to flash slot 2, switch pointer, never brick.

---

## Best Practices

1. **Use MAX 10 for board-level glue** — level shifters, button debounce, power sequencing. It removes ~$5 BOM (external config flash + supervisor CPLD).
2. **Pair MAX 10 with Cyclone V on the same board** — MAX 10 handles power-up sequencing, reset generation, and watchdog; Cyclone V handles compute.
3. **Leverage the internal ADC** for voltage monitoring, temperature sensing, and low-speed analog acquisition without external ADC chips.

---

## Pitfall: Flash Endurance

The internal flash is good for **~10,000 program/erase cycles**. If you intend to reconfigure the FPGA multiple times per day over years of deployment, use Cyclone V + external flash instead (QSPI flash is ~100,000 cycles). This matters for continuous FPGA reconfiguration use-cases like MiSTer's core-switching — this is why MAX 10 isn't used for that purpose.

---

## Development Boards

### Intel / Terasic (First-Party)

| Board | MAX 10 Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **MAX 10 10M50 Eval Kit** | 10M50DAF484 | 50K | DDR3, GbE, HDMI, HSMC, audio codec, temp sensor | ~$249 | Full-featured MAX 10, Nios II Linux eval |
| MAX 10 10M08 Eval Kit | 10M08SAE144 | 8K | Arduino header, accelerometer, 7-seg, SRAM | ~$79 | Entry-level eval, Arduino shield-compatible |
| MAX 10 Plus (Terasic) | 10M50DAF484 | 50K | 7-seg ×6, VGA, audio, switches/buttons, GPIO | ~$149 | University/teaching, peripheral-rich |
| BeMicro MAX 10 (Arrow) | 10M08S/10M02S | 2K–8K | USB Blaster on-board, GPIO, accelerometer | ~$49 | Ultra-low-cost entry, smallest MAX 10 |

### Third-Party / Community

| Board | MAX 10 Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **MAX 1000 (Arrow)** | 10M08SAU169 | 8K | Integrated USB Blaster + accelerometer + 8 MB SDRAM, Arduino MKR form-factor | ~$29 | Cheapest all-in-one MAX 10, Arduino-compatible |
| QMTech MAX 10 | 10M08S/10M50 | 8K/50K | Bare board, DDR3 SODIMM option (50K), GPIO | ~$20–60 | Hobbyist, lowest-cost MAX 10 |
| MKR Vidor 4000 (Arduino) | 10M16SAU169 | 16K | Arduino MKR ecosystem, SAMD21 co-processor, WiFi, HDMI | ~$60 | Arduino FPGA hybrid, education |

### Choosing a Board

| You want... | Get... |
|---|---|
| Full-featured MAX 10 development | MAX 10 10M50 Eval Kit (~$249) |
| Cheapest possible MAX 10 | QMTech 10M08S (~$20) or MAX 1000 (~$29) |
| Arduino FPGA hybrid | MKR Vidor 4000 |
| University/teaching lab | MAX 10 Plus |
| Nios II soft CPU evaluation | MAX 10 10M50 Eval Kit |

---

## References

| Source | Path |
|---|---|
| MAX 10 Device Handbook | Intel FPGA documentation |
| MAX 10 FPGA Design Guidelines | Intel FPGA documentation |
