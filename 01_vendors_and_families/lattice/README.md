[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-C — Lattice Semiconductor

The champion of open-source FPGA toolchains. Lattice's iCE40 and ECP5 families have fully open-source synthesis and placement flows (Yosys + nextpnr), making them the de facto choice for community-driven hardware projects. Founded in 1983, Lattice occupies the low-to-mid-range sweet spot: ultra-low-power iCE40 (<1 mW standby), open-source powerhouse ECP5 (up to 85K LUTs with 5G SERDES), and the newer 28nm FD-SOI Nexus platform (CrossLink-NX, CertusPro-NX) with 3× lower soft-error rate than bulk CMOS competitors.

---

## Why Lattice Matters

Lattice is the only major FPGA vendor with **first-class open-source toolchain support** — not reverse-engineered, but published bitstream documentation (Project Icestorm for iCE40, Project Trellis for ECP5) enabling Yosys+nextpnr flows that rival the proprietary tools. This has made Lattice the backbone of:

- **Open hardware boards**: iCEBreaker, ULX3S, OrangeCrab, TinyFPGA, Colorlight
- **Retro computing FPGA cores**: many MiSTer alternatives target ECP5
- **LiteX SoC builder**: first-class Lattice board support
- **Education**: cheap boards ($8 Upduino) with complete open toolchain

---

## Technology Platforms

| Platform | Process | Families | Key Features |
|---|---|---|---|
| **iCE40** | 40nm LP | iCE40LP/HX/UltraPlus | Ultra-low power, hardened MIPI D-PHY (UP5K), 1K–8K LUTs, fully open Icestorm |
| **ECP5** | 40nm | LFE5U/UM/UM5G | Mid-range workhorse, 12K–85K LUTs, DDR3, 5G SERDES (UM5G), fully open Trellis |
| **Nexus (FD-SOI)** | 28nm | CrossLink-NX, CertusPro-NX, Avant | 3× lower SER, 2× lower static power vs bulk CMOS, hard MIPI, PCIe Gen3 |
| **MachXO** | 130nm/65nm/40nm | MachXO2, MachXO3 | Non-volatile flash, instant-on, limited open-source support |

---

## Family Directories

| Directory | Coverage |
|---|---|
| [ice40/](ice40/README.md) | **iCE40** — ultra-low-power open-source pioneer (Project Icestorm). UP5K sweet spot: 5,280 LUTs, 8 DSP, MIPI D-PHY, $8–12 boards (Upduino, iCEBreaker). FPGA viewers, sensors, low-speed glue |
| [ecp5/](ecp5/README.md) | **ECP5** — open-source mid-range powerhouse (Project Trellis). Up to 85K LUTs, 5G SERDES, DDR3, ULX3S, Colorlight, OrangeCrab boards. ECP5 vs Cyclone V vs Artix-7 comparison |
| [crosslink_nx/](crosslink_nx/README.md) | **CrossLink-NX** — 28nm FD-SOI with hard MIPI CSI/DSI. 17K–40K LUTs, LPDDR4, 3× lower soft error rate, 2× lower static power vs ECP5. Embedded vision, edge AI |
| [certuspro_nx/](certuspro_nx/README.md) | **CertusPro-NX** — scaled FD-SOI: 96K LUTs, PCIe Gen3 ×4, 10.3 Gbps SERDES, large RAM blocks. Industrial, bridging, protocol conversion |

---

## Family Comparison

| Family | Process | LUTs (max) | SERDES | Key Differentiator | Board Price |
|---|---|---|---|---|---|
| **iCE40 UP5K** | 40nm | 5,280 | None | Fully open, MIPI D-PHY, <1 mW standby | $8–50 |
| iCE40 HX | 40nm | 7,680 | None | Higher density no-MIPI variant | $15–30 |
| **ECP5-85F** | 40nm | 84K | None | Best open-source density/dollar | $30 (Colorlight) |
| ECP5-85UM5G | 40nm | 84K | 5 Gbps (×4) | Open source + SERDES | $150 (ULX3S) |
| **CrossLink-NX** | 28nm FD-SOI | 40K | 2.5 Gbps | Hard MIPI, low SER, instant-on | $50–200 |
| **CertusPro-NX** | 28nm FD-SOI | 96K | 10.3 Gbps | PCIe Gen3, highest Nexus density | $200–500 |
| MachXO3 | 40nm | 9.4K | None | Non-volatile, instant-on, limited open support | $20–100 |
| Avant | 16nm | ~500K | 25 Gbps | Higher-end platform, PCIe, fast SERDES | $500+ |

---

## Development Board Highlights

| Board | Family | Key Spec | Price | Best For |
|---|---|---|---|---|
| **iCEBreaker** | iCE40 UP5K | 5K LUTs, Pmod, open-source debugger, USB | ~$69 | iCE40 learning & prototyping |
| Upduino 3.1 | iCE40 UP5K | 5K LUTs, breadboard-friendly, 3-LED | ~$8 | Cheapest open-source FPGA entry |
| TinyFPGA BX | iCE40 LP8K | 8K LUTs, USB bootloader, tiny form | ~$38 | Breadboard FPGA projects |
| **ULX3S** | ECP5-85F | 84K LUTs, HDMI, USB, ESP32 WiFi/BT, SD | ~$110 | Most capable open-source FPGA board |
| Colorlight 5A-75B | ECP5-55F | 55K LUTs, GbE ×2, $15 on Aliexpress | ~$15 | Cheapest ECP5, LED panel driver repurposed |
| **OrangeCrab** | ECP5-85F | 84K LUTs, DDR3, 128MB flash, Feather form | ~$100 | Portable ECP5 dev, LiteX target |
| ButterStick | ECP5-85UM5G | 84K LUTs, 5G SERDES, SYZYGY, GbE | ~$300 | Open-source SERDES development |
| CrossLink-NX Eval | CrossLink-NX-40 | 40K LUTs, 2× MIPI CSI, 2× MIPI DSI | ~$200 | Embedded vision prototyping |

---

## Best Practices

1. **iCE40 UP5K for ultra-low-power and open-source-first** — if the design fits in 5K LUTs, no other FPGA gives you a complete open toolchain at this power and price point.
2. **ECP5 for open-source mid-range** — 85K LUTs with open-source Yosys+nextpnr. The ULX3S is the most capable fully-open FPGA development board available.
3. **CrossLink-NX when MIPI is mandatory** — hardened MIPI CSI/DSI at up to 2.5 Gbps/lane. Saves fabric LUTs vs soft MIPI implementations on ECP5.
4. **CertusPro-NX for PCIe bridging on FD-SOI** — only Lattice family with PCIe Gen3 ×4 in a low-SER FD-SOI package.
5. **MachXO3 for non-volatile glue logic** — instant-on flash, no external configuration, reliable for board management.

## Pitfalls

1. **iCE40 HX ≠ UP5K** — HX has no SPRAM, no MIPI, no RGB drivers. The UP5K is almost always the right iCE40 for new designs.
2. **ECP5 SERDES is limited (5 Gbps)** — Lattice's ECP5 transceivers max out at 5 Gbps. For 10G+ you need CertusPro-NX or another vendor.
3. **Radiant vs Diamond toolchain split** — Nexus families (CrossLink-NX, CertusPro-NX) require Radiant. ECP5 and iCE40 work in both Diamond and Radiant. Radiant is the forward path.
4. **Lattice toolchains are Windows-first** — Linux support exists but lags. Diamond/Radiant on Linux has more rough edges than Vivado or Quartus.
5. **ECP5 open-source P&R isn't timing-closed by default** — nextpnr-ecp5 is great for exploration but may require manual constraint tuning to meet tight timing. Treat timing closure as a verify-in-Diamond step.

---

## References

| Source | Description |
|---|---|
| Lattice Documentation | https://www.latticesemi.com/en/Products/FPGAandCPLD |
| Project Icestorm (iCE40) | https://github.com/YosysHQ/icestorm — complete open-source iCE40 flow |
| Project Trellis (ECP5) | https://github.com/YosysHQ/prjtrellis — complete open-source ECP5 flow |
| nextpnr | https://github.com/YosysHQ/nextpnr — open-source place-and-route for iCE40, ECP5, Nexus |
| ULX3S Board | https://github.com/emard/ulx3s — flagship open-source ECP5 board |
| LiteX ECP5 support | https://github.com/enjoy-digital/litex — SoC builder with first-class ECP5 targets |
