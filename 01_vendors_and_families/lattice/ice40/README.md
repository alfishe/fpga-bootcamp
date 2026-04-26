[← Lattice Home](../README.md) · [← Section Home](../../README.md)

# Lattice iCE40 — Ultra-Low-Power Open-Source Pioneer

The iCE40 was the first FPGA family with a fully open-source toolchain (Project Icestorm, 2015). It is tiny, cheap, and designed for always-on, battery-powered applications. The complete toolchain is auditable:

```
RTL (Verilog/VHDL)
│
├─► Yosys — open-source synthesis
├─► nextpnr — open-source place & route
├─► Project Icestorm — bitstream documentation (reverse-engineered)
├─► iceprog — open-source programming
│
└─► Bitstream loaded to SRAM or external flash
```

---

## Family Variants

| Sub-family | LUTs | Block RAM | PLLs | DSP | Notes |
|---|---|---|---|---|---|
| **iCE40LP** | 640–7,680 | 64 Kb–128 Kb | 1–2 | None | Lowest power, smallest packages (UCSP16 → QFN48) |
| **iCE40HX** | 640–7,680 | 64 Kb–128 Kb | 1–2 | None | Higher performance variant of LP |
| **iCE40 Ultra** | 1,760–3,520 | 64 Kb–96 Kb | 1 | None | Integrated SPI/I2C hard IP, RGB LED drivers |
| **iCE40 UltraPlus** | 2,800–5,280 | 128 Kb–1,080 Kb | 2 | 4–8 DSP (16-bit) | **Most capable iCE40**: 1 Mb SPRAM, DSP, dual MIPI D-PHY |

---

## iCE40 UltraPlus (UP5K) — The Sweet Spot

| Feature | Specification |
|---|---|
| **LUTs** | 5,280 |
| **BRAM (EBR)** | 30 blocks × 4 Kb = 120 Kb |
| **SPRAM** | 4 blocks × 128 Kb = 512 Kb scratchpad |
| **DSP** | 8 multipliers (16×16) |
| **PLL** | 2 |
| **MIPI D-PHY** | 2 lanes, up to 900 Mbps |
| **Package** | SG48 (QFN48, 7×7mm) — hand-solderable |
| **Boards** | iCEBreaker ($69), TinyFPGA BX ($38), Upduino ($8–12) |

The iCE40UP5K is the $8–$12 FPGA that's completely open-source and fits in a QFN package that can be hand-assembled with a hot-air gun. No other FPGA at this price point has comparable toolchain freedom.

---

## What iCE40 Can't Do

| Constraint | Reason |
|---|---|
| No multi-gigabit transceivers | Pure GPIO (LVDS up to ~540 Mbps via DDR) |
| No hard CPU | Can barely fit PicoRV32 (1,300–2,000 LUTs) |
| No external DDR | Only on-chip SRAM + QSPI PSRAM via soft controller |
| Max 8 DSP blocks | No 27×27 mode, no pre-adder, no cascade chains |
| 2.5V core only | No dynamic voltage scaling |

---

## Pitfall: PLL Configuration Limits

The open-source iCE40 PLL flow cannot synthesize all mathematically possible frequency combinations. Check `icepll -q` before designing around a specific clock frequency.

---

## Development Boards

### Lattice (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **iCE40 UltraPlus Breakout Board** | iCE40UP5K | 5,280 | MIPI D-PHY, 512 KB SPRAM, DSP ×8, USB programmer on-board | ~$49 | Official Lattice UP5K eval |
| iCE40HX1K Breakout Board | iCE40HX1K | 1,280 | Pmod headers, USB programmer, breadboard-friendly | ~$29 | Entry-level Lattice eval |

### Third-Party / Community

| Board | FPGA | LUTs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **iCEBreaker** | iCE40UP5K | 5,280 | Pmod ×2, RPi header, USB-serial + USB-JTAG onboard, open-hardware | ~$69 | Best all-around UP5K dev board |
| **TinyFPGA BX** | iCE40LP8K | 7,680 | USB bootloader, tiny form-factor (18×36 mm), open-hardware | ~$38 | Ultra-portable, USB-powered |
| **Upduino** | iCE40UP5K | 5,280 | Minimalist bare board, USB-JTAG onboard, breadboard header | ~$8–12 | Cheapest iCE40, large-volume hobbyist |
| Fomu | iCE40UP5K | 5,280 | USB-A plug form-factor, fits in USB port, open-hardware | ~$30 | FPGA in a USB dongle |
| Alchitry Cu | iCE40HX4K | 3,520 | Alchitry ecosystem (Br/Al/Au shields), breadboard-compatible | ~$50 | Education, modular expansion system |
| BlackIce MX | iCE40HX4K | 3,520 | Arduino form-factor, PSRAM, microSD, HDMI-compatible header | ~$50 | Arduino FPGA + storage |
| OrangeCrab (ice40) | iCE40UP5K | 5,280 | DDR3L 128 MB via soft controller, USB DFU boot | ~$59 | DDR3-capable iCE40 |

### Choosing a Board

| You want... | Get... |
|---|---|
| Best all-around iCE40 dev board | iCEBreaker (~$69) |
| Cheapest possible | Upduino (~$8–12) |
| Ultra-portable, USB-powered | TinyFPGA BX (~$38) |
| Official Lattice eval | iCE40UP5K Breakout (~$49) |
| Education + shields | Alchitry Cu (~$50) |
| FPGA-in-a-dongle | Fomu (~$30) |

---

## References

| Source | Path |
|---|---|
| Project Icestorm | https://github.com/YosysHQ/icestorm |
| iCE40 Family Data Sheet | DS1048 |
