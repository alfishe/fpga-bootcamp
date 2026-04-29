[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Altera Quartus Prime — Design Suite for Cyclone, Arria, Stratix, Agilex

Quartus Prime is Altera's design environment for all FPGA families from MAX 10 through Agilex. The "Prime" branding (since v15.1) distinguishes it from the older "Quartus II" (v13.1 and earlier, Cyclone IV and prior).

> [!NOTE]
> **Company status (2025–2026):** Altera is now an independent company. Intel acquired Altera in 2015 for ~$16.7B, operated it as the Programmable Solutions Group (PSG), then spun it back out. Altera officially became independent in January 2025. In September 2025, Silver Lake acquired a 51% stake ($8.75B), with Intel retaining 49%. The tools retain "Intel Quartus Prime" branding during the transition, but the company behind them is now **Altera Corporation** (altera.com).

---

## Altera Independence Timeline

| Date | Event |
|---|---|
| **2015** | Intel acquires Altera for ~$16.7B, rebrands as Intel PSG |
| **Late 2023** | Intel announces plan to spin out PSG as a standalone business |
| **Feb 2024** | Altera brand revived; Sandra Rivera appointed CEO |
| **Jan 2025** | Altera officially independent — unfurls Altera flag at San Jose HQ |
| **May 2025** | Raghib Hussain succeeds Rivera as CEO |
| **Sep 2025** | Silver Lake closes 51% acquisition ($8.75B); Intel retains 49% |
| **2026** | Altera operates as world's largest pure-play independent FPGA company |

**What this means for users:**
- **Tooling unchanged** — Quartus Prime still works the same way, same executables, same commands
- **Download site** — now at [altera.com](https://www.altera.com) (redirects from intel.com FPGA pages still work)
- **Licensing** — existing Intel FPGA licenses remain valid; new licenses via Altera
- **Device families** — all existing families (Cyclone V through Agilex) continue unchanged
- **Foundry** — Altera can now use multiple foundries (Intel + TSMC), not locked to Intel fabs

> **Key takeaway for knowledge base references:** Throughout this knowledge base, "Intel/Altera" or "Intel PSG" refers to the same FPGA lineage. Pre-2025 documentation uses Intel branding; post-2025 uses Altera. The silicon is the same.

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

| Source | Link |
|---|---|
| Altera Website (post-independence) | [altera.com](https://www.altera.com) |
| Quartus Prime Software Download | [altera.com/download](https://www.altera.com/download) |
| Quartus Prime Handbook (all volumes) | Intel FPGA documentation (archived at intel.com, migrating to altera.com) |
| Platform Designer User Guide | Altera documentation |
| Altera Independence Press Release (Jan 2025) | [Altera Newsroom](https://www.altera.com/newsroom/news/press-release/altera-standalone-2025) |
| Silver Lake Investment Press Release (Sep 2025) | [Altera Newsroom](https://www.altera.com/newsroom/news/press-release/altera-silver-lake) |
