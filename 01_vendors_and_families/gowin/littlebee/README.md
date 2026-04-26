[← Gowin Home](../README.md) · [← Section Home](../../README.md)

# Gowin LittleBee — 55nm Ultra-Low-Cost FPGA Family

The ultra-low-cost workhorse from Gowin on 55nm. Tang Nano boards start under $10, making LittleBee the cheapest path to FPGA development. Growing open-source support via Project Apicula.

---

## Device Table

| Device | LUT4 | BlockRAM | SDRAM | DSP | PLL | Package | Position |
|---|---|---|---|---|---|---|---|
| **GW1N-1** | 1,152 | 72 Kb | None | None | 1 | QFN32 / LQFP144 | $1.50 chip, $6 board — world's cheapest |
| GW1N-4 | 4,608 | 180 Kb | None | None | 2 | QFN48 / QFP100 | Tang Nano 4K ($7) |
| GW1N-9 | 8,640 | 468 Kb | SDR SDRAM (64 Mb) | None | 2 | LQFP144 | General IO + peripherals |
| **GW1NR-9** | 8,640 | 468 Kb | 64 Mb PSRAM + 32 Mb NOR flash on-chip | None | 2 | QFN48 / PBGA | Integrated flash+PSRAM, lowest BOM |
| **GW1NSR-2C** | ~2,000 + **hard PicoRV32** | 72 Kb | None | None | 1 | QFN48 | SoC: hard PicoRV32 at 30 MHz |
| GW1NSR-4C | ~4,600 + hard PicoRV32 | 180 Kb | None | None | 2 | LQFP144 | SoC: PicoRV32 + larger FPGA |
| GW1N-9C | 8,640 | 468 Kb | SDR SDRAM | 16 DSP (18×18) | 2 | UBGA256 | Adds DSP blocks |

---

## LUT Architecture

Gowin uses a **4-input LUT + flip-flop** cell:

```
┌─────── Logic Cell ───────┐
│  ┌───────┐  ┌─────────┐  │
│  │ LUT4  │  │  FF     │  │
│  └──┬────┘  └──┬──────┘  │
│     │          │          │
│     └────┬─────┘          │
│          ▼                │
│     Carry + ADDSUB        │
└───────────────────────────┘
```

Classic 4-LUT architecture — no fracturable 6-LUT. Simpler cell is easier for open-source synthesis, but requires ~30% more LUTs for deep logic paths.

---

## Project Apicula — Open-Source Flow

| Tool | Status |
|---|---|
| **Project Apicula** (bitstream docs) | Active — GW1N-1/4/9 mostly documented |
| **Yosys** (synthesis) | Native support |
| **nextpnr-gowin** | Working for GW1N-1/4; GW1N-9+DSP in progress |
| **openFPGALoader** | Flash programming works |

Gowin also provides their own **Gowin IDE** (free, proprietary): ~600 MB download, starts in seconds (vs Vivado's 50 GB).

---

## Market Position

| Criterion | Gowin | Lattice | Intel Cyclone V |
|---|---|---|---|
| Entry chip price | ~$1.50 (GW1N-1) | ~$1.80 (iCE40LP384) | ~$15 (5CSEA2) |
| Entry board price | $6–8 (Tang Nano 1K) | $8–12 (Upduino) | $50+ |
| Open-source tools | Growing (Apicula) | Complete (IceStorm/Trellis) | None |
| MIPI D-PHY | GW1NR-9 (2 lanes) | iCE40UP5K, ECP5 | No native |

---

## When to Choose LittleBee

| You have... | Pick |
|---|---|
| >100K unit production, need <$5 FPGA silicon | GW1N-1 or GW1N-4 |
| Need integrated flash + PSRAM, smallest footprint | GW1NR-9 |
| Need hard PicoRV32 built in | GW1NSR-2C/4C |
| Need open-source flow | GW1N-1/4/9 (Apicula) or Lattice ECP5 (Trellis) |
| Getting started with zero budget | Tang Nano 1K or 4K |

---

## Best Practices

1. **Use Gowin IDE for initial bring-up, Yosys+Apicula for CI** — Gowin IDE is fastest for first design; open flow gives reproducibility.
2. **Internal flash is ~10,000 cycles** — same endurance constraint as MAX 10.

---

## Development Boards

### Sipeed (Semi-Official Partner)

| Board | FPGA | LUT4 | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Tang Nano 9K** | GW1NR-9 | 8,640 | HDMI, 64 Mb PSRAM, NOR flash on-chip, USB-JTAG, GPIO ×40 | ~$10 | Best all-around LittleBee, 8640 LUTs at $10 |
| **Tang Nano 4K** | GW1NSR-4C | 4,608 | Hard PicoRV32 SoC, HDMI, RGB LCD header, USB-JTAG | ~$7 | Cheapest PicoRV32 hard SoC FPGA |
| Tang Nano 1K | GW1NZ-1 | 1,152 | Ultra-minimal, breadboard-friendly, USB-JTAG | ~$5–6 | Cheapest FPGA in existence |
| Tang Nano 20K | GW2AR-18 | 20,736 | DDR3 128 MB, HDMI, BLE, microSD, USB-JTAG | ~$27 | Larger LUT count + DDR3 (see Arora) |

### Third-Party / Community

| Board | FPGA | LUT4 | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Runber** | GW1N-4 | 4,608 | Gowin IDE tutorial board, integrated programmer | ~$10 | Gowin IDE learning path |
| LicheeTang (Sipeed) | GW1N-9 | 8,640 | Breadboard form-factor, DVP camera header | ~$12 | DVP camera projects |

### Choosing a Board

| You want... | Get... |
|---|---|
| Best general LittleBee development | Tang Nano 9K (~$10) |
| Cheapest FPGA in the world | Tang Nano 1K (~$5) |
| Hard PicoRV32 SoC | Tang Nano 4K (~$7) |
| Larger logic + DDR3 | Tang Nano 20K (~$27) |
| Gowin IDE learning | Runber (~$10) |

---

## References

| Source | Path |
|---|---|
| Gowin Semiconductor | https://www.gowinsemi.com |
| Project Apicula | https://github.com/YosysHQ/apicula |
| Tang Nano boards (Sipeed) | https://wiki.sipeed.com/tang |
