[← Section Home](README.md) · [← Project Home](../README.md)

# SDC / XDC / QSF — Timing Constraint Basics

> [!IMPORTANT]
> Without timing constraints, a synthesis tool optimizes for area and speed without understanding your clock frequencies or IO requirements. The result: a design that passes functional simulation but fails at speed on hardware. Constraints are not optional — they are the contract between your design intent and the tool's implementation.

This article covers the **cross-vendor common subset** of timing constraint syntax: clocks, generated clocks, IO delays, exceptions, and clock groups. For vendor-specific features (XDC's `set_property`, QSF's assignment groups, SDC-on-Quartus intricacies), see the per-tool articles in this section.

---

## Why Constraints Exist

An FPGA toolchain answers one question: *given this RTL and these constraints, can I place-and-route a circuit that meets timing at the specified frequencies?*

Without constraints, the tool makes guesses:
- It doesn't know your clock frequency → treats all paths as single-cycle at the slowest P&R estimate
- It doesn't know your IO timing → may place registers far from pins
- It doesn't know which paths are false → wastes effort optimizing paths you don't care about

The result is a design that may work, but with no guarantees — and when it fails, you have no benchmark for what "correct" looks like.

---

## The Three Constraint Languages

| Language | Used By | Origin | Key Differences |
|---|---|---|---|
| **SDC** (Synopsys Design Constraints) | Intel Quartus, Lattice Diamond, Microchip Libero, Synplify | Tcl-based, industry standard (IEEE/IEC 62530) | The baseline. Most tools implement a vendor-specific subset + extensions |
| **XDC** (Xilinx Design Constraints) | Xilinx Vivado | Originally a superset of SDC; has diverged | Replaces many SDC commands with `set_property`; uses `get_*` object model extensively |
| **QSF** (Quartus Settings File) | Intel Quartus (legacy) | Tcl-based but fundamentally different structure | Assignment groups, pin-centric model; still used alongside SDC in modern Quartus |

**The practical reality:** SDC works everywhere. XDC is SDC-like but has vendor-specific idioms. QSF is a parallel system in Intel tools — you use both SDC (for timing) and QSF (for pin assignments, device settings, compilation options).

---

## Clock Definitions

### create_clock — The Primary Clock

Every timing constraint file starts here. Define every input clock:

```tcl
# SDC / XDC: define a 100 MHz clock on port "clk"
create_clock -name sys_clk -period 10.0 [get_ports clk]

# With 50% duty cycle (default), waveform for non-50%:
create_clock -name sys_clk -period 10.0 -waveform {0 3.0} [get_ports clk]
#                                          rising at 0ns, falling at 3ns (30% duty)
```

### Intel Quartus SDC — Exact Same Syntax

```tcl
# Quartus SDC file (.sdc) — identical to standard SDC
create_clock -name sys_clk -period 10.0 [get_ports clk]
```

### Xilinx XDC — Close but With Object Model

```tcl
# XDC: nearly identical, but -name is optional and ports use get_ports
create_clock -period 10.000 -name sys_clk [get_ports clk]

# XDC also supports -add for multiple clocks on the same port:
create_clock -period 10.000 -name clk_100 [get_ports clk]
create_clock -add -name clk_125 -period 8.000 [get_ports clk]
```

### Intel QSF — Completely Different

```tcl
# QSF uses assignment pairs, not SDC commands
set_global_assignment -name FMAX_REQUIREMENT "100 MHz"
set_instance_assignment -name CLOCK_SETTINGS clock_name -to clk
```

---

## Generated Clocks

When a PLL, MMCM, or clock divider produces a new clock from a primary clock:

```tcl
# SDC: PLL output at 200 MHz (×2 multiplication of 100 MHz input)
create_generated_clock -name clk_200m     -source [get_ports clk]     -divide_by 1 -multiply_by 2     [get_pins pll_inst/clk_out]

# Simple divide-by-2 from a register
create_generated_clock -name clk_div2     -source [get_pins clk_reg/Q]     -divide_by 2     [get_pins clk_div_reg/Q]
```

