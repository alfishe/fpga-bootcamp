[← Section Home](../README.md) · [← Project Home](../../README.md)

# 02-A — Fabric: Programmable Logic

The FPGA fabric is the programmable logic that distinguishes an FPGA from a fixed-function ASIC. This folder covers the atomic building blocks and how they connect.

## Index

| File | Topic |
|---|---|
| [luts_and_clbs.md](luts_and_clbs.md) | LUT architecture (4-input, 6-input, fracturable), CLB/ALM/Slice structure, carry chains, flip-flops, distributed RAM |
| [bram_and_uram.md](bram_and_uram.md) | Block RAM architectures: 18Kb/36Kb/20Kb variants, dual-port modes, byte-write enables, ECC, URAM for UltraScale+ |
| [dsp_slices.md](dsp_slices.md) | DSP48/DSP58/18x18 multiplier-accumulator architecture, cascading, pipelining, pattern detect, SIMD modes |
| [routing.md](routing.md) | Interconnect architecture, long lines, direct connections, switch matrices, congestion, pipelining routes |

---

## Reference Development Boards (Pure FPGA)

This folder covers architecture blocks shared across all FPGAs. For vendor-specific development boards, see the family guides below. Pure FPGA boards (no hard CPU) are typically lower cost and focus on programmable logic exploration.

### Entry-Level Pure FPGA Boards

| Board | Vendor | FPGA Family | Price Range | Best For |
|---|---|---|---|---|
| **Basys 3** | Digilent | Artix-7 | ~$150 | Education, Verilog/VHDL learning |
| **Nexys A7** | Digilent | Artix-7 | ~$300 | Prototyping, microblaze soft CPU |
| **DE0-CV** | Terasic | Cyclone V | ~$150 | Education, Intel Quartus practice |
| **iCEstick** | Lattice | iCE40 | ~$30 | Ultra-low power, open-source tools |
| **ECP5 Evaluation Board** | Lattice | ECP5 | ~$150 | SerDes, DDR3, open-source (yosys/nextpnr) |
| **Tang Nano 9K** | Sipeed / Gowin | GW1NR-9 | ~$20 | Hobbyists, RISC-V soft core |

> **Note:** Pure FPGA boards are ideal for learning fabric architecture (LUTs, BRAM, DSP, routing) without the complexity of a hard processor system. For SoC boards with integrated ARM/RISC-V cores, see [soc/](../soc/README.md).
