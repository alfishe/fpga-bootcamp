[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# Power Integrity — FPGA Power Delivery Network (PDN) Design

FPGA core current can swing from 0A to 10A+ in nanoseconds. Without a well-designed Power Delivery Network (PDN), the voltage at the die droops below spec, causing bit errors, timing failures, and mysterious resets. PDN design is about keeping the FPGA's supply impedance low from DC to the maximum transient frequency.

This article covers the complete PDN design flow: rail identification, impedance budget calculation, decoupling strategy, power sequencing, IR drop analysis, and vendor tool walkthroughs.

---

## FPGA Power Rails

| Rail | Typical Voltage | Current (small FPGA) | Current (large FPGA) | Tolerance | Notes |
|---|---|---|---|---|---|
| **VCCINT (core)** | 0.85–1.1V | 1–3A | 20–100A | ±3% | Highest current, tightest tolerance |
| **VCCAUX (auxiliary)** | 1.8V | 0.2–0.5A | 1–3A | ±5% | Configuration, JTAG, PLLs |
| **VCCIO (I/O banks)** | 1.2/1.5/1.8/2.5/3.3V | 0.1–1A/bank | 0.1–2A/bank | ±5% | One rail per voltage standard |
| **VCCBRAM** | 0.85–1.0V | 0.1–0.5A | 1–5A | ±3% | Some FPGAs combine with VCCINT |
| **MGTAVCC (transceiver)** | 0.9–1.0V | 0.5–1A | 3–10A | ±2% | Low-noise analog supply |
| **MGTAVTT (transceiver term)** | 1.2V | 0.2–0.5A | 1–3A | ±3% | Termination voltage |
| **VCCADC** | 1.8V | <0.1A | <0.1A | ±1% | XADC / SYSADC supply (very quiet) |

> **A typical Xilinx UltraScale+ FPGA has 6–12 separate power rails.** A high-pin-count device may need 8+ voltage regulators on the PCB.

---

## PDN Impedance Budget

### Calculating Target Impedance

```
Z_target = (V_rail × %ripple) / I_transient_max
```

**Example: VCCINT rail for a Kintex UltraScale+**
```
V_rail        = 0.85V
Ripple spec   = ±3%  (0.85 × 0.03 = 25.5 mV)
I_transient   = 15A  (core current swing from idle to full utilization)

Z_target = 25.5 mV / 15A = 1.7 mΩ
```

The PDN must present **<1.7 mΩ** impedance from DC to ~100 MHz (the frequency content of a 1 ns current step). This is extremely low — it requires careful capacitor selection and placement.

### Typical Target Impedances by Rail

| Rail | Z_target (typical) | Difficulty |
|---|---|---|
| VCCINT (0.85V, 20A) | 1–3 mΩ | Very hard — most caps, tightest layout |
| VCCAUX (1.8V, 2A) | 10–30 mΩ | Moderate |
| VCCIO (3.3V, 1A) | 30–100 mΩ | Easy |
| MGTAVCC (0.9V, 5A) | 2–5 mΩ | Hard — must also be low-noise |
| VCCADC (1.8V, 0.1A) | 100+ mΩ | Easy — but must be clean |

### Frequency-Domain Decomposition

| Frequency Range | What Dominates Z | Solution | Typical Values |
|---|---|---|---|
| DC – 10 kHz | Voltage regulator (VRM) output impedance | Proper regulator selection, remote sense, output inductor | VRM Z_out ~1–10 mΩ in this range |
| 10 kHz – 1 MHz | Bulk capacitors | Tantalum/polymer 100–470 µF near VRM | 2–4 bulk caps per rail |
| 1 MHz – 100 MHz | Ceramic decoupling caps | MLCC 0.1–10 µF, low ESL, placed at FPGA balls | 10–50 MLCCs per rail |
| 100 MHz – 1 GHz | On-die capacitance + package inductance | Built into FPGA die/package — you can't add more | 10–100 nF on-die |

The PDN is a parallel combination of all these impedance curves. The peak between regions (the "anti-resonance peak") is where most designs fail.

---

## Anti-Resonance Peaks — The Silent Killer

When different capacitor types have overlapping impedance curves, their parallel combination can create impedance peaks at the crossover frequency:

```
Z (mΩ)
  │
3 ┤─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Z_target
  │         ╱ ╲
2 ┤       ╱     ╲        ← ANTI-RESONANCE PEAK
  │     ╱         ╲           Exceeds Z_target!
1 ┤   ╱             ╲──────────────────── MLCC Z
  │ ╱                              ╲
0 ┤╱─────────────────────────────────── Bulk cap Z
  └───────────────────────────────────── Frequency
         100kHz  1MHz  10MHz  100MHz
```

**Fix:** Add intermediate-value capacitors to fill the gap. If you have 100 µF bulk and 100 nF ceramic, add 10 µF and 1 µF ceramics to smooth the transition. The goal is a **monotonically decreasing** impedance curve.

---

## Decoupling Capacitor Selection

| Capacitor Type | Capacitance Range | ESL | ESR | Best For |
|---|---|---|---|---|
| **MLCC X7R (0201)** | 0.001–0.1 µF | ~0.2 nH | ~10 mΩ | Highest-frequency decoupling |
| **MLCC X7R (0402)** | 0.01–1 µF | ~0.3 nH | ~15 mΩ | High-frequency decoupling |
| **MLCC X7R (0306)** | 0.01–0.47 µF | ~0.15 nH | ~10 mΩ | Reverse-geometry: lowest ESL per size |
| **MLCC X7R (0603)** | 0.1–10 µF | ~0.5 nH | ~20 mΩ | Mid-frequency |
| **MLCC X7R (0805)** | 1–47 µF | ~0.8 nH | ~30 mΩ | Bulk-ish decoupling |
| **Tantalum Polymer** | 47–470 µF | ~2–5 nH | ~20–50 mΩ | Bulk capacitance, low ESR |
| **OSCON / Al-Polymer** | 100–1000 µF | ~3–10 nH | ~10–30 mΩ | VRM output bulk |

### DC Bias Derating — The Hidden Trap

MLCCs lose capacitance as DC voltage approaches their rating. A 10V-rated 1 µF 0402 cap at 3.3V may only deliver 0.6 µF actual.

```
Applied Voltage as % of Rating    Actual Capacitance (% of nominal)
─────────────────────────────────────────────────────────────────
0%                                100%
25%                               90%
50%                               70–80%    ← Most FPGA rails
75%                               50–60%
90%                               30–40%    ← DO NOT operate here
```

**Rule of thumb:** Choose MLCC voltage rating ≥ 2× the rail voltage. For a 1.0V rail, use 10V-rated caps (derating to ~90% of nominal at 10% of rated voltage).

### Placement Priority

1. **0402 100 nF caps** — directly under FPGA, on BGA power balls (bottom side of PCB)
2. **0402/0603 1 µF caps** — as close as possible to BGA edge
3. **0805 10 µF caps** — around FPGA periphery
4. **Bulk 100–470 µF** — near VRM output

The 100 nF cap at the FPGA ball is **100× more effective at 100 MHz** than a 100 µF tantalum 2 cm away.

---

## Power Sequencing

FPGAs require specific power-up and power-down sequences. Violating the sequence can cause latch-up, excessive inrush current, or permanent damage.

### Xilinx UltraScale+ Sequencing

```
Power-up order:
  1. VCCINT / VCCBRAM     (core — first)
  2. VCCAUX                (auxiliary — after core stable)
  3. VCCIO                 (I/O — last, prevents I/O glitching)

Power-down order:
  Reverse of power-up (VCCIO first, VCCINT last)
```

### Intel Agilex Sequencing

```
Power-up order:
  1. VCC_CORE / VCC_BRAM
  2. VCC_AUX
  3. VCCIO_PIO / VCCIO_HPS
  4. MGTAVCC / MGTAVTT      (transceiver rails last)

All rails must reach minimum operating voltage
within the vendor-specified ramp time (typically 1–50 ms).
```

### Sequencing Implementation

| Method | How It Works | Pros | Cons |
|---|---|---|---|
| **Sequencer IC** (e.g., LM3880, TPS3870) | Dedicated IC asserts enable pins in order | Simple, reliable, few external parts | Fixed sequence; limited flexibility |
| **PMBus / I2C sequencer** (e.g., LTM4676) | Program sequence via I2C, monitor rails | Flexible, monitor voltage/current/temp | Requires firmware, more expensive |
| **RC delay on enable pins** | Resistor-capacitor delay on each regulator EN | Cheapest solution | Imprecise, temperature-dependent |
| **Fusion / CPLD sequencer** | Small CPLD monitors power-good signals | Customizable, can handle faults | Additional IC and firmware |

**Critical parameter — ramp time:** Most FPGAs specify that all rails must reach operating voltage within a maximum ramp time (e.g., 50 ms). Too-slow ramps can cause latch-up; too-fast ramps cause inrush current spikes.

---

## IR Drop Analysis

Voltage drops across PCB traces and planes reduce the voltage actually reaching the FPGA die. At 20A, even 1 mΩ of trace resistance causes a 20 mV drop — significant on a 0.85V rail with ±3% (25.5 mV) tolerance.

### IR Drop Budget

```
V_die = V_VRM - I × (R_trace + R_via + R_plane)

For VCCINT at 0.85V, 20A:
  VRM output:        0.85V (setpoint)
  PCB plane drop:    -10 mV  (5 mΩ × 2A/in × length)
  Via drop:          -5 mV   (0.25 mΩ × 20A × 1 via)
  BGA ball drop:     -2 mV
  ──────────────────────────
  Voltage at die:    0.833V

Remaining margin:    0.833V - (0.85V × 0.97) = 0.833V - 0.8245V = 8.5 mV ← TIGHT
```

### Mitigation Strategies

| Strategy | Effect | Implementation |
|---|---|---|
| **Dedicated power planes** | Reduces R_plane to <1 mΩ | Full copper pour on inner layer for VCCINT |
| **Multiple parallel vias** | Via R = 0.25 mΩ each; N vias = R/N | Use 4+ vias per BGA power ball |
| **Remote voltage sensing** | VRM adjusts output to compensate for drop | Connect VRM sense pins at FPGA pins, not at VRM output |
| **Copper thickness** | 2 oz copper = 0.7 mΩ/sq vs 1 oz = 1.4 mΩ/sq | Specify 2 oz on power planes |
| **Via-in-pad** | Eliminates trace between BGA ball and via | Required for high-current BGA power pins |

---

## Vendor PDN Tools

### AMD/Xilinx — Power Design Manager (PDM)

[PDM](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/power-design-manager.html) replaced XPE (Xilinx Power Estimator) starting with Vivado 2022.2.

**Workflow:**
```
1. Select FPGA device in PDM
2. Enter resource utilization (# LUTs, BRAMs, DSPs, I/Os)
3. Enter toggle rates and clock frequencies
4. PDM calculates: per-rail current, power, Z_target
5. PDM recommends: capacitor count, value, and placement per rail
6. Export: capacitor BOM, PDN impedance plot
```

PDM accounts for:
- Package parasitics (unique per device/package combination)
- On-die capacitance
- Minimum required decoupling per rail
- Maximum allowed impedance per frequency

**PDM output example (Kintex UltraScale+ KU25P):**
```
VCCINT rail:
  Z_target:          2.1 mΩ
  Required MLCCs:    24 × 100 nF (0402) + 8 × 1 µF (0402) + 4 × 10 µF (0805)
  Required bulk:     2 × 330 µF (tantalum polymer)
  Placement:         MLCCs on bottom side under BGA, bulk near VRM
```

### Altera — PDN Tool (Web-based)

Altera provides PDN design tools integrated into their device documentation:

**Workflow:**
```
1. Select device family (Agilex, Stratix 10, Arria 10, Cyclone 10)
2. Enter power consumption per rail (from Quartus Power Analyzer)
3. PDN tool calculates target impedance
4. Recommends decoupling: per-rail capacitor table
5. Generates: impedance vs frequency plot, BOM
```

Available at [docs.altera.com](https://docs.altera.com/r/docs/683073/current/an-958-board-design-guidelines) (AN 958: Board Design Guidelines).

---

## PDN Simulation

### Lumped-Element Simulation (SPICE)

For quick verification, model the PDN as an RLC network:

```
VRM ──[R_vrm + L_vrm]──┬──[C_bulk + R_bulk + L_bulk]──┬── FPGA die
                         │                            │
                         ├──[C_mid + R_mid + L_mid]───┤
                         │                            │
                         ├──[C_cer + R_cer + L_cer]───┤
                         │                            │
                         └──[C_die (on-chip)]─────────┘
```

```spice
* PDN AC analysis
VRFM  1 0 DC 0.85 AC 1
LRFM  1 2 1n
RRFM  2 3 2m

* Bulk capacitor (330 µF, 5 nH ESL, 30 mΩ ESR)
CBULK 3 0 330u
RBULK 3 4 30m
LBULK 4 0 5n

* MLCC (100 nF, 0.3 nH ESL, 15 mΩ ESR)
CMLCC 3 0 100n
RMLCC 3 5 15m
LMLCC 5 0 0.3n

* On-die capacitance (100 nF)
CDIE 3 0 100n

.ac dec 100 1k 1G
```

### 2.5D Field Solver (Ansys SIwave, Cadence Sigrity)

For production boards, a field solver analyzes the actual PCB layout:

1. Import PCB layout (ODB++ or Gerber)
2. Assign material properties (copper, dielectric)
3. Define port locations (VRM output, FPGA power balls)
4. Run simulation → Z-parameter matrix vs frequency
5. Identify impedance peaks above Z_target
6. Add capacitors in simulation → verify peaks reduced

**Typical results:**
```
Without optimization:  Z_peak = 8 mΩ at 15 MHz (fails 2.1 mΩ target)
After adding 8× 1µF:   Z_peak = 1.8 mΩ at 15 MHz (passes)
```

---

## Multi-Rail PDN Design Example

### Design: Kintex UltraScale+ KU15P on a 12-layer PCB

| Rail | Voltage | Max Current | Z_target | Cap Strategy |
|---|---|---|---|---|
| VCCINT | 0.72V | 18A | 1.2 mΩ | 30× 100nF + 12× 1µF + 6× 10µF + 4× 330µF |
| VCCBRAM | 0.72V | 4A | 5.4 mΩ | 8× 100nF + 4× 1µF + 2× 330µF |
| VCCAUX | 1.8V | 1.5A | 60 mΩ | 4× 100nF + 2× 10µF + 1× 100µF |
| VCCIO_3V3 | 3.3V | 0.5A | 330 mΩ | 2× 100nF + 1× 10µF |
| VCCIO_1V8 | 1.8V | 0.3A | 300 mΩ | 2× 100nF + 1× 10µF |
| MGTAVCC | 0.9V | 6A | 3 mΩ | 16× 100nF + 8× 1µF + 2× 330µF |
| MGTAVTT | 1.2V | 2A | 18 mΩ | 6× 100nF + 2× 1µF + 1× 100µF |

**Total: ~130 capacitors** for one FPGA. This is typical for a high-end device.

### Layer Stackup (PDN-optimized)

```
Layer 1:  Signal (top) — BGA breakouts, high-speed traces
Layer 2:  GND plane    — Reference for Layer 1
Layer 3:  Signal
Layer 4:  VCCINT plane — Full copper pour, 2 oz
Layer 5:  GND plane    — Reference for Layer 4; inter-plane cap with L4
Layer 6:  VCCIO/MGT planes — Split for different voltages
Layer 7:  GND plane
Layer 8:  Signal
Layer 9:  Signal
Layer 10: GND plane    — Reference for Layer 11
Layer 11: Signal (bottom) — Decoupling cap pads under BGA
Layer 12: GND plane    — Bottom-side cap reference
```

**Key:** VCCINT plane (L4) is sandwiched between two GND planes (L2, L5), providing:
- Low-impedance power delivery
- Inter-plane capacitance (~100 pF/in²) for high-frequency decoupling
- Shielding from signal layers

---

## Bring-Up Verification

Before applying power, verify the PDN with impedance checks:

| Rail | Typical Impedance (Unpowered) | Danger Zone | Action if Failed |
|---|---|---|---|
| **VCCINT** | 5–50Ω (depends on die size) | < 1Ω | Check decoupling cap solder bridges under BGA |
| **VCCAUX** | > 100Ω | < 10Ω | Inspect auxiliary power regulator output |
| **VCCIO** | > 500Ω | < 10Ω | Check connected peripherals for shorts |
| **MGTAVCC** | 10–100Ω | < 2Ω | Inspect PLL/transceiver dedicated regulators |

After first power-on:
1. Measure each rail voltage at the FPGA pins (not at the VRM)
2. Verify ripple with oscilloscope (20 MHz bandwidth, 1:1 probe)
3. Check sequencing with 4+ channel oscilloscope
4. Run FPGA at max utilization → measure VCCINT droop under load

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Over-relying on one large bulk cap** | Voltage droops under transient load | Bulk caps have high ESL; can't respond in <1 µs. Add MLCCs near FPGA |
| **Wrong capacitor dielectric** | Y5V/Z5U caps lose 80% capacitance at temp/DC bias | Use X7R or X5R; derate by 50% for DC bias |
| **Ignoring power sequencing** | FPGA latch-up or permanent damage | Follow vendor sequencing: VCCINT → VCCAUX → VCCIO |
| **Single via per BGA power ball** | 0.25 mΩ per via × 20A = 5 mV drop per via | Use 4+ vias per high-current BGA ball |
| **Measuring voltage at VRM, not FPGA** | Die sees 50+ mV less than you think | Use remote sense; measure at FPGA pins |
| **Anti-resonance peak exceeds Z_target** | Intermittent failures under specific workloads | Add intermediate-value caps to fill the gap |
| **Insufficient ramp time** | Latch-up during power-on | Ensure all rails reach minimum voltage within spec ramp time |
| **Shared VCCINT plane between FPGAs** | One FPGA's transient causes the other to glitch | Separate VRM per FPGA, or isolate with ferrite bead |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [AMD Power Design Manager](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/power-design-manager.html) | AMD/Xilinx | Official power estimation and PDN design tool |
| [AN 958: Board Design Guidelines](https://docs.altera.com/r/docs/683073/current/an-958-board-design-guidelines) | Altera | Intel/Altera PDN design, decoupling, sequencing |
| [Agilex 3 PDN Design Summary](https://docs.altera.com/r/docs/853726/current/pcb-design-guidelines-agilextm-3-fpgas-and-socs/agilextm-3-device-family-pdn-design-summary) | Altera | Agilex-specific PDN requirements |
| [BGA Routing](bga_routing.md) | This KB | BGA escape routing, via strategies, decoupling cap placement |
| [High-Speed Signals](high_speed_signals.md) | This KB | Signal integrity, impedance control |
| [Thermal Design](thermal_design.md) | This KB | Junction temperature, heat sink selection |
| [Bring-Up Checklist](../15_case_studies/bring_up_checklist.md) | This KB | First power-on verification |
