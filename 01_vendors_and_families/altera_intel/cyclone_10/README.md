[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel Cyclone 10 — Cost-Optimized LP & GX Refresh

Cyclone 10 devices are cost-reduced derivatives introduced later in the Cyclone product lifecycle. They come in two sub-families with very different fabrics:

| Sub-family | Based On | Process | LEs | DSP | Transceivers | Notes |
|---|---|---|---|---|---|---|
| **Cyclone 10 LP** | Cyclone IV E lineage | 60nm (optimized) | 6K–120K | 10–288 (18×18) | None | Bare-bones, lowest cost/density |
| **Cyclone 10 GX** | Cyclone V GX derivative | 20nm | 85K–220K | 84–192 (18×18) | 12× 12.5 Gbps | Cheaper than Arria 10, 12G lanes |

---

## Cyclone 10 LP — Legacy Low-Cost Workhorse

Focuses on functional safety certification and absolute minimum BOM cost. It's a matured 60nm process, essentially a Cyclone IV with improved production yields and certification packages.

**Use when:** board cost is the dominant constraint and you don't need transceivers, SoC, or high-speed memory interfaces.

## Cyclone 10 GX — Mid-Range with 12G Lanes

Uses the 20nm transceiver process to deliver 12.5 Gbps lanes at a lower cost than Arria 10 (28 Gbps). Good for 10G Ethernet and CPRI applications where you've outgrown Cyclone V GX's 3–6 Gbps but don't need Arria 10's 28G tiers.

---

## Cyclone 10 vs Cyclone V — Decision Matrix

| You want... | Pick |
|---|---|
| Highest LUT/dollar, no transceivers | Cyclone 10 LP |
| Radiation/functional-safety certification needed | Cyclone 10 LP (has functional safety package) |
| 12G lanes but cheaper than Arria 10 | Cyclone 10 GX |
| 28nm, mature tooling, USB/EMAC on-chip (SoC) | Stick with Cyclone V |
| **New design default** | Cyclone V or Agilex 5, not Cyclone 10 |

---

## Best Practices

1. **Don't use Cyclone 10 LP unless you identify a specific cost or certification advantage.** It's a legacy platform; new designs should default to Cyclone V or Agilex 5.
2. **Cyclone 10 GX ≠ Cyclone V GX.** GX variant uses different transceiver PHYs (20nm-based). Ports require re-characterizing the entire transceiver chain.

---

## Development Boards

### Intel (First-Party)

| Board | Cyclone 10 Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Cyclone 10 LP Eval Kit** | 10CL120YF780 (LP) | 120K | DDR3, GbE, HSMC, audio codec, 7-seg, switches | ~$249 | Legacy low-cost, functional safety eval |
| **Cyclone 10 GX Dev Kit** | 10CX220YF780 (GX) | 220K | 12.5 Gbps XCVR, PCIe Gen2 ×4, FMC, HSMC, GbE, DDR4 | ~$549 | 12G transceiver + PCIe dev at lower cost than Arria 10 |

### Choosing a Board

| You want... | Get... |
|---|---|
| 12G transceivers cheaper than Arria 10 | Cyclone 10 GX Dev Kit (~$549) |
| Functional safety certification eval | Cyclone 10 LP Eval Kit |
| New design default (not LP) | Skip Cyclone 10 LP — use Cyclone V or Agilex 5 |

---

## References

| Source | Path |
|---|---|
| Cyclone 10 LP/GX Device Overview | Intel FPGA documentation |
