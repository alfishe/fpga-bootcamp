[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# External Logic Analyzers — When ILA Isn't Enough

On-chip logic analyzers (ILA/SignalTap) are great until you run out of BRAM, need to capture across a reset, or need to correlate FPGA signals with external chip behavior. External logic analyzers bridge the gap — they connect to FPGA pins and capture unlimited-depth traces with protocol decoding.

---

## When to Use External vs On-Chip

| Scenario | Use |
|---|---|
| Trace depth >128K samples | **External LA** — captures gigabytes to disk |
| Debugging across FPGA reconfiguration | **External LA** — data survives bitstream reload |
| Correlating FPGA + external chip signals | **External LA** — probe FPGA + SPI/I2C bus simultaneously |
| Very wide bus (1024+ signals) | **External LA** — no BRAM limit (just pin count) |
| Quick internal signal check (no board mods) | **ILA/SignalTap** — no soldering |
| Automated regression in CI | **ILA/SignalTap** — Tcl-scriptable |
| High-speed serial (multi-Gbps) | **Neither** — use oscilloscope with serial decode |

---

## Hardware Options

| Analyzer | Channels | Max Sample Rate | Buffer | Protocol Decode | Price |
|---|---|---|---|---|---|
| **Saleae Logic 8** | 8 | 100 MHz (digital) | Unlimited (USB streaming) | UART, SPI, I2C, CAN, 1-Wire, etc. | ~$399 |
| **Saleae Logic Pro 16** | 16 | 500 MHz (digital), 50 MHz (analog) | Unlimited | 20+ protocols | ~$1,099 |
| **DSLogic Plus** | 16 | 400 MHz | Unlimited (USB 3.0 streaming) | Via sigrok | ~$149 |
| **DSLogic U3Pro16** | 16 | 1 GHz | 2 Gb on-board + USB | Via sigrok | ~$299 |
| **Kingst LA5016** | 16 | 500 MHz | 2 Gb on-board | UART, SPI, I2C, CAN, etc. | ~$199 |
| **Ikalogic ScanaQuad** | 4/9 | 200 MHz | Unlimited (streaming) | 10+ protocols | ~$199–399 |

---

## sigrok — Open-Source LA Software

`sigrok` is the open-source Swiss Army knife for logic analyzers. It supports 100+ hardware devices with a unified interface:

```bash
# Install sigrok + PulseView GUI
# Windows: https://sigrok.org/download/
# Linux: apt install sigrok pulseview

# Command-line capture
sigrok-cli -d saleae-logic16 --samples 10M -o capture.sr

# Protocol decode from command line
sigrok-cli -i capture.sr -P uart:rx=0:baudrate=115200
```

### Supported Protocol Decoders (Partial List)

| Protocol | Decoder Name | Channels Needed |
|---|---|---|
| UART (async serial) | `uart` | 1 (RX) or 2 (RX+TX) |
| SPI | `spi` | 4 (CS, CLK, MOSI, MISO) |
| I2C | `i2c` | 2 (SDA, SCL) |
| CAN | `can` | 1 (RX) or 2 (RX+TX) |
| 1-Wire | `onewire` | 1 |
| I2S (audio) | `i2s` | 4 (MCLK, BCLK, LRCLK, DATA) |
| MDIO (Ethernet PHY mgmt) | `mdio` | 2 (MDC, MDIO) |
| JTAG | `jtag` | 4 (TDI, TDO, TMS, TCK) |
| Parallel bus | `parallel` | Up to 32 data + 1 clock |

---

## FPGA-to-LA Connection Strategy

### Pin Assignment for Debug

Reserve a debug header on your board design:

```
┌──────────────┐
│ FPGA         │  16-pin Debug Header (2×8, 0.1" pitch)
│              │       Pin 1:  GND
│ debug_bus[0] ├────── Pin 2:  debug_bus[0]
│ debug_bus[1] ├────── Pin 3:  debug_bus[1]
│ ...          │       ...
│ debug_bus[7] ├────── Pin 10: debug_bus[7]
│ dbg_clk_out  ├────── Pin 12: debug_clock
│ dbg_trig_in  ├────── Pin 14: external trigger input
│              │       Pin 15: GND
└──────────────┘
```

**Key design rules:**
1. Add 22Ω series resistors on all debug outputs (reflection control)
2. Route debug clock as a length-matched pair with data (source-synchronous)
3. Use a dedicated FPGA PLL output for debug clock — not gated logic

### Voltage Level Caution

Most USB logic analyzers are **not 5V-tolerant**. FPGA I/O at 3.3V LVCMOS is safe. If your FPGA I/O bank is 1.8V or 2.5V, use a level shifter board.

---

## Debug Bus HDL Pattern

```verilog
// Dedicated debug bus output — always included, gated by generics
module debug_bus #(
    parameter ENABLE = 1
) (
    input  wire        clk,
    input  wire [15:0] debug_signals,  // your internal signals
    output wire [15:0] debug_pins      // to physical FPGA pins
);
    generate
        if (ENABLE) begin
            // Register the outputs to control timing
            reg [15:0] debug_reg;
            always @(posedge clk)
                debug_reg <= debug_signals;
            assign debug_pins = debug_reg;
        end else begin
            assign debug_pins = 16'b0;  // tie low when not debugging
        end
    endgenerate
endmodule
```

This pattern lets you:
- Keep debug signals in your design permanently (gated by parameter)
- Control output timing with a register stage
- Remove debug in production with zero logic (synthesis optimizes away tied-low outputs)

---

## Best Practices

1. **Always output a debug clock** — sampling LA on the same clock as your FPGA logic eliminates timing uncertainty.
2. **Use source-synchronous capture** — route clock + data together, length-matched on PCB.
3. **Start with 10–20 signals** — you rarely need 128 signals on an external LA. Choose the most diagnostic signals.
4. **Protocol decode beats manual bit-bashing** — if your design uses SPI/I2C/UART, let sigrok decode it.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Sampling without clock** | Data looks random, setup/hold violations | LA must sample on FPGA's clock, not its internal async clock |
| **Ground loop noise** | Sporadic glitches on capture | Connect LA GND directly to FPGA board GND plane with short wire |
| **Pin count explosion** | Needed 32 signals, only have 16 LA channels | Multiplex signals onto debug bus: output A on clock cycle 0, B on cycle 1 |
| **5V overvoltage** | LA input damaged | Check FPGA IO bank voltage; use level shifter if >3.3V |

---

## References

| Source | Path |
|---|---|
| sigrok / PulseView | https://sigrok.org/ |
| Saleae Logic Analyzers | https://www.saleae.com/ |
| DSLogic | https://www.dreamsourcelab.com/ |
| sigrok Protocol Decoder List | https://sigrok.org/wiki/Protocol_decoders |
