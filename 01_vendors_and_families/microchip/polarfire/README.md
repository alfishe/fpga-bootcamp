[← Microchip Home](../README.md) · [← Section Home](../../README.md)

# Microchip PolarFire — 28nm Flash-Based FPGA & RISC-V SoC

PolarFire is Microchip's current-generation mid-range family on 28nm SONOS non-volatile process. The SoC variant integrates **five hard RISC-V CPU cores** — unique in the industry. Flash-based configuration means instant-on (<1 ms), SEU immunity, and near-zero standby power.

---

## Why Non-Volatile FPGA?

| Property | SRAM FPGA (Intel, Xilinx, Lattice) | Microchip Flash FPGA |
|---|---|---|
| **Config storage** | External QSPI flash chip | Internal SONOS flash |
| **Boot time** | 50–500 ms | **<1 ms** (live at power-on) |
| **SEU immunity** | Prone (SRAM cell flips in radiation) | **Immune** (flash cell doesn't disturb) |
| **Standby power** | High (SRAM leakage) | Near-zero |
| **Live-at-power-up IO** | No (tri-stated until configured) | Yes |
| **Bitstream security** | Encryption (key in eFuse/Battery RAM) | **Inherent** — no external bitstream to intercept |
| **Reprogramming endurance** | Unlimited SRAM (flash wears) | 500–1,000 cycles |

---

## PolarFire FPGA-Only

| Device | LEs (4-LUT+FF) | Math Blocks (18×18) | LSRAM | SERDES | PCIe |
|---|---|---|---|---|---|
| MPF100T | 109K | 336 | 336 blocks | 4–8 (12.7 Gbps) | Gen2 x4 |
| MPF200T | 192K | 616 | 616 blocks | 8–16 | Gen2 x4/x8 |
| MPF300T | 300K | 924 | 952 blocks | 16–24 | Gen2 x8 |
| MPF500T | 482K | 1,500+ | 1,500+ + 72 Mb eSRAM | 4–24 | Gen2 x8 |

LEs are **4-LUT + FF** (like Lattice ECP5, Gowin LittleBee). No HBM on FPGA-only variants.

---

## PolarFire SoC — Five RISC-V Hard Cores

```
┌──────────── PolarFire SoC Die ────────────┐
│  ┌──────────────────────────────────┐     │
│  │     RISC-V CPU Complex            │     │
│  │  U54-1 U54-2 U54-3 U54-4 E51    │     │
│  │  └────────┬─────────────┘        │     │
│  │           ▼                       │     │
│  │     AXI4 Bus Matrix (128-bit)     │     │
│  │   L2 Cache 2 MB (shared)         │     │
│  │   DDR4/LPDDR4 Ctrl (2,133 Mbps)  │     │
│  └──────────────────┬───────────────┘     │
│                     │                      │
│  ┌──────────────────▼───────────────────┐ │
│  │        FPGA Fabric (PolarFire)        │ │
│  │        100K–460K LEs, SERDES, PCIe   │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

| CPU | Architecture | Purpose |
|---|---|---|
| **U54-MC (×4)** | RV64IMAFDC, 667 MHz | Linux-capable application cores, FPU, MMU |
| **E51 Monitor** | RV64IMAC, 667 MHz | Boot, system monitor, debug |

---

## PolarFire SoC vs Cyclone V SoC

| Criterion | Cyclone V (5CSEA6) | PolarFire SoC (MPFS) |
|---|---|---|
| CPU | 2× Cortex-A9 (32-bit ARMv7) | 4× U54 + 1× E51 (64-bit RISC-V) |
| CPU freq | 800 MHz | 667 MHz |
| L2 cache | 512 KB shared | 2 MB shared |
| FPGA LEs | 110K | 100K–460K |
| SERDES | None (SE variant) | 12.7 Gbps |
| Boot time | ~500 ms | <1 ms instant-on |
| Power | ~5W | ~1.5W |
| Toolchain | Quartus Lite (free) | Libero SoC (free for MPFS) |

> 📖 **Deep Dive:** [PolarFire SoC RISC-V Architecture](soc/README.md) — MSS block diagrams, 5-core RISC-V cluster (U54×4 + E51), coherent-by-default AXI4 switch, FIC0/FIC1/FIC2 fabric interfaces, HSS boot flow, RISC-V PLIC interrupt architecture, and vs-ARM comparison table.

---

## RT PolarFire — Radiation-Tolerant for Space

| Feature | Standard PolarFire | RT PolarFire |
|---|---|---|
| TID (Total Ionizing Dose) | <15 Krad | >100 Krad |
| SEE immunity | Flash-based (good) | No SEL up to LET >63 MeV-cm²/mg |
| Temperature | 0°–85°C | −40°–125°C |

---

## When to Choose Microchip

| Your constraint | Pick |
|---|---|
| 24/7 operation in high-radiation environment | RT PolarFire or SmartFusion2 |
| Must boot in microseconds from power-up | Any PolarFire / IGLOO2 |
| <2W total board power | PolarFire or SmartFusion2 |
| Need 5× RISC-V Linux CPUs on one FPGA | **PolarFire SoC** — unique |
| FIPS 140-2 / Common Criteria required | SmartFusion2 |
| Cost-sensitive | Gowin or Lattice, not Microchip |
| Open-source tools desired | Lattice ECP5, not Microchip |

---

## Best Practices

1. **Plan around flash endurance** — 500 reliable reprogramming cycles. Enough for prototyping, not for daily reconfiguration over a 2-year development cycle.
2. **U54 cores run Linux, E51 boots you** — E51 monitor core initializes the system, then boots U54 application cores. Don't try to use U54 directly.
3. **Libero is free but scripting is TCL-heavy** — the GUI is inferior to Vivado/Quartus; expect manual TCL workflows.

---

## Development Boards

### Microchip (First-Party)

| Board | FPGA Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **PolarFire FPGA Eval Kit** | MPF300T-1FCG1152 | 300K | PCIe Gen2 ×4, DDR4, FMC, GbE, QSPI, UART via USB | ~$499 | Best general PolarFire eval |
| **PolarFire SoC Icicle Kit** | MPFS250T-FCVG484 | 254K | 4× U54 + 1× E51 RISC-V, PCIe Gen2, DDR4, GbE, mikroBUS, Raspberry Pi header | ~$499 | RISC-V Linux SoC FPGA eval |
| PolarFire SoC Discovery Kit | MPFS095T-FCSG325 | 95K | 4× U54 + 1× E51 RISC-V, mikroBUS, Raspberry Pi header, USB-powered | ~$132 | Lowest-cost RISC-V SoC FPGA entry |

### Third-Party

| Board | FPGA Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Avalanche (Future Electronics)** | MPF300T | 300K | PCIe ×4 card, FMC, DDR4, QSFP, industrial use-cases | ~$1,000+ | PCIe accelerator deployment |
| Sundance V3 SoM | MPFS250T | 254K | SODIMM SoC module, DDR4, GbE, production-ready | ~$600+ | Production embedded RISC-V deployment |

### Choosing a Board

| You want... | Get... |
|---|---|
| General PolarFire FPGA evaluation | PolarFire Eval Kit (~$499) |
| RISC-V Linux SoC development | PolarFire SoC Icicle Kit (~$499) |
| Cheapest RISC-V SoC FPGA | PolarFire SoC Discovery Kit (~$132) |
| PCIe accelerator card | Avalanche (Future Electronics) |
| Production SoC module | Sundance V3 SoM |

---

## References

| Source | Path |
|---|---|
| PolarFire FPGA Data Sheet | DS0145 |
| PolarFire SoC Data Sheet | DS0146 |
| PolarFire SoC User Guide | UG0820 |
| RT PolarFire Data Sheet | DS00004005 |
| Mi-V RISC-V ecosystem | https://www.microchip.com/en-us/products/fpgas-and-plds/ip-cores/miv-risc-v |
