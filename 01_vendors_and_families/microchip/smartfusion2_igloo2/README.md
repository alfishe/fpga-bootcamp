[← Microchip Home](../README.md) · [← Section Home](../../README.md)

# Microchip SmartFusion2 & IGLOO2 — 65nm Flash with Mixed-Signal

Older 65nm flash-based families still active for low-power, mixed-signal, and high-security applications. SmartFusion2 is the only FPGA with integrated hard Cortex-M3, 12-bit ADCs, and FIPS 140-2 certified crypto chain.

---

| Family | CPU | LEs | Key Feature |
|---|---|---|---|
| **SmartFusion2** | Hard ARM Cortex-M3 (166 MHz) | 5K–150K | Integrated 12-bit ADCs, crypto accelerator (AES/SHA/RSA/ECC) |
| **IGLOO2** | None (soft CPU options) | 5K–150K | Same fabric as SmartFusion2 without Cortex-M3 and analog |

---

## SmartFusion2 — Security & Mixed-Signal Uniquely Integrated

SmartFusion2 is the only FPGA with:
- Hard SECDED-protected memories
- **Anti-tamper** — active mesh, voltage/temperature/frequency monitors
- **Zeroization** — wipe entire design in microseconds on tamper detection
- FIPS 140-2 certified crypto chain

Most commonly found in military and defense applications where FIPS 140-2 certification is mandatory.

---

## When to Choose SmartFusion2/IGLOO2

| Constraint | Pick |
|---|---|
| FIPS 140-2 certification required | SmartFusion2 |
| Need hard Cortex-M3 + ADC on the same die as FPGA | SmartFusion2 |
| Pure non-volatile but cheaper than PolarFire | IGLOO2 |

---

## Development Boards

### Microchip (First-Party)

| Board | FPGA Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **SmartFusion2 Advanced Dev Kit** | M2S150-FCG1152 | 150K | Hard Cortex-M3, 12-bit ADC, crypto accelerator (AES/SHA/RSA/ECC), DDR3, FMC, GbE | ~$599 | Full SmartFusion2 security + mixed-signal eval |
| **SmartFusion2 Starter Kit** | M2S010-1VF400 | 10K | Hard Cortex-M3, ADC, mikroBUS, Arduino header, USB-powered | ~$129 | Entry-level SmartFusion2 |
| IGLOO2 Eval Kit | M2GL010-1VF400 | 10K | Same fabric as SmartFusion2, no CPU, low-power | ~$99 | Non-volatile entry-level FPGA |

### Third-Party

| Board | FPGA Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Arrow SmartFusion2 SoM** | M2S010 | 10K | SODIMM SoM, industrial temp, production-oriented | ~$100+ | Embedded deployment |

### Choosing a Board

| You want... | Get... |
|---|---|
| Full SmartFusion2 security eval | Advanced Dev Kit (~$599) |
| Entry-level SmartFusion2 | Starter Kit (~$129) |
| Non-volatile FPGA only (no CPU) | IGLOO2 Eval Kit (~$99) |
| FIPS 140-2 / secure applications | SmartFusion2 Advanced Dev Kit |
| Production module | Arrow SoM |

---

## References

| Source | Path |
|---|---|
| SmartFusion2 Data Sheet | DS0110 |
