[← Others Home](../README.md) · [← Section Home](../../README.md)

# Efinix — 40nm/16nm with Over-Provisioned Routing & Open Yosys Flow

Efinix has a fully functional, production-shipping FPGA architecture designed from scratch (2017), not derived from decades-old Altera/Xilinx lineages. Their secret weapon: massively **over-provisioned routing fabric** that lets designs hit 80%+ utilization without timing closure stress.

---

## Trion Family (40nm)

| Device | LUTs | Block RAM | DSP (18×18) | PLL | Price (1K) |
|---|---|---|---|---|---|
| T4 | 4,160 | 452 Kb | 10 | 2 | ~$3 |
| T8 | 7,872 | 932 Kb | 16 | 4 | ~$5 |
| T13 | 12,928 | 1,452 Kb | 24 | 6 | ~$10 |
| T20 | 19,712 | 2,200 Kb | 32 | 4 | ~$18 |

## Titanium Family (16nm)

| Device | LUTs | Block RAM | DSP (18×18) | SERDES | MIPI | PCIe |
|---|---|---|---|---|---|---|
| Ti60 | 62,000 | 2.8 Mb | 120 | 4× 12.5 Gbps | 2× 4-lane D-PHY | Gen3 x4 |
| Ti180 | 180,000 | ~7 Mb | 280+ | up to 16× 12.5 Gbps | 2× 4-lane | Gen3 x4 |

---

## What Makes Eifinix Different — Hybrid Architecture

1. **Logic mapped to LUTs normally** (Yosys/synplify)
2. **Routing is massively over-provisioned** — ~4× more wires than equivalent Intel/Xilinx
3. **Layout uses simulated annealing** — Efinity P&R exploits excess routing for near-trivial placements

Result: a T20 at 80% utilization still closes timing, something nearly impossible on Artix-7 or Cyclone V at that fill level.

---

## Efinix vs Others

| Criterion | Efinix Trion | Gowin LittleBee | Lattice ECP5 |
|---|---|---|---|
| Max LUTs | 20K (T20) | 9K (GW1N-9) | 85K (LFE5U-85F) |
| Open-source | Efinity Yosys flow (Efinix-provided) | Apicula community RE | IceStorm/Trellis (mature) |
| SERDES | Ti60 only | GW5A-25 (6.25G) | ECP5-5G (5G) |
| Tools | Efinity (modern, lightweight, very fast) | Gowin IDE | Radiant or Yosys+PnR |

---

## Development Boards

### Efinix (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Trion T20 BGA324 Dev Kit** | T20F324 | 19,712 | DDR3, GbE, HDMI, USB, GPIO, breadboard-friendly | ~$49 | Best entry-level Efinix, open tool flow |
| Trion T120 BGA576 Dev Kit | T120F576 | 120,000 | DDR3, GbE, HDMI, FMC, QSPI | ~$199 | Larger Trion evaluation |
| **Titanium Ti60 F225 Dev Kit** | Ti60F225 | 62,000 | 16nm, 12.5G SERDES, PCIe Gen3 ×4, MIPI D-PHY ×2, DDR4 | ~$499 | 16nm SERDES + PCIe eval |

### Choosing a Board

| You want... | Get... |
|---|---|
| Best Efinix entry, open tool flow | Trion T20 Kit (~$49) |
| 16nm SERDES + PCIe | Titanium Ti60 Kit (~$499) |
| Larger logic at low cost | Trion T120 Kit (~$199) |

---

## References

| Source | Path |
|---|---|
| Efinix | https://www.efinixinc.com |
