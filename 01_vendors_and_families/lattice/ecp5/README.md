[← Lattice Home](../README.md) · [← Section Home](../../README.md)

# Lattice ECP5 — Open-Source Mid-Range Powerhouse

ECP5 is Lattice's mid-range family with SERDES transceivers, DDR3 memory controllers, and ~20× more logic than iCE40. It powers the ULX3S, OrangeCrab, and Colorlight open-hardware projects. Fully supported by Yosys + nextpnr + Project Trellis.

---

## Specifications

| Feature | ECP5 (LFE5U) | ECP5-5G (LFE5UM5G) |
|---|---|---|
| **LUTs** | 12K–83,840 | 24K–83,840 |
| **SysMEM Block RAM** | 576 Kb–3,735 Kb (18 Kb blocks) | Same |
| **Distributed RAM** | 156 Kb–668 Kb | Same |
| **DSP (sysDSP)** | 28–156 slices (18×18 + 36-bit acc) | Same |
| **PLL/DLL** | 2–4 PLLs + 2 DLLs | Same |
| **SERDES** | None | 4–8 lanes, 5 Gbps per lane |
| **DDR3** | Up to 800 Mbps via soft controller | Same |
| **PCIe** | None (soft core in large devices) | Gen2 ×1/×4 via SERDES |
| **MIPI D-PHY** | Hard IP on some devices | Yes (2× 4-lane) |
| **Package** | caBGA (256–756 balls) | Same |

---

## LUT Architecture

ECP5 uses a **4-input LUT + flip-flop** as the basic logic cell (Programmable Logic Cell, PLC), grouped into slices of 2 PLCs:

```
┌───────── Slice ──────────┐
│  ┌──────┐    ┌──────┐    │
│  │ LUT4 │    │ LUT4 │    │
│  │ + FF │    │ + FF │    │
│  └──┬───┘    └──┬───┘    │
│     └────┬──────┘        │
│          ▼               │
│     carry chain +        │
│     wide mux (MUXF2)     │
└──────────────────────────┘
```

Simpler than Intel's ALM (fracturable 6-LUT) or Xilinx 7-series slice (4× 6-LUTs), the simpler cell structure makes nextpnr's placement algorithms more predictable.

---

## ECP5 vs Entry-Level Competitors

| Criterion | ECP5-85F | Cyclone V (5CSEA5) | Artix-7 (XC7A50T) |
|---|---|---|---|
| Effective LUTs | ~84K | ~85K | ~52K |
| Block RAM | 3,735 Kb | 4,860 Kb (M10K) | 2,700 Kb (36Kb) |
| DSP slices | 156 (18×18) | 174 (18×18) | 120 (25×18 DSP48E1) |
| Transceivers | None (5G: 4× 5G) | None | 4× 6.6G GTX |
| DDR mem | 800 Mbps DDR3 | Hard 400 MHz DDR3 | Soft or MIG IP |
| Dev boards | ULX3S ($65), Colorlight ($8–15) | DE10-Nano ($108) | Arty A7 ($129) |
| Toolchain cost | **Free, open-source** | Quartus Lite (free) | Vivado ML Standard (free, proprietary) |
| Linux + CPU | Soft RISC-V only | Hard dual Cortex-A9 | Hard dual Cortex-A9 (Zynq) |

---

## Development Boards

### Lattice (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **ECP5 Versa Dev Kit** | LFE5UM-85F | 84K | DDR3, GbE, FMC, HDMI, USB, PCIe edge (via 5G SERDES) | ~$499 | Official Lattice eval, full-featured |
| Lattice ECP5 5G VIP Board | LFE5UM5G-85F | 84K | 5G SERDES + MIPI D-PHY, HDMI in/out, DDR3 | ~$399 | Video + transceiver eval |

### Third-Party / Community

| Board | FPGA | LUTs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **ULX3S** | LFE5U-45F/85F | 44K/84K | WiFi+BT (ESP32), SDRAM 32 MB, HDMI, OLED, GPIO, audio, USB | ~$65–125 | Best general ECP5 dev board, open-hardware |
| **OrangeCrab** | LFE5U-25F/85F | 25K/84K | DDR3 SO-DIMM (up to 256 MB), USB DFU bootloader, tiny form-factor | ~$99–199 | DDR3-capable ECP5 in portable form |
| Colorlight i5 | LFE5U-25F | 25K | Repurposed LED driver: GbE, 2× RGMII, 2× DDR3, 5V powered | ~$8–15 | Ultra-cheapest ECP5 board, hackable |
| Colorlight i9 | LFE5U-85F | 84K | Same as i5 but larger FPGA + dual RGMII | ~$25 | Larger ECP5 on a budget |
| ECP5 Evaluation Board | LFE5UM-45F | 44K | DDR3, GbE, HDMI, USB, SWD debug header | ~$149 | Mid-range Lattice reference |
| ButterStick | LFE5UM-85F | 84K | Pmod ×4, RPi header, USB-JTAG, open-hardware | ~$89 | Compact RPi-compatible ECP5 |

### Choosing a Board

| You want... | Get... |
|---|---|
| Best general ECP5 development | ULX3S (~$65–125) |
| Cheapest ECP5 | Colorlight i5 (~$8–15) |
| DDR3 memory with ECP5 | OrangeCrab or Colorlight |
| 5G SERDES evaluation | ECP5 Versa or 5G VIP Board |
| CircleCI open-source workflow | Any with Yosys + nextpnr + Trellis |
| Portable + USB DFU | OrangeCrab |

---

## Pitfall: Trellis Doesn't Cover 100%

Project Trellis documents ~99% of ECP5 bitstream, not 100%. Unknown bits affect only edge features (dynamic partial reconfiguration). For production designs, validate on Lattice Radiant alongside the open flow.

---

## References

| Source | Path |
|---|---|
| Project Trellis | https://github.com/YosysHQ/prjtrellis |
| nextpnr | https://github.com/YosysHQ/nextpnr |
| ECP5 Family Data Sheet | FPGA-DS-02040 |
| ULX3S | https://github.com/emard/ulx3s |
