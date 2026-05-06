[← Advanced Topics Home](README.md) · [← Project Home](../README.md)

# FPGA Power Optimization — Clock Gating, Operand Isolation, and Power-Aware Design

FPGA power consumption is the sum of three components: static (leakage), dynamic (switching), and IO (off-chip drivers). For modern 28nm and below devices, dynamic power dominates at high activity factors, while static power dominates at low activity. Reducing FPGA power is not a single technique but a disciplined approach across the design stack: architecture-level decisions (clock domains, pipeline depth), RTL-level coding (clock gating, operand isolation), tool-level settings (power-aware synthesis, placement), and board-level design (voltage regulator efficiency, IO standards). This article covers all techniques with quantified impact and vendor-specific tool flows.

> [!NOTE]
> For board-level power delivery design (PDN, decoupling, sequencing), see [Power Integrity](../09_boards_and_board_design/power_integrity.md). This article covers chip-level and RTL-level power optimization.

---

## Power Model: Where the Watts Go

### Power Breakdown

| Component | Typical Share | 28nm | 16nm | 7nm |
|---|---|---|---|---|
| **Dynamic (switching)** | 50–80% | 60% | 55% | 50% |
| **Static (leakage)** | 15–40% | 25% | 30% | 35% |
| **IO (off-chip)** | 5–20% | 15% | 15% | 15% |

### Dynamic Power Equation

\[
P_{dynamic} = \alpha \cdot C \cdot V^2 \cdot f
\]

Where:
- **α** = Activity factor (0–1, fraction of toggles per clock)
- **C** = Capacitance of the switching node
- **V** = Supply voltage
- **f** = Clock frequency

**Key insight:** Voltage has a quadratic effect. Reducing V by 10% cuts dynamic power by ~19%. Reducing frequency by 10% cuts dynamic power by 10% linearly. Reducing activity by 10% cuts power by 10%.

---

## Technique 1: Clock Gating

Clock gating disables the clock to idle logic, eliminating all dynamic power in the gated domain. It is the single most effective power reduction technique.

### Global Clock Gating (BUFGCE)

Xilinx provides the BUFGCE (Global Clock Buffer with Clock Enable) primitive that gates the global clock tree:

```verilog
// BUFGCE: Global clock gating with glitch-free enable
wire clk_gated;
wire clk_enable;

BUFGCE u_bufgce (
    .CE (clk_enable),     // Clock enable — 0 = hold output low
    .I  (clk_100m),       // Input clock
    .O  (clk_gated)       // Gated output clock
);

// When clk_enable = 0, the entire clock tree stops toggling
// All flip-flops clocked by clk_gated consume zero dynamic power
```

**Impact:** 30–60% dynamic power reduction for the gated domain, depending on duty cycle.

### Local Clock Gating (Flip-Flop Clock Enable)

Most FPGA flip-flops have a built-in clock enable (CE) pin. When CE is low, the flip-flop holds its value and does not consume switching power on its data input:

```verilog
// Without clock enable: FF toggles every cycle
always @(posedge clk) begin
    if (enable) begin
        data_out <= data_in;   // Captures only when enable=1
    end
    // When enable=0, data_out holds — but internal mux still toggles
end

// With explicit CE: FF input mux does not toggle when CE=0
// The synthesizer maps this to the FF's CE pin automatically
always @(posedge clk) begin
    if (enable)
        data_out <= data_in;
end
```

> [!NOTE]
> In Xilinx FPGAs, the flip-flop CE pin is a dedicated hardware signal. When deasserted, the internal multiplexer that selects between D and Q is disabled — reducing power without any clock glitch risk.

### Intel Clock Gating

Intel FPGAs use the same flip-flop CE mechanism. For global clock gating, Intel provides the `CLKENA` primitive:

```verilog
// Intel Arria 10 / Agilex: Clock gating via CLKENA
wire clk_gated;
wire clk_enable;

cyclone10_clkena u_clkena (
    .clkin   (clk_100m),
    .ena     (clk_enable),
    .clkout  (clk_gated)
);
```

### Quantified Impact

