[← 02 Architecture Home](../README.md) · [← Hybrid Home](README.md) · [← Project Home](../../../README.md)

# RF Direct Sampling — RF ADC/DAC Integration on FPGA Die

Traditional FPGA-based RF systems require external ADC/DAC chips connected via JESD204B/C serial links. RFSoC architecture collapses the entire RF signal chain into the FPGA package — ADCs and DACs sit on the same silicon interposer as the FPGA fabric.

---

## Why Direct RF Sampling Changes Everything

```
Traditional:  Antenna → LNA → Mixer → IF Amp → ADC Chip → JESD204B → FPGA → DSP
                                      ↑ Local Oscillator

RFSoC:        Antenna → LNA → Direct RF ADC → FPGA DSP
                                  (on-die)
```

Eliminating external ADC/DAC chips removes:
- **JESD204B/C links** — multi-gigabit serial links with complex determinism requirements
- **Board-level RF layout** — impedance-controlled differential pairs at >10 GHz
- **Clock distribution** — sample-clock fanout with <100 fs jitter across multiple converters
- **Power** — 2–5W per external converter chip eliminated

---

## Xilinx RFSoC Generations

| Gen | Family | Max ADC Rate | Max DAC Rate | ADC Count | Process | Year |
|---|---|---|---|---|---|---|
| **Gen 1** | Zynq UltraScale+ RFSoC (ZU2x) | 4.096 GSPS | 6.554 GSPS | 8–16 | 16nm | 2017 |
| **Gen 2** | Zynq UltraScale+ RFSoC (ZU4x) | 5.0 GSPS | 9.85 GSPS | 16 | 16nm | 2019 |
| **Gen 3** | Zynq UltraScale+ RFSoC (ZU6x) | 5.0 GSPS | 10.0 GSPS | 16 | 16nm | 2020 |
| **Gen 4** | Versal AI RF | 8.0 GSPS (planned) | 16.0 GSPS | 16–32 | 7nm | 2025+ |

---

## ADC Architecture

### RF-ADC Block Diagram

```
Analog In ──→ [Balun] ──→ [VGA] ──→ [Track & Hold] ──→ [Pipeline ADC]
                                                              │
                                              ┌───────────────┘
                                              ▼
                              [Digital Down-Converter (DDC)]
                              ├─ NCO (Numerically Controlled Oscillator)
                              ├─ Mixer (I/Q)
                              ├─ Decimation (÷2, ÷4, ÷8, ÷16)
                              └─ AXI4-Stream Output → FPGA Fabric
```

| Parameter | Gen 1 | Gen 2/3 |
|---|---|---|
| **Resolution** | 12-bit | 14-bit |
| **SFDR** | 75 dBc at 1.8 GHz | 80 dBc at 2 GHz |
| **ENOB** | 9.5–10.5 bits | 10.5–11.5 bits |
| **Input bandwidth** | 4 GHz (-3 dB) | 6 GHz (-3 dB) |
| **Input impedance** | 100 Ω differential | 100 Ω differential |
| **Full-scale input** | 1.0 Vpp differential | 1.0 Vpp differential |

### Nyquist Zones & Frequency Planning

At 4 GSPS, the Nyquist frequency is 2 GHz. But the analog input bandwidth extends to 4 GHz, enabling direct sampling in the 2nd Nyquist zone (2–4 GHz). A DDC with NCO applies digital mixing to bring the signal of interest to baseband.

**Key constraint:** Aliasing from higher-order Nyquist zones folds noise into the band of interest. Input anti-alias filtering is still required, but at a much higher frequency than traditional IF sampling.

---

## DAC Architecture

### RF-DAC Block Diagram

```
AXI4-Stream ← [Digital Up-Converter (DUC)] ← [Interpolation] ← [RF-DAC Core]
     │              ├─ NCO                        ├─ ×2, ×4, ×8         │
     │              └─ Mixer (I/Q)                └─ ×16, ×32           │
     │                                                                 │
     └─────────────────── FPGA Fabric ─────────────────────────────────┘
                                                                      Analog Out
```

| Parameter | Gen 1 | Gen 2/3 |
|---|---|---|
| **Resolution** | 14-bit | 14-bit |
| **Max sample rate** | 6.554 GSPS | 9.85/10.0 GSPS |
| **SFDR** | 70 dBc at 1 GHz | 75 dBc at 2 GHz |
| **Output power** | -5 dBm (no external amp) | -3 dBm |
| **Output impedance** | 100 Ω differential | 100 Ω differential |

---

## Clocking — The Critical Path

RF converter performance is dominated by sample clock quality:

| Parameter | Requirement | Why |
|---|---|---|
| **Clock jitter** | <100 fs RMS (10 kHz – 100 MHz) | Jitter directly limits SNR: SNR = -20·log₁₀(2π·f_in·t_jitter) |
| **Phase noise** | <-150 dBc/Hz at 1 MHz offset (at 4 GHz carrier) | Avoids reciprocal mixing of close-in blockers |
| **Multi-chip sync** | <1 sample deterministic latency | Required for phased-array beamforming |
| **Reference** | External 10 MHz or on-board OCXO | GPS-disciplined for coherent multi-board systems |

**RFSoC clock distribution:** The on-die PLL (`RF-PLL`) synthesizes the sample clock from a lower-frequency reference. External clocking via `SYSREF` (JESD204B-style) ensures multi-converter and multi-chip determinism.

---

## Use Cases

| Application | Band | Converters Used | Why RFSoC |
|---|---|---|---|
| **5G NR RU (Radio Unit)** | Sub-6 GHz (n77/n78/n79) | 8× ADC + 8× DAC | Direct RF eliminates external converters, saves 50% BOM |
| **Phased-Array Radar** | X-band (8–12 GHz) | 16× ADC (Gen 3) | Multi-chip sync enables 64+ element digital beamforming |
| **Electronic Warfare (EW)** | 0.1–18 GHz | 16× ADC + DAC | Wideband spectrum monitoring, 4 GHz IBW per channel |
| **Cable/DSL Access** | DOCSIS 3.1/4.0 | 8× DAC | Full-band digital pre-distortion (DPD) in FPGA fabric |
| **Quantum Computing Control** | 4–8 GHz | 8× DAC | Phase-coherent multi-tone generation for qubit control |

---

## Best Practices

1. **Clock jitter budget first** — model the clock chain end-to-end. A 100 fs RMS jitter at 4 GHz limits SNR to 52 dB regardless of ADC resolution.
2. **DDC/DUC use saves fabric** — the hardened digital down/up-converters eliminate FPGA DSP consumption for frequency translation.
3. **Thermal management is non-negotiable** — 8× ADC + 8× DAC on Gen 3 can dissipate 15–25W for the converter block alone.
4. **Plan Nyquist zone upfront** — sampling at 2nd or 3rd Nyquist zone changes anti-alias filter requirements dramatically.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Poor clock jitter** | SNR 5–10 dB below datasheet | Use dedicated low-jitter clock synth (LMK04828, HMC7044); route REFCLK as differential, length-matched |
| **ADC input overdrive** | Clipping, harmonics, permanent damage | Ensure input signal never exceeds 1.0 Vpp; use external attenuator if uncertain |
| **DDC decimation too aggressive** | Aliasing into band of interest | Ensure decimation ratio keeps output bandwidth ≥ 2× signal bandwidth (Nyquist at output rate) |
| **Multi-chip sync drift** | Phase wanders between boards | Use SYSREF with deterministic latency; GPS-discipline the 10 MHz reference |
| **Thermal runaway** | Converters shut down, reduced SFDR | Active cooling mandatory; monitor on-die temperature via SYSMON |

---

## References

| Source | Path |
|---|---|
| Zynq UltraScale+ RFSoC Data Sheet (DS926) | Xilinx / AMD |
| RFSoC RF Data Converter IP LogiCORE (PG269) | Xilinx / AMD |
| ZCU111 Evaluation Board User Guide (UG1271) | Xilinx / AMD |
| RFSoC Clocking Design Guide (UG1433) | Xilinx / AMD |
| JESD204B/C Survival Guide | Analog Devices |
| LMK04828 Ultra-Low Jitter Clock Synthesizer | Texas Instruments |
