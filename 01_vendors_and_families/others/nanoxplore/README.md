[← Others Home](../README.md) · [← Section Home](../../README.md)

# NanoXplore — European Radiation-Hardened Space FPGA

French company providing European-sourced radiation-hardened FPGAs for the ESA Galileo navigation system and other EU space programs. Supports **SEL immune latch technology** (no latch-up possible).

---

| Device | System Gates | SERDES | Package | Notes |
|---|---|---|---|---|
| NG-Medium | 3M gates | Up to 16× 3.125 Gbps | CGA 415 | ~50K LUTs equivalent |
| NG-Large | 17M gates | 24× 10.3 Gbps | CGA 1752 | ~280K LUTs equivalent |
| NG-Ultra | 30M gates | 40× 28 Gbps | — | Coming 2026 |

Used in Ariane rockets and OneWeb constellations. European-endorsed since EU strategic autonomy mandates require non-US/non-Chinese silicon for critical infrastructure.

---

## Development Boards

### NanoXplore (First-Party)

| Board | FPGA | Equivalent LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **NG-Large Dev Kit** | NG-Large | ~280K | 24× 10.3 Gbps SERDES, DDR3, FMC, space-qualified | Contact vendor | European space-grade FPGA eval |
| NG-Medium Dev Kit | NG-Medium | ~50K | 16× 3.125 Gbps SERDES, radiation-hardened, SEL immune | Contact vendor | Entry-level rad-hard FPGA |

### Choosing a Board

| You want... | Get... |
|---|---|
| European-sourced space FPGA | NG-Large or NG-Medium Dev Kit |
| Note: ITAR-free, non-US/non-Chinese | Required for ESA/EU critical infrastructure |

---

## References

| Source | Path |
|---|---|
| NanoXplore | https://www.nanoxplore.com |
