[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Lattice Diamond & Radiant — Two Toolchains, One Vendor

Lattice maintains two parallel toolchains for different device families. Choosing the right one depends on which FPGA you're targeting — they're not interchangeable. Diamond supports the classic families (ECP5, MachXO2/3), while Radiant supports newer 28nm+ devices (CertusPro-NX, CrossLink-NX, Avant).

---

## Diamond vs Radiant

| Feature | Diamond | Radiant |
|---|---|---|
| **Target devices** | ECP5, MachXO2/3, iCE40 (older), CrossLink | CertusPro-NX, CrossLink-NX, Avant, iCE40 UltraPlus |
| **Synthesis engine** | Synplify Pro (included) | Synplify Pro (included) |
| **Simulator** | Active-HDL Lattice Edition (included) | QuestaSim (limited free license) |
| **Debug** | Reveal Inserter + Analyzer | Reveal Inserter + Analyzer (same) |
| **Constraint format** | LPF (Lattice Preference Format) | LPF + SDC (some SDC support) |
| **OS support** | Windows, Linux (limited) | Windows, Linux |
| **Yosys/nextpnr compat** | Yes (ECP5 has excellent open-source flow) | Not yet (CertusPro-NX, Avant) |
| **Status** | Maintenance mode | Active development |
| **License** | Free | Free |

---

## Which Toolchain for Which Device?

| Device Family | Use | Notes |
|---|---|---|
| **ECP5** | Diamond 3.12+ | Best open-source support (Yosys + nextpnr) |
| **MachXO2/MachXO3** | Diamond | Stable; no Radiant support |
| **iCE40 (LP/HX)** | Diamond or Yosys | Excellent open-source flow (IceStorm/nextpnr) |
| **iCE40 UltraPlus** | Radiant or Yosys | Both work |
| **CrossLink-NX** | Radiant | 28nm FD-SOI, no open-source flow yet |
| **CertusPro-NX** | Radiant 3.0+ | 28nm FD-SOI, SerDes up to 10.3 Gbps |
| **Avant** | Radiant 5.0+ | Mid-range 16nm, PCIe Gen4 |

---

## Diamond Design Flow

### GUI Flow

```
1. File → New Project → select device (e.g., ECP5-85F)
2. Add RTL source files (.v, .sv, .vhd)
3. Add constraints (.lpf)
4. Synplify Pro → Synthesize
5. Lattice Diamond Implementation → Place & Route
6. Generate Bitstream
7. Programmer → JTAG or SPI flash
```

### Command-Line Flow (PNR+C)

```bash
# Synthesize with Synplify Pro
synplify_pro -f top.prj

# Place & Route
diamond -f top_impl1.pb

# Generate bitstream
diamond -f top_bitgen.pb

# Program
diamond_programmer -f top.xcf
```

### Full Tcl Script (Diamond)

```tcl
# build.tcl — Run with: diamond build.tcl
prj_project new -name top -dev LFE5U-85F -package CABGA381
prj_project add src/top.v src/fifo.v src/uart.v
prj_project add constraints/top.lpf

# Synthesize
prj_run Synthesis -impl impl1

# Place & Route
prj_run Map -impl impl1
prj_run PAR -impl impl1

# Generate bitstream
prj_run Bitgen -impl impl1

# Export timing report
prj_run TRCE -impl impl1
```

---

## Radiant Design Flow

### GUI Flow

```
1. File → New Project → select device (e.g., LFD2NX-40)
2. Add RTL source files
3. Add constraints (.lpf, .sdc)
4. Synplify Pro → Synthesize
5. Radiant Implementation → Place & Route
6. Generate Bitstream
7. Programmer
```

### Command-Line (Radiant)

```bash
# Radiant uses similar Tcl interface
radiant -c build.tcl
```

---

## Constraint Format

### LPF — Lattice Preference Format (Both Diamond and Radiant)

```tcl
# Pin location and I/O type
LOCATE COMP "clk_pin" SITE "A9";
IOBUF PORT "clk_pin" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk_pin" 100 MHz;

LOCATE COMP "led[0]" SITE "B12";
IOBUF PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;

# Differential pair
LOCATE COMP "ddr_clk_p" SITE "A3";
LOCATE COMP "ddr_clk_n" SITE "A4";
IOBUF PORT "ddr_clk_p" IO_TYPE=SSTL18_I;
IOBUF PORT "ddr_clk_n" IO_TYPE=SSTL18_I;

# Pull-up on input
IOBUF PORT "btn[0]" IO_TYPE=LVCMOS33 PULLMODE=UP;
```

### SDC Constraints (Radiant)

```tcl
# Radiant supports standard SDC syntax
create_clock -name clk -period 10 [get_ports clk_pin]

create_generated_clock -name clk_pll \
    -source [get_ports clk_pin] \
    [get_pins pll_inst/clkout[0]]

set_false_path -from [get_ports rst_n]

set_max_delay -from [get_cells tx_reg*] -to [get_ports uart_tx] 5
```

LPF is simpler than SDC but less expressive — no multi-cycle paths, no generated clocks. For complex timing, use Radiant with SDC.

---

## Reveal Debugger

Lattice's on-chip logic analyzer (both Diamond and Radiant):

### Configuration

```
1. Tools → Reveal Inserter
2. Select signals to probe
3. Set trigger condition (basic: value match; advanced: state machine)
4. Set sample depth (uses BRAM)
5. Insert → Rebuild design
6. Program FPGA
7. Tools → Reveal Analyzer → Arm → Capture → View waveform
```

### Resource Cost

| Sample Depth | 32-bit probe width | 64-bit probe width |
|---|---|---|
| 256 | 1 BRAM | 2 BRAM |
| 512 | 2 BRAM | 4 BRAM |
| 1024 | 4 BRAM | 8 BRAM |
| 4096 | 16 BRAM | 32 BRAM |

### HDL Attribute for Signal Preservation

```verilog
// Prevent synthesis from optimizing away debug signals
(* preserve *) reg [7:0] debug_counter;
(* keep *) wire debug_fifo_full;
```

---

## IP Cores

| IP Core | Diamond | Radiant | Notes |
|---|---|---|---|
| **PLL** | Yes | Yes | Up to 2 per ECP5, 4 on CertusPro-NX |
| **Block RAM** | Yes | Yes | Dual-port, 18Kb blocks |
| **DSP** | Yes (ECP5) | Yes | 18×18 multipliers |
| **DDR3 Controller** | Yes | Yes | Via IP Express |
| **SPI Flash Controller** | Yes | Yes | For configuration + data |
| **SerDes** | No | Yes (CertusPro-NX) | Up to 10.3 Gbps |
| **PCIe Gen2/3** | No | Yes (CertusPro-NX) | Hard IP blocks |
| **UART** | Yes | Yes | 16550-compatible |
| **I2C** | Yes | Yes | Standard/Fast mode |

---

## Programming Hardware

| Adapter | Diamond | Radiant | Notes |
|---|---|---|---|
| **Lattice USB Cable (FT2232H)** | Yes | Yes | Official, ~$50 |
| **FPGA-MCU02** | Yes | Yes | Lattice evaluation board debugger |
| **openFPGALoader** | Yes | Partial | Open-source, supports ECP5 and some NX |
| **FTDI-based adapters** | Yes | No | Via Diamond programmer |

```bash
# Program ECP5 via openFPGALoader
openFPGALoader -b ulx3s top.bit

# Program via Diamond CLI
diamond_programmer -cable USB -file top.xcf
```

---

## Best Practices

1. **Use Diamond for ECP5** — Diamond is more mature for ECP5; Radiant adds no benefit.
2. **Export to open-source flow for CI** — Yosys + nextpnr for ECP5 is faster, fully scriptable, and free.
3. **Reveal probe signals need `(* preserve *)`** — synthesis may optimize them away otherwise.
4. **Use SDC in Radiant for complex timing** — LPF can't express generated clocks or multi-cycle paths.
5. **Check Yosys QoR** — for ECP5, Yosys sometimes produces better area results than Synplify Pro.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Wrong toolchain for device** | Project won't open or device not listed | Check device family → toolchain mapping |
| **LPF missing FREQUENCY** | Timing not analyzed, no Fmax report | Add `FREQUENCY PORT "clk" N MHz` |
| **Reveal rebuild required** | Changing probes requires full recompile | Plan probes carefully before first build |
| **Synplify over-optimizing** | Signals disappear from Reveal | Add `(* preserve *)` or `(* keep *)` attributes |
| **openFPGALoader not finding cable** | Programming fails | Check FTDI driver installation; try `openFPGALoader --detect` |
| **CertusPro-NX only in Radiant** | Device not in Diamond | Must use Radiant 3.0+ for NX devices |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Lattice Diamond User Guide](https://www.latticesemi.com/support/technicaldocuments) | Lattice | Complete Diamond reference |
| [Lattice Radiant User Guide](https://www.latticesemi.com/support/technicaldocuments) | Lattice | Complete Radiant reference |
| [Lattice Reveal User Guide](https://www.latticesemi.com/support/technicaldocuments) | Lattice | Logic analyzer configuration |
| [Open-Source Flow](open_source_flow.md) | This KB | Yosys + nextpnr for Lattice ECP5/iCE40 |