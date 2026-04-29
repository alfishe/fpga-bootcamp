[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Gowin EDA — Gowin Semiconductor's FPGA Design Suite

Gowin EDA is the free, all-in-one design environment for Gowin FPGAs: LittleBee (GW1N), Arora (GW2A), and their newer families. It's lighter-weight than Vivado/Quartus but capable enough for most designs.

---

## Device Support

| Family | Devices | Max LUTs | Notes |
|---|---|---|---|
| **LittleBee (GW1N)** | GW1N-1 through GW1N-9 | 864–8,640 | Ultra-low-power, 55nm flash |
| **Arora (GW2A)** | GW2A-18 through GW2A-55 | 20,736–55,296 | 55nm SRAM, DSP blocks, DDR3 |
| **Arora V (GW5A)** | GW5A-25 through GW5A-138 | 23,040–138,240 | 22nm, SerDes, PCIe Gen3 |
| **Tang series** | Various | Various | Popular hobbyist dev boards |

---

## Key Tools

| Tool | Purpose |
|---|---|
| **Gowin Synthesis** | RTL synthesis — Gowin's own engine (not Synplify) |
| **Place & Route** | Gowin's P&R engine |
| **GAO (Gowin Analyzer Oscilloscope)** | On-chip logic analyzer — Gowin's SignalTap equivalent |
| **Programmer** | JTAG bitstream loading, flash programming via Gowin USB Cable |
| **IP Generator** | Block RAM, PLL, DSP multiplier, DDR controller, Gowin_EMPU (soft CPU) |
| **FloorPlanner** | I/O and logic placement constraints |

---

## Constraint Format (CST)

Gowin uses `.cst` (physical constraints) and `.sdc` (timing constraints):

```tcl
# CST example
IO_LOC "clk" 52;
IO_PORT "clk" IO_TYPE=LVCMOS33;
IO_LOC "led[0]" 10;
IO_PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;
```

SDC syntax is standard (same as Vivado/Quartus). CST is Gowin-specific.

---

## Programming Hardware

| Adapter | Notes |
|---|---|
| **Gowin USB Cable (FT2232H-based)** | Official, ~$30, works with any Gowin FPGA |
| **Tang Nano/Nano 4K/Nano 9K** | Built-in USB-JTAG via onboard MCU; no separate cable needed |
| **Sipeed Tang Primer/MEGA** | Onboard debugger (BL702/CKLink) |
| **openFPGALoader** | Open-source, supports Gowin via FTDI |

---

## Best Practices

1. **Use GAO sparingly** — GAO consumes BRAM (same as ILA/SignalTap). Keep debug signals minimal.
2. **The Gowin synthesis engine is less aggressive than Synplify/Design Compiler** — some RTL patterns that optimize fine in Vivado may leave extra logic in Gowin EDA.
3. **CST pin constraints are case-sensitive** — `"clk"` ≠ `"CLK"`.

## References

| Source |
|---|
| Gowin EDA User Guide (SUG100) |
| Gowin Schematic Manual |
| Gowin GAO User Guide (SUG114) |
