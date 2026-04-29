[← 14 References Home](README.md) · [← Project Home](../../README.md)

# Register Map Documentation Template

A standard template for documenting memory-mapped registers in custom AXI4-Lite, Avalon-MM, or Wishbone peripherals. Consistent register documentation prevents firmware/FPGA integration bugs.

---

## Template

```markdown
# My_Peripheral — Register Map

## Overview
- **Base Address:** 0x43C0_0000
- **Address Range:** 4 KB (0x1000)
- **Bus Interface:** AXI4-Lite, 32-bit data, single-beat only
- **Clock Domain:** `s_axi_aclk` (100 MHz)
- **Reset:** Active-low, synchronous to `s_axi_aclk`

## Register Summary

| Offset | Name | Access | Width | Reset Value | Description |
|---|---|---|---|---|---|
| 0x00 | CTRL | R/W | 32 | 0x0000_0000 | Control register |
| 0x04 | STATUS | RO | 32 | 0x0000_0000 | Status register |
| 0x08 | DATA_TX | WO | 32 | — | Transmit data FIFO write |
| 0x0C | DATA_RX | RO | 32 | 0x0000_0000 | Receive data FIFO read |
| 0x10 | BAUD_DIV | R/W | 32 | 0x0000_01B2 | Baud rate divider (clk/baud) |
| 0x14 | INTR_EN | R/W | 32 | 0x0000_0000 | Interrupt enable mask |
| 0x18 | INTR_STATUS | RO/W1C | 32 | 0x0000_0000 | Interrupt status (write 1 to clear) |

---

## Register Details

### CTRL (0x00) — Control Register

| Bits | Name | Access | Reset | Description |
|---|---|---|---|---|
| 0 | EN | R/W | 0 | Enable peripheral (1 = enabled) |
| 1 | TX_START | R/W/SC | 0 | Start transmission. Self-clears after TX complete. |
| 2 | LOOPBACK | R/W | 0 | Enable internal loopback for test |
| 7:3 | — | RO | 5'h0 | Reserved |
| 8 | PARITY_EN | R/W | 0 | Enable parity generation/checking |
| 9 | PARITY_ODD | R/W | 0 | Parity type: 0 = even, 1 = odd |
| 31:10 | — | RO | 22'h0 | Reserved |

### STATUS (0x04) — Status Register

| Bits | Name | Access | Reset | Description |
|---|---|---|---|---|
| 0 | TX_BUSY | RO | 0 | Transmitter active |
| 1 | RX_VALID | RO | 0 | Receive data available in DATA_RX |
| 2 | TX_FIFO_FULL | RO | 0 | TX FIFO full — do not write DATA_TX |
| 3 | RX_FIFO_EMPTY | RO | 1 | RX FIFO empty — DATA_RX invalid |
| 4 | PARITY_ERR | RO | 0 | Parity error on last received byte (sticky) |
| 7:5 | — | RO | 3'h0 | Reserved |
| 31:8 | RX_FIFO_COUNT | RO | 0 | Number of bytes available in RX FIFO |

### DATA_TX (0x08) — Transmit Data (Write-Only)

Writing any value pushes a byte into the TX FIFO. Only bits [7:0] are used.

| Bits | Name | Description |
|---|---|---|
| 7:0 | TX_BYTE | Byte to transmit |
| 31:8 | — | Ignored on write |

### DATA_RX (0x0C) — Receive Data (Read-Only)

Reading pops a byte from the RX FIFO.

| Bits | Name | Description |
|---|---|---|
| 7:0 | RX_BYTE | Received byte |
| 31:8 | — | Read as 0 |

### BAUD_DIV (0x10) — Baud Rate Divider

Baud rate = clk_freq / BAUD_DIV. Default 0x1B2 (434) gives 115200 baud at 50 MHz.

### INTR_EN (0x14) — Interrupt Enable Mask

| Bits | Name | Description |
|---|---|---|
| 0 | TX_DONE_IE | Interrupt when TX complete |
| 1 | RX_AVAIL_IE | Interrupt when RX data available |
| 2 | RX_ERR_IE | Interrupt on parity/framing error |

### INTR_STATUS (0x18) — Interrupt Status (W1C)

| Bits | Name | Access | Description |
|---|---|---|---|
| 0 | TX_DONE | RO/W1C | TX complete. Write 1 to clear. |
| 1 | RX_AVAIL | RO/W1C | RX data available. Write 1 to clear. |
| 2 | RX_ERR | RO/W1C | RX error detected. Write 1 to clear. |

---

## Access Type Definitions

| Type | Description |
|---|---|
| **R/W** | Read/Write — software can read and write |
| **RO** | Read-Only — write ignored, read returns current value |
| **WO** | Write-Only — read returns 0 or undefined |
| **RO/W1C** | Read-Only / Write-1-to-Clear — write 1 to clear bit, 0 has no effect |
| **R/W/SC** | Read/Write / Self-Clearing — bit auto-clears after action |
| **RO/V** | Read-Only / Volatile — value changes without software write |

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2024-01-15 | Initial release |
| 1.1 | 2024-03-20 | Added interrupt registers |
```

---

## Usage Notes

1. **Always define reserved bits** — firmware should mask reserved bits on write and ignore on read
2. **Use W1C for interrupt status** — prevents read-modify-write race conditions
3. **Document side effects** — e.g., reading DATA_RX pops FIFO
4. **Specify reset values** — firmware needs to know initial state before any register writes
5. **Group related registers** — control/status pairs at consecutive offsets

---

## Tools That Can Generate This

| Tool | Output | Notes |
|---|---|---|
| **Vivado AXI4-Lite Wizard** | Register map in IP-XACT | Auto-generates VHDL/Verilog + docs |
| **Platform Designer** | Memory map report | From auto-assigned addresses |
| **regtool (LiteX)** | CSR definitions | From Python SoC description |
| **SystemRDL** | Industry standard register format | Compilers generate RTL + docs + headers |
