[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# High-Speed Signal Integrity — FPGA PCB Design

At FPGA edge rates (sub-nanosecond), every PCB trace is a transmission line. A 100 MHz clock has a 5th harmonic at 500 MHz — and at 500 MHz, a 6-inch FR4 trace is 1/4 wavelength. Impedance mismatches, via stubs, and crosstalk that were invisible at 10 MHz become show-stoppers.

This article covers impedance control, loss budgets, eye diagrams, differential pair routing, via effects, crosstalk, and the SI simulation workflow.

---

## Key Concepts

| Concept | What It Means | Why It Matters |
|---|---|---|
| **Characteristic impedance (Z₀)** | The impedance a signal "sees" on a trace | Mismatch → reflections → eye closure |
| **Differential impedance (Z_diff)** | Impedance between a differential pair | LVDS, MIPI, PCIe all require 100Ω diff |
| **Insertion loss (S₂₁)** | Signal attenuation over distance | FR408HR at 10 GHz: ~1.5 dB/inch; limits trace length |
| **Return loss (S₁₁)** | Signal reflected back to source | Poor via transitions cause S₁₁ spikes |
| **Crosstalk (NEXT/FEXT)** | Signal coupling to adjacent traces | >5% crosstalk → bit errors on adjacent lanes |
| **Jitter** | Timing uncertainty at the receiver | ISI from lossy traces is the #1 jitter source |
| **Eye diagram** | Overlay of all bit transitions on one plot | Shows margin: eye opening = usable signal |
| **S-parameters** | Frequency-domain characterization of a channel | Standard format for SI simulation models |

---

## When Is a Trace "High-Speed"?

```
A trace is a transmission line when:
  Round-trip delay > signal rise time / 2

Example: 0.5 ns rise time (typical LVCMOS33)
  Round-trip on FR4: ~150 ps/inch
  Critical length = 0.5 ns / (2 × 150 ps/in) ≈ 1.7 inches

Any trace longer than 1.7 inches needs impedance control.
Most FPGA traces are longer than this → most traces need impedance control.
```

| Signal Type | Rise Time | Critical Length | Impedance Control Required? |
|---|---|---|---|
| Slow SPI (1 MHz) | ~50 ns | ~170 inches | No |
| UART (115 kbaud) | ~100 ns | ~330 inches | No |
| DDR3-1600 | ~0.3 ns | ~1 inch | Yes — tightly controlled |
| LVDS (1 Gbps) | ~0.2 ns | ~0.7 inches | Yes |
| PCIe Gen3 (8 GT/s) | ~0.05 ns | ~0.17 inches | Yes — every millimeter matters |

---

## Impedance Control

### Single-Ended Microstrip

```
          ┌───────────── Trace (W width, T thickness)
          │
   ───────┴───────────  ← Top copper
   ╔═════════════════╗
   ║   Dielectric    ║  ← Height H
   ║   (FR4, εᵣ≈4.2) ║
   ╠═════════════════╣
   ║   GND Plane     ║  ← Reference layer
   ╚═════════════════╝

Z₀ ≈ (87 / √(εᵣ + 1.41)) × ln(5.98H / (0.8W + T))

Typical: W=4.5 mil, H=3.5 mil, T=1.4 mil, εᵣ=4.2 → Z₀ ≈ 50Ω
```

### Differential Pair (Edge-Coupled Microstrip)

```
          ┌───── D+ ─────┐   ┌───── D- ────┐
          │   (W width)  │   │             │
   ───────┴──────────────┴───┴─────────────┴──  ← Top copper
   ╔═══════════════════════════════════════════╗
   ║   Dielectric                              ║  ← S = spacing between traces
   ╠═══════════════════════════════════════════╣
   ║   GND Plane                               ║
   ╚═══════════════════════════════════════════╝

Z_diff ≈ 2 × Z₀ × (1 - 0.48 × e^(-0.96×S/H))
```

### Common Impedance Targets

| Interface | Z₀ (single-ended) | Z_diff | Notes |
|---|---|---|---|
| DDR3/DDR4 | 40–50 Ω | 80–100 Ω (diff clock) | Single-ended data lines, diff strobes |
| LVDS | N/A | 100 Ω | Differential only |
| PCIe Gen2/3/4 | 85 Ω | 100 Ω (85+85 – coupling) | CEM spec |
| USB 2.0 | 45 Ω | 90 Ω | Spec: 90Ω ±15% |
| USB 3.0 | N/A | 100 Ω | SuperSpeed lanes |
| HDMI | N/A | 100 Ω | TMDS pairs |
| SGMII | 50 Ω | 100 Ω | Can be single-ended or differential |
| 10GBASE-KR | N/A | 100 Ω | Backplane Ethernet |
| SMPTE (SDI) | 75 Ω | N/A | 75Ω coax / BNC |

**Fab note:** Always specify controlled-impedance with your PCB fabricator. A 0.1 mm trace width difference can shift Z₀ by 5–10 Ω. Include impedance coupons on your panel for verification.

---

## Insertion Loss and Loss Budgets

### Why Traces Lose Signal

| Loss Mechanism | Frequency Dependence | Dominant At |
|---|---|---|
| **Conductor loss** (skin effect) | ∝ √f | Low-GHz range |
| **Dielectric loss** (tangent δ) | ∝ f | High-GHz range (dominates >5 GHz on FR4) |
| **Radiation loss** (bends, vias) | ∝ f² | Above 10 GHz |
| **Roughness loss** (copper foil) | ∝ f | VLP copper helps above 5 GHz |

### Loss per Inch by Material

| Material | εᵣ | tan δ | Loss at 5 GHz | Loss at 10 GHz | Cost |
|---|---|---|---|---|---|
| FR4 (standard) | 4.5 | 0.02 | ~0.8 dB/in | ~1.8 dB/in | $ |
| FR408HR | 3.7 | 0.012 | ~0.5 dB/in | ~1.2 dB/in | $$ |
| Isola 370HR | 4.0 | 0.015 | ~0.6 dB/in | ~1.4 dB/in | $$ |
| Megtron 6 | 3.4 | 0.004 | ~0.25 dB/in | ~0.5 dB/in | $$$ |
| Megtron 7 | 3.3 | 0.002 | ~0.15 dB/in | ~0.3 dB/in | $$$$ |

### Loss Budget Example: PCIe Gen3 (8 GT/s)

```
Total budget:     -20 dB (spec limit from TX to RX)
───────────────────────────────────────────────
TX package:       -1.5 dB
PCB trace (6 in): -7.2 dB  (FR408HR: 1.2 dB/in × 6)
Connectors (2×):  -2.5 dB  (1.25 dB each)
Via transitions:  -1.0 dB  (4 vias × 0.25 dB)
RX package:       -1.5 dB
───────────────────────────────────────────────
Total:            -13.7 dB ← 6.3 dB margin (GOOD)

If using standard FR4 instead:
PCB trace (6 in): -10.8 dB (1.8 dB/in × 6)
Total:            -17.3 dB ← 2.7 dB margin (RISKY)
```

**If the budget exceeds the spec limit, the eye closes and BER degrades.** Solutions: shorter traces, better dielectric, fewer vias, or lower-loss connectors.

---

## Eye Diagrams

An eye diagram overlays all possible bit transitions onto a single UI (unit interval). The "opening" of the eye is the margin available for the receiver to sample correctly.

### Reading an Eye Diagram

```
            Voltage
              ▲
              │    ┌───────┐    ┌───────┐
           1──┤   ╱         ╲  ╱         ╲
              │  ╱    ┌──────╲╱────┐      ╲
              │ ╱     │      V     │       ╲
              │╱      │  EYE OPEN  │        ╲
           0──┤       │   AREA     │         ╲
              │       │            │          ╲
              │  ╲    │            │      ┌────┘
              │   ╲   │            │      │
          -1──┤    ╲──┘            └──────┘
              │
              └────────────────────────────────► Time
                   │←─ UI ─→│
                   │        │
              ←── Jitter ──→
```

| Eye Feature | What It Indicates | Ideal | Failing |
|---|---|---|---|
| **Eye height** (vertical opening) | Signal-to-noise ratio | >70% of full swing | <30% → bit errors |
| **Eye width** (horizontal opening) | Jitter margin | >80% of UI | <50% → timing violations |
| **Rise/fall time** | Channel bandwidth | Fast, clean | Slow, smeared → ISI |
| **Overshoot/undershoot** | Impedance mismatch | <10% | >20% → reflections, EMI |
| **Jitter** (eye width reduction) | Timing uncertainty | <10% UI | >30% UI → BER failure |

### What Kills the Eye

| Problem | Eye Symptom | Root Cause |
|---|---|---|
| **Excessive trace loss** | Eye closes vertically (ISI) | Trace too long, wrong dielectric |
| **Impedance mismatch** | Ringing, overshoot | Z₀ off by >10% |
| **Via stub resonance** | Eye collapses at specific frequencies | Unback-drilled via acts as notch filter |
| **Crosstalk** | Eye jitters horizontally | Traces too close, no shielding |
| **Power noise** | Eye closes vertically | PDN impedance too high at data rate harmonics |

---

## Length Matching

| Interface | Within-Pair Matching | Lane-to-Lane Matching | Why |
|---|---|---|---|
| DDR3 byte lane (DQ+DQS) | ±10 mil | ±25 mil | DQS strobes sample DQ at center |
| DDR3 CK to CMD/ADDR | — | ±25 mil | Setup/hold margin at DRAM |
| LVDS pair (P to N) | ±5 mil | ±50 mil | Skew → common-mode noise |
| PCIe Gen2 (×4) | ±5 mil | ±10 mil | Multi-lane deskew range |
| PCIe Gen3 (×4) | ±2 mil | ±5 mil | Tighter for 8 GT/s |
| USB 3.0 | ±5 mil | ±15 mil | SuperSpeed pair matching |
| HDMI | ±5 mil | ±50 mil | TMDS per-pair matching |
| 10GBASE-KR | ±2 mil | ±5 mil | IEEE 802.3 spec |

### Length Matching Techniques

**Serpentine (accordion) routing:**
```
D+ ──────╱╲──╱╲──╱╲──────────
D- ───────────────────────────
          ↑
    Serpentine adds length to D+
    to match the longer D- trace
```

**Rules:**
1. Match within a pair first, then between pairs
2. Use small serpentine amplitude (<3× trace width) to minimize crosstalk to self
3. Keep serpentine sections away from connectors and vias
4. Add length on the shorter trace, never cut the longer one

---

## Via Effects and Mitigation

Each via adds:
- **~0.5–1 pF capacitance** (pad + anti-pad + stub)
- **~0.5–1 nH inductance** (barrel)
- **Impedance discontinuity** (Z₀ drops ~30% at via)
- **~0.2–0.5 dB loss** at 5 GHz per via

### Via Stub Problem

```
Signal layer (L1) ────┐
                      ├── Via barrel
Inner layer (L3) ─────┤    (connected)
                      │
                      │ ← STUB: unconnected portion
                      │    acts as resonant cavity at λ/4
                      │
Bottom layer (L12) ───┘

Stub length = board thickness - signal layer depth
For a 62 mil board, signal on L3: stub ≈ 45 mil

Resonant frequency = c / (4 × stub_length × √εᵣ)
For 45 mil stub on FR4: f_res ≈ 27 GHz ← above most protocols
For 100 mil stub on FR4: f_res ≈ 12 GHz ← INSIDE PCIe Gen3 band!
```

### Mitigations

| Technique | What It Does | When Required | Cost Impact |
|---|---|---|---|
| **Back-drilling** | Drill out stub from bottom side | >5 Gbps, thick boards (>40 mil stub) | +10–20% board cost |
| **Blind/buried vias** | Via only spans needed layers | >10 Gbps, HDI boards | +50–100% board cost |
| **Via-in-pad** | Eliminates fanout trace | BGA pitch ≤ 0.8 mm | +20% board cost |
| **Ground return vias** | Adjacent GND vias provide return path | All high-speed designs | Minimal |
| **Pad removal on inner layers** | Reduces via capacitance | >8 Gbps | Free (design choice) |

### Ground Via Spacing Rule

Place ground return vias within **1/10 wavelength** of the highest frequency component along any differential pair route:

```
For 10 GHz signal: λ/10 ≈ 60 mil on FR4
→ Place GND stitching vias every 50–60 mil along the pair
```

---

## Crosstalk

### NEXT and FEXT

```
Aggressor trace:  ═══════════════════════►
Victim trace:     ═══════════════════════►
                  ←─ NEXT ─→  ←─ FEXT ─→
                  (near-end)   (far-end)

NEXT: Coupling at the same end as the aggressor driver
FEXT: Coupling at the opposite end from the aggressor driver
```

| Crosstalk Type | Direction | Frequency Dependence | Primary Coupling |
|---|---|---|---|
| **NEXT** (near-end) | Backward | Relatively flat with frequency | Capacitive + inductive |
| **FEXT** (far-end) | Forward | Increases with frequency × length | Capacitive – inductive (differential) |

### Spacing Rules

| Spacing (S) vs Trace Width (W) | Crosstalk (typical) | Use When |
|---|---|---|
| 1W (edge to edge) | ~5–10% | Minimum for any digital trace |
| 2W | ~2–5% | DDR data lines, SPI |
| 3W | ~1–2% | High-speed differential pairs |
| 5W | <0.5% | Clocks, sensitive analog |

**Differential pair isolation:**
- Pair-to-pair spacing: ≥ 3W (between adjacent pairs)
- Pair-to-single-ended: ≥ 4W
- Pair-to-clock: ≥ 5W (clocks are the worst aggressors)

---

## Differential Pair Routing Rules

| Rule | Why | Violation Consequence |
|---|---|---|
| Route P and N on same layer | Different layers → different Z₀ | Mode conversion, EMI |
| Keep S constant along the pair | Z_diff changes with spacing | Impedance mismatch at connectors |
| Minimize via count (match on both P/N) | Asymmetric vias → skew | Reduced eye width |
| No splitting reference plane | Return current detour | EMI, crosstalk |
| Route tightly coupled (edge-coupled) | Better noise rejection | Loosely coupled pairs are less immune |
| Length match within ±5 mil | Skew → common-mode | Reduces receiver margin |

### Tight vs Loose Coupling

| Coupling | Spacing | Z_diff | Pros | Cons |
|---|---|---|---|---|
| **Tight** (S ≈ W) | 4–5 mil | 100Ω (lower Z₀ per line) | Best noise rejection; common-mode cancellation | Harder to route around obstacles |
| **Loose** (S ≈ 2W) | 8–10 mil | 100Ω (higher Z₀ per line) | Easier routing; less sensitive to spacing variation | Weaker noise rejection; more EMI |

---

## SI Simulation Workflow

### Pre-Layout Simulation

```
1. Define channel: TX model → PCB trace → Connector → RX model
2. Extract S-parameters for each element:
   - TX/RX: vendor IBIS-AMI models
   - PCB trace: 2D field solver (Polar Si9000, AppCAD)
   - Connector: vendor S-parameter model
3. Cascade S-parameters in time-domain simulator
4. Generate eye diagram
5. Verify eye opening meets spec
6. If FAIL: adjust trace length, dielectric, via strategy, connector
```

### Post-Layout Simulation

```
1. Import PCB layout (ODB++ or Gerber) into field solver
2. Extract actual trace geometries, via models
3. Run 3D EM simulation (HyperLynx, Sigrity, Ansys HFSS)
4. Generate S-parameters for actual routed channels
5. Simulate with IBIS-AMI TX/RX models
6. Verify eye diagram at RX
7. If FAIL: reroute, add back-drilling, change dielectric
```

### Tools

| Tool | Vendor | Type | Cost |
|---|---|---|---|
| **HyperLynx** | Siemens | Pre/post-layout SI + PI | Paid |
| **Sigrity** | Cadence | Post-layout SI/PI, power-aware SI | Paid |
| **Ansys HFSS** | Ansys | 3D EM field solver | Paid |
| **Polar Si9000** | Polar Instruments | 2D impedance calculator | Paid (affordable) |
| **AppCAD** | Broadcom (free) | 2D impedance + loss calculator | Free |
| **Saturn PCB Toolkit** | Saturn PCB (free) | Impedance, crosstalk, current capacity | Free |
| **sparameters.com** | Signal Integrity Journal | Online S-parameter viewer | Free |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Via stub resonance** | S₁₁ spike at λ/4; eye collapses at specific data rate | Back-drill or use blind vias |
| **Reference plane gap under diff pair** | Common-mode radiation, fails EMI | Keep solid reference plane under entire route |
| **90° corners (pre-2010 myth)** | Real issue is impedance change, not the angle itself | Route 45° or curved; don't obsess below 5 Gbps |
| **Wrong dielectric for data rate** | Eye doesn't open at target speed | Use Megtron 6/7 for >8 Gbps; FR408HR for <5 Gbps |
| **Length matching without impedance matching** | Matched length but mismatched Z₀ | Both matter; check Z₀ at every transition |
| **Forgetting AC coupling caps** | DC bias on link; RX input out of spec | Add 0.1 µF AC coupling on PCIe, SATA, 10GBASE-KR |
| **Crosstalk from parallel clocks** | Intermittent errors on adjacent data lanes | Route clocks with 5W spacing; shield with GND vias |
| **Not simulating the full channel** | Individual parts pass, full channel fails | Simulate end-to-end: TX → PCB → connector → cable → RX |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Stratix 10 High-Speed Board Design](https://docs.altera.com/r/docs/683738/current/stratix-10-device-design-guidelines/high-speed-board-design) | Altera | Intel/Altera high-speed PCB design guidelines |
| [BGA Routing](bga_routing.md) | This KB | BGA escape routing, via strategies, layer stackup |
| [Power Integrity](power_integrity.md) | This KB | PDN design, decoupling, IR drop |
| [Thermal Design](thermal_design.md) | This KB | Junction temperature, heat sink selection |