### Common Pitfall: Missing Generated Clocks

If you define `clk_100` but forget to define the PLL's 200 MHz output, all logic in the 200 MHz domain is analyzed with the wrong period. The tool may pass timing when it should fail, or (more commonly) fail with confusing violations.

**Rule:** Every PLL/MMCM output that drives logic needs its own `create_generated_clock`.

---

## IO Timing Constraints

### set_input_delay / set_output_delay

These tell the tool how much of the timing budget is consumed *outside* the FPGA:

```tcl
# Input: data_valid arrives 2.0 ns after the clock edge (external device tco)
#         and must be stable for 0.5 ns before the next clock edge
set_input_delay -clock sys_clk -max 2.0 [get_ports data_in*]
set_input_delay -clock sys_clk -min 0.5 [get_ports data_in*]

# Output: FPGA must drive data_out such that it arrives 3.0 ns
#         before the external device's setup time
set_output_delay -clock sys_clk -max 3.0 [get_ports data_out*]
set_output_delay -clock sys_clk -min 0.0 [get_ports data_out*]
```

### The Mental Model

```
External Device                FPGA
┌──────────────┐              ┌─────────────┐
│  tco = 2ns   │   data_in    │ set_input_  │
│  (clock→Q)   │─────────────→│ delay -max  │
│              │              │   = 2.0 ns  │
│              │  Board trace │             │
│              │  delay = ?   │  FPGA must  │
│   clk        │              │  meet setup │
└──────┬───────┘              │  with       │
       └──────────────────────│  remaining  │
          shared clock        │  budget     │
                              └─────────────┘
```

`set_input_delay -max 2.0` means: "2.0 ns of the clock period is consumed before the signal reaches my FPGA pin. The tool must ensure the remaining budget is sufficient for internal routing + setup."

---

## Clock Groups and Exclusions

When clocks are unrelated (different sources, no fixed phase), paths between them are unconstrained by default but will still generate timing reports. Use clock groups to suppress meaningless violations:

```tcl
# SDC / XDC: clocks from different oscillators are asynchronous
set_clock_groups -asynchronous     -group [get_clocks sys_clk]     -group [get_clocks eth_rx_clk]     -group [get_clocks video_pclk]
```

> **Critical:** Clock group exclusion does NOT handle CDC safely. It only suppresses timing analysis. You still need synchronizers (2-FF, async FIFO) — see [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md).

---

## Timing Exceptions

### False Paths

Paths that can never cause functional failure — use sparingly:

```tcl
# SDC / XDC: data only captured when enable is high
set_false_path -from [get_ports async_config_signal]                -to [get_cells sync_ff_reg[0]]

# CDC synchronizer first stage (intentionally metastable)
# See cdc_coding.md for why this is safe
set_false_path -from [get_ports async_in]                -to [get_cells sync_ff_reg*]
```

### Multicycle Paths

When a path legitimately takes more than one clock cycle:

```tcl
# SDC / XDC: multiplier takes 4 cycles to produce result
set_multicycle_path -setup 4 -from [get_cells mult_in_reg*]                               -to [get_cells mult_out_reg*]
set_multicycle_path -hold  3 -from [get_cells mult_in_reg*]                               -to [get_cells mult_out_reg*]
```

**Hold multicycle is always N−1.** If setup is 4 cycles, hold is 3. This prevents the tool from artificially constraining hold to the launching edge.

---

## Cross-Vendor Cheat Sheet

