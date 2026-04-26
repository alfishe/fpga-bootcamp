[← Xilinx/AMD Home](../README.md) · [← Section Home](../../README.md)

# Xilinx Versal — 7nm Adaptive Compute Acceleration Platform (ACAP)

Versal is Xilinx's most radical architecture shift since the invention of the FPGA. It integrates **AI Engines** (arrays of VLIW SIMD vector processors), a hard **NoC** (Network-on-Chip), scalar ARM processors, and adaptive logic on a single die.

---

## Tile Architecture

```
┌────────────── Versal Premium Die ──────────────┐
│  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Scalar Engines   │  │ Adaptable Engines    │  │
│  │ Dual A72 + R5F   │  │ (Programmable Logic) │  │
│  └────────┬────────┘  └──────────┬──────────┘  │
│           │                      │              │
│  ┌────────▼──────────────────────▼──────────┐   │
│  │         Network-on-Chip (NoC)             │   │
│  │   AXI4-based, 2D mesh, QoS, 2+ Tbps     │   │
│  └──┬──────────────┬──────────────────┬─────┘   │
│     │              │                  │          │
│  ┌──▼──────┐  ┌────▼────────┐  ┌─────▼──────┐   │
│  │ AI Eng. │  │DDR/HBM Ctrl│  │GTY/GTM XCVR│   │
│  │400 tiles│  │DDR4-3200   │  │112G PAM4    │   │
│  └─────────┘  └─────────────┘  └────────────┘   │
└──────────────────────────────────────────────────┘
```

---

## AI Engine — The Heart of Versal

Each AI Engine tile contains:

| Unit | Capability |
|---|---|
| **Vector processor** | VLIW SIMD, 512-bit vector, 4-way superscalar |
| **Scalar processor** | 32-bit RISC, program control |
| **Local memory** | 32 KB data, 16 KB program |
| **Stream switch** | AXI4-Stream interconnect to adjacent tiles + NoC |
| **Floating point** | FP32 vector (native), FP16/BF16/INT8 for ML |
| **Throughput** | 8 FP32 MACs/cycle ≈ 10 GOPS at 1.25 GHz |

400 AI Engine tiles deliver **~4 TFLOPS FP32** or **~100 TOPs INT8**. This is the same class of compute as a mid-range GPU, but on the same die as programmable logic.

---

## Versal Family Variants

| Series | Focus | AI Engines | Scalar CPU | DSP Engines | Use |
|---|---|---|---|---|---|
| **Versal Prime** | Baseline ACAP | None or few | Dual A72 + Dual R5F | DSP58 (27×24) | General SoC+, FPGA replacement |
| **Versal AI Core** | AI acceleration | 64–400 tiles (1–4 TFLOPS) | Dual A72 + Dual R5F | DSP58 | Streaming AI inference, radar, 5G |
| **Versal AI Edge** | Embedded AI | 8–64 tiles | Dual A72 + Dual R5F | DSP58 | ADAS, embedded vision, drone |
| **Versal Premium** | High-speed networking | 0–128 tiles | Dual A72 + Dual R5F | DSP58 | 112G PAM4, 400G/800G Ethernet, PCIe Gen5 |
| **Versal HBM** | Compute + memory | AI Engines | Dual A72 | DSP58 | HBM2e (32 GB+), high-bandwidth compute |

---

## Xilinx vs Intel — Generation Comparison

| Generation | Xilinx | Intel | Key Difference |
|---|---|---|---|
| 28nm workhorse | **7-series** (2010–) | **Cyclone V / Arria V** (2011–) | Xilinx has more transceiver options; Intel has hard DDR controller on Arria V |
| SoC tier | **Zynq-7000** | **Cyclone V SoC** | Zynq has ACP (coherent FPGA cache access); CV SoC has F2S bridges |
| 20nm generation | **UltraScale** (Kintex/Virtex) | **Arria 10** | Xilinx has denser CLB (8 slices vs ALM); Intel has HyperFlex routing on Stratix only |
| 16/14nm | **UltraScale+** (16nm) | **Stratix 10** (14nm) | Both deliver HBM, Gen4 PCIe, 28G/58G XCVR |
| 64-bit ARM SoC | **Zynq MPSoC** (A53, GPU, VCU) | **Stratix 10 SoC** (A53, no GPU) | Xilinx has integrated GPU+codec; Intel SoC focuses on fabric density |
| Latest platform | **Versal** (7nm ACAP + AIE) | **Agilex 7** (Intel 7 chiplet) | Xilinx has AI Engine tile array (stream compute); Intel puts AI tensor ops in DSP blocks |

---

## Best Practices

1. **Versal AI Engine requires a pure dataflow mental model** — the AIE tile processor grids are not like ARM cores or FPGA fabric. They are streaming directed-graph nodes with non-blocking writes.
2. **NoC replaces AXI interconnect fabric** — don't hand-route AXI buses on Versal; use the NoC compiler.
3. **Versal requires Vivado/Vitis paid license** — Vivado ML Standard Edition does **not** support Versal (same licensing constraint as Intel Agilex).

---

## Development Boards

### AMD / Xilinx (First-Party)

| Board | Series | AI Engines | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **VCK190 Eval Kit** | Versal AI Core VC1902 | 400 tiles | Quad A72 + Dual R5F, DDR4, FMC, QSFP28, PCIe Gen4 ×8 | ~$12,495 | Full Versal AI Engine evaluation (4 TFLOPS) |
| **VEK280 Eval Kit** | Versal AI Edge VE2802 | 32 tiles | Dual A72 + Dual R5F, LPDDR4, HDMI, MIPI, PCIe Gen4 | ~$3,995 | Embedded AI vision eval |
| VP1802 Eval Kit | Versal Premium VP1802 | None | 112G PAM4, QSFP-DD, PCIe Gen5, DDR4, 400G/800G Eth | ~$19,995 | High-speed networking eval |
| VMK180 Eval Kit | Versal Prime VM1802 | None | Dual A72 + Dual R5F, DDR4, FMC, QSFP28, PCIe Gen4 | ~$7,995 | General Versal Prime evaluation |

### Third-Party

| Board | Series | AI Engines | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **HiTech Global** PCIe cards | Versal AI Core/Premium | up to 400 | PCIe Gen4/Gen5 ×16, QSFP-DD, DDR4, production form-factor | ~$10,000+ | Production 400G network card |

### Choosing a Board

| You want... | Get... |
|---|---|
| Full AI Engine evaluation (4 TFLOPS) | VCK190 (~$12,495) |
| Embedded AI/vision at lower cost | VEK280 (~$3,995) |
| 112G PAM4 + 400G/800G networking | VP1802 Premium (~$19,995) |
| General Versal evaluation without AI Engines | VMK180 (~$7,995) |
| Production deployment | HiTech Global or custom PCB |
| Note: all require Vivado/Vitis paid license | Budget for software (~$3K+/yr) |

---

## References

| Source | Path |
|---|---|
| Versal ACAP Architecture Manual (AM011) | AMD/Xilinx documentation |
| Versal AI Engine Architecture | AMD/Xilinx documentation |
