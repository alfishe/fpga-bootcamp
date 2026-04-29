[← 12 Open Source Open Hardware Home](../README.md) · [← Memory Controllers Home](README.md) · [← Project Home](../../../README.md)

# Specialized Memory Controllers

For designs where a full DDR PHY is overkill: HyperRAM, QSPI PSRAM, and async SRAM controllers for FPGA.

---

## Memory Type Comparison

| Type | Interface | Max Bandwidth | Pins | Best For |
|---|---|---|---|---|
| **HyperRAM** | 12-pin (CS, CK, RWDS, DQ[7:0], RESET) | 400 MB/s (200 MHz DDR) | 12 | Medium bandwidth, pin-constrained |
| **QSPI PSRAM** | 6-pin (CS, CLK, DQ[3:0]) | 50 MB/s (100 MHz QSPI) | 6 | Ultra-low pin count, small buffers |
| **Async SRAM** | 20+ pin (address, data, control) | ~100 MB/s (depends on FPGA fmax) | 40+ | Lowest latency, simplest controller |

## Open Controllers

| Controller | Memory Type | Key Trait | Repository |
|---|---|---|---|
| **hyperram** | HyperRAM | Wishbone, configurable frequency | ultraembedded/hyperram |
| **litex_hyperram** | HyperRAM | LiteX-integrated, auto-calibrated | LiteX-Hub |
| **qspi_psram** | QSPI PSRAM | SPI-like protocol, simple state machine | Various on GitHub |
| **async_sram** | Async SRAM | Trivial combinatorial interface | DIY (\u003c100 lines of Verilog) |

## When to Choose Each

| Scenario | Memory Type | Why |
|---|---|---|
| Need \u003e10 MB, pins are tight | **HyperRAM** | 8 MB × 8-bit, 12 pins total |
| Need \u003c100 KB buffer on a tiny FPGA | **QSPI PSRAM** | 6 pins, \u003c500 LUTs for controller |
| Need zero-latency random access | **Async SRAM** | No refresh, no CAS/RAS, just address → data |
| I have enough pins for DDR | **DDR3/4** | Skip these — go straight to [DDR controllers](ddr_controllers.md) |

---

## Original Stub Description

HyperRAM, QSPI PSRAM, async SRAM controllers — for designs where a full DDR PHY is overkill

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
