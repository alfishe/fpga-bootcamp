[← 14 References Home](README.md) · [← Project Home](../../README.md)

# Constraint Quick Reference: XDC, SDC, and LPF Rosetta Stone

## Overview

Timing and physical constraints are the mechanism by which the designer communicates board-level intent (clock frequencies, pin locations, IO standards, and external delays) to the FPGA synthesis and implementation engines. While the industry has largely converged on Synopsys Design Constraints (SDC) for timing, the syntax for physical constraints (pins, I/O standards) remains fiercely vendor-specific. This reference provides a translation matrix between Xilinx (XDC), Intel/Altera (SDC/QSF), and Lattice (LPF) to rapidly port designs across platforms.

## Physical Constraints (Pinout & IO Standards)

Physical constraints map top-level RTL ports to physical package pins and define the electrical characteristics (drive strength, pull-ups) of those pins.

| Intent | Xilinx Vivado (XDC) | Intel Quartus (QSF) | Lattice Diamond (LPF) |
|---|---|---|---|
| **Pin Location** | `set_property PACKAGE_PIN Y9 [get_ports clk]` | `set_location_assignment PIN_Y9 -to clk` | `LOCATE COMP "clk" SITE "Y9" ;` |
| **I/O Standard** | `set_property IOSTANDARD LVCMOS33 [get_ports rx]` | `set_instance_assignment -name IO_STANDARD "3.3-V LVCMOS" -to rx` | `IOBUF PORT "rx" IO_TYPE=LVCMOS33 ;` |
| **Pull-Up Resistor** | `set_property PULLUP true [get_ports i2c_sda]` | `set_instance_assignment -name WEAK_PULL_UP_RESISTOR ON -to i2c_sda` | `IOBUF PORT "i2c_sda" PULLMODE=UP ;` |
| **Drive Strength** | `set_property DRIVE 12 [get_ports tx]` | `set_instance_assignment -name CURRENT_STRENGTH_NEW 12MA -to tx` | `IOBUF PORT "tx" DRIVE=12 ;` |

## Timing Constraints (SDC-based)

Both Xilinx (XDC) and Intel (SDC) utilize the Tcl-based SDC syntax for timing. Lattice uses a proprietary syntax (LPF) for Diamond, but utilizes standard SDC for its newer Radiant toolchain and in open-source tools like `nextpnr`.

| Intent | XDC / SDC (Xilinx, Intel, Radiant) | LPF (Lattice Diamond) |
|---|---|---|
| **Primary Clock** | `create_clock -name sys_clk -period 10.0 [get_ports clk_in]` | `FREQUENCY PORT "clk_in" 100.0 MHz ;` |
| **Generated Clock** | `create_generated_clock -name div_clk -source [get_pins pll/in] -divide_by 2 [get_pins pll/out]` | (Inferred automatically by PLL block) |
| **Clock Groups (Async)** | `set_clock_groups -asynchronous -group [get_clocks clkA] -group [get_clocks clkB]` | `BLOCK ASYNCPATHS ;` (Global) |
| **False Path** | `set_false_path -from [get_cells rst_reg] -to [get_cells core/*]` | `BLOCK PATH FROM REG "rst_reg" TO CELL "core/*" ;` |

## Advanced Timing Definitions

### I/O Timing (Setup and Hold at the boundary)
When interfacing with external chips, you must define the clock-to-out and setup/hold times of the *external* device so the FPGA router knows how to meet timing at the I/O ring.

```tcl
# XDC/SDC Example: Input delay for an external ADC
# The ADC guarantees data is stable 2ns after the clock edge, and holds for 1ns before the next edge.
create_clock -name adc_clk -period 10.0 [get_ports adc_clk_in]
set_input_delay -clock adc_clk -max 2.0 [get_ports adc_data[*]]
set_input_delay -clock adc_clk -min 1.0 [get_ports adc_data[*]]
```

### Multicycle Paths
Used when the logic between two registers requires more than one clock cycle to resolve, but the registers share the same clock domain (e.g., a complex DSP multiplier with a clock enable).

