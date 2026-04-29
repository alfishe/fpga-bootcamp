[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Xilinx Vivado — Design Suite for 7-Series, UltraScale+, Versal

Vivado is Xilinx/AMD's unified design environment for all devices from 7-series (2010) through Versal (current). It replaces the older ISE toolchain (Spartan-6/Virtex-6 and earlier) and provides synthesis, simulation, implementation, and debug in one framework.

---

## Editions

| Edition | Devices Supported | Cost |
|---|---|---|
| **Vivado ML Standard** | All 7-series, Zynq-7000, small UltraScale+ (XCKU3P, XCZU2–5) | Free (WebPack license) |
| **Vivado ML Enterprise** | All devices including large UltraScale+, Versal | Paid (~$3,000+/year) |

**WebPack limit for most hobbyists:** Artix-7 up to XC7A200T, Kintex-7 up to XC7K70T, Zynq-7000 up to XC7Z030. DE10-Nano equivalent (Cyclone V) uses Quartus — not Vivado.

---

## Project vs Non-Project Mode

| Feature | Project Mode | Non-Project Mode |
|---|---|---|
| **Storage** | `.xpr` file + directory tree | All in-memory, script-driven |
| **GUI** | Full block design, IP integrator | Tcl console only |
| **Reproducibility** | Project state drifts with GUI clicks | Script is the source of truth |
| **CI/CD** | Difficult (project files don't diff) | Ideal — scripts are version-controlled |
| **Best for** | Exploration, IP integration, block design | Production builds, regression, CI |

> **Recommendation:** Use project mode for initial exploration and block design. For anything that ships or is built in CI, convert to non-project Tcl script.

---

## Key Tools in Vivado

| Tool | Purpose |
|---|---|
| **Vivado Synthesis** | RTL → generic netlist (EDIF/structural Verilog) |
| **Vivado Implementation** | Place + Route + Physical optimization |
| **IP Integrator** | Block-diagram IP assembly (AXI Interconnect, MIG, etc.) |
| **Vivado Simulator (xsim)** | Built-in simulator (free, limited vs Questa) |
| **Hardware Manager** | JTAG programming, ILA control, debug probes |
| **Timing Analyzer** | Static timing analysis with XDC constraints |
| **Power Analyzer** | Post-route power estimation |

---

## Vivado Version Compatibility

| Vivado Version | Last Device Support | Notes |
|---|---|---|
| Vivado 2024.x | Current (Versal, US+, 7-series) | Latest |
| Vivado 2023.x | All through Versal | Stable LTS-like release |
| Vivado 2020.x | Last with Spartan-6/Virtex-6 support | Transition — use ISE 14.7 for these |
| ISE 14.7 | Spartan-6, Virtex-6, older | End-of-life; Windows 10/11 compatibility issues |

---

## Best Practices

1. **Pin your Vivado version** — don't upgrade mid-project. Vivado project files are not backward-compatible.
2. **Use `write_checkpoint` after synthesis** — saves hours if implementation fails; resume from checkpoint.
3. **Incremental compile saves 50%+ time** — `-incremental` flag reuses previous placement for unchanged logic.
4. **XDC is order-sensitive** — constraints are processed sequentially. Put clock constraints first, then IO, then exceptions.

## References

| Source |
|---|
| Vivado Design Suite User Guide (UG910) |
| Vivado Tcl Command Reference (UG835) |
| UltraFast Design Methodology (UG949) |
