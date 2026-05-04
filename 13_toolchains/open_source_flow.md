[← 13 Toolchains Home](README.md) · [← Project Home](../../README.md)

# Open-Source FPGA Toolchain — Yosys, nextpnr, and F4PGA

The open-source FPGA toolchain has matured from a curiosity to a production-capable flow for select device families. Yosys (synthesis) + nextpnr (place & route) + bitstream tools provide a fully open, scriptable, CI-friendly alternative to vendor tools.

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
| **nextpnr** | Place & Route → bitstream config | Vivado Implementation, Quartus Fitter |
| **Project IceStorm** | iCE40 bitstream documentation + tools | Lattice Diamond (for iCE40) |
| **Project Trellis** | ECP5 bitstream documentation + tools | Lattice Diamond (for ECP5) |
| **Project X-Ray** | Xilinx 7-series bitstream documentation | Vivado (for Artix-7, Zynq) |
| **Project Apicula** | Gowin bitstream documentation | Gowin EDA |
| **openFPGALoader** | JTAG programming | Vivado HW Manager, Quartus Programmer |
| **F4PGA** | Multi-architecture umbrella | Vendor tools for multiple families |

---

## Device Support Matrix

| Family | Synthesis | P&R | Bitstream | Programming | Maturity |
|---|---|---|---|---|---|
| **iCE40 (LP/HX/UP)** | Yosys ✓ | nextpnr-ice40 ✓ | IceStorm ✓ | openFPGALoader ✓ | **Production** |
| **ECP5** | Yosys ✓ | nextpnr-ecp5 ✓ | Trellis ✓ | openFPGALoader ✓ | **Production** |
| **Xilinx 7-series** | Yosys ✓ | nextpnr-xilinx ✓ | X-Ray ✓ | openFPGALoader ✓ | **Experimental** |
| **Gowin GW1N/GW2A** | Yosys ✓ | nextpnr-gowin ✓ | Apicula ✓ | openFPGALoader ✓ | **Experimental** |
| **MachXO2** | Yosys ✓ | nextpnr-machxo2 WIP | — | — | Early development |
| **Cyclone V** | No | No | No | — | Not supported |
| **UltraScale+** | No | No | No | — | Not supported |

---

## Installation

### Ubuntu/Debian (apt)

```bash
# Yosys
sudo apt install yosys

# nextpnr (build from source for latest)
sudo apt install build-essential cmake libeigen3-dev \
    libftdi-dev qtbase5-dev python3-dev
git clone https://github.com/YosysHQ/nextpnr
cd nextpnr && mkdir build && cd build
cmake .. -DARCH=ecp5 -DTRELLIS_ROOT=/usr/share/trellis
make -j$(nproc) && sudo make install

# openFPGALoader
sudo apt install openfpgaloader
```

### Nix (reproducible)

```bash
# One-command install with all tools
nix-shell -p yosys nextpnr projtrellis openfpgaloader
```

### Conda

```bash
conda install -c conda-forge yosys nextpnr openfpgaloader
```

---

## Quick Start: iCE40 (iCEBreaker / TinyFPGA BX)

```bash
# Synthesize
yosys -p "synth_ice40 -json top.json -top top" top.v

# Place & Route
nextpnr-ice40 --json top.json --write top.pnr \
    --up5k --package sg48 --pcf top.pcf

# Generate bitstream
icepack top.pnr top.bin

# Program
openFPGALoader -b icebreaker top.bin
```

### PCF Constraints (iCE40 Physical Constraints)

```
# top.pcf — Pin assignments for iCE40
set_io clk 35
set_io led[0] 40
set_io led[1] 41
set_io uart_rx 6
set_io uart_tx 9
```

---

## Quick Start: ECP5 (ULX3S / OrangeCrab)

```bash
# Synthesize
yosys -p "synth_ecp5 -json top.json -top top" top.v

# Place & Route (ECP5 85F on ULX3S)
nextpnr-ecp5 --json top.json --textcfg top.config \
    --85k --package CABGA381 --lpf constraints.lpf

# Generate bitstream
ecppack top.config top.bit

# Program
openFPGALoader -b ulx3s top.bit
```

### LPF Constraints (ECP5)

```tcl
# constraints.lpf
LOCATE COMP "clk" SITE "A9";
IOBUF PORT "clk" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk" 25 MHz;

LOCATE COMP "led[0]" SITE "B12";
IOBUF PORT "led[0]" IO_TYPE=LVCMOS33 DRIVE=8;
```

---

## Quick Start: Xilinx 7-Series (Arty A7)

```bash
# Synthesize
yosys -p "synth_xilinx -json top.json -top top" top.v

# Place & Route (Artix-7 35T)
nextpnr-xilinx --json top.json --write top.pnr \
    --chipdb /usr/share/nextpnr-xilinx/xc7a35t.bin \
    --xdc constraints.xdc

# Generate bitstream (requires Project X-Ray)
xc7frames2bit top.frames top.bit

# Program
openFPGALoader -b arty_a7_35t top.bit
```

> **Note:** Xilinx 7-series open-source flow is experimental. Clock routing and I/O constraints have significant limitations. Use Vivado for production Xilinx designs.

---

## Yosys Synthesis Reference

### Common Synthesis Commands

```tcl
# Basic synthesis for ECP5
synth_ecp5 -json top.json -top top

# With optimizations
synth_ecp5 -json top.json -top top -abc9

# Verilog only (no VHDL support in Yosys)
read_verilog top.v
synth_ecp5 -json top.json -top top

# SystemVerilog (limited support)
read_verilog -sv top.sv
synth_ecp5 -json top.json -top top

# VHDL via GHDL plugin
read_verilog top.v
ghdl -a --std=08 top.vhd
ghdl --import top
synth_ecp5 -json top.json -top top

# Lint only (check without generating netlist)
read_verilog top.v
synth_ecp5 -top top -noiopad -json /dev/null
```