```tcl
# XDC/SDC: Tell the router it has 3 cycles for setup, and adjust hold accordingly
set_multicycle_path -setup -from [get_cells mult_in_reg*] -to [get_cells mult_out_reg*] 3
set_multicycle_path -hold  -from [get_cells mult_in_reg*] -to [get_cells mult_out_reg*] 2
```

## Pitfalls & Common Mistakes

### 1. Mixing up `-name` and `[get_ports]`
In SDC/XDC, `create_clock` requires you to define a logical name for the clock and bind it to a physical net/port.

**Bad Code:**
```tcl
# Will create a virtual clock not attached to any physical pin!
create_clock -name [get_ports sys_clk] -period 10.0
```

**Good Code:**
```tcl
# Logical name is 'sys_clk_100', attached to the physical top-level port 'sys_clk'
create_clock -name sys_clk_100 -period 10.0 [get_ports sys_clk]
```

### 2. The Unconstrained I/O Fallacy
Beginners often constrain the primary clock and ignore I/O constraints. 

> [!WARNING]
> **Missing I/O Constraints:** If you do not apply `set_input_delay` and `set_output_delay`, the place-and-route engine considers the I/O paths as **unconstrained**. It will place the I/O registers randomly in the fabric instead of the IOB (Input/Output Block), causing massive, unpredictable setup/hold violations when communicating with external chips.

### 3. Misusing `set_false_path` for CDC
Using `set_false_path` between two asynchronous clock domains prevents the tool from reporting timing errors, but it **does not** synchronize the signals or prevent metastability.

**Antipattern:**
```tcl
# Blindly ignoring crossing errors without a synchronizer
set_false_path -from [get_clocks clk_100] -to [get_clocks clk_50]
```

**Good Practice:**
You must still use a 2-FF synchronizer, async FIFO, or handshake protocol in RTL. Once the synchronizer is physically present, use `set_clock_groups -asynchronous` or specifically target the synchronizer's first stage with `set_max_delay -datapath_only`.

## Code Example: Full RGMII Constraint Set (XDC)

A real-world example showing physical and timing constraints combining for a gigabit ethernet interface.

```tcl
# 1. Physical Constraints
set_property PACKAGE_PIN M16 [get_ports rgmii_rxc]
set_property IOSTANDARD LVCMOS25 [get_ports rgmii_rxc]
set_property PACKAGE_PIN M18 [get_ports {rgmii_rxd[0]}]
set_property IOSTANDARD LVCMOS25 [get_ports {rgmii_rxd[0]}]

# 2. Timing Constraints: The 125 MHz RGMII RX Clock
create_clock -name rx_clk -period 8.000 [get_ports rgmii_rxc]

# 3. I/O Constraints: Double Data Rate (DDR) Input Delays
# RGMII specifies 1.2ns min/max delay
set_input_delay -clock [get_clocks rx_clk] -max 1.200 [get_ports rgmii_rxd*]
set_input_delay -clock [get_clocks rx_clk] -min -1.200 [get_ports rgmii_rxd*]
set_input_delay -clock [get_clocks rx_clk] -max 1.200 [get_ports rgmii_rxd*] -clock_fall -add_delay
set_input_delay -clock [get_clocks rx_clk] -min -1.200 [get_ports rgmii_rxd*] -clock_fall -add_delay
```

## Clock Domain Crossing Constraints

### Asynchronous Clock Groups

```tcl
# XDC/SDC: Declare two clock domains as asynchronous
create_clock -name clk_100 -period 10.0 [get_ports clk_100_in]
create_clock -name clk_50  -period 20.0 [get_ports clk_50_in]
set_clock_groups -asynchronous -group [get_clocks clk_100] -group [get_clocks clk_50]
```

| Approach | When to Use | Risk |
|---|---|---|
| `set_clock_groups -asynchronous` | True async domains with synchronizers | Low — correct for CDC with 2-FF sync |
| `set_false_path -from ... -to ...` | One-off paths (e.g., reset sync) | Medium — doesn't cover new paths added later |
| `set_max_delay -datapath_only` | Constrain path length within CDC | Best — limits how bad the skew can get |

