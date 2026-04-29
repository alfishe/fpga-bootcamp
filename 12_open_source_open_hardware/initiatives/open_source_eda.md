[← 12 Open Source Open Hardware Home](../README.md) · [← Initiatives Home](README.md) · [← Project Home](../../../README.md)

# Open-Source EDA Tooling

A brief survey of the open-source FPGA/ASIC toolchain ecosystem. Deep dives for specific tools live in [Section 13 — Toolchains](../../13_toolchains/README.md).

---

## The Open FPGA Flow

```
RTL (Verilog/VHDL) ──► Yosys ──► JSON netlist ──► nextpnr ──► bitstream
                                       │
                         ┌─────────────┴──────────────┐
                         │                            │
                   nextpnr-ice40               nextpnr-ecp5
                   (Lattice iCE40)             (Lattice ECP5)
                         │                            │
                    nextpnr-gowin              nextpnr-xilinx
                    (Gowin, experimental)      (Xilinx, experimental)
```

## Core Open FPGA Tools

| Tool | Function | FPGA Families | Status |
|---|---|---|---|
| **Yosys** | RTL synthesis (Verilog → netlist) | Generic (all families via plugins) | Mature, production |
| **nextpnr** | Place-and-route | iCE40, ECP5, Gowin (experimental), Xilinx (WIP) | iCE40/ECP5: mature; Xilinx: WIP |
| **Project IceStorm** | iCE40 bitstream documentation & tools | Lattice iCE40 | Mature, complete |
| **Project Trellis** | ECP5 bitstream documentation & tools | Lattice ECP5 | Mature, complete |
| **Project Apicula** | Gowin bitstream documentation | Gowin GW1N/LittleBee | Usable, maturing |

## Open ASIC Flow (for reference)

| Tool | Function |
|---|---|
| **OpenROAD** | Full RTL-to-GDSII flow (floorplanning, placement, CTS, routing) |
| **OpenLane** | OpenROAD-based automated flow (used with SkyWater/GF PDKs) |
| **SkyWater 130nm PDK** | First open-source foundry PDK (Google-sponsored) |
| **IHP SG13G2** | Open-source SiGe BiCMOS PDK (130nm, for RF/mixed-signal) |
| **GF180MCU** | GlobalFoundries 180nm open PDK |

## Deep Dives

For detailed how-to, installation, constraint syntax, and workflow guides:

- **[Open Source Flow](../../13_toolchains/open_source_flow.md)** — Practical guide: Yosys → nextpnr → bitstream, Makefile examples
- **[Vivado](../../13_toolchains/vivado.md)** / **[Quartus](../../13_toolchains/quartus.md)** — Proprietary tool guides in Section 13

## Planned Content

- Detailed technical coverage to be expanded as tools evolve.

## Referenced By

- [README.md](README.md)