### Yosys Optimization Passes

```tcl
# Manual optimization pipeline (what synth_* does internally)
hierarchy -check -top top
proc
fsm
opt
memory
opt
techmap
opt
clean
```

### Yosys Attributes

```verilog
// Prevent signal from being optimized away
(* keep *) wire debug_sig;

// Force register to use flip-flop (not latch)
(* nomux *) reg q;

// Mark black-box module (no implementation, external IP)
(* blackbox *) module vendor_ip (...);

// Force no merging of instances
(* dont_touch *) module my_module (...);
```

---

## nextpnr Configuration Options

### Common Options (All Architectures)

| Option | Purpose |
|---|---|
| `--json` | Input netlist from Yosys |
| `--write` | Output P&R result |
| `--top` | Top module name |
| `--seed` | Random seed for placement (try different seeds for better QoR) |
| `--router router2` | Use improved router (recommended) |
| `--slack_redistribution_iter N` | Iterative timing optimization |
| `--estimate-timeout N` | Timeout in seconds |

### Multi-Seed P&R for Better QoR

```bash
# Try multiple seeds, pick the one with best timing
best_seed=0
best_slack=-999

for seed in $(seq 0 9); do
    nextpnr-ecp5 --json top.json --textcfg top_${seed}.config \
        --85k --package CABGA381 --lpf top.lpf \
        --seed $seed --router router2 2>&1 | tee log_${seed}.txt

    slack=$(grep "Max delay" log_${seed}.txt | grep -oP '[0-9.-]+')
    if (( $(echo "$slack > $best_slack" | bc -l) )); then
        best_slack=$slack
        best_seed=$seed
    fi
done

echo "Best seed: $best_seed (slack: $best_slack)"
ecppack top_${best_seed}.config top.bit
```

---

## F4PGA — Multi-Architecture Umbrella

[F4PGA](https://f4pga.org/) (formerly SymbiFlow) provides a unified flow:

```bash
# Install F4PGA
pip install f4pga

# Build for ECP5
f4pga build --flow ecp5 --top top --part LFE5U-85F \
    --sources top.v fifo.v --constraints top.lpf

# Build for Xilinx 7-series
f4pga build --flow xc7 --top top --part xc7a35tcsg324-1 \
    --sources top.v --constraints top.xdc
```

---

## CI/CD with Open-Source Tools

```yaml
# .github/workflows/fpga-ci.yml
name: FPGA CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Toolchain
        run: |
          sudo apt update
          sudo apt install -y yosys nextpnr-ecp5 projtrellis openfpgaloader

      - name: Synthesize
        run: yosys -p "synth_ecp5 -json top.json -top top" src/*.v

      - name: Place & Route
        run: |
          nextpnr-ecp5 --json top.json --textcfg top.config \
            --85k --package CABGA381 --lpf constraints.lpf

      - name: Generate Bitstream
        run: ecpack top.config top.bit

      - name: Upload Bitstream
        uses: actions/upload-artifact@v4
        with:
          name: bitstream
          path: top.bit
```

---

## Open vs Vendor Tool Comparison

| Feature | Open-Source (Yosys+nextpnr) | Vivado | Quartus |
|---|---|---|---|
| **Cost** | Free | Free (WebPack) or paid | Free (Lite) or paid |
| **CI/CD friendly** | Excellent (CLI-native, no license) | Poor (needs license server) | Poor (needs license server) |
| **Build speed** | Fast (seconds for small designs) | Slow (minutes) | Slow (minutes) |
| **Timing QoR** | Good for iCE40/ECP5; worse for 7-series | Best for Xilinx | Best for Intel |
| **Device support** | Limited (iCE40, ECP5 best) | All Xilinx | All Intel |
| **IP cores** | Open IP only (no vendor IP) | Full vendor IP catalog | Full vendor IP catalog |
| **Timing analysis** | Basic (estimated) | Full STA with SDF back-annotation | Full TimeQuest STA |
| **Debug** | Simulation only (no ILA) | ILA, HW Manager | SignalTap |
| **Documentation** | Community wiki + source code | Extensive vendor docs | Extensive vendor docs |

---

## Best Practices

1. **Start with open-source-supported hardware** — iCE40 (iCEBreaker) or ECP5 (ULX3S, OrangeCrab) for guaranteed tool flow.
2. **Vendor tools for timing closure, open tools for CI** — vendor P&R still produces better QoR for complex designs.
3. **Use multi-seed P&R** — nextpnr is heuristic; different seeds produce different results. Run 5–10 seeds and pick the best.
4. **Keep RTL vendor-neutral** — avoid vendor-specific pragmas and IP. Use portable inference patterns.
5. **Use GHDL for VHDL** — Yosys + GHDL plugin provides VHDL synthesis for open-source flow.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Yosys Manual](https://yosyshq.readthedocs.io/) | YosysHQ | Complete synthesis reference |
| [nextpnr](https://github.com/YosysHQ/nextpnr) | GitHub | P&R tool documentation |
| [Project Trellis (ECP5)](https://github.com/YosysHQ/prjtrellis) | GitHub | ECP5 bitstream tools |
| [Project IceStorm (iCE40)](https://github.com/YosysHQ/icestorm) | GitHub | iCE40 bitstream tools |
| [F4PGA](https://f4pga.org/) | f4pga.org | Multi-architecture umbrella |
| [openFPGALoader](https://github.com/trabucayre/openFPGALoader) | GitHub | Open-source JTAG programmer |