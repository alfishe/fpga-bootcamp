[← 09 Board Design Home](README.md) · [← Project Home](../../README.md)

# Thermal Design — Keeping Your FPGA Alive

FPGAs burn power — and that power becomes heat. A modern high-end FPGA (Virtex UltraScale+, Agilex 7) can dissipate 40–100 W. Without adequate thermal management, junction temperature (Tⱼ) exceeds the rated maximum (typically 85–100°C commercial, 125°C industrial) and the device enters thermal shutdown, degrades over time, or fails outright.

---

## The Thermal Problem in One Equation

\[T_J = T_A + (P \times \theta_{JA})\]

Where:
- **Tⱼ** = Junction temperature (°C) — the number you must keep below spec
- **Tₐ** = Ambient temperature (°C) — inside the enclosure, not room temperature
- **P** = Total power dissipation (W) — static + dynamic
- **θⱼₐ** = Junction-to-ambient thermal resistance (°C/W) — depends on package, heatsink, airflow

**Example:** Kintex-7 410T at 15 W, no heatsink, θⱼₐ = 6.5 °C/W (FFG-900 still air):
\[T_J = 45°C + (15 \times 6.5) = 142.5°C\]
That's over the 100°C commercial limit. **You need a heatsink.**

---

## Power Dissipation: Where Does the Heat Come From?

| Source | Contribution | How to estimate |
|---|---|---|
| **Static power** (leakage) | 10–30% of total | Vendor power estimator (XPE, EPE). Increases with Tⱼ (~2× per 30°C rise) |
| **Dynamic power (logic)** | 40–60% | \(P_{dyn} = \frac{1}{2} C V^2 f \times \text{toggle-rate}\) |
| **Dynamic power (DSP)** | 10–20% | Per-tile power × number of DSPs used × toggle rate |
| **Transceivers** | 5–15% | ~0.5–1.5 W per GTY/GTH channel at max rate |
| **I/O (DDR, LVDS)** | 5–10% | Termination power + driver current × voltage swing |
| **Hard IP (PCIe, 100G MAC)** | 2–5% | Fixed per block (vendor datasheet) |

**Practical rule:** After place-and-route, export power report → multiply by 1.2× for margin (routing congestion increases dynamic power beyond estimation).

---

## Thermal Resistance: Understanding θ Values

```
Junction (Tⱼ)
    │
    ▼ θⱼₑ (junction-to-case top) — typically 0.1–0.5 °C/W for FPGAs
Case Top
    │
    ▼ TIM (thermal interface material) — 0.05–0.3 °C/W for good grease/pads
Heatsink Base
    │
    ▼ θₛₐ (heatsink-to-ambient) — 1–20 °C/W depending on size, fins, airflow
Ambient (Tₐ)
```

| Parameter | What It Means | Where to Find It |
|---|---|---|
| θⱼₑ | Junction-to-case (top) | FPGA datasheet thermal section |
| θⱼₑ_ᵦₒₜₜₒₘ | Junction-to-case (bottom) | For bottom-side cooling through PCB vias |
| θⱼₐ (still air) | No heatsink, no airflow | Datasheet — worst-case baseline |
| θⱼₐ (with airflow) | Depends on LFM (linear feet/minute) | Heatsink vendor curve |

---

## Cooling Methods — When to Use What

| Method | θⱼₐ Range | Power Budget | Cost | FPGA Families |
|---|---|---|---|---|
| **No heatsink** | 5–20 °C/W | <3 W | $0 | ICE40, CrossLink-NX, GW1N, MAX 10 |
| **PCB copper pour only** | 15–30 °C/W | <2 W | $0 (just copper) | LQFP packages (MAX 10, LittleBee QFP) |
| **Stick-on heatsink** | 8–15 °C/W | 3–8 W | $0.50–2 | Artix-7, Cyclone V, ECP5 |
| **Heatsink + airflow (200 LFM)** | 2–6 °C/W | 8–25 W | $5–20 | Kintex-7, Zynq-7045, Arria 10 |
| **Heatsink + fan (400+ LFM)** | 0.5–2 °C/W | 25–60 W | $15–50 | Virtex-7, Stratix 10, UltraScale+ KU |
| **Active fan + heat pipe** | 0.2–0.8 °C/W | 60–100 W | $50–150 | Virtex UltraScale+, Agilex 7 |
| **Liquid cooling** | 0.05–0.3 °C/W | 100+ W | $200–1000+ | VU47P, multi-FPGA systems |

