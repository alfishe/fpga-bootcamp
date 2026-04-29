[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Open-Source FPGA Toolchain — Yosys, nextpnr, and the Open Flow

The open-source FPGA toolchain has matured from a curiosity to a production-capable flow for select device families. Yosys (synthesis) + nextpnr (place & route) + Project Trellis/IceStorm (bitstream) provide a fully open, scriptable, CI-friendly alternative to vendor tools.

---

## Toolchain Components

```
RTL (Verilog/VHDL) → Yosys → Netlist → nextpnr → Bitstream → openFPGALoader → FPGA
                        │                    │               │
                    Synthesis           Place & Route     Programming
```

| Tool | Role | Replaces |
|---|---|---|
| **Yosys** | RTL synthesis → netlist | Vivado Synthesis, Quartus Map, Synplify |
| **nextpnr** | Place & Route → bitstream | Vivado Implementation, Quartus Fitter |
| **Project IceStorm** | iCE40 bitstream documentation + tools | Lattice Diamond (for iCE40) |
| **Project Trellis** | ECP5 bitstream documentation + tools | Lattice Diamond (for ECP5) |
| **nextpnr-xilinx** | Xilinx 7-series P&R (experimental) | Vivado (for Artix-7, Zynq) |
| **nextpnr-gowin** | Gowin P&R (experimental) | Gowin EDA |
| **openFPGALoader** | JTAG programming | Vivado HW Manager, Quartus Programmer |
| **F4PGA (SymbiFlow successor)** | Multi-architecture umbrella | Vendor tools for multiple families |

---

## Device Support Matrix

| Family | Synthesis | P&R | Bitstream | Maturity |
|---|---|---|---|---|
| **iCE40 (LP/HX/UP)** | Yosys ✓ | nextpnr-ice40 ✓ | IceStorm ✓ | Production-ready |
| **ECP5** | Yosys ✓ | nextpnr-ecp5 ✓ | Project Trellis ✓ | Production-ready |
| **Xilinx 7-series** | Yosys ✓ | nextpnr-xilinx ✓ | Project X-Ray ✓ | Experimental (limited IO/clock support) |
| **Gowin GW1N/GW2A** | Yosys ✓ | nextpnr-gowin ✓ | Project Apicula ✓ | Experimental |
| **MachXO2** | Yosys ✓ | nextpnr-machxo2 WIP | — | Early development |
| **Cyclone V** | No | No | No | Not supported |
| **UltraScale+** | No | No | No | Not supported |

---

## Quick Start (ECP5)

```bash
# Synthesis
nix-shell -p yosys
yosys -p "synth_ecp5 -json top.json" top.v

# Place & Route (ECP5 85F on ULX3S)
nextpnr-ecp5 --json top.json --textcfg top.config \
  --85k --package CABGA381 --lpf constraints.lpf

# Bitstream generation
ecp5 --textcfg top.config top.bit

# Program
openFPGALoader -b ulx3s top.bit
```

---

## Best Practices

1. **Start with open-source-supported hardware** — iCE40 (iCEBreaker) or ECP5 (ULX3S, OrangeCrab) for guaranteed tool flow.
2. **Vendor tools for timing closure, open tools for CI** — vendor P&R still produces better QoR. Use open tools for fast CI iteration; vendor for final timing closure.
3. **Check F4PGA for Xilinx experiments** — F4PGA is the spiritual successor to SymbiFlow and the best path for open-source Xilinx flow.

## References

| Source | URL |
|---|---|
| Yosys Manual | https://yosyshq.readthedocs.io/ |
| nextpnr | https://github.com/YosysHQ/nextpnr |
| Project Trellis (ECP5) | https://github.com/YosysHQ/prjtrellis |
| Project IceStorm (iCE40) | https://github.com/YosysHQ/icestorm |
| F4PGA | https://f4pga.org/ |
| openFPGALoader | https://github.com/trabucayre/openFPGALoader |