| Gating Strategy | Power Savings | Complexity | Risk |
|---|---|---|---|
| **FF clock enable** | 5–15% per module | Low (auto-inferred) | None |
| **BUFGCE global gating** | 30–60% per domain | Medium (must manage enable) | Must handle enable transitions cleanly |
| **Domain shutdown (PLL off)** | 50–80% per domain | High (must manage PLL lock) | Long re-enable latency (100 µs PLL relock) |

---

## Technique 2: Operand Isolation

Operand isolation prevents unnecessary toggling of combinational logic when its output is not used. The synthesizer inserts a "gate" that holds the input stable when the output is not needed.

### How It Works

```verilog
// Without operand isolation: adder toggles even when result is not used
wire [31:0] sum = a + b;       // a and b toggle → adder toggles
wire [31:0] result = select ? sum : cached_value;

// With operand isolation (manual):
wire [31:0] a_iso = select ? a : a_hold;   // a only toggles when needed
wire [31:0] b_iso = select ? b : b_hold;
wire [31:0] sum = a_iso + b_iso;
```

### Tool-Driven Operand Isolation

Vivado and Quartus can automatically insert operand isolation during synthesis:

**Vivado:**
```tcl
# Enable operand isolation in Vivado
set_property OPERATOR_ISOLATION true [current_design]
```

**Quartus:**
```tcl
# Enable power-driven synthesis
set_global_assignment -name OPTIMIZE_POWER_DURING_SYNTHESIS "ON"
```

**Impact:** 5–20% dynamic power reduction, depending on the number of idle datapaths.

---

## Technique 3: Clock Frequency Reduction

Reducing the clock frequency proportionally reduces dynamic power. This is the simplest technique but trades performance for power.

### DVFS (Dynamic Voltage and Frequency Scaling)

On Xilinx Zynq UltraScale+ and Intel Agilex SoCs, the processor subsystem can dynamically adjust voltage and frequency:

| Voltage/Frequency | Power | Performance |
|---|---|---|
| 1.0V / 1 GHz | 100% | 100% |
| 0.9V / 800 MHz | ~58% | 80% |
| 0.8V / 600 MHz | ~30% | 60% |

> [!NOTE]
> DVFS applies to the hard processor subsystem (ARM/RISC-V), not the FPGA fabric. FPGA fabric voltage is typically fixed. Fabric frequency can be changed by reconfiguring the PLL via DRP.

### Fabric Frequency Scaling

```verilog
// Dynamic clock switching using MMCM DRP
// When workload is low, reduce fabric clock from 200 MHz to 50 MHz
// Power reduction: ~4× (linear with frequency) minus static power
```

---

## Technique 4: Memory Power Optimization

### BRAM Sleep Mode

Xilinx UltraScale+ BRAMs support a low-power mode where unused ports are disabled:

```tcl
# Vivado: Enable BRAM low-power mode
set_property BRAM_LOW_POWER true [current_design]

# Or per-instance:
set_property BRAM_LOW_POWER true [get_cells my_bram_inst]
```

**Impact:** 10–30% BRAM power reduction when one port is idle.

### BRAM Enable Gating

```verilog
// Gate BRAM enable when data is not needed
wire bram_en = read_valid && !fifo_empty;  // Only enable when reading

// The BRAM's ENA/ENB pins control whether internal sense amplifiers are active
// When EN=0, the BRAM consumes significantly less dynamic power
```

### Distributed vs BRAM Trade-off

| Memory Type | Power per bit | When to Use |
|---|---|---|
| **BRAM** | Lower per bit at high utilization | Large memories (> 512 bits), dual-port access |
| **Distributed RAM** | Higher per bit but zero when idle | Small memories (< 512 bits), read-only or single-port |

---

## Technique 5: IO Power Optimization

### IO Standard Selection

| IO Standard | Power per Pin (typical) | Speed | When to Use |
|---|---|---|---|
| **LVCMOS18** | ~2 mW | < 200 MHz | General-purpose 1.8V |
| **LVCMOS33** | ~8 mW | < 100 MHz | Legacy 3.3V systems |
| **LVDS** | ~10 mW (pair) | < 1 Gbps | High-speed differential |
| **HSTL-15** | ~5 mW | < 400 MHz | DDR3 memory interfaces |
| **SSTL-15** | ~4 mW | < 400 MHz | DDR3 (lower power than HSTL) |

