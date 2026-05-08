[← Infrastructure Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# Power Estimation & Management — Static Power, Dynamic Power, Clock Gating, Vendor Tools

FPGA power consumption is the sum of static leakage (transistors draw current even when idle) and dynamic switching (every toggling net charges and discharges capacitance). On modern FPGAs at 16 nm and below, static power can exceed 40% of total power at low utilization. This article covers how to estimate power before silicon, how to measure it on the bench, and how to reduce it through RTL and architecture decisions.

For power delivery network (PDN) design — decoupling, sequencing, IR drop — see [Power Integrity](../../09_boards_and_board_design/power_integrity.md). For clock architecture, see [Clocking](clocking.md). For thermal design, see [Thermal Design](../../09_boards_and_board_design/thermal_design.md).

---

## Power Components

### Static Power (Quiescent)

| Source | Mechanism | Typical % of Total | Scales With |
|--------|-----------|-------------------|-------------|
| **Subthreshold leakage** | MOSFET channel not fully off at low Vth | 60–80% of static | Temperature (∝ T²), process node |
| **Gate leakage** | Tunneling through thin gate oxide | 10–20% of static | Oxide thickness, voltage |
| **Junction leakage** | Reverse-biased PN junctions | 5–10% of static | Die area, temperature |

**Key insight:** Static power doubles approximately every 10–15°C. A device specified at 85°C junction draws roughly 2× the static power of the same device at 55°C.

```
P_static ≈ P_leak(T_junction)
          ≈ P_leak(25°C) × e^(α × (T_junction - 25°C))
          where α ≈ 0.03–0.05 /°C (vendor-specific)
```

### Dynamic Power

| Source | Mechanism | Typical % of Total | Scales With |
|--------|-----------|-------------------|-------------|
| **Clock tree** | BUFG → H-tree → thousands of FF clock pins | 30–50% of dynamic | Clock frequency, FF count, toggle rate |
| **Logic switching** | LUT + routing capacitance per toggle | 20–40% of dynamic | Activity factor, frequency, routing length |
| **BRAM/DSP switching** | Read/write port activity | 10–20% of dynamic | Access rate, port width |
| **I/O switching** | IOB output driver + termination | 5–15% of dynamic | Number of outputs, frequency, IO standard |
| **Transceiver** | Serializer + CDR + TX driver | 0–30% of dynamic | Line rate per channel × channel count |

```
P_dynamic = α × C × V² × f

Where:
  α = activity factor (0.0–1.0, typical 0.05–0.20 for logic)
  C = switched capacitance (function of routing + load)
  V = core voltage (0.85–1.0V on 16nm/7nm)
  f = clock frequency (Hz)
```

---

## Power Estimation Flow

### Stage 1: Pre-RTL (Early Estimation)

Before writing any HDL, estimate using vendor spreadsheet or web estimator:

| Tool | Vendor | URL / Access | Input | Output |
|------|--------|-------------|-------|--------|
| **Xilinx Power Estimator (XPE)** | AMD/Xilinx | [XPE web tool](https://www.xilinx.com/products/technology/power/xpe.html) | Device, clock freq, resource count, toggle rates | Total power by rail, thermal |
| **Intel Early Power Estimator (EPE)** | Intel/Altera | Intel website (Excel) | Device, resource utilization | Power by rail, ICB current |
| **Lattice Power Calculator** | Lattice | Diamond/Radiant GUI | Device, resource count | Total & per-rail power |
| **Microchip Libero Power Estimator** | Microchip | Libero SoC | Device, clock, toggle rate | Total power |
| **Gowin Power Analyzer** | Gowin | Gowin EDA GUI | Post-synthesis netlist | Estimated power |

**Accuracy:** ±30% at this stage. Useful for power supply sizing and thermal planning.

### Stage 2: Post-Synthesis

After synthesis, the tool knows actual resource usage and can estimate routing capacitance:

| Tool | Input | Accuracy | Speed |
|------|-------|----------|-------|
| **Vivado `report_power`** | Post-synth netlist + activity file | ±20% | Minutes |
| **Quartus Power Analyzer** | Post-synth + VCD/FSDB | ±15% | Minutes |
| **Libero SmartPower** | Post-synth + activity | ±20% | Minutes |

### Stage 3: Post-Implementation (Most Accurate)

After place-and-route, the tool has exact routing capacitance:

| Tool | Command | Input | Accuracy |
|------|---------|-------|----------|
| **Vivado** | `report_power -file power.rpt` | Post-impl netlist + SAIF/VCD | ±10% |
| **Quartus** | Power Analyzer Tool | Post-fit + VCD/FSDB | ±10% |
| **Diamond** | Power Calculator | Post-route + toggle data | ±15% |

### Activity File Generation

The most common error in power estimation is using default toggle rates (50%) instead of real activity:

```tcl
# Vivado: generate SAIF from simulation
# 1. Run behavioral simulation with design activity
# 2. Write SAIF from simulator
# 3. Read SAIF into Vivado for power estimation

# In Vivado Tcl:
read_saif -hw_netlist impl/netlist.v -input sim_output.saif
report_power -file power_with_saif.rpt
```

```tcl
# Quartus: generate VCD from simulation
# In ModelSim:
# vcd file power.vcd
# vcd add -r /dut/*
# run -all
# vcd flush

# In Quartus:
# Assignments → Settings → Power Analyzer Tool → Input File: power.vcd
```

**Default toggle rate vs real activity impact:**

| Scenario | Default (50% toggle) | Real SAIF | Overestimate |
|----------|---------------------|-----------|-------------|
| Video pipeline (high activity) | 8.2W | 7.5W | 9% |
| Control logic (low activity) | 4.1W | 2.3W | 78% |
| Idle state (no activity) | 3.8W | 1.1W | 245% |

**Always feed real activity data into power estimation for meaningful results.**

---

## Power Reduction Techniques

### RTL-Level Techniques

#### 1. Clock Gating

The single most effective technique — a gated clock stops all toggling in the disabled domain:

```verilog
// BAD: clock enable wastes power on clock tree
always @(posedge clk) begin
    if (clk_en) begin
        data_reg <= data_in;
    end
    // FF clock pin still toggles even when clk_en=0!
end

// GOOD: inferred clock gating
// Synthesis inserts an integrated clock-gating cell (ICG)
// that gates the clock at the buffer output
module gated_domain (
    input  wire        clk,
    input  wire        rst,
    input  wire        enable,
    input  wire [15:0] data_in,
    output reg  [15:0] data_out
);

    // Xilinx / Intel synthesis will infer BUFGCE or clock-gating cell
    reg clk_gated;
    always @(*) begin
        clk_gated = clk & enable;  // Latch-based gating inferred
    end

    always @(posedge clk_gated) begin
        if (rst)
            data_out <= 0;
        else
            data_out <= data_in;
    end

endmodule
```

**Better approach — use vendor primitives for clock gating:**

```verilog
// Xilinx: BUFGCE (global buffer with clock enable)
BUFGCE u_bufgce (
    .I  (clk),
    .CE (enable),
    .O  (clk_gated)
);

// Intel: use altera_clock_gating IP
// Or infer via synthesis: the tool inserts ICG automatically
// when it detects the pattern below
```

| Clock Gating Method | Vendor | Glitch-Free | Power Saving |
|---------------------|--------|------------|-------------|
| `BUFGCE` | Xilinx | Yes (HW) | Full clock tree |
| `BUFHCE` | Xilinx (regional) | Yes (HW) | Regional clock tree |
| `ALTCLKCTRL` | Intel | Yes (HW) | Clock network segment |
| Inferred ICG | Both | Yes (latch-based) | Full clock tree |
| `assign gated = clk & en` | Any | **No (glitches!)** | Unsafe — never use |

#### 2. Operand Isolation

Prevent unnecessary switching in datapath when output is not used:

```verilog
module operand_isolation (
    input  wire        clk,
    input  wire        valid,
    input  wire [15:0] a, b,
    output reg  [31:0] result
);

    reg [15:0] a_gated, b_gated;

    // Gated inputs: hold previous value when not valid
    // Prevents multiplier inputs from toggling uselessly
    always @(posedge clk) begin
        if (valid) begin
            a_gated <= a;
            b_gated <= b;
        end
        // else: a_gated and b_gated hold → multiplier inputs stable
    end

    always @(posedge clk) begin
        result <= a_gated * b_gated;
    end

endmodule
```

**Impact:** For a 16×16 multiplier switching at 200 MHz with α=0.1, operand isolation can reduce DSP power by 40–60%.

#### 3. Data-Dependent Clock Gating

Gate individual BRAM read ports when not accessed:

```verilog
// BRAM with gated read clock
reg rd_en_gated;
always @(posedge clk) begin
    rd_en_gated <= rd_en;  // registered enable
end

// Only assert read when actually needed
// When rd_en=0, BRAM internal sense amps don't fire
```

### Architecture-Level Techniques

#### 4. Clock Frequency Reduction

Power ∝ frequency. Running at 2× the required frequency wastes 2× the power:

| Design | Clock | Logic Resources | Power | Throughput |
|--------|-------|-----------------|-------|------------|
| Single-clock @ 200 MHz | 200 MHz | 1× | 1× | 200 Mops/s |
| Dual-clock @ 100 MHz × 2 pipelines | 100 MHz | 1.2× | 0.65× | 200 Mops/s |

**The dual-pipeline approach uses 20% more area but 35% less power.**

#### 5. Power Domains (Partial Power-Down)

Some FPGAs support partial reconfiguration as a proxy for power gating:

```
┌───────────────────────────────────────────┐
│              FPGA Fabric                   │
│  ┌─────────────┐  ┌─────────────────┐    │
│  │ Always-On   │  │ Processing Core │    │
│  │ Domain      │  │ (DFX Module)    │    │
│  │ - Clocks    │  │ - Can be swapped│    │
│  │ - Control   │  │   to idle bit-  │    │
│  │ - Comm      │  │   stream when   │    │
│  └─────────────┘  │   not needed    │    │
│                    └─────────────────┘    │
└───────────────────────────────────────────┘
```

With DFX, you can swap a heavy processing module with a minimal "sleep" module that draws near-zero dynamic power. See [DFX & Partial Reconfiguration](../../16_advanced_topics/dfx_partial_reconfiguration.md).

#### 6. Voltage Scaling

Some FPGA families support voltage margining (reducing VCCINT below nominal):

| Family | VCCINT Nominal | Minimum (typical) | Power Reduction | fMAX Impact |
|--------|---------------|-------------------|----------------|-------------|
| Xilinx 7-series | 1.0V | 0.95V | ~10% | -5–10% |
| Xilinx UltraScale+ | 0.85V | 0.80V | ~12% | -5–8% |
| Intel Cyclone 10 GX | 0.9V | 0.87V | ~8% | -3–5% |
| Lattice ECP5 | 1.1V | 1.05V | ~9% | -5% |

> **Warning:** Undervolting voids warranties and is not guaranteed by vendors. Only use for thermally constrained designs where you can verify timing at the reduced voltage.

---

## Vendor Power Estimation Tools — Walkthrough

### Vivado Power Analysis

```tcl
# 1. After implementation, generate power report
open_checkpoint impl.dcp
report_power -file power_report.rpt -verbose

# 2. With SAIF activity data (recommended)
read_saif impl.saif
report_power -file power_with_saif.rpt

# 3. Set toggle rates manually (less accurate)
set_switching_activity -toggle_rate 0.1 -static_probability 0.5 [get_nets data_bus*]

# 4. Power report sections:
#    - Power Summary (total, on-chip, off-chip)
#    - Power by Rail (VCCINT, VCCBRAM, VCCIO, etc.)
#    - Power by Block (BRAM, DSP, Logic, Clock, IO)
#    - Power by Hierarchy (per-module breakdown)
#    - Confidence level (Low/Medium/High)
```

**Understanding the confidence metric:**

| Confidence | Meaning | How to Improve |
|-----------|---------|---------------|
| **Low** | Using default toggle rates | Provide SAIF/VCD |
| **Medium** | Some nodes have real activity | Provide full SAIF |
| **High** | All nodes have real activity data | Full SAIF + post-impl netlist |

### Quartus Power Analyzer

```tcl
# 1. Enable power analysis
set_global_assignment -name POWER_PRESET_COOLING_SOLUTION "NO HEAT SINK WITH STILL AIR"
set_global_assignment -name POWER_BOARD_THERMAL_MODEL "NONE (DEFAULT)"

# 2. After fitter, run power analysis
execute_flow -analyze_power

# 3. With VCD activity
set_global_assignment -name POWER_INPUT_VCD_FILE "power.vcd"
set_global_assignment -name POWER_VCD_FILE_GLITCH_LENGTH "0.1 ns"

# 4. Results: Power Analyzer Report
#    - Total thermal power
#    - Dynamic vs static breakdown
#    - By block type
#    - By clock domain
#    - Junction temperature estimate
```

### Lattice Diamond / Radiant

```tcl
# Diamond Power Calculator
# Tools → Power Calculator → Run

# Radiant Power Analysis
# Run → Power Analysis
# Requires post-route database
```

### Open-Source: Yosys + nextpnr

Yosys does not have a built-in power estimator. For open-source flows:

1. Use vendor estimator for the target device (even if using Yosys for P&R)
2. For iCE40/ECP5, use Lattice Power Calculator with Yosys utilization numbers
3. For simulation-based activity, generate VCD from Verilator or GHDL

---

## Measuring Power on the Bench

### Current Sense Resistors

Most dev boards include current-sense resistors on key rails:

| Rail | Typical Shunt | Measurement | Tool |
|------|---------------|-------------|------|
| VCCINT | 10 mΩ | Voltage across shunt | DMM or INA219 |
| VCCIO | 50 mΩ | Voltage across shunt | DMM |
| MGTAVCC | 10 mΩ | Voltage across shunt | DMM |

```
P = V_rail × I = V_rail × (V_shunt / R_shunt)
```

### Bench Measurement Procedure

1. **Idle power:** Program a minimal bitstream (single BUFG + inverter). Measure P_static.
2. **Design power:** Program full design. Measure total power.
3. **Dynamic power:** P_dynamic = P_total - P_static
4. **Per-clock domain:** Gate each clock one at a time and measure the difference.

### Vendor Tools for Real-Time Power

| Tool | Vendor | Access Method |
|------|--------|---------------|
| **Xilinx XADC / SysMon** | Xilinx | JTAG or AXI register reads — voltage, current (with shunt), temperature |
| **Intel Sensor Monitoring** | Intel | JTAG or Avalon register — temperature, voltage |
| **Microchip Temp/Volt Monitor** | Microchip | MSS register reads |

```tcl
# Vivado: read XADC for on-chip temperature and voltage
create_hw_axi_txn rd_temp [get_hw_axis] -address 0x32_4000 -len 1 -type read
```

---

## Power Budget Template

| Parameter | Min | Typical | Max | Unit |
|-----------|-----|---------|-----|------|
| VCCINT static | — | 0.8 | 1.5 | W |
| VCCINT dynamic | — | 2.5 | 6.0 | W |
| VCCBRAM | — | 0.3 | 1.0 | W |
| VCCAUX | — | 0.2 | 0.5 | W |
| VCCIO total (all banks) | — | 0.5 | 2.0 | W |
| MGT (per channel) | — | 0.15 | 0.3 | W |
| **Total on-chip** | — | **4.45** | **11.3** | **W** |
| T_junction max | — | — | 85 | °C |
| T_ambient | — | 25 | 55 | °C |
| θ_JA (with heatsink) | — | 5 | 8 | °C/W |

```
T_junction = T_ambient + (P_total × θ_JA)
           = 55 + (4.45 × 5) = 77.25°C  ← OK (below 85°C limit)
           = 55 + (11.3 × 8) = 145.4°C   ← EXCEEDS LIMIT — need better cooling
```

---

## Quick Reference — Power Reduction Checklist

| # | Technique | Est. Savings | Effort | When to Apply |
|---|-----------|-------------|--------|--------------|
| 1 | Clock gating (ICG) | 30–50% dynamic | Low | Any design with idle domains |
| 2 | Operand isolation | 20–40% DSP/BRAM | Low | Datapath with sporadic valid |
| 3 | Reduce clock frequency | ∝ frequency | Medium | Over-clocked designs |
| 4 | Use low-power attributes | 5–15% | Low | `(* use_dsp = "no" *)` for small multiplies |
| 5 | DFX idle module swap | 50–90% of module | High | Systems with duty-cycled modes |
| 6 | Undervolting (VCCINT) | 10–15% | High | Thermally constrained, at own risk |
| 7 | Disable unused BRAM ports | 5–10% BRAM | Low | Write-only or read-only memories |
| 8 | Use BRAM output register | 5–8% | Low | Reduces internal switching |
| 9 | Compact state encoding | 2–5% | Low | One-hot for speed, binary for area/power |
| 10 | Choose smaller device | 30–60% static | High | Right-size the FPGA for the task |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Power delivery network design | [Power Integrity](../../09_boards_and_board_design/power_integrity.md) |
| Thermal management | [Thermal Design](../../09_boards_and_board_design/thermal_design.md) |
| Clock architecture | [Clocking](clocking.md) |
| Clock network design | [Clock Network Design](clock_network_design.md) |
| DFX & partial reconfiguration | [DFX](../../16_advanced_topics/dfx_partial_reconfiguration.md) |
| IO standards & voltage banks | [IO Standards](io_standards.md) |