---

## Thermal Vias — PCB as Heatsink

For BGAs without topside heatsink access (or as secondary path):

| Parameter | Recommendation |
|---|---|
| Via diameter | 0.2–0.3 mm (8–12 mil) |
| Via pitch | 1.0–1.2 mm grid under FPGA footprint |
| Via plating | 25 μm (1 mil) Cu minimum |
| Via fill | Conductive epoxy fill or Cu-plugged (better) |
| Target θⱼₐ improvement | 15–30% reduction vs no thermal vias |

**Vendor guidance:** Xilinx UG440 recommends thermal vias under exposed pad packages. Intel AN 788 covers thermal via design for Stratix series.

---

## Vendor-Specific Thermal Specs

| FPGA Family | Max Tⱼ (Commercial) | Max Tⱼ (Industrial) | Typical θⱼₑ (°C/W) | Package Notes |
|---|---|---|---|---|
| Artix-7 (FTG256) | 85°C | 100°C | 4.0 | Small BGA, passive cooling viable |
| Kintex-7 (FFG900) | 85°C | 100°C | 0.31 | Large BGA, heatsink recommended >10 W |
| Zynq-7000 (CLG484) | 85°C | 100°C | 4.0 | CPU+FPGA — worst-case is both active |
| Cyclone V (F484) | 85°C | 100°C | 4.0 | Similar to Artix-7 |
| Cyclone V SoC (U672) | 85°C | 100°C | 3.2 | HPS + FPGA simultaneously → derate |
| ECP5 (csBGA285) | 85°C | 100°C | 12.0 | Small package, poor thermal path — limit to <3 W |

**SoC derating rule:** When both HPS and FPGA are near full utilization, derate max ambient by 10–15°C vs FPGA-only operation at the same chip.

---

## Practical Workflow

1. **Estimate power before synthesis** — use Xilinx XPE (Excel-based) or Intel EPE (Early Power Estimator)
2. **Post-PAR power report** — after place-and-route, export SAIF/VCD switching activity for accurate dynamic power
3. **Calculate Tⱼ** using worst-case Tₐ (enclosure temperature, not room ambient)
4. **Select cooling** based on Tⱼ < Tⱼ_ᴍᴀx with 10°C margin
5. **Verify with thermal camera** during prototype bring-up — the first power-on should include a FLIR measurement

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| **"It's only an Artix-7, no heatsink needed"** | Artix-7 at 85% utilization can hit 8 W. Without heatsink, Tⱼ can exceed 100°C. |
| **Using CPU TDP as FPGA power estimate** | CPU TDP is an average. FPGA dynamic power is toggle-rate dependent — a crypto workload can double power vs estimation. |
| **Ignoring enclosure ambient** | 25°C room → 45°C inside sealed enclosure. Your Tⱼ calculation must use enclosure Tₐ. |
| **Not measuring in final enclosure** | Open-air bench testing gives false thermal confidence. The enclosure traps heat. |
| **Relying on vendor power estimator alone** | XPE/EPE are early estimates. Post-PAR power can be 30% higher. Always verify with hardware. |

---

## References

- Xilinx UG440: Power Analysis and Optimization Guide
- Intel AN 788: Thermal Management for Intel FPGAs
- JEDEC JESD51: Thermal measurement standards (θⱼₐ, θⱼₑ definitions)
- IPC-2152: Standard for determining current-carrying capacity in printed board design
