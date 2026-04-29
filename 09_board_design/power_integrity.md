[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# Power Integrity — FPGA Power Delivery Network (PDN) Design

FPGA core current can swing from 0A to 10A+ in nanoseconds. Without a well-designed Power Delivery Network (PDN), the voltage at the die droops below spec, causing bit errors, timing failures, and mysterious resets. PDN design is about keeping the FPGA's supply impedance low from DC to the maximum transient frequency.

---

## FPGA Power Rails

| Rail | Typical Voltage | Current (small FPGA) | Current (large FPGA) | Notes |
|---|---|---|---|
| **VCCINT (core)** | 0.85–1.1V | 1–3A | 20–100A | Highest current, tightest tolerance (±3%) |
| **VCCAUX (auxiliary)** | 1.8V | 0.2–0.5A | 1–3A | Configuration, JTAG, PLLs |
| **VCCIO (I/O banks)** | 1.2/1.5/1.8/2.5/3.3V | 0.1–1A per bank | 0.1–2A per bank | Multiple rails (one per voltage standard) |
| **VCCBRAM** | 0.85–1.0V | 0.1–0.5A | 1–5A | Some FPGAs combine with VCCINT |
| **MGTAVCC (transceiver)** | 0.9–1.0V | 0.5–1A | 3–10A | Low-noise analog supply |
| **MGTAVTT (transceiver term)** | 1.2V | 0.2–0.5A | 1–3A | Termination voltage |

---

## PDN Impedance Budget

```
Z_target = (V_rail × %ripple) / I_transient_max

Example: VCCINT = 1.0V, ripple = 3%, I_transient = 10A
Z_target = (1.0 × 0.03) / 10 = 3 mΩ
```

The PDN must present <3 mΩ impedance from DC to ~100 MHz (the frequency content of a 1 ns current step).

| Frequency Range | What Dominates Z | Solution |
|---|---|---|
| DC – 10 kHz | Voltage regulator (VRM) | Proper regulator selection, remote sense |
| 10 kHz – 1 MHz | Bulk capacitors | Tantalum/polymer 100–470 µF near VRM |
| 1 MHz – 100 MHz | Ceramic decoupling caps | MLCC 0.1–10 µF, low ESL, placed at FPGA balls |
| 100 MHz – 1 GHz | On-die capacitance + package | Built into FPGA die/package — you can't add more |

---

## Decoupling Capacitor Selection

| Capacitor Type | Capacitance Range | ESL | Best For |
|---|---|---|---|
| **MLCC X7R (0402)** | 0.01–1 µF | ~0.3 nH | High-frequency decoupling (best: reverse-geometry 0306) |
| **MLCC X7R (0603)** | 0.1–10 µF | ~0.5 nH | Mid-frequency |
| **MLCC X7R (0805)** | 1–47 µF | ~0.8 nH | Bulk-ish decoupling |
| **Tantalum Polymer** | 47–470 µF | ~2–5 nH | Bulk capacitance |
| **OSCON / Aluminum Polymer** | 100–1000 µF | ~3–10 nH | VRM output bulk |

**Placement priority:** Put the smallest-value, lowest-ESL caps closest to FPGA power balls. The 100 nF 0402 cap at the ball is 100× more effective at 100 MHz than a 100 µF tantalum 2 cm away.

---

## Best Practices

1. **Use vendor PDN tool** — Xilinx Power Design Manager (PDM), Intel PDN Tool. They account for package parasitics specific to your FPGA.
2. **Place caps on the opposite side of the board, directly under FPGA** — minimizes via inductance (loop area).
3. **Multiple vias per capacitor pad** — one via adds ~0.5 nH; two vias in parallel halve it.
4. **Power plane over ground plane** — the inter-plane capacitance provides ~100 pF/in² of "free" high-frequency decoupling.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Over-relying on one large bulk cap** | Voltage droops under transient load | Bulk caps have high ESL; they can't respond in <1 µs. Add MLCCs near FPGA |
| **Wrong capacitor dielectric** | Y5V/Z5U caps lose 80% capacitance at temperature/DC bias | Use X7R or X5R; derate by 50% for DC bias effect |
| **Ignoring power sequencing** | FPGA latch-up or permanent damage | Follow vendor sequencing: VCCINT first, then VCCAUX, then VCCIO |

---

## References

| Source |
|---|
| Xilinx UG440: Power Management |
| Intel AN 727: Power Sequencing Requirements |
| Istvan Novak, "Power Distribution Network Design" |
| KEMET MLCC DC Bias Derating Tool |
