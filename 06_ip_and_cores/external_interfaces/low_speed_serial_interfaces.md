[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# Slow Serial Interfaces — I2C, SPI, UART, CAN, 1-Wire

The workhorses of embedded systems. Every FPGA can implement these protocols in fabric logic using only general-purpose IO pins. No transceivers, no DDR banks, no special hardware — just state machines and level shifters.

---

## Overview

| Interface | Speed | Pins | Topology | Voltage | FPGA Implementation |
|---|---|---|---|---|---|
| **I2C** | 100/400 kHz (Fast), 3.4 MHz (HS) | 2 (SDA, SCL) | Multi-master bus | 3.3V / 5V | Soft core; Zynq/PolarFire SoC have hard I2C controllers |
| **SPI** | 1–50+ MHz | 4 (MOSI, MISO, SCLK, /CS) | Single master, multi-slave | 1.8–3.3V | Soft core; nearly all FPGAs implement trivially |
| **UART** | 300 bps – 3 Mbps | 2 (TX, RX) | Point-to-point | 3.3V / 5V / RS-232 ±15V | Soft core; SoC FPGAs have hard UARTs |
| **CAN** | 125 kbps – 1 Mbps (CAN-FD: 8 Mbps) | 2 (CAN_H, CAN_L) | Multi-master bus | Differential ±2V | Soft core; some SoC FPGAs have hard CAN; external transceiver required |
| **1-Wire** | 16.3 kbps standard | 1 (DQ) | Single master, multi-slave | 3.3V / 5V | Soft core; simple bit-banging |
| **SMBus** | 10–100 kHz | 2 (SDA, SCL) | I2C subset with timeout | 3.3V | Same as I2C with stricter timing |

---

## I2C — Inter-Integrated Circuit

### Protocol Basics

I2C uses two open-drain lines with pull-up resistors:
- **SDA** — Serial Data (bidirectional)
- **SCL** — Serial Clock (master-driven, slave can stretch)

```
        SDA ──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──
              │S │A7│A6│A5│A4│A3│A2│A1│R/│A │D7│..│D0│A │
              │T │  │  │  │  │  │  │  │W │C │  │  │  │C │
        SCL ──┘  └─┐  └─┐  └─┐  └─┐  └─┐  └─┐  └─┐  └─┘
                   ↑     ↑     ↑     ↑     ↑     ↑
                 Start  bit   bit   bit   bit   bit
```

### FPGA Implementation

**Soft core approach:**
- ~50–100 LUTs for a basic I2C master
- ~200–300 LUTs for a multi-master capable controller
- Bit-banging from a microcontroller soft core (e.g., PicoRV32) is also common

**Hard IP availability:**
| FPGA Family | Hard I2C Controllers | Notes |
|---|---|---|
| Xilinx Zynq-7000 | 2× (PS side) | Cortex-A9 peripheral, not PL accessible directly |
| Xilinx Zynq MPSoC | 2× (PS side) | Cortex-A53/R5 peripheral |
| Intel Cyclone V SoC | 2× (HPS side) | ARM Cortex-A9 peripheral |
| Microchip PolarFire SoC | 2× (MSS) | RISC-V peripheral |
| Lattice ECP5 / CrossLink-NX | None | Soft core only |

### Level Translation

I2C is **open-drain**, making it the easiest bus to level-shift:
- **PCA9306** — Dedicated I2C level translator with enable pin
- **TXS0102/TXS0108** — Auto-direction, handles I2C pull-ups correctly
- **BSS138 + pull-ups** — Cheap FET-based solution for prototypes

See [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) for detailed circuit examples.

---

## SPI — Serial Peripheral Interface

### Protocol Basics

SPI is a synchronous, full-duplex bus with separate MOSI and MISO lines:
- **SCLK** — Clock (master output)
- **MOSI** — Master Out, Slave In
- **MISO** — Master In, Slave Out
- **/CS** — Chip Select (per-slave, active low)

Unlike I2C, SPI is **push-pull** on all lines except /CS (which is typically push-pull too). This means:
- Faster speeds (no pull-up RC time constant)
- No multi-master arbitration
- Level translation requires push-pull capable translators

### FPGA Implementation

SPI is trivial to implement in fabric:
- **Master:** ~30–50 LUTs (shift register + state machine)
- **Slave:** ~50–80 LUTs (synchronized shift register)
- **Quad-SPI (QSPI):** 4 data lines for flash — common for FPGA configuration

Most FPGA vendor tools provide free SPI controller IP (Xilinx AXI Quad SPI, Intel SPI Slave to Avalon). No license required.

### Maximum Speed by FPGA Family

| FPGA Family | SPI Max Speed (fabric) | Notes |
|---|---|---|
| Xilinx 7-series Artix | ~50 MHz | Limited by fabric routing delay |
| Xilinx Zynq PS | ~50 MHz | Hard SPI controller |
| Intel Cyclone V | ~40 MHz | Fabric limited |
| Lattice ECP5 | ~60 MHz | Fast fabric |
| Gowin LittleBee | ~25 MHz | Slower fabric, verify in timing |

---

## UART — Universal Asynchronous Receiver/Transmitter

### Protocol Basics

UART is asynchronous — no shared clock. Both sides agree on baud rate:

```
Idle │ Start │ D0 │ D1 │ D2 │ D3 │ D4 │ D5 │ D6 │ D7 │ Stop │ Idle
─────┘       └────┴────┴────┴────┴────┴────┴────┴────┘      └────
  1     0    LSB                                    MSB      1
```

Standard baud rates: 9600, 115200, 921600, 3 Mbps (high-speed UART).

### FPGA Implementation

- **Baud rate generator:** Divide system clock by (clock / baud_rate)
- **Core size:** ~40–60 LUTs for basic TX/RX
- **FIFO addition:** +~20 LUTs for 16-byte FIFO

RS-232 uses ±3V to ±15V levels. **Never connect RS-232 directly to FPGA pins.** Use a level translator like MAX3232 (3.3V ↔ RS-232).

---

## CAN — Controller Area Network

### Protocol Basics

CAN is a differential, multi-master bus using non-destructive arbitration:
- **CAN_H** and **CAN_L** — Differential pair
- **Dominant** state = logic 0 (driven differential voltage)
- **Recessive** state = logic 1 (weak pull to same voltage)

### FPGA Implementation

CAN requires two parts:
1. **CAN controller** — Protocol logic (can be soft core or hard IP)
2. **CAN transceiver** — Physical layer chip (external, e.g., MCP2551, TJA1051)

**Soft core CAN controllers:**
- CANopen implementations in VHDL/Verilog (open source)
- ~500–800 LUTs for a basic CAN controller
- CAN-FD requires more logic (~1000+ LUTs)

**Hard IP availability:**
| FPGA Family | Hard CAN | Notes |
|---|---|---|
| Intel MAX 10 | No | Soft core only |
| Microchip PolarFire SoC | No | Soft core only |
| Some automotive SoC FPGAs | Yes | Check specific device |

CAN transceivers are **always external** — no FPGA has a built-in CAN PHY.

---

## 1-Wire — Dallas/Maxim Protocol

1-Wire uses a single data line with parasitic power. Very slow (16.3 kbps standard, 142 kbps overdrive). Used for temperature sensors (DS18B20), EEPROMs, and iButtons.

**FPGA implementation:** Pure bit-banging. ~20 LUTs. Timing is relaxed enough that even a soft microcontroller can handle it.

---

## FPGA Family Support Matrix

| Interface | Hard IP Available On | Soft Core LUT Cost | External Components |
|---|---|---|---|
| I2C Master | Zynq, Cyclone V HPS, PolarFire SoC | 50–100 | Pull-up resistors |
| I2C Slave | Same | 100–200 | Pull-up resistors |
| SPI Master | Most SoC FPGAs | 30–50 | None (level translator if voltage mismatch) |
| SPI Slave | Same | 50–80 | None |
| UART | Most SoC FPGAs | 40–60 | MAX3232 for RS-232 |
| CAN | Rarely | 500–1000 | External CAN transceiver |
| 1-Wire | Never | ~20 | Pull-up resistor |

---

## Best Practices

1. **Use vendor IP for complex variants** — QSPI flash controllers, I2C with DMA, multi-channel UARTs
2. **Always check voltage levels** — 5V I2C/SPI sensors need level translation to 1.8V/3.3V FPGA banks
3. **Add pull-ups on I2C** — 4.7kΩ for 100 kHz, 2.2kΩ for 400 kHz, 1kΩ for 3.4 MHz
4. **Terminate SPI traces for high speed** — At >20 MHz, series resistors (22–47Ω) prevent ringing
5. **Buffer CAN transceiver from FPGA** — Use 3.3V CAN transceivers (MCP2562) to avoid level translation

---

## Pitfalls

1. **"I2C is slow, so timing doesn't matter"** — I2C has strict setup/hold times for START/STOP conditions. A poorly clocked soft core can miss repeated START conditions.
2. **SPI without tri-state MISO** — Multiple SPI slaves must tri-state their MISO when /CS is inactive. A slave that always drives MISO causes bus contention.
3. **RS-232 voltage levels** — Connecting RS-232 ±15V to a 3.3V FPGA pin destroys the IO cell. Always use a transceiver IC.
4. **CAN without termination** — 120Ω termination resistors at both ends of the CAN bus are mandatory. Without them, signal reflections cause frame errors.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| NXP UM10204 — I2C-bus specification | NXP | Official I2C timing specs, Fast-mode+, HS-mode |
| TI SCPS206 — PCA9306 Datasheet | TI | I2C level translator with enable |
| Microchip AN734 — CAN Basics | Microchip | CAN protocol fundamentals, bit timing calculation |
| Maxim AN126 — 1-Wire Communication | Maxim/ADI | 1-Wire timing, parasitic power, CRC |
| [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) | This KB | Level translation for 5V I2C/SPI to 3.3V/1.8V FPGAs |
