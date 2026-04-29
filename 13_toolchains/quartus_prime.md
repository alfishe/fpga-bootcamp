[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Intel Quartus Prime — Design Suite for Cyclone, Arria, Stratix, Agilex

Quartus Prime is Intel/Altera's design environment for all FPGA families from MAX 10 through Agilex. The "Prime" branding (since v15.1) distinguishes it from the older "Quartus II" (v13.1 and earlier, Cyclone IV and prior).

---

## Editions

| Edition | Devices Supported | Cost |
|---|---|---|
| **Quartus Prime Lite** | Cyclone V, Cyclone 10 LP, MAX 10 | Free |
| **Quartus Prime Standard** | Arria V/GZ/10, Stratix V, Cyclone 10 GX | Paid (~$3,000+) |
| **Quartus Prime Pro** | Agilex 5/7/9, Stratix 10, Arria 10 (advanced features) | Paid (~$4,000+) |

**For DE10-Nano/MiSTer:** Quartus Prime Lite is sufficient — Cyclone V is fully supported.

---

## Key Tools in Quartus Prime

| Tool | Executable | Purpose |
|---|---|---|
| **Platform Designer** (formerly Qsys) | GUI within Quartus | Drag-and-drop SoC assembly: CPU, bridges, peripherals, IP |
| **Analysis & Synthesis** | `quartus_map` | RTL → technology-mapped netlist |
| **Fitter** | `quartus_fit` | Place & Route |
| **Assembler** | `quartus_asm` | Generate .sof programming file |
| **Timing Analyzer** (TimeQuest) | `quartus_sta` | SDC-based static timing analysis |
| **SignalTap II** | GUI (`quartus_stp` for Tcl) | On-chip logic analyzer |
| **Programmer** | `quartus_pgm` | JTAG programming, flash writing |
| **Power Analyzer** | `quartus_pow` | Post-fit power estimation |
| **EDA Netlist Writer** | `quartus_eda` | Export netlist for Questa/ModelSim, Synplify |

---

## Platform Designer (Qsys)

Platform Designer replaced SOPC Builder in Quartus II 13.0. It assembles SoC subsystems from IP cores:

- **HPS (Hard Processor System)** — instantiate Cyclone V/Arria 10 HPS with DDR, bridges, peripherals
- **Nios II/V soft CPU** — parameterized soft processor
- **AXI/Avalon interconnect** — auto-generated bus fabric
- **IP library** — DDR controllers (UniPHY/EMIF), PCIe, Ethernet, SPI, I2C, UART, etc.

Output: `.qsys` file → generates HDL + IP constraint files.

---

## Quartus Version Notes

| Version | Key Feature |
|---|---|
| **Quartus Prime 24.x** | Latest; Agilex 5/7 support, improved synthesis |
| **Quartus Prime 21.x** | Last with Cyclone V Lite Edition support (stable) |
| **Quartus Prime 18.x** | Last widely used for Cyclone V; good MiSTer compatibility |
| **Quartus II 13.0sp1** | Last version for Cyclone III/IV; separate download |

> **MiSTer note:** Most MiSTer cores build with Quartus Prime 17.0–21.x. Newer versions may require constraint or IP updates.

---

## Best Practices

1. **Use `quartus_sh --flow compile` for CI** — one command runs synthesis → fit → assembly → timing.
2. **Archive project before Quartus upgrade** — `.qpf`/`.qsf` files may not open in newer versions.
3. **SDC constraints are order-independent** — unlike Xilinx XDC, Quartus SDC is processed as a set (order doesn't matter within a file).

## References

| Source |
|---|
| Quartus Prime Handbook (all volumes) |
| Intel Quartus Prime Pro Edition User Guide |
| Platform Designer User Guide |
