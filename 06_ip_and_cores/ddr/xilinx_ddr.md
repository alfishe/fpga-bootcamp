[← 06 IP & Cores Home](../README.md) · [← DDR Home](README.md) · [← Project Home](../../../README.md)

# Xilinx MIG — Memory Interface Generator

The **Memory Interface Generator (MIG)** is Xilinx's DDR controller IP. It supports the entire Xilinx portfolio — from Spartan-6 through Versal — with graduated PHY architectures that scale from simple DDR3 to high-speed DDR4 and LPDDR4.

---

## Architecture Overview

```
┌─────────────────── MIG IP ───────────────────┐
│                                               │
│  AXI4 Slave  ──→│  Memory    ──→│  PHY        │──→ DDR3/DDR4/LPDDR4
│                 │  Controller    │  (hard/soft) │
│  AXI4-Lite    ──→│ (user config) │              │
│                                               │
│  Clocking:  ────→ ui_clk (AXI side)           │
│                  ddr_clk (PHY side)            │
└───────────────────────────────────────────────┘
```

### PHY Generations

| Series | PHY Type | Max Speed | Technology |
|---|---|---|---|
| **7-series** (Artix/Kintex/Virtex/Zynq) | Hard PHY + soft calibration | DDR3-1866 | 28nm |
| **UltraScale** (Kintex/Virtex) | Hard PHY (PHASER) | DDR4-2666 | 20nm |
| **UltraScale+** (Kintex/Virtex/ZynqMP) | Hard PHY (PHASER) | DDR4-3200, LPDDR4-4266 | 16nm |
| **Versal** | Hardened DDRMC (NoC attached) | DDR4-3200, LPDDR4-4266 | 7nm |

> **7-series PHY is half-hard**: the SERDES and delay lines are hardened, but the calibration logic and data formatting run in soft logic. UltraScale+ moves more into the hard block.

---

## MIG Configuration

The MIG IP wizard walks through these configuration steps:

### Step 1: Pin/Bank Selection

The MIG uses **byte lanes** — groups of 8 DQ bits + 1 DQS pair + 1 DM. Each byte lane must be placed within a single I/O bank:

```
Byte Lane 0:  DQ[7:0], DQS_P[0], DQS_N[0], DM[0]  → I/O Bank X
Byte Lane 1:  DQ[15:8], DQS_P[1], DQS_N[1], DM[1] → I/O Bank Y
...
```

The MIG generates pin location constraints (.xdc) automatically based on the selected FPGA package and chosen banks.

### Step 2: Memory Parameters

| Parameter | Options | Notes |
|---|---|---|
| **Memory type** | DDR3, DDR3L, DDR4, LPDDR4 | LPDDR4: UltraScale+ and Versal only |
| **Components** | UDIMM, RDIMM, LRDIMM, Component | Component = direct DRAM soldered |
| **Data width** | 16/32/64/72 (with ECC) | Wider = fewer controllers needed |
| **Clock period** | Varies by speed grade | -1/-2/-3 grade determines max frequency |
| **Burst length** | BL8 (fixed) | Xilinx PHY is optimized for BL8 |
| **Ordering** | Normal (strided) or Strict (bank+row+col) | Normal maximizes throughput |

### Step 3: AXI Configuration

| Parameter | Options |
|---|---|
| **AXI data width** | 32/64/128/256/512-bit |
| **AXI ID width** | 1–16 (for out-of-order transactions) |
| **Address width** | Depends on density (row+col+bank+rank bits) |
| **Narrow burst support** | Enable/disable (sub-size transfers) |

---

## Calibration Sequence (7-series)

The MIG runs a multi-stage calibration at startup, controlled by the `init_calib_complete` signal:

```
init_calib_complete = 0
│
├── Stage 1: Write Leveling
│   ├── DQS-to-CK alignment per byte lane
│   └── Compensates fly-by routing skew
│
├── Stage 2: Read DQS Gate Training
│   ├── Align internal DQS gate to read preamble
│   └── Determines valid read window per byte
│
├── Stage 3: Read Data Eye Training
│   ├── Per-bit deskew: aligns each DQ to its DQS
│   └── Centers DQS in the data eye
│
├── Stage 4: Write Data Eye Training
│   ├── Write leveling fine-tune
│   └── Per-bit write DQ-to-DQS alignment
│
└── init_calib_complete = 1 → user logic can begin
```

**Status signals:**
- `init_calib_complete` — overall calibration done
- `dbg_*` debug bus — per-stage pass/fail, delay tap counts

The AXI interface should be held in reset (ARESETn = 0) until `init_calib_complete` asserts.

---

## PHY-to-Controller Clocking

```
sys_clk (200 MHz)  ──────────→ MMCM ──→ ui_clk (100–300 MHz, AXI side)
                 reference      │────→ ddr_clk (DDR PHY side)
                  PLL           │────→ ref_clk (IDELAY reference, 200 MHz)
```

- **ui_clk** = AXI clock, frequency = (data_width × ddr_clk_freq) / (2 × DDR data width)
  - Example: 32-bit AXI at DDR3-1600 → ui_clk = 32×800/64 = 400 MHz (but clamped by fabric speed)
  - More typical: 128-bit AXI at DDR3-1600 → ui_clk = 128×800/64 = 200 MHz (half the DDR rate)
- **4:1 ratio** is common for best throughput/frequency balance

---

## Dual-Rank and Multi-Slot

| Configuration | Pins | Throughput | Use Case |
|---|---|---|---|
| **Single rank, single slot** | 1×DQ bus | Full bandwidth to one rank | Simple, low-cost designs |
| **Dual rank, single slot** | 1×DQ bus, 2×CS | Same bus, interleaved ranks | Higher capacity, better bank utilization |
| **Multi-slot** | Multiple DQ buses | Parallel independent channels | Maximum bandwidth (UltraScale+ has multiple hard controllers) |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **sys_clk wrong frequency** | MIG IP generation error | Must be 200 MHz for 7-series, 300 MHz for UltraScale DDR4 |
| **Bank I/O standard mismatch** | Place error: "IOSTANDARD conflict" | All DQ/DQS in a byte lane bank must be SSTL15 (DDR3) or POD12 (DDR4) |
| **Pin swap violations** | DQS must be on clock-capable pin (MRCC/SRCC) | Check FPGA pin table; DQS_N can be on any pin in pair, DQS_P is fixed |
| **init_calib_complete never asserts** | AXI reads return garbage | Check VREF calibration, termination resistors, board routing |
| **ui_clk too slow** | Low AXI throughput | Increase AXI data width to 256-bit or 512-bit |
| **VRN/VRP unconnected** | Calibration fails on DCI (digitally controlled impedance) | Connect VRN to GND through reference resistor, VRP to VCCO through matching resistor |

---

## Further Reading

| Article | Topic |
|---|---|
| [intel_ddr.md](intel_ddr.md) | Intel UniPHY/EMIF DDR controllers |
| [lattice_others_ddr.md](lattice_others_ddr.md) | Lattice, Microchip, Gowin DDR |
| [ddr_pin_planning.md](ddr_pin_planning.md) | PCB routing, fly-by topology, pin constraints |
| Xilinx UG586 | 7-Series MIG Product Guide |
| Xilinx UG1085 | Zynq-7000 TRM (DDR section) |
