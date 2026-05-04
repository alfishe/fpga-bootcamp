[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Gowin EDA — Gowin Semiconductor's FPGA Design Suite

Gowin EDA is the free, all-in-one design environment for Gowin FPGAs: LittleBee (GW1N), Arora (GW2A), and newer families. It's lighter-weight than Vivado/Quartus but capable enough for most designs targeting the budget-friendly Gowin ecosystem.

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
| **GAO (Gowin Analyzer Oscilloscope)** | On-chip logic analyzer — Gowin's SignalTap/ILA equivalent |
| **Programmer** | JTAG bitstream loading, flash programming via Gowin USB Cable |
| **IP Generator** | Block RAM, PLL, DSP multiplier, DDR controller, Gowin_EMPU (soft CPU) |
| **FloorPlanner** | I/O and logic placement constraints |
| **Timing Analyzer** | SDC-based static timing analysis |
| **Power Analyzer** | Estimated power consumption |

---

## Design Flow

### GUI Flow (Gowin EDA IDE)

```
1. File → New Project → select device (e.g., GW1N-9)
2. Add RTL source files (.v, .sv, .vhd)
3. Add constraints (.cst, .sdc)
4. Synthesize → Place & Route → Generate Bitstream
5. Program via Programmer tool
```

### Command-Line Flow (shell mode)

```bash
# Synthesize
gw_sh -c "run syn -top top -device GW1N-9"

# Place & Route
gw_sh -c "run pnr -top top -device GW1N-9"

# Generate bitstream
gw_sh -c "run bit -top top -device GW1N-9"

# Program
gw_sh -c "run program -top top -device GW1N-9 -cable GowinUSB"
```

### Full Tcl Script

```tcl
# build.tcl — Run with: gw_sh build.tcl
set_device GW1N-9

# Add source files
add_file src/top.v
add_file src/fifo.v
add_file src/uart.v
add_file constraints/top.cst
add_file constraints/top.sdc

# Synthesize
run syn -top top

# Place & Route
run pnr -top top

# Generate bitstream
run bit -top top

# Report timing
run sta
```

```bash
gw_sh build.tcl
```

---

## Constraint Format (CST + SDC)

### CST — Physical Constraints (Gowin-Specific)

```tcl
# Pin location and I/O type
IO_LOC "clk" 52;
IO_PORT "clk" IO_TYPE=LVCMOS33;

IO_LOC "led[0]" 10;
IO_PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;

IO_LOC "uart_rx" 15;
IO_PORT "uart_rx" IO_TYPE=LVCMOS33 PULLUP=ON;

IO_LOC "uart_tx" 16;
IO_PORT "uart_tx" IO_TYPE=LVCMOS33 DRIVE=8 SLEW=SLOW;

# Differential pair
IO_LOC "ddr_dq[0]" 35;
IO_PORT "ddr_dq[0]" IO_TYPE=SSTL18_I;
```

### SDC — Timing Constraints (Standard)

```tcl
# Clock constraints (same syntax as Vivado/Quartus)
create_clock -name clk -period 10 [get_ports clk]

# Generated clock from PLL
create_generated_clock -name clk_50m \
    -source [get_ports clk] \
    -multiply_by 1 \
    [get_pins pll_inst/clkout[0]]

# False paths
set_false_path -from [get_ports rst_n]

# Multi-cycle paths
set_multicycle_path 2 -setup -from [get_cells slow_reg*]
```

---

## GAO — Gowin Analyzer Oscilloscope

GAO is Gowin's on-chip logic analyzer, equivalent to Xilinx ILA or Intel SignalTap:

### Configuration

```tcl
# GAO configuration (in CST or via GUI)
# 1. Select signals to probe
# 2. Set trigger condition (e.g., fifo_full = 1)
# 3. Set sample depth (uses BRAM)
# 4. Build → GAO is integrated into bitstream

# Resource cost: ~1 BRAM per 512 samples × 32-bit probe width
```

### GAO Usage Flow

```
1. Design → GAO Inserter → Select signals and trigger
2. Rebuild design (GAO adds probe logic + BRAM)
3. Program FPGA
4. GAO Analyzer → Arm trigger → Capture → View waveform
5. Waveform format: viewable in Gowin EDA only (no VCD export)
```

---

## IP Generator

| IP Core | Families | Notes |
|---|---|---|
| **PLL** | All | Up to 2 PLLs on GW1N, 4 on GW2A |
| **Block RAM** | All | Dual-port, 18Kb blocks |
| **DSP** | GW2A, GW5A | 18×18 multipliers |
| **DDR3 Controller** | GW2A, GW5A | Up to DDR3-800 |
| **SPI Flash Controller** | All | For configuration and data storage |
| **Gowin_EMPU** | GW2A, GW5A | Soft CPU (custom ISA, not RISC-V) |
| **UART** | All | 16550-compatible |
| **SPI Master/Slave** | All | Configurable CPOL/CPHA |
| **I2C Master** | All | Standard-mode (100K) and Fast-mode (400K) |
| **GPIO** | All | Configurable width |

---

## Programming Hardware

| Adapter | Notes |
|---|---|
| **Gowin USB Cable (FT2232H)** | Official, ~$30, works with any Gowin FPGA |
| **Tang Nano/Nano 4K/Nano 9K** | Built-in USB-JTAG via onboard MCU; no separate cable needed |
| **Sipeed Tang Primer/MEGA** | Onboard debugger (BL702/CKLink) |
| **openFPGALoader** | Open-source, supports Gowin via FTDI |

```bash
# Program via openFPGALoader (open source)
openFPGALoader -b tangnano9k top.fs

# Program via Gowin Programmer CLI
programmer_cli --device GW1N-9 --file top.fs --cable GowinUSB
```

---

## Open-Source Flow for Gowin

Gowin FPGAs have a growing open-source toolchain:

```bash
# Yosys synthesis for Gowin
yosys -p "synth_gowin -json top.json" top.v

# nextpnr place & route
nextpnr-gowin --json top.json --write top.pnr \
    --device GW1N-9 --family GW1N-9

# Bitstream generation (Project Apicula)
gowin_pack -d GW1N-9 -o top.fs top.pnr

# Program
openFPGALoader -b tangnano9k top.fs
```

| Tool | Status | Notes |
|---|---|---|
| **Yosys (synth_gowin)** | Good | Supports most Verilog constructs |
| **nextpnr-gowin** | Experimental | Works for GW1N, limited for GW2A |
| **Project Apicula** | Good | Bitstream reverse-engineering for GW1N |
| **openFPGALoader** | Good | Full JTAG programming support |

---

## Best Practices

1. **Use GAO sparingly** — GAO consumes BRAM (same as ILA/SignalTap). Keep debug signals minimal.
2. **Gowin synthesis is less aggressive than Synplify** — some RTL patterns that optimize fine in Vivado may leave extra logic. Add `(* keep *)` attributes where needed.
3. **CST pin constraints are case-sensitive** — `"clk"` ≠ `"CLK"`.
4. **Use openFPGALoader for CI/CD** — no GUI required, scriptable.
5. **Check Yosys synthesis if Gowin synthesis produces poor results** — Yosys `synth_gowin` sometimes produces better QoR for specific patterns.
6. **GW1N-1 has only 864 LUTs** — carefully budget resources; even a small UART + SPI + GPIO SoC may not fit.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Case mismatch in CST** | Pin not assigned, design fails P&R | Match signal names exactly (case-sensitive) |
| **No SDC constraints** | Timing not analyzed, design may fail at speed | Always add `create_clock` constraints |
| **GAO uses all BRAM** | P&R fails: "no BRAM available" | Reduce GAO sample depth or probe width |
| **PLL not locked** | Design doesn't start | Add PLL lock detector; hold reset until locked |
| **Flash programming fails** | Bitstream doesn't load from flash | Check SPI flash type in Programmer settings |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Gowin EDA User Guide (SUG100)](https://www.gowinsemi.com/en/support/documentation/) | Gowin | Complete tool reference |
| [Gowin GAO User Guide (SUG114)](https://www.gowinsemi.com/en/support/documentation/) | Gowin | Logic analyzer configuration |
| [Project Apicula](https://github.com/apicula/apicula) | GitHub | Open-source Gowin bitstream tools |
| [Open-Source Flow](open_source_flow.md) | This KB | Yosys + nextpnr for Gowin |