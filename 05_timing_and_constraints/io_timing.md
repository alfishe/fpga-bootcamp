[← Section Home](README.md) · [← Project Home](../README.md)

# IO Timing — Source-Synchronous, System-Synchronous, and DDR Interfaces

FPGA IO timing is where your design meets the physical world. Unlike internal paths — where the tool controls both launch and capture clocks — IO paths involve an external device with its own timing characteristics. Getting IO constraints right is the difference between a design that works on the bench and one that fails in the field.

---

## The Two IO Timing Models

```
SYSTEM-SYNCHRONOUS                    SOURCE-SYNCHRONOUS
(single common clock)                 (clock forwarded with data)

External          FPGA                External           FPGA
┌────────┐       ┌────────┐           ┌────────┐        ┌────────┐
│ Device │ data  │        │           │ Device │ data   │        │
│        │──────→│ Capture│           │        │───────→│ Capture│
│        │       │  FF    │           │        │ clk    │  FF    │
│        │       │        │           │        │───────→│        │
└────────┘       └────────┘           └────────┘        └────────┘
     │                │                     └── clk forwarded with data
     └── clk ────────┘                          (same source, matched trace)
     (shared system clock)
```

| Model | When Used | Timing Critical Path | Constraint Focus |
|---|---|---|---|
| **System-synchronous** | Legacy, slow (<50 MHz) | Board trace + FPGA internal | Large input/output delays |
| **Source-synchronous** | Modern, fast (>100 MHz) | Data-to-clock skew | Small, tightly-bounded delays |

---

## Input Timing — set_input_delay

`set_input_delay` tells the tool how much of the clock period is consumed **outside** the FPGA. The remaining budget is for internal routing and setup:

```tcl
# External device: tco_max = 2.5 ns, tco_min = 0.8 ns
# Board trace delay: 0.3 ns (estimated from trace length)
# Clock skew between device and FPGA: 0.1 ns

# Maximum external delay (worst-case setup):
set_input_delay -clock sys_clk -max 2.9 \
    [get_ports data_in*]  # 2.5 (tco_max) + 0.3 (trace) + 0.1 (skew)

# Minimum external delay (worst-case hold):
set_input_delay -clock sys_clk -min 0.8 \
    [get_ports data_in*]  # 0.8 (tco_min) - 0.3 (trace) — skew may reduce
```

### The Mental Model

```
One Clock Period (10 ns at 100 MHz)
├─────────────────────────────────────────┤
│←── External ──→│←── Internal (FPGA) ──→│
│  set_input_    │  routing + setup       │
│  delay -max    │                        │
│  = 2.9 ns      │  must be ≤ 7.1 ns     │
└────────────────┴────────────────────────┘
```

---

## Output Timing — set_output_delay

`set_output_delay` tells the tool how much time the external device needs AFTER the clock edge to capture data:

```tcl
# External device: tsu = 1.5 ns, th = 0.5 ns
# Board trace delay: 0.3 ns

# Maximum external delay (device setup requirement):
set_output_delay -clock sys_clk -max 1.8 \
    [get_ports data_out*]  # 1.5 (tsu) + 0.3 (trace)

# Minimum external delay (device hold requirement):
set_output_delay -clock sys_clk -min 0.2 \
    [get_ports data_out*]  # 0.5 (th) - 0.3 (trace)
```

```
FPGA must drive data so it arrives at the device with:
├── FPGA internal ──┤←─ Board trace ─→│← Device tsu ─│
                     │  0.3 ns        │   1.5 ns      │
                     │                │               │
clock ───────────────┼────────────────┼───────────────┼── next edge
                     │                │               │
                     └── set_output_delay -max = 1.8 ns ──┘
```

---

## Center-Aligned vs Edge-Aligned Capture

Source-synchronous interfaces have a choice of where the capture clock edge falls relative to the data valid window:

### Center-Aligned (Preferred for DDR)

```
Data valid window:    ├──────────┤
                      ┌──────────┐
data                  └──────────┘
                      ↑          ↑
clk              ┌───┐          ┌───
                 ┘   └──────────┘
                 ↑
         clock edge centered in data valid window
         → Maximizes setup AND hold margin
```

```tcl
# Center-aligned: capture on clock edge that is 90° phase-shifted
create_generated_clock -name ddr_clk_90 \
    -source [get_ports clk_in] \
    -edges {1 2 3} -edge_shift {2.5 5.0 7.5} \
    [get_pins pll_inst/clk_90]
```

### Edge-Aligned (Simpler, Lower Speed)

```
data           ┌──────────┐
               └──────────┘
clk        ┌───┐          ┌───
           ┘   └──────────┘
           ↑   ↑
    data changes at clock edge → capture on OPPOSITE edge
    (or use PLL to shift for center-aligned capture)
```

---

## Common Interface Patterns

### RGMII (Reduced Gigabit Media Independent Interface)

125 MHz DDR, 4 data bits + 1 control bit. Clock forwarded with data:

```tcl
# RGMII receive: external PHY sends clk + data (source-synchronous)
create_clock -period 8.0 -name rgmii_rx_clk [get_ports eth_rx_clk]

# Data aligned to clock edge — use IDELAY to shift into center
set_input_delay -clock rgmii_rx_clk -max 1.0 [get_ports eth_rxd*]
set_input_delay -clock rgmii_rx_clk -min 0.0 [get_ports eth_rxd*]
set_input_delay -clock rgmii_rx_clk -max 1.0 [get_ports eth_rx_ctl]

# RGMII transmit: FPGA generates clk + data
create_generated_clock -name rgmii_tx_clk \
    -source [get_pins pll/clk_out_125] \
    -divide_by 1 [get_ports eth_tx_clk]

set_output_delay -clock rgmii_tx_clk -max 1.0 [get_ports eth_txd*]
set_output_delay -clock rgmii_tx_clk -min 0.0 [get_ports eth_txd*]
```

### SPI — Slow, Simple, System-Synchronous

```tcl
# SPI: FPGA is master, generates SCK. MISO captured on SCK edge.
create_clock -period 100.0 -name spi_sck [get_ports spi_clk]

# MISO comes from external device
set_input_delay -clock spi_sck -max 20.0 [get_ports spi_miso]
set_input_delay -clock spi_sck -min  5.0 [get_ports spi_miso]

# MOSI is driven by FPGA
set_output_delay -clock spi_sck -max 15.0 [get_ports spi_mosi]
set_output_delay -clock spi_sck -min  5.0 [get_ports spi_mosi]
```

### DDR3/DDR4 Memory — The Hard Case

DDR memory interfaces use specialized IO blocks (IODELAY, PHY, hard memory controller) that handle most timing internally. The FPGA fabric-side interface typically runs at 1/4 or 1/2 the DDR rate:

```tcl
# DDR3 at 800 MHz (400 MHz clock), UI runs at 200 MHz (1/4 rate)
create_clock -period 5.0 -name ddr_clk [get_ports ddr3_clk_p]

# The MIG/DDR controller generates these automatically.
# Fabric-side constraints: set_multicycle_path on the UI interface
set_multicycle_path -setup 2 -from [get_cells app_*_reg] -to [get_cells ddr_ui_*]
set_multicycle_path -hold  1 -from [get_cells app_*_reg] -to [get_cells ddr_ui_*]
```

---

## IO Timing Closure Checklist

| Step | Check |
|---|---|
| 1 | `create_clock` on every input clock (including forwarded clocks) |
| 2 | `set_input_delay -max/-min` for every input bus |
| 3 | `set_output_delay -max/-min` for every output bus |
| 4 | Verify min/max values against device datasheet (tco, tsu, th) |
| 5 | Add board trace delay estimates (~150 ps/inch for FR4) |
| 6 | `report_datasheet` to verify IO timing summary |
| 7 | Check both slow and fast corners |
| 8 | If using IODELAY/IDELAY: verify tap values in hardware |

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **No IO constraints** | Tool optimizes for internal timing only; IO paths fail in hardware | Add `set_input_delay`/`set_output_delay` for ALL IO |
| **Missing min delay** | Hold violations on IO paths at fast corner | Always set both `-min` and `-max` |
| **Ignoring board trace delay** | Timing looks good but fails in hardware (real delay unaccounted) | Add trace delay to both min and max |
| **Wrong clock for IO delays** | IO timing checked against unrelated clock | Verify `-clock` parameter |
| **DDR data aligned to wrong clock edge** | Data captured on the wrong half of the DDR cycle | Use PLL phase shift or IDELAY to center-align |
| **IO registers not placed in IOB** | Extra routing delay on IO paths | `set_property IOB TRUE` (XDC) or `FAST_INPUT_REGISTER` (QSF) |

---

## Cross-Vendor Quick Reference

| Operation | SDC (Intel/Lattice/Microchip) | XDC (Xilinx) | QSF (Intel) |
|---|---|---|---|
| Input delay | `set_input_delay -clock CLK -max 2.0 [get_ports din]` | Same | N/A — use SDC |
| Output delay | `set_output_delay -clock CLK -max 3.0 [get_ports dout]` | Same | N/A — use SDC |
| Register in IOB | `FAST_INPUT_REGISTER` / `FAST_OUTPUT_REGISTER` | `set_property IOB TRUE` | `set_instance_assignment FAST_INPUT_REGISTER ON` |
| IDELAY/ODELAY | IODELAY primitives (device-specific) | IDELAY/ODELAY primitives + `IDELAY_VALUE` | IODELAY primitives |

---

## Further Reading

| Article | Topic |
|---|---|
| [sdc_basics.md](sdc_basics.md) | Constraint syntax — clock, input/output delay basics |
| [clock_domain_crossing.md](clock_domain_crossing.md) | CDC constraints for IO clocks from different domains |
| [false_paths.md](false_paths.md) | False paths for async IO signals |
| [multicycle_paths.md](multicycle_paths.md) | Multicycle paths for source-synchronous DDR |
| [timing_closure.md](timing_closure.md) | Using IO timing reports in the closure loop |
| Xilinx UG903 | Vivado I/O Timing Constraints |
| Intel AN 433 | Constraining Source-Synchronous Interfaces |
