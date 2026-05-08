[← Infrastructure Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# Clock Network Design Deep Dive — Buffers, Gating, MMCM Plumbing & Strategy

The clock network determines whether your design meets timing, stays within power budget, and has enough clock domains for all subsystems. This article goes deeper than the [Clocking](clocking.md) overview, covering the specific buffer types (BUFG, BUFH, BUFR, BUFGCE), clock gating strategies at the network level, MMCM/PLL plumbing patterns, and the clock architecture decisions that make or break large FPGA designs.

For the clocking basics (PLL/MMCM/DCM operation), see [Clocking](clocking.md). For clock domain crossing coding, see [CDC Coding](../../04_hdl_and_synthesis/cdc_coding.md). For power estimation, see [Power Estimation](power_estimation.md).

---

## Clock Buffer Taxonomy — Xilinx

### Global Buffers (BUFG)

| Property | Value |
|----------|-------|
| **Drive** | Entire device (all clock regions) |
| **Skew** | < 50 ps across device |
| **Jitter (additive)** | < 30 ps |
| **Count per device** | 24–32 (7-series), 32–48 (UltraScale+) |
| **Fanout** | Unlimited (dedicated routing) |

**When to use:** Primary clock domains, high-fanout signals, domain crossings.

```verilog
// Explicit BUFG instantiation
BUFG u_bufg_clk (
    .I (clk_from_pll),
    .O (clk_global)
);
```

### Horizontal Buffers (BUFH)

| Property | Value |
|----------|-------|
| **Drive** | Single clock region (horizontal row) |
| **Skew** | < 20 ps within region |
| **Count** | 12–24 per device (varies) |
| **Power** | ~30% of BUFG |

**When to use:** Regional clocks (single clock domain), clock gating within a region, save BUFG resources.

```verilog
BUFH u_bufh_clk (
    .I (clk_from_mmcm),
    .O (clk_regional)
);
```

### Regional Buffers (BUFR)

| Property | Value |
|----------|-------|
| **Drive** | Single clock region + adjacent |
| **Divider** | Built-in 1–8 integer divider |
| **Count** | 4–8 per clock region |
| **Use case** | Source-synchronous capture, SerDes interface clocks |

```verilog
BUFR #(.BUFR_DIVIDE("4")) u_bufr_clk (
    .I (clk_from_pin),
    .O (clk_div4),
    .CE (1'b1),
    .CLR (1'b0)
);
```

### Clock-Gating Buffers (BUFGCE)

| Property | Value |
|----------|-------|
| **Drive** | Global (same as BUFG) |
| **Enable** | Synchronous, glitch-free |
| **Use case** | Clock gating for power domains |

```verilog
BUFGCE u_bufgce (
    .I  (clk),
    .CE (domain_enable),
    .O  (clk_gated)
);
```

**BUFGCE timing:** Enable is sampled on the rising edge of the input clock. The output stops cleanly after the current rising edge. No glitch risk.

### Buffer Selection Decision Tree

```
Does the clock need to reach the entire device?
├── YES → BUFG (global)
│         └── Do you need to gate it?
│             ├── YES → BUFGCE
│             └── NO  → BUFG
└── NO → Does it need a frequency divider?
          ├── YES → BUFR (divide 1–8)
          └── NO → Single clock region only?
                    ├── YES → BUFH (saves power + BUFG count)
                    └── NO  → BUFG (safest default)
```

---

## Clock Buffer Taxonomy — Intel

| Buffer | Intel Name | Drive Scope | Notes |
|--------|-----------|-------------|-------|
| **Global** | GCLK | Entire device | Similar to BUFG |
| **Regional** | RCLK | Clock region | Similar to BUFH |
| **Periphery** | PCLK | I/O element + adjacent | For source-synchronous capture |
| **PLL output** | Direct from PLL | Regional or global | Automatic buffer insertion |

**Intel clock gating:** Use `altera_clock_gate` IP or let synthesis infer clock gating from the `clk & en` pattern with latch-based gating.

---

## Clock Buffer Taxonomy — Lattice

| Buffer | Family | Drive Scope | Notes |
|--------|--------|-------------|-------|
| **Global** | All | Entire device | 4–8 per device |
| **Quad** | ECP5 | Quarter device | Regional clocking |
| **Edge** | ECP5 | I/O edge | Source-synchronous |
| **Secondary** | iCE40 | Half device | Limited resources |

---

## MMCM/PLL Plumbing Patterns

### Pattern 1: Single MMCM, Multiple Outputs

```
           ┌──────────────┐
clk_in ───►│    MMCM      │──► CLKOUT0 (200 MHz, 0°)
           │              │──► CLKOUT1 (100 MHz, 0°)
           │              │──► CLKOUT2 (100 MHz, 90°)
           │              │──► CLKOUT3 (50 MHz, 0°)
           │              │──► CLKOUT4 (25 MHz, 0°)
           │              │──► CLKFBOUT (feedback)
           └──────────────┘
```

```tcl
# Vivado: MMCM with 5 outputs
create_clock -period 10 [get_ports clk_100m_in]

create_generated_clock -name clk_200m -multiply_by 2 [get_pins mmcm_inst/CLKOUT0]
create_generated_clock -name clk_100m  -multiply_by 1 [get_pins mmcm_inst/CLKOUT1]
create_generated_clock -name clk_100m_90 -multiply_by 1 [get_pins mmcm_inst/CLKOUT2]
create_generated_clock -name clk_50m   -divide_by 2 [get_pins mmcm_inst/CLKOUT3]
create_generated_clock -name clk_25m   -divide_by 4 [get_pins mmcm_inst/CLKOUT4]
```

### Pattern 2: Cascaded MMCMs (Ultra-Low Jitter)

When one MMCM cannot achieve the required jitter, cascade two:

```
clk_in ──►[MMCM #1]──►(cleaned clock)──►[MMCM #2]──► clk_out
           (coarse)                       (fine jitter
            cleanup)                       filtering)
```

```tcl
# First MMCM: coarse cleanup (jitter filter)
create_generated_clock -name clk_cleaned \
    -multiply_by 8 [get_pins mmcm1_inst/CLKOUT0]

# Second MMCM: fine frequency synthesis
create_generated_clock -name clk_final \
    -multiply_by 5 -divide_by 4 \
    -master_clock [get_clocks clk_cleaned] \
    [get_pins mmcm2_inst/CLKOUT0]
```

**Caution:** Cascaded MMCMs add latency and reduce available clock resources. Only use when jitter requirements demand it.

### Pattern 3: Zero-Delay Buffer (Feedback)

For board-level clock deskew:

```
clk_in ──►[MMCM]──► clk_to_FPGA_logic
              │
              └──► CLKFBOUT ──► (external loopback pin) ──► CLKFBIN
                   (board trace, matched to output path)
```

The MMCM adjusts its phase so `CLKFBIN` is phase-aligned with `CLKIN`. This deskews the output clock relative to the input, compensating for on-chip and off-chip delays.

### Pattern 4: Dynamic Clock Switching

Switch between two clock sources without glitches:

```verilog
module clock_mux #(
    parameter NUM_CLKS = 2
) (
    input  wire [NUM_CLKS-1:0] clk_in,
    input  wire [$clog2(NUM_CLKS)-1:0] sel,
    output wire clk_out
);

    // Xilinx: use BUFGMUX primitive (glitch-free)
    BUFGMUX u_clk_mux (
        .I0 (clk_in[0]),
        .I1 (clk_in[1]),
        .S  (sel),
        .O  (clk_out)
    );

endmodule
```

| Primitive | Vendor | Glitch-Free | Switch Latency |
|-----------|--------|------------|---------------|
| `BUFGMUX` | Xilinx 7-series | Yes | 2–3 cycles |
| `BUFGCTRL` | Xilinx UltraScale+ | Yes (with proper CE) | 1–2 cycles |
| `CLKMUX` | Intel | Yes | 2–3 cycles |
| Manual mux (`assign`) | Any | **No** | Instant (but glitchy!) |

---

## Clock Gating at the Network Level

### Per-Domain Gating Architecture

```
               ┌──────────────┐
               │    MMCM      │
               │  CLKOUT0 ────┤──►[BUFGCE (en_0)]──► clk_domain_0
               │  CLKOUT1 ────┤──►[BUFGCE (en_1)]──► clk_domain_1
               │  CLKOUT2 ────┤──►[BUFGCE (en_2)]──► clk_domain_2
               └──────────────┘
                      ▲
                      │
               Software-controlled enable register:
               [2:0] domain_enable — one bit per domain
```

**Advantages:**
- Clock tree stops toggling when disabled → significant power savings
- No modifications to domain-internal logic
- Software can enable/disable domains at runtime

### Gating Enable Timing

```
                ┌───┐   ┌───┐   ┌───┐   ┌───┐
clk_in    ──────┤   ├───┤   ├───┤   ├───┤   ├───
                └───┘   └───┘   └───┘   └───┘
                           ┌───────────────────
en        ────────────────┤                    (asserted)
                          └───────────────────
                               ┌───┐   ┌───┐
clk_out   ─────────────────────┤   ├───┤   ├───
     (stops after last posedge) └───┘   └───┘
```

**Rule:** The enable must be stable at least 1 cycle before the clock edge where gating takes effect. BUFGCE samples the enable on the rising edge.

---

## Clock Resource Budget by Device

| Device | BUFG/BUFGCE | BUFH | BUFR | MMCM/PLL | Max Clock Regions |
|--------|-------------|------|------|----------|-------------------|
| Artix-7 35T | 16 | 0 | 8 | 5 PLL | 5 |
| Kintex-7 325T | 32 | 0 | 16 | 10 MMCM + 10 PLL | 16 |
| Virtex UltraScale+ VU9P | 32 | 24 | 36 | 12 MMCM + 12 PLL | 36 |
| Zynq 7020 | 16 | 0 | 8 | 4 PLL | 5 |
| Zynq US+ ZU7EV | 24 | 24 | 16 | 8 MMCM + 8 PLL | 24 |
| Cyclone V 5CEA7 | 15 GCLK | — | — | 8 PLL | — |
| Stratix 10 GX 2800 | 64 GCLK | — | — | 24 I/O PLL + 24 fPLL | — |
| ECP5-85 | 8 | 16 quad | — | 4 PLL | — |
| iCE40 UP5K | 8 | — | — | 1 PLL | — |
| GW2A-18 | 8 | — | — | 4 PLL | — |

**Planning rule:** Reserve 20% of clock resources for ECO and future features. If you're using > 80% of BUFGs, redesign your clock architecture.

---

## Common Clock Architecture Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| **Too many clock domains** | Run out of BUFGs, excessive CDC complexity | Merge similar-frequency domains; use clock enables instead of separate clocks |
| **BUFG on gated clock** | `BUFG` after `BUFGCE` → double-buffered, wasteful | Gate at the BUFGCE; no second BUFG needed |
| **Unconstrained generated clocks** | Timing tool ignores MMCM outputs | Always add `create_generated_clock` constraints |
| **Clock on general routing** | Huge skew, timing failure | Never route clocks through LUTs or general interconnect |
| **Missing `set_clock_groups`** | Tool analyzes paths between async clocks → false failures | Add `set_clock_groups -asynchronous` |
| **Clock forwarded without ODDR** | Duty cycle distortion, jitter | Use ODDR to forward clock: `ODDR` → `OBUF` → pin |
| **PLL feedback not connected** | Phase alignment broken | Always connect CLKFBOUT → CLKFBIN (even for internal use) |

### Clock Forwarding with ODDR

```verilog
// Forward a clock output (source-synchronous TX clock)
ODDR #(
    .DDR_CLK_EDGE("SAME_EDGE")
) u_clk_fwd (
    .C  (clk_out),
    .CE (1'b1),
    .D1 (1'b1),
    .D2 (1'b0),
    .Q  (clk_fwd_pin),
    .R  (1'b0),
    .S  (1'b0)
);
```

This produces a 50% duty-cycle clock on the output pin, aligned with the data outputs.

---

## Clock Planning Worksheet

| Domain | Frequency | Source | Buffer Type | Resources | Notes |
|--------|-----------|--------|------------|-----------|-------|
| clk_200m | 200 MHz | MMCM CLKOUT0 | BUFG | 1 BUFG, 1 MMCM out | Main processing |
| clk_100m | 100 MHz | MMCM CLKOUT1 | BUFGCE | 1 BUFGCE | Gated when idle |
| clk_50m | 50 MHz | MMCM CLKOUT2 | BUFG | 1 BUFG | UART + SPI |
| clk_125m | 125 MHz | MMCM CLKOUT3 | BUFG | 1 BUFG | Ethernet MAC |
| clk_156m25 | 156.25 MHz | External SFP+ | BUFG | 1 BUFG | 10G XFI |
| clk_adc | 80 MHz | External ADC | BUFR/4 | 1 BUFR | ADC sample clock |
| **Total** | | | | **6 BUFG + 1 BUFGCE + 1 BUFR + 4 MMCM outs** | |

---

## Cross-References

| Topic | Article |
|-------|---------|
| Clocking basics (PLL/MMCM/DCM) | [Clocking](clocking.md) |
| CDC coding patterns | [CDC Coding](../../04_hdl_and_synthesis/cdc_coding.md) |
| Power estimation | [Power Estimation](power_estimation.md) |
| IO standards | [IO Standards](io_standards.md) |
| Constraint reference | [Constraint Quickref](../../14_references/constraint_quickref.md) |