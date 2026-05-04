[← 12 Open Source Open Hardware Home](../README.md) · [← Initiatives Home](README.md) · [← Project Home](../../../README.md)

# Open-Source EDA Tooling — The FPGA & ASIC Toolchain Survey

A survey of the open-source FPGA and ASIC toolchain ecosystem. These tools form the foundation of every open-source FPGA project — from Yosys synthesis to nextpnr place-and-route to OpenROAD's ASIC flow. Deep dives for specific tools live in [Section 13 — Toolchains](../../13_toolchains/README.md).

---

## Overview

The open-source EDA (Electronic Design Automation) ecosystem has matured from experimental hobby projects to production-capable tools. The Yosys + nextpnr combination now supports three FPGA families (iCE40, ECP5, Gowin) with quality that rivals vendor tools for many designs. The ASIC flow (OpenROAD + OpenLane + SkyWater PDK) has produced multiple tape-outs, including Google's Open MPW shuttle program.

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

| Flow Stage | Tool | Input | Output | Status |
|---|---|---|---|---|
| **Synthesis** | Yosys | Verilog/VHDL | JSON netlist (RTLIL) | Production (iCE40, ECP5) |
| **Place & Route** | nextpnr | JSON netlist + constraints | Routed design | Production (iCE40, ECP5) |
| **Bitstream generation** | IceStorm/Trellis/Apicula | Routed design | FPGA bitstream | Production (iCE40, ECP5) |
| **Simulation** | Verilator / Icarus Verilog | Verilog + testbench | Waveform (FST/VCD) | Production |
| **Formal verification** | SBY (SymbiYosys) | Verilog + properties | Pass/Fail + counterexamples | Production |

---

## Core Open FPGA Tools

| Tool | Function | FPGA Families | Language | Status | License |
|---|---|---|---|---|---|
| **Yosys** | RTL synthesis (Verilog → netlist) | Generic (all families via plugins) | C++ | Mature, production | ISC |
| **nextpnr** | Place-and-route | iCE40, ECP5, Gowin (experimental), Xilinx (WIP) | C++ | iCE40/ECP5: mature; Xilinx: WIP | ISC |
| **Project IceStorm** | iCE40 bitstream documentation & tools | Lattice iCE40 | C/Python | Mature, complete | ISC |
| **Project Trellis** | ECP5 bitstream documentation & tools | Lattice ECP5 | C++/Python | Mature, complete | ISC |
| **Project Apicula** | Gowin bitstream documentation | Gowin GW1N/LittleBee | Python | Usable, maturing | ISC |

### Yosys — The Synthesis Engine

Yosys is the backbone of every open FPGA flow. It reads Verilog (and, via plugins, VHDL, SystemVerilog), performs RTL elaboration, technology mapping, and optimization, and produces a JSON netlist that nextpnr can place and route.

```bash
# Yosys synthesis script for ECP5
yosys -p "read_verilog top.v
           synth_ecp5 -json top.json"
```

| Yosys Pass | Function |
|---|---|
| `read_verilog` | Parse Verilog into RTLIL |
| `hierarchy` | Resolve module hierarchy |
| `proc` | Convert processes to netlists |
| `fsm` | Extract and optimize finite state machines |
| `memory` | Map arrays to BRAM/registers |
| `opt` | Optimization passes (constant folding, dead code elimination) |
| `synth_ecp5` | Technology mapping for ECP5 (LUT + BRAM + DSP) |
| `synth_ice40` | Technology mapping for iCE40 |
| `synth_gowin` | Technology mapping for Gowin |

### nextpnr — The Place-and-Route Engine

nextpnr is a vendor-neutral FPGA place-and-route tool. It reads the JSON netlist from Yosys and produces a placed-and-routed design ready for bitstream generation.

```bash
# nextpnr-ecp5 for ULX3S board
nextpnr-ecp5 --json top.json \
              --textcfg top.config \
              --85k \
              --package CABGA381 \
              --freq 50 \
              --lpf ulx3s.lpf
```

| nextpnr Feature | Detail |
|---|---|
| **Timing-driven** | Respects clock constraints, reports timing violations |
| **Heuristic placement** | Simulated annealing for initial placement, iterative improvement |
| **Router** | A* pathfinding with congestion avoidance |
| **Constraint support** | .lpf (Lattice), .pcf (iCE40) pin constraints |
| **Multi-clock** | Supports multiple clock domains with independent constraints |

---

## Open ASIC Flow

| Tool | Function | Status |
|---|---|---|
| **OpenROAD** | Full RTL-to-GDSII flow (floorplanning, placement, CTS, routing) | Production (SkyWater 130nm) |
| **OpenLane** | OpenROAD-based automated flow (used with SkyWater/GF PDKs) | Production |
| **Magic** | VLSI layout editor, DRC checking | Mature |
| **Netgen** | LVS (Layout vs Schematic) comparison | Mature |
| **KLayout** | GDSII viewer and editor | Mature |

### Open PDKs (Process Design Kits)

| PDK | Node | Notes |
|---|---|---|
| **SkyWater 130nm** | 130 nm | First open-source foundry PDK (Google-sponsored), used in MPW shuttles |
| **IHP SG13G2** | 130 nm SiGe BiCMOS | For RF/mixed-signal designs |
| **GF180MCU** | 180 nm | GlobalFoundries open PDK for MCU-class designs |
| **ASAP7** | 7 nm (predictive) | Academic predictive PDK, not for real tape-out |

---

## Simulation & Verification

| Tool | Type | Speed vs Icarus | Language | Notes |
|---|---|---|---|---|
| **Verilator** | Compiled cycle-accurate | 10–100× faster | C++ | Best for large designs, no timing-accurate simulation |
| **Icarus Verilog** | Interpreted event-driven | Baseline | C++ | Most compatible, slow for large designs |
| **Cocotb** | Python cosimulation | Depends on backend | Python | Write testbenches in Python, uses Verilator/Icarus as backend |
| **SBY (SymbiYosys)** | Formal verification | N/A | Python/Yosys | Prove properties, find counterexamples |

---

## Tool Comparison: Open vs Vendor

| Capability | Open (Yosys + nextpnr) | Xilinx (Vivado) | Intel (Quartus) |
|---|---|---|---|
| **Supported families** | iCE40, ECP5, Gowin (partial) | All Xilinx | All Intel |
| **Synthesis quality** | Good (smaller designs) | Excellent | Excellent |
| **Timing closure** | Basic (no multi-corner) | Full (multi-corner, incremental) | Full |
| **DSP inference** | ✅ Basic | ✅ Full (DSP48 inference) | ✅ Full |
| **BRAM inference** | ✅ Full | ✅ Full | ✅ Full |
| **IP integration** | Manual (no IP catalog) | Vivado IP catalog | Quartus IP catalog |
| **Build time** | 1–5 minutes | 10–60 minutes | 10–60 minutes |
| **License cost** | Free | Free (WebPACK) to $3,000+ | Free (Lite) to $5,000+ |

---

## Deep Dives

For detailed installation, constraint syntax, and workflow guides:

- **[Open Source Flow](../../13_toolchains/open_source_flow.md)** — Practical guide: Yosys → nextpnr → bitstream, Makefile examples
- **[Vivado](../../13_toolchains/vivado.md)** / **[Quartus](../../13_toolchains/quartus.md)** — Proprietary tool guides in Section 13

---

## When to Use / When NOT to Use Open EDA Tools

### When to Use

- **Lattice iCE40 or ECP5** — the open tools are production-quality for these families
- **Reproducible builds** — Yosys + nextpnr produce deterministic bitstreams (unlike vendor tools)
- **CI/CD pipelines** — no license server needed; run synthesis in GitHub Actions
- **Learning FPGA design** — no vendor tool installation hassle; `apt install yosys nextpnr-ecp5`

### When NOT to Use

- **Xilinx Ultrascale+ or Intel Stratix** — the open tools don't support these families
- **Timing-critical designs** — open tools lack multi-corner timing analysis and incremental compilation
- **Production designs needing vendor IP** — open tools have no equivalent of Xilinx MIG or Intel EMIF
- **Large designs (>50K LUTs on Xilinx)** — nextpnr-xilinx is not ready; use Vivado

---

## Best Practices

1. **Use a Makefile** — standardize your build flow: `make synth`, `make pnr`, `make prog`
2. **Pin constraints in .pcf/.lpf** — keep pin assignments separate from RTL; they change per board
3. **Use Verilator for simulation** — it's 10–100× faster than Icarus Verilog for RTL simulation
4. **Use SBY for formal verification** — prove your CDC logic, FIFO pointers, and state machines are correct
5. **Version your bitstream** — commit the Yosys + nextpnr versions alongside your RTL; different versions can produce different bitstreams

---

## Antipatterns

- **The Vendor Tool on Lattice** — using Diamond or Radiant when Yosys + nextpnr is available; the open tools are faster and more reproducible
- **The Open Tool on Xilinx Ultrascale+** — trying to use nextpnr-xilinx for a production design on Ultrascale+; it's not ready
- **The No-Constraint Design** — running nextpnr without pin constraints; the resulting bitstream will have random pin assignments

---

## Pitfalls

1. **Yosys SystemVerilog support is limited** — Yosys supports a subset of SystemVerilog via the `read_verilog -sv` flag; complex SV features (classes, interfaces, packages) may not work
2. **nextpnr timing reports are approximate** — the open tools report STA results, but they're not as accurate as vendor STA; always verify timing on real hardware
3. **Gowin open tools are still maturing** — Apicula + nextpnr-gowin work for basic designs but may fail on complex ones; the Gowin EDU IDE is more reliable
4. **No incremental compilation** — open tools recompile the entire design every time; there's no equivalent of Vivado's incremental synthesis
5. **VHDL support requires a plugin** — Yosys can read VHDL via the GHDL plugin, but it requires separate installation and configuration

---

## Use Cases

- **Hobbyist FPGA development** — Yosys + nextpnr on iCE40/ECP5 boards
- **CI/CD for FPGA** — deterministic, license-free builds in automated pipelines
- **ASIC prototyping** — OpenROAD + SkyWater PDK for tape-out preparation
- **Education** — no vendor license management, fast build times, open-source analysis tools

---

## References

- [Yosys (GitHub)](https://github.com/YosysHQ/yosys)
- [nextpnr (GitHub)](https://github.com/YosysHQ/nextpnr)
- [Project IceStorm (GitHub)](https://github.com/YosysHQ/icestorm)
- [Project Trellis (GitHub)](https://github.com/YosysHQ/prjtrellis)
- [Project Apicula (GitHub)](https://github.com/YosysHQ/apicula)
- [Verilator (GitHub)](https://github.com/verilator/verilator)
- [Cocotb (GitHub)](https://github.com/cocotb/cocotb)
- [OpenROAD (GitHub)](https://github.com/The-OpenROAD-Project/OpenROAD)
- [OpenLane (GitHub)](https://github.com/The-OpenROAD-Project/OpenLane)
- [SkyWater 130nm PDK](https://github.com/google/skywater-pdk)
- [Section 13 — Toolchains](../../13_toolchains/README.md) — detailed tool guides
- [FOSSi & CHIPS Alliance](fossi_chips_alliance.md) — the organizations behind these tools
