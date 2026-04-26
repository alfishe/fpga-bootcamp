[← Section Home](../README.md) · [← Project Home](../../README.md)

# 02-D — Hybrid: Specialized On-Die Compute & Analog

Beyond CPU + FPGA, some architectures integrate specialized compute engines (AI processor arrays, GPU tiles) or analog blocks (RF DACs/ADCs, MIPI PHYs) directly on the FPGA die. These are not "FPGA + CPU" — they're FPGA + specialized domain-specific silicon.

## Index

| File | Topic |
|---|---|
| [rf_direct_sampling.md](rf_direct_sampling.md) | RF ADC/DAC integration: Xilinx RFSoC architecture, direct RF sampling (4-6.5 GSPS), JESD204B/C elimination, Nyquist zones |
| [ai_engine_arrays.md](ai_engine_arrays.md) | AI compute integration: Xilinx Versal AI Engine (VLIW SIMD, 400-tile arrays), Intel Agilex AI Tensor Blocks, Achronix MLP |
| [hbm_integration.md](hbm_integration.md) | High-Bandwidth Memory: HBM2/HBM2e stack integration, Intel Stratix 10 MX / Agilex M-Series, Xilinx Virtex UltraScale+ HBM, bandwidth vs DDR5 |

---

## Why a Separate Folder?

These architectures don't fit in "soc/" because:
- **No general-purpose CPU required** — RFSoC and Versal AI Core can operate with or without ARM cores
- **Analog + digital co-design** — RF converters require mixed-signal verification, clock jitter budget, thermal management
- **Compute paradigm shift** — AI Engines and HBM are streaming-dataflow architectures, not instruction-fetch machines
- **Vendor-specific** — these are unique to Xilinx (RFSoC, AIE), Intel (AI Tensor, HBM), Achronix (MLP), not cross-vendor patterns

## RFSoC: FPGA + Direct RF Sampling

The RFSoC collapses the RF signal chain into the FPGA package:

```
Traditional:  ADC Chip → JESD204B SerDes → FPGA → Processing
RFSoC:        Antenna → Direct Sampling (4 GSPS) → FPGA DSP
```

No external ADC/DAC chips. No JESD204B link. No board-level RF layout. Everything from antenna to DSP happens on one package.

## Versal AI Engine: FPGA + Processor Array

```
┌─────────── Versal AI Core ──────────────┐
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ AIE  │ │ AIE  │ │ ...  │ │ AIE  │   │
│  │Tile 0│ │Tile 1│ │      │ │Tile N│   │
│  └──┬───┘ └──┬───┘ └──────┘ └──┬───┘   │
│     │        │                 │        │
│  ┌──┴────────┴─────────────────┴────┐   │
│  │        AXI4-Stream NoC            │   │
│  └─────────────┬────────────────────┘   │
│                │                         │
│  ┌─────────────┴────────────────────┐   │
│  │   Adaptable Engines (FPGA)       │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

400 AI Engine tiles × 1.25 GHz × 8 FP32 MACs/tile = ~4 TFLOPS on-die. This is GPU-class compute integrated with FPGA fabric, not a soft accelerator built from LUTs.
