[← 14 References Home](README.md) · [← Project Home](../../README.md)

# Vendor Tool Command Cheatsheet

Quick-reference commands for the most common FPGA toolchain operations. All commands assume the tool is in PATH.

---

## Vivado (Xilinx)

### Project Mode
```tcl
# Create project
vivado -mode tcl -source build.tcl

# Non-project (scripted) flow — preferred for CI
vivado -mode batch -source build.tcl

# Read sources
read_verilog [glob src/*.v]
read_vhdl [glob src/*.vhd]
read_xdc constraints.xdc

# Synthesis
synth_design -top my_top -part xc7a35t-cpg236-1

# Implementation
opt_design
place_design
route_design

# Bitstream
write_bitstream my_design.bit
write_cfgmem -format mcs -size 16 -interface spix4 my_design.mcs

# Reports
report_timing_summary -file timing.rpt
report_utilization -file utilization.rpt
report_power -file power.rpt
```

### Tcl-Only (No GUI)
```bash
# Synthesize and implement from command line
vivado -mode batch -source build.tcl -nojournal -nolog

# Program device
vivado -mode batch -source program.tcl
  # program.tcl:
  # open_hw
  # connect_hw_server
  # program_hw_devices [get_hw_devices]
```

---

## Quartus (Intel)

### CLI Commands
```bash
# Synthesize + fit + assemble (all steps)
quartus_sh --flow compile my_project

# Individual steps
quartus_map my_project      # Analysis & Synthesis
quartus_fit my_project       # Fitter (place & route)
quartus_asm my_project       # Assembler (bitstream)
quartus_sta my_project       # Timing analysis

# Generate .sof/.pof
quartus_cpf -c output.sof output.pof

# Program device
quartus_pgm -c USB-Blaster -m JTAG -o "p;output.sof"

# Reports
quartus_sta --report_level=high my_project
```

### Tcl Scripting
```tcl
# project_new my_project -overwrite
# set_global_assignment -name FAMILY "Cyclone V"
# set_global_assignment -name DEVICE 5CSEMA5F31C6
# execute_flow -compile
```

---

## Yosys + nextpnr (Open-Source)

### Synthesis
```bash
# Yosys synthesis (Lattice ICE40)
yosys -p "
    read_verilog src/*.v
    synth_ice40 -top my_top -json synth.json
"

# Yosys synthesis (Lattice ECP5)
yosys -p "
    read_verilog src/*.v
    synth_ecp5 -top my_top -json synth.json
"

# Yosys synthesis (Xilinx 7-Series)
yosys -p "
    read_verilog src/*.v
    synth_xilinx -top my_top -json synth.json
"
```

### Place & Route
```bash
# ICE40
nextpnr-ice40 --hx8k --package ct256 --json synth.json --asc bitstream.asc
icepack bitstream.asc bitstream.bin

# ECP5
nextpnr-ecp5 --85k --package CABGA381 --json synth.json --textcfg bitstream.config
ecppack bitstream.config bitstream.bit

# Xilinx 7-Series (experimental)
nextpnr-xilinx --xc7a35t --package cpg236-1 --json synth.json
```

---

## OpenOCD (JTAG / Debug)

```bash
# Program FPGA via JTAG
openocd -f interface/ftdi/jtag.cfg -f board/my_board.cfg \
    -c "init; pld load 0 my_bitstream.bit; exit"

# GDB debug for RISC-V soft CPU
openocd -f board/my_board.cfg &
riscv64-unknown-elf-gdb my_firmware.elf \
    -ex "target extended-remote :3333"
```

---

## Gowin EDA

```bash
# Synthesize (command-line)
gw_sh my_project.gprj -batch -c "run all"

# Program device
gw_pgm -c FTDI -o "p;my_fs.bit"
```

---

## Lattice Diamond

```bash
# Build from command line
pcli -f build.tcl
  # build.tcl:
  # prj_project open my_project.ldf
  # prj_run Synthesis
  # prj_run Map
  # prj_run PAR
  # prj_run Export -task Bitgen
```

---

## Common Tcl Patterns (Cross-Vendor)

```tcl
# Find all .v files recursively
set rtl_files [glob -nocomplain -types f [file join src ** *.v]]

# Loop and add sources
foreach f $rtl_files { read_verilog $f }

# Check if file exists before reading
if {[file exists constraints.xdc]} { read_xdc constraints.xdc }
```
