[← Xilinx/AMD Home](../README.md) · [← Section Home](../../README.md)

# Xilinx UltraScale & UltraScale+ — 20nm & 16nm High-Performance

UltraScale is the second-generation Vivado-native architecture, introducing ASIC-like clocking and routing. UltraScale+ shrinks to 16nm FinFET and integrates HBM memory, quad 64-bit ARM cores, GPU, and video codec in the MPSoC variant.

---

## What Changed from 7-Series

| Feature | 7-series | UltraScale / UltraScale+ |
|---|---|---|
| **LUT** | 6-input, 2 FF per slice | 6-input + 2× 5-LUT fracturable, 8 FF per slice |
| **CLB** | 2 slices (8 LUTs) | **8 slices (32 LUTs)** per CLB — much denser |
| **Block RAM** | 36 Kb | 36 Kb (UltraScale), **288 Kb URAM** added (UltraScale+) |
| **DSP** | DSP48E1 (25×18) | DSP48E2 (27×18, wider accumulator, pre-adder, FP), plus DSP58 in Versal |
| **Clock Routing** | Global + regional BUFG/BUFR | BUFG_GT (ultra-low-jitter), leaf-level clock gating |
| **CARRY8** | CARRY4 per slice | **CARRY8** (8-bit carry chain per slice, 2× faster arithmetic) |
| **URAM** | No | **288 Kb** single-port memory, efficient for deep FIFOs/packet buffers |

---

## UltraScale+ Family (the active high-performance line)

| Family | LEs | Transceivers | PCIe | Key Feature |
|---|---|---|---|---|
| **Kintex UltraScale+** | 356K–1,143K | 16–76× 16.3 Gbps (GTH) or 28.2 (GTY) | Gen3/Gen4 x8 | Balanced performance/dollar |
| **Virtex UltraScale+** | 862K–3,780K | 36–128× 28.2/58 Gbps | Gen4 x16 | Maximum density + HBM on select devices (VU31P/VU33P) |
| **Zynq UltraScale+ MPSoC** | 154K–1,143K | Up to 48× 16.3 Gbps | Gen2 ×4 (PL) + CCIX/PCIe via PS | **Quad Cortex-A53 + dual Cortex-R5**, GPU (Mali-400), VCU (H.264/H.265) |
| **Zynq UltraScale+ RFSoC** | 237K–930K | Up to 48× 28.2 Gbps | Gen3 ×8/×16 | **RF ADCs/DACs** (14-bit, 4–6.5 GSPS, direct sampling to S-band) |
| **HD-Series** | Same fabric | Rad-hard by design | — | Space-grade UltraScale+ for LEO/GEO satellites |

---

## Zynq MPSoC — 64-bit Upgrade Path

Zynq MPSoC is the generational leap from Zynq-7000 (and Cyclone V SoC) to 64-bit ARM:

| Criterion | Zynq-7000 | Zynq MPSoC |
|---|---|---|
| Application CPUs | 2× Cortex-A9 (ARMv7-A) | **4× Cortex-A53** (ARMv8-A 64-bit) |
| Real-time CPUs | None | **2× Cortex-R5** (lockstep or independent) |
| GPU | None | Mali-400 MP2 (OpenGL ES 2.0) |
| Video codec | None | H.264/H.265 encode/decode (VCU) |
| Max LEs | 444K | 1,143K |
| DDR | DDR3/DDR3L | DDR4/LPDDR4 (ECC), 2,400 Mbps |
| eMMC | SD 3.0 | eMMC 5.1 / SD 3.0 |
| Boot security | AES only | RSA (4K) + AES-GCM + SHA-3, secure key storage (eFuse/BBRAM) |

---

## Best Practices

1. **UltraScale+ is the hardware verification target for most ASICs** — Virtex UltraScale+ HBM variants match HBM-capable ASICs in bandwidth for pre-silicon validation.
2. **Use URAM for deep data paths** — 288 Kb URAM blocks are more area-efficient than chained BRAM36s for packet buffers, line buffers, and deep FIFOs.
3. **RFSoC eliminates external ADCs/DACs** — if your design currently uses JESD204B ADC/DAC interface chips, RFSoC can collapse that into the FPGA package.

---

## Development Boards

### AMD / Xilinx (First-Party)

| Board | Family | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **ZCU102 Eval Kit** | Zynq MPSoC XCZU9EG | 600K | Quad A53 + Dual R5F, DDR4, FMC, HDMI, GbE, 16G XCVR | ~$3,495 | General MPSoC development, most popular |
| ZCU104 Eval Kit | Zynq MPSoC XCZU7EV | 504K | Quad A53 + Dual R5F + GPU + VCU, HDMI in/out, DDR4 | ~$1,995 | Video/ML edge dev (has codec) |
| ZCU106 Eval Kit | Zynq MPSoC XCZU7EV | 504K | Full-featured: FMC, QSFP, DDR4, VCU, HDMI, DP | ~$3,195 | Video codec + networking combo |
| **ZCU111 RFSoC Eval Kit** | Zynq RFSoC XCZU28DR | 930K | 8× 4 GSPS ADC + 8× 6.5 GSPS DAC, Quad A53 + Dual R5F | ~$8,995 | Direct RF sampling, 5G/wireless eval |
| ZCU208 RFSoC Eval Kit | Zynq RFSoC XCZU48DR | 930K | 8× 5 GSPS ADC + 8× 10 GSPS DAC, extended bandwidth | ~$12,995 | Higher-bandwidth RF evaluation |
| KCU116 Eval Kit | Kintex US+ XCKU5P | 474K | FMC, DDR4, GbE, QSFP28, 16G XCVR, PCIe Gen3 | ~$3,495 | Kintex UltraScale+ general eval |
| VCU118 Eval Kit | Virtex US+ XCVU9P | 2,586K | FMC ×2, DDR4, QSFP28, GbE, PCIe Gen3 ×16, 28G XCVR | ~$7,995 | High-end Virtex US+ evaluation |
| VCU128 Eval Kit | Virtex US+ XCVU37P | 2,852K | HBM2 8 GB, QSFP-DD, PCIe Gen4 ×16, 58G PAM4 | ~$14,995 | HBM + 58G PAM4 eval |

### Third-Party

| Board | Family | LUTs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Zynqberry** (Trenz) | Zynq MPSoC | 504K | Raspberry Pi form-factor, RPi HAT compatible | ~$400+ | Embedded Linux + FPGA in Pi form-factor |
| UltraZed SoM (Avnet) | Zynq MPSoC | 504K | SODIMM SoM, industrial temp, production-ready | ~$500+ | Production deployment, custom carrier |
| HiTech Global PCIe cards | Virtex/Kintex US+ | up to 2,852K | PCIe Gen3/Gen4 x16, QSFP, DDR4 | ~$5,000+ | Datacenter/telecom accelerator |

### Choosing a Board

| You want... | Get... |
|---|---|
| General Zynq MPSoC development | ZCU102 (~$3,495) — most popular, best documented |
| Video/ML with hardware codec | ZCU104 (~$1,995) or ZCU106 |
| RF direct sampling | ZCU111 RFSoC (~$8,995) |
| Pure FPGA (no CPU), mid-range | KCU116 Kintex US+ (~$3,495) |
| HBM2 + 58G transceivers | VCU128 (~$14,995) |
| Embedded Pi form-factor | Zynqberry |
| Production SoC module | UltraZed SoM |

---

## References

| Source | Path |
|---|---|
| UltraScale+ Data Sheet (DS922–DS926) | AMD/Xilinx documentation |
| Zynq UltraScale+ MPSoC TRM (UG1085) | AMD/Xilinx documentation |
