[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# High-Speed Signal Integrity — FPGA PCB Design

At FPGA edge rates (sub-nanosecond), every PCB trace is a transmission line. This covers impedance control, length matching, differential pair routing, via effects, and crosstalk — the physical-layer concerns that determine whether your design works at speed.

---

## Key Concepts

| Concept | What It Means | Why It Matters |
|---|---|---|
| **Characteristic impedance (Z₀)** | The impedance a signal "sees" on a trace | Mismatch → reflections → eye closure |
| **Differential impedance (Z_diff)** | Impedance between a differential pair | LVDS, MIPI, PCIe all require 100Ω diff |
| **Insertion loss (S₂₁)** | Signal attenuation over distance | FR408HR at 10 GHz: ~1.5 dB/inch; limits trace length |
| **Return loss (S₁₁)** | Signal reflected back to source | Poor via transitions cause S₁₁ spikes |
| **Crosstalk (NEXT/FEXT)** | Signal coupling to adjacent traces | >5% crosstalk → bit errors on adjacent lanes |
| **Jitter** | Timing uncertainty at the receiver | ISI (inter-symbol interference) from lossy traces is the #1 jitter source |

---

## Impedance Control

| Trace Type | Typical Z₀ (single-ended) | Typical Z_diff |
|---|---|---|
| DDR3/DDR4 (single-ended) | 40–50 Ω | 80–100 Ω (differential clock) |
| LVDS | N/A | 100 Ω |
| PCIe Gen2/3 | 85 Ω (single-ended) | 100 Ω (differential) |
| USB 2.0/3.0 | 90 Ω (differential) | N/A |
| HDMI | N/A | 100 Ω |
| SGMII/RGMII | 50 Ω | N/A |

**Fab note:** Always specify controlled-impedance with your PCB fabricator. A 0.1mm trace width difference can shift Z₀ by 5–10 Ω.

---

## Length Matching

| Interface | Matching Requirement | Why |
|---|---|---|
| DDR3 byte lane (DQ + DQS) | ±10 mil within lane | DQS strobes sample DQ at center |
| DDR3 clock to address/command | ±25 mil | Setup/hold margin at DRAM |
| LVDS pair (P to N) | ±5 mil within pair | Skew converts to common-mode noise |
| PCIe lane-to-lane (×4) | ±5 mil (Gen1/2), ±2 mil (Gen3) | Multi-lane deskew buffer has limited range |
| Source-synchronous bus | Match to clock trace ±25 mil | Data must arrive within setup/hold window |

---

## Via Effects

Each via adds:
- ~0.5–1 pF capacitance (stub effect)
- ~0.5–1 nH inductance (barrel + pads)
- Impedance discontinuity (Z₀ drops ~30% at via)

**Mitigations:**
1. Back-drill unused via stubs (essential above 5 Gbps)
2. Use ground vias adjacent to signal vias (return path continuity)
3. Minimize via count — each via adds ~1 dB loss at 10 GHz

---

## Best Practices

1. **Simulate before layout** — HyperLynx, Sigrity, or free tools like SiSoft QCD for pre-layout SI.
2. **Reference plane continuity** — never route high-speed signals across a split plane gap (return current must detour → EMI).
3. **Use ground stitching vias** — every 5–10 mm along differential pairs, add ground vias to maintain common-mode impedance.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Stubs on high-speed vias** | S₁₁ spike at λ/4 frequency | Back-drill or use blind vias |
| **Reference plane gap under diff pair** | Common-mode radiation, fails EMI | Keep solid reference plane under entire route |
| **90° corners (pre-2010 myth)** | Actual problem: impedance change at corner, not the angle | Miter corners or route 45° — but don't obsess over it below 5 Gbps |

---

## References

| Source |
|---|
| Howard Johnson, "High-Speed Digital Design: A Handbook of Black Magic" |
| Eric Bogatin, "Signal and Power Integrity — Simplified" |
| IPC-2152 (Standard for Determining Current-Carrying Capacity) |
| Intel AN 529: High-Speed Board Design Guidelines |