### Generated Clock Constraints

```tcl
# PLL/MMCM output clocks must be declared as generated clocks
create_generated_clock -name clk_200 \
  -source [get_pins pll/clk_in] \
  -multiply_by 2 \
  [get_pins pll/clk_out]

# Clock from serializer (e.g., DDR output)
create_generated_clock -name clk_ddr_out \
  -source [get_pins serdes/clk_in] \
  -divide_by 1 \
  [get_ports ddr_clk_p]
```

### Common Missing Constraints

| Missing Constraint | Symptom | Fix |
|---|---|---|
| No `create_clock` on input port | Unconstrained paths, random placement | Add `create_clock` for every top-level clock input |
| No `set_input_delay` / `set_output_delay` | I/O timing ignored by P&R | Add I/O delays based on external device datasheet |
| No `set_clock_groups` for async domains | False timing failures across CDC | Add `-asynchronous` between truly independent clocks |
| Missing generated clock on PLL output | Paths from PLL output are unconstrained | Add `create_generated_clock` on PLL output pin |
| No `set_multicycle_path` for enabled logic | Failing setup on multi-cycle paths | Add MCP for logic with clock enable |

---

## Physical Constraints: Advanced Patterns

### Differential I/O

```tcl
# XDC: Differential LVDS output pair
set_property IOSTANDARD LVDS_25 [get_ports data_p]
set_property IOSTANDARD LVDS_25 [get_ports data_n]
set_property PACKAGE_PIN A1 [get_ports data_p]
set_property PACKAGE_PIN A2 [get_ports data_n]  # Must be the negative pair pin

# Intel QSF: Differential LVDS
set_instance_assignment -name IO_STANDARD "LVDS" -to data_p
set_location_assignment PIN_A1 -to data_p
```

### Clock-Capable I/O Constraints

```tcl
# XDC: Route clock to clock-capable pin (required for MMCM/PLL)
set_property CLOCK_DEDICATED_ROUTE TRUE [get_nets clk_in]
# If accidentally routed through fabric:
# ERROR: [Place 30-574] Non-clock resource used for clock signal
```

### Multi-Voltage I/O Banks

```tcl
# XDC: Different I/O standards per bank (VADJ must be set correctly)
set_property IOSTANDARD LVCMOS18 [get_ports {bank34_*}]  # Bank 34 = 1.8V
set_property IOSTANDARD LVCMOS33 [get_ports {bank35_*}]  # Bank 35 = 3.3V
```

---

## Gowin Constraint Syntax (SDC/CST)

Gowin uses SDC for timing and CST for physical constraints:

| Intent | Gowin SDC (Timing) | Gowin CST (Physical) |
|---|---|---|
| **Clock** | `create_clock -name sys -period 20 [ports clk]` | `IO_LOC "clk" 15;` |
| **Pin** | N/A | `IO_PORT "led" IO_TYPE=LVCMOS33 DRIVE=8;` |
| **False path** | `set_false_path -from [ports clk_a] -to [ports clk_b]` | N/A |

---

## Cross-References

| Topic | Article |
|---|---|
| SDC deep dive | [SDC Basics](../05_timing_and_constraints/sdc_basics.md) |
| Clock network design | [Clock Network Design](../02_architecture/infrastructure/clock_network_design.md) |
| CDC design patterns | [Design Patterns](../04_hdl_and_synthesis/design_patterns.md) |
| Vendor migration constraints | [Vendor Migration](../03_design_flow/vendor_migration.md) |

---

## References

- [UG903: Vivado Using Constraints](https://docs.xilinx.com/)
- [Intel Quartus Prime Timing Analyzer Cookbook](https://www.intel.com/)
- [Lattice Diamond Help: LPF Syntax](#)
- [SDC Basics](../05_timing_and_constraints/sdc_basics.md)
- [Gowin SDC/CST User Guide](https://www.gowinsemi.com/)
- [Xilinx UG912: Design Analysis and Closure](https://docs.xilinx.com/)