| Operation | SDC (Intel / Lattice / Microchip) | XDC (Xilinx) | QSF (Intel legacy) |
|---|---|---|---|
| **Primary clock** | `create_clock -period 10.0 [get_ports clk]` | Same, plus `-name` optional | `set_global_assignment FMAX_REQUIREMENT` |
| **Generated clock** | `create_generated_clock -source ... -divide_by N` | Same | Not available; use SDC |
| **Input delay** | `set_input_delay -clock CLK -max 2.0 [get_ports din]` | Same | Not available; use SDC |
| **Output delay** | `set_output_delay -clock CLK -max 3.0 [get_ports dout]` | Same | Not available; use SDC |
| **False path** | `set_false_path -from ... -to ...` | Same | `set_instance_assignment FALSE_PATH` |
| **Multicycle** | `set_multicycle_path -setup N` | Same | Not available; use SDC |
| **Clock groups** | `set_clock_groups -asynchronous` | Same, plus `-physically_exclusive` / `-logically_exclusive` | Not available; use SDC |
| **Pin location** | `set_location_assignment PIN_A12 -to port_name` | `set_property PACKAGE_PIN A12 [get_ports port_name]` | `set_location_assignment PIN_A12 -to port_name` |
| **IO standard** | `set_instance_assignment IO_STANDARD "3.3-V LVTTL"` | `set_property IOSTANDARD LVCMOS33 [get_ports port_name]` | `set_instance_assignment IO_STANDARD "3.3-V LVTTL"` |

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| **No constraints file at all** | Tool uses 1 GHz default clock; fails every path | Define at minimum: `create_clock` for every input clock |
| **Missing generated clock** | PLL output logic fails timing with wrong period | `create_generated_clock` for every PLL/MMCM output |
| **Using same constraint for all IOs** | Some pins fail setup, others fail hold | Per-bus `set_input_delay`/`set_output_delay` with realistic min/max |
| **`set_clock_groups -asynchronous` without synchronizers** | Noise-free timing report; intermittent silicon failure | Clock groups suppress analysis; you STILL need synchronizers |
| **Hold multicycle set to same as setup** | Hold violation on first edge because tool constrains hold to launch edge | Hold multicycle = setup multicycle − 1 |
| **Applying constraints to wrong objects** | Constraint silently ignored | Use `report_clock_networks` / `report_clocks` to verify constraints are applied |

---

## Quick Start Template

```tcl
# === CLOCKS ===
create_clock -period 10.0 -name sys_clk [get_ports clk_100m]
create_clock -period 8.0  -name pcie_clk [get_ports pcie_refclk_p]

# === PLL OUTPUTS ===
create_generated_clock -name clk_200m     -source [get_pins pll_inst/clk_in]     [get_pins pll_inst/clk_out_200m]
create_generated_clock -name clk_50m     -source [get_pins pll_inst/clk_in]     -divide_by 2     [get_pins pll_inst/clk_out_50m]

# === IO TIMING ===
set_input_delay -clock sys_clk -max 2.0 [get_ports data_in*]
set_input_delay -clock sys_clk -min 0.5 [get_ports data_in*]
set_output_delay -clock sys_clk -max 3.0 [get_ports data_out*]
set_output_delay -clock sys_clk -min 0.0 [get_ports data_out*]

# === CLOCK GROUPS ===
set_clock_groups -asynchronous \
    -group [get_clocks sys_clk clk_200m clk_50m] \
    -group [get_clocks pcie_clk]

# === FALSE PATHS ===
set_false_path -from [get_ports rst_n]  # Reset is static during operation
set_false_path -from [get_ports async_signal] -to [get_cells sync_ff_reg[0]]

# === VERIFY ===
report_clock_networks
report_clocks
check_timing
```

---

## Further Reading

| Resource | Description |
|---|---|
| [cdc_coding.md](../04_hdl_and_synthesis/cdc_coding.md) | CDC patterns and metastability — the complement to timing constraints |
| [clock_domain_crossing.md](clock_domain_crossing.md) | CDC constraint methodology (false paths, max_delay) |
| [false_paths.md](false_paths.md) | When and how to use false paths safely |
| [multicycle_paths.md](multicycle_paths.md) | Multicycle path patterns and hold adjustment |
| [timing_closure.md](timing_closure.md) | End-to-end timing closure methodology |
| [io_timing.md](io_timing.md) | Source-synchronous, system-synchronous, and DDR IO timing |
| Synopsys SDC Specification | IEEE/IEC 62530 — the standard |
| Xilinx UG903 | Vivado Using Constraints — the definitive XDC reference |
| Intel AN 433 | Constraining and Analyzing Source-Synchronous Interfaces |