**Key insight:** Using 1.8V IO instead of 3.3V IO reduces IO power by ~4× (V² scaling). If the system allows, use the lowest voltage IO standard.

### IO Slew Rate and Drive Strength

```tcl
# Reduce drive strength to minimum required (reduces dynamic current)
set_property IOSTANDARD LVCMOS18 [get_ports data_out]
set_property DRIVE 4 [get_ports data_out]        # 4 mA instead of default 12 mA
set_property SLEW SLOW [get_ports data_out]      # Slower edge rate = less EMI + lower power
```

---

## Technique 6: Resource Optimization

### Reducing LUT Count

Fewer LUTs = less switching capacitance = less dynamic power:

| Optimization | Power Impact |
|---|---|
| **Resource sharing** (time-multiplex a multiplier) | 30–50% reduction in DSP/LUT power for shared function |
| **Pipelining** (adds registers but reduces glitching) | 10–20% reduction in combinational power |
| **Dead code elimination** (remove unused logic) | 5–15% reduction depending on design cleanliness |
| **FSM encoding** (one-hot vs binary) | Negligible for small FSMs; one-hot uses more FFs but may have less switching |

### DSP Power Management

```verilog
// Gate DSP input when not computing
wire [17:0] dsp_a = compute_en ? data_a : 18'd0;
wire [17:0] dsp_b = compute_en ? data_b : 18'd0;

// When compute_en=0, DSP inputs are 0 — internal switching minimized
// This is "operand isolation" applied at the DSP boundary
```

---

## Vendor Power Analysis Tools

| Vendor | Tool | Capability |
|---|---|---|
| **Xilinx** | Vivado Power Report (`report_power`) | Post-synthesis or post-implementation power estimation with activity factors |
| **Xilinx** | Xilinx Power Estimator (XPE) | Pre-design spreadsheet estimator for device selection |
| **Intel** | Quartus Power Analyzer | Early power estimator + post-fit analysis |
| **Intel** | Intel Early Power Estimator (EPE) | Spreadsheet-based pre-design estimator |
| **Lattice** | Diamond Power Calculator | Post-implementation power analysis |
| **Gowin** | Gowin EDA Power Analysis | Basic power estimation |

### Vivado Power Report Example

```tcl
# Generate power report with switching activity from simulation
open_project my_design.xpr
open_run impl_1

# Option 1: Use default activity factors (50% toggle rate — pessimistic)
report_power -file power_default.rpt

# Option 2: Use SAIF from simulation (accurate)
# First: write SAIF during simulation
# write_sdf -file design.sdf
# Then: read SAIF into power analysis
read_saif -file sim_mole.saif
report_power -file power_with_saif.rpt
```

---

## Power Optimization Decision Guide

| Power Problem | Primary Technique | Impact | Effort |
|---|---|---|---|
| High idle power (system doing nothing) | Clock gating (BUFGCE) | 30–60% | Medium |
| Data path toggling when output not used | Operand isolation | 5–20% | Low (tool-driven) |
| Too many clock domains all running | Domain consolidation + gating | 20–40% | High |
| BRAM consuming too much power | Enable gating + low-power mode | 10–30% | Low |
| IO power too high | Lower IO voltage, reduce drive strength | 30–60% (IO only) | Low |
| Static power too high (leakage) | Select smaller/lower-power device | Device-dependent | High (respin) |
| Total power over budget | Frequency reduction | Linear with freq | Low |

---

## References

| Source | Description |
|---|---|
| Xilinx UG906 — Vivado Design Suite Power Analysis | Power analysis methodology and tool usage |
| Xilinx WP380 — Power Management in Xilinx FPGAs | Architecture-level power optimization techniques |
| Intel AN-730 — Power Management for Intel FPGAs | Quartus power optimization flow |
| Xilinx XAPP555 — Minimizing Power Consumption in 7 Series FPGAs | Practical clock gating and BRAM techniques |
| [Power Integrity](../09_boards_and_board_design/power_integrity.md) | Board-level PDN design and decoupling |
| [Clock Management IP](../06_ip_and_cores/clocking_ip/clock_management_ip.md) | PLL frequency scaling via DRP |
| [Clock Domain Crossing](../05_timing_and_constraints/clock_domain_crossing.md) | Fewer domains = less power |
