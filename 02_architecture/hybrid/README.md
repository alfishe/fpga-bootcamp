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

---

## Reference Development Boards

### RFSoC Platforms

| Board | Vendor | Price Range | RF Specs | Best For |
|---|---|---|---|---|
| **ZCU111** | Xilinx / Avnet | ~$8,000 | 8× ADC 4 GSPS, 8× DAC 6.4 GSPS, Gen 1 | 5G NR sub-6 GHz, research |
| **ZCU216** | Xilinx / Avnet | ~$12,000 | 16× ADC 5 GSPS, 16× DAC 9.85 GSPS, Gen 3 | Radar, EW, wideband SDR |
| **ZCU208** | Xilinx / Avnet | ~$10,000 | 8× ADC 5 GSPS, 8× DAC 9.85 GSPS, Gen 3 | T&M, spectrum analysis |
| **RFSoC Explorer** | Avnet | ~$6,000 | ZCU111-based, pre-loaded RF toolkit | Education, rapid RF prototyping |

> **RFSoC pricing:** These boards include precision RF front-end components (clock synthesis, baluns, filters) that represent a significant portion of the cost. The bare RFSoC silicon is available separately for custom board designs.

### AI Engine / Versal Platforms

| Board | Vendor | Price Range | AI Engine Specs | Best For |
|---|---|---|---|---|
| **VCK190** | Xilinx / Avnet | ~$12,000 | VC1902, 400 AI Engines, INT8/FP32 | AI inference, computer vision |
| **VEK280** | Xilinx / Avnet | ~$15,000 | VE2802, video codec, 8K capable | Automotive, broadcast |
| **VHK158** | Xilinx / Avnet | ~$20,000 | VH1582, 32 GB HBM2e, HPC | Genomics, financial modeling |

### HBM-Integrated FPGA Platforms

| Board | Vendor | Price Range | HBM Specs | Best For |
|---|---|---|---|---|
| **Stratix 10 MX Dev Kit** | Intel | ~$10,000 | 2× HBM2 stacks, 512 GB/s | AI training, HPC |
| **VHK158** | Xilinx / Avnet | ~$20,000 | 32 GB HBM2e, 820 GB/s | Graph analytics, simulation |
| **BittWare S10-MX** | BittWare | Contact | Stratix 10 MX, 3U VPX | Military SIGINT |

> **HBM note:** HBM dev kits are premium platforms targeting data center and HPC applications. For evaluation, Intel and Xilinx both offer cloud-based FPGA instances (AWS F1, Azure NP-series) with HBM-equipped devices.
