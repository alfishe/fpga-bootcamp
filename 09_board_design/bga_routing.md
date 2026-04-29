[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# BGA Escape Routing — Strategy for High-Pin-Count FPGAs

Modern FPGAs ship as BGA (Ball Grid Array) packages with 256–2,572+ balls at 0.5–1.0 mm pitch. Routing signals out from under the package is the defining physical-design challenge of any FPGA board — get it wrong and you'll need a respin.

---

## BGA Package Landscape (FPGA-Relevant)

| Package | Typical FPGA Families | Ball Count | Pitch (mm) | Layer Count (typ) |
|---|---|---|---|---|
| FBGA-256 | Artix-7, Cyclone V, ECP5 | 256 | 1.0 | 4–6 |
| FBGA-484 | Artix-7, Cyclone V GX, Zynq-7010 | 484 | 1.0 | 6–8 |
| FBGA-676 | Kintex-7, Zynq-7020/7035 | 676 | 1.0 | 8–10 |
| FFG-900 | Kintex-7, Virtex-7, Stratix V | 900 | 1.0 | 10–14 |
| FFG-1156 | Ultrascale+ KU/K, Agilex | 1,156 | 0.8 | 12–16 |
| FFG-1924 | Virtex UltraScale+, Agilex 7 | 1,924 | 0.8 | 16–22 |
| FFG-2572 | Virtex UltraScale+ VU47P | 2,572 | 0.8 | 20–30 |

**Rule of thumb:** At 0.8 mm pitch, you get ~2 traces between pads with 3.5 mil line/space on outer layers. At 1.0 mm, ~3 traces.

---

## Escape Routing Strategies

### Strategy 1: Dog-Bone (Through-Hole Vias)

```
Pad → short trace → through-hole via → inner layer
  ○──────────────────╳
```

- **Cost:** Lowest — standard PCB fab, no laser drilling
- **Limits:** 1.0 mm pitch minimum. One trace per channel at 0.8 mm.
- **FPGA families:** Artix-7, Cyclone V, ECP5 (≤676 balls)
- **Layer count:** Typically 6–10 layers for 484-ball packages

### Strategy 2: Via-in-Pad (Microvia)

```
Pad = Via → inner layer (laser-drilled microvia directly on pad)
  ╳
```

- **Cost:** +30–50% PCB cost (laser drilling, filled-and-plated vias)
- **Required for:** 0.8 mm pitch, high pin count (>676 balls)
- **FPGA families:** Kintex-7, Ultrascale+, Agilex
- **Process:** Cu fill + planarization → flat pad for soldering
- **Stack:** Can stack microvias for layer 1→2→3 transitions (staggered microvias cheaper than stacked)

### Strategy 3: Escape by Quadrant

The BGA ball map is not random. FPGA manufacturers organize balls into:

| Region | Signal Type | Routing Direction |
|---|---|---|
| Core (center) | Power/GND (solid planes needed) | Directly to inner planes |
| Inner ring | I/O banks | Escape outward in all directions |
| Outer 2–3 rows | Single-ended I/O | Easiest — shortest breakout |
| Corner clusters | GTY/GTH transceivers | Escape toward board edge (shortest path to connectors) |

**Key insight:** Route the outer 2 rows first, then inner rows, saving the center for last. The center often has power/ground pads that connect directly to planes (no routing needed).

### Strategy 4: Blind and Buried Vias

| Via Type | Connects | Cost Factor | When to Use |
|---|---|---|---|
| Through-hole | All layers | 1× | ≤8 layers, ≥1.0 mm pitch |
| Blind (L1–L2) | Top → inner | 1.5× | Free up L3+ for routing |
| Buried (L2–L5) | Inner only | 2× | High layer count stacks |
| Microvia (L1–L2) | Top → L2 only | 1.8× | Via-in-pad at 0.8 mm |
| Stacked microvia | L1→L2→L3… | 3×+ | Dense 0.8 mm with many IOs |

---

## Layer Stackup Design

### Minimum Layer Estimation

For N signal balls, with D dog-bone traces per channel and L layers:

\[L \approx \lceil \frac{N}{D \times \text{routing-channels-per-layer}} \rceil + 2_{\text{planes}}\]

**Practical example (FBGA-484, 1.0 mm pitch, dog-bone):**
- ~320 signal balls (rest are power/GND)
- 3 traces per channel, ~40 channels per layer ≈ 120 signals/layer
- \(\lceil 320/120 \rceil = 3\) signal layers + 2 plane + 2 power = **8 layers minimum**

### Recommended Stackups

| BGA Size | Pitch | Layers | Stackup (Top→Bottom) | Via Strategy |
|---|---|---|---|---|
| 256-ball | 1.0 mm | 6 | SIG-GND-SIG-PWR-GND-SIG | Through-hole |
| 484-ball | 1.0 mm | 8 | SIG-GND-SIG-PWR-GND-SIG-GND-SIG | Through-hole |
| 676-ball | 1.0 mm | 10 | SIG-GND-SIG-PWR-GND-SIG-GND-SIG-GND-SIG | Through-hole |
| 900-ball | 1.0 mm | 12 | 2×SIG-GND-SIG-PWR… | Blind on top 4 |
| 1156-ball | 0.8 mm | 16 | Microvia L1→L2, buried L3→L14 | Via-in-pad required |

---

## Vendor-Specific Notes

| Vendor | Notes |
|---|---|
| **Xilinx** | GTY transceiver pins always at package edge. Route them FIRST — they have the tightest length-matching requirements. |
| **Intel (Altera)** | Stratix 10/Agilex use embedded capacitors in substrate — reduces PDN BGA ball count, more room for signals. |
| **Lattice** | ECP5 in csBGA-285: 0.8 mm pitch but only 285 balls — dog-bone still works. CrossLink-NX in BGA-72: trivial. |
| **Gowin** | LittleBee in LQFP-144: no BGA needed. GW2A in FBGA-256: standard dog-bone. |

---

## Signal Layer Assignment Rules

1. **Transceivers:** Route on top layer ONLY (or L2 with blind via). Never via-transition a 28 Gbps trace — each via adds ~1 dB insertion loss at 14 GHz.
2. **DDR memory:** Route entire byte lane on one layer. If layer change is required, change ALL signals in the byte lane together.
3. **Clocks:** Dedicated inner stripline layer, sandwiched between two GND planes.
4. **Power/GND:** Minimum 1 oz Cu for planes. For >30 A core supplies, consider 2 oz Cu or embedded Cu planes.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| **"We'll autoroute the BGA"** | Autorouters fail catastrophically on BGA escape. You'll get 40+ layers and unresolved connections. |
| **Changing layer stackup after layout starts** | Impedance targets shift, requiring re-simulation of every controlled-impedance trace. |
| **Not reserving space for decoupling caps** | 0201/0402 caps must be placed on the bottom side directly under the BGA. No room → PDN fails. |
| **Assuming 0.5 mm pitch is hobbyist-accessible** | 0.5 mm BGA requires HDI (microvia, laser drill) — not available at prototype fabs (JLCPCB, PCBWay standard service). |

---

## References

- IPC-2221/2222: Generic standard for PCB design
- IPC-6012: Qualification and performance for rigid PCBs (Class 2 = industrial, Class 3 = mil/aero)
- Xilinx UG109: Packaging and Pinouts Specification
- Intel AN 114: Board Design Guidelines for Intel FPGA Packages
