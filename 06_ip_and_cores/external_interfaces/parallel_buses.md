[← 06 IP & Cores Home](../README.md) · [External Interfaces](README.md)

# Legacy Parallel Buses — 68000, Zorro, ISA, PCI

Modern FPGAs are increasingly used to replace or interface with vintage computing hardware. Retro-computing projects (Amiga, Atari ST, Macintosh, PC/ISA, arcade systems) require understanding legacy parallel buses that predate serial protocols like PCIe and USB. These buses are **multi-master, asynchronous or semi-synchronous, and use 5V TTL logic levels** — a very different world from modern FPGA design.

---

## Overview

| Bus | Width | Speed | Voltage | Topology | Key FPGA Use Case |
|---|---|---|---|---|---|
| **Motorola 68000** | 16-bit data + 24-bit address | ~8 MHz | 5V TTL | Single master (CPU) | Amiga/ST accelerator, cycle-exact CPU replacement |
| **Zorro II** | 16-bit data + 24-bit address | ~3.5 MHz | 5V TTL | Single master, auto-config | Amiga 500/2000 expansion |
| **Zorro III** | 32-bit data + 32-bit address | ~10 MHz | 5V TTL | Multi-master, DMA capable | Amiga 3000/4000 expansion |
| **ISA (PC/AT)** | 16-bit data + 24-bit address | 8.33 MHz | 5V TTL | Single master | XT/AT chipset replacement, sound cards |
| **PCI 2.3** | 32/64-bit data + 32-bit address | 33/66 MHz | 3.3V / 5V | Multi-master, arbiter required | PCI bridge, retro GPU replacement |
| **VME** | 16/32-bit data + 32-bit address | 25–40 MHz | 5V TTL | Multi-master, backplane | Industrial control, retrocomputing |

---

## Motorola 68000 Bus

The 68000 uses a **non-multiplexed** address/data bus with asynchronous handshaking:
- **A1–A23** — Address bus (A0 implied by UDS/LDS)
- **D0–D15** — Data bus (bidirectional, tri-state)
- **/AS** — Address Strobe (indicates valid address)
- **/UDS, /LDS** — Upper/Lower Data Strobe (byte select)
- **R/W** — Read/Write direction
- **/DTACK** — Data Transfer Acknowledge (slave ready)
- **/BERR, /VPA, /VMA** — Bus error, Valid Peripheral Address, Valid Memory Address

### FPGA Implementation

A 68000 bus interface in an FPGA needs:
1. **5V-tolerant inputs** or level translators (modern FPGAs are NOT 5V tolerant)
2. **Bidirectional tri-state buffers** for D0–D15
3. **Async state machine** sensitive to /AS, /UDS, /LDS, R/W edges
4. **Cycle timing** matching original CPU (S2–S7 states)

```
68000 Bus Cycle (Read):
  ────────────────────────────────────────────────────────────────
  Clock    ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
          ─┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └─
  State      S0    S1    S2    S3    S4    S5    S6    S7
  /AS    ────┐     └───────────────────────────────────────┐
             ↑Address valid    Data valid →↑
  /UDS/LDS ──┐     └───────────────────────────────────────┐
  R/W    ────────────────────────────────┐                 (high=read)
  /DTACK ────────────────────────────────┘← Slave asserts when ready
```

### FPGA Family Suitability

| FPGA | 68000 Bus Suitability | Notes |
|---|---|---|
| Intel MAX 10 | Excellent | 3.3V with 5V-tolerant inputs on Bank 1; instant-on flash |
| Xilinx Spartan-7 | Good | HR banks at 3.3V; need SN74LVC8T245 for 5V |
| Lattice MachXO3 | Excellent | Instant-on, 3.3V with 5V-tolerant inputs |
| Gowin LittleBee | Good | Low cost; verify 5V tolerance per pin |
| Microchip PolarFire | Fair | No 5V tolerance; level translators required |

---

## Zorro II / Zorro III (Amiga Expansion)

Zorro is the Amiga's native expansion bus. FPGA projects commonly implement:
- **Zorro II/III slave cards** (accelerators, RTG graphics, network, USB)
- **Complete Amiga chipset replacements** (using FPGA as Paula/Agnus/Denise)

### Zorro II (16-bit)

| Signal | Function |
|---|---|
| **/CFGIN, /CFGOUT** | Auto-configuration chain |
| **/SLAVE** | Card claims the bus cycle |
| **/OVR** | Override — card wants bus mastership |
| **/INT2, /INT6, /INT7** | Interrupts to CPU |

### Zorro III (32-bit, DMA)

Zorro III added:
- **32-bit data bus** (D0–D31)
- **32-bit address bus** (A0–A31)
- **/FCS** — Fast Cycle Start
- **/MTCR** — Master Transfer Complete Request (DMA handshaking)
- **Burst transfers** — 32 bytes in one bus acquisition

### Critical: The 68000 Read-Modify-Write Problem

The 68000's TAS (Test and Set) instruction does a **read-modify-write cycle** that cannot be interrupted. FPGA slaves must complete the full RMW atomically or the Amiga's multitasking breaks.

---

## ISA Bus (PC/AT)

ISA is simpler than Zorro but has its own quirks:
- **I/O space** (separate from memory space) accessed with /IOR and /IOW
- **8-bit and 16-bit transfers** — /IOCS16 or /MEMCS16 indicates 16-bit capable
- **3 DMA channels** (DRQ1–DRQ3, DACK1–DACK3) for floppy, sound, etc.
- **No auto-configuration** — jumpers or DIP switches for base address

### FPGA as ISA Device

Common retro FPGA projects:
- **Sound Blaster compatible** — OPL3 FM + DAC on FPGA
- **NE2000 Ethernet** — RTL8019AS-compatible MAC
- **VGA/ET4000 video** — SVGA core with ISA interface

---

## PCI 2.3

PCI is more modern but still "legacy" compared to PCIe. Key differences from PCIe:
- **Parallel shared bus** (not point-to-point serial)
- **3.3V or 5V signaling** (universal cards support both)
- **Arbiter required** for multi-master systems
- **33 MHz or 66 MHz clock**

### FPGA Implementation

PCI in an FPGA is a **soft core** — no vendor provides hardened PCI blocks anymore:
- OpenCores has PCI host/target cores (~3000 LUTs)
- Vendor IP: Xilinx LogiCORE PCI32 (discontinued), Intel PCI Lite
- Modern FPGAs can easily handle 33 MHz PCI in fabric

| Signal | Direction | Function |
|---|---|---|
| AD[31:0] | Bidir | Multiplexed address/data |
| C/BE[3:0]# | Bidir | Command/Byte enable |
| PAR | Bidir | Even parity |
| FRAME# | Output | Transaction start |
| IRDY#, TRDY# | Output | Initiator/Target ready |
| STOP# | Output | Target requests disconnect |
| DEVSEL# | Output | Target claims the cycle |
| REQ#, GNT# | Output | Bus request/grant |
| IDSEL | Input | Configuration space chip select |

---

## Level Translation for All Legacy Buses

Every legacy bus uses **5V TTL**. Modern FPGAs do not tolerate 5V. See [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) for:
- **SN74LVC16T245** — 16-bit bidirectional translator (perfect for 68000/Zorro data bus)
- **TXS0108E** — Auto-direction for control signals
- **BSS138 + resistor networks** — Cheap prototype solution

### Recommended Translation Strategy

```
68000/Zorro Data Bus (D0-D15):
  5V bus ──→ SN74LVC16T245 (A side) ──→ (B side) ──→ FPGA HR bank @ 3.3V

Control signals (/AS, /UDS, /LDS, R/W, /DTACK):
  5V bus ──→ SN74LVC8T245 (direction controlled by R/W) ──→ FPGA

/DTACK generation:
  FPGA ──→ SN74LVC8T245 (B→A when FPGA is slave) ──→ 5V bus
```

---

## FPGA Resource Costs

| Bus Implementation | LUTs | FFs | Notes |
|---|---|---|---|
| 68000 slave (simple memory) | 200–400 | 100–200 | Address decode, async state machine |
| 68000 slave (full cycle-acact) | 800–1500 | 400–800 | S2–S7 state machine, DTACK timing |
| Zorro II auto-config slave | 300–500 | 150–300 | Configuration ROM, address decoder |
| Zorro III slave + DMA | 1000–2000 | 500–1000 | 32-bit, burst, DMA master logic |
| ISA device (I/O + MEM) | 200–400 | 100–200 | Simple address decode |
| ISA DMA controller | 500–800 | 300–500 | DRQ/DACK handshaking |
| PCI 2.3 target | 2000–3000 | 1000–1500 | Full protocol, parity, configuration space |
| PCI 2.3 host bridge | 4000–6000 | 2000–3000 | Arbiter, initiator, target combined |

---

## Best Practices

1. **Use 3.3V FPGAs with 5V-tolerant inputs when possible** — Intel MAX 10 Bank 1 and Lattice MachXO3 have 5V-tolerant pins
2. **Add series resistors (33–100Ω) on every 5V→FPGA path** — Even with level translators, resistors protect against transients
3. **Match bus timing exactly** — Vintage computers have strict cycle timings; use oscilloscope to verify /DTACK assertion time
4. **Implement open-drain /DTACK** — Multiple devices can drive /DTACK; FPGA output must be open-drain or tri-state
5. **Buffer the FPGA from the bus during configuration** — Use /CFGOUT or external buffer to isolate FPGA until configured

---

## Pitfalls

1. **"My FPGA has 3.3V banks, so it's fine with 5V"** — No. 3.3V absolute maximum is typically 3.6V. 5V WILL destroy the IO cell over time.
2. **Missing /DTACK on read-modify-write** — TAS instruction on 68000 expects /DTACK on both read and write phases. Missing the second /DTACK causes bus error.
3. **Zorro III burst mode without proper /MTCR handling** — Burst transfers require precise /MTCR assertion timing. Wrong timing hangs the DMA controller.
4. **ISA I/O space vs memory space confusion** — Some vintage cards respond to both. Check /IOR, /IOW, /MEMR, /MEMW separately.
5. **PCI parity errors** — PCI requires even parity across AD and C/BE. Miscalculated parity causes target aborts.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| MC68000 User's Manual (8th Ed.) | NXP/Freescale | Full bus timing, S-states, RMW cycles |
| Amiga Hardware Reference Manual (3rd Ed.) | Commodore/Addison-Wesley | Zorro II/III, autoconfig, DMA, Gary/Alice/Bridgette |
| ISA System Architecture (MindShare) | Addison-Wesley | PC/AT bus timing, DMA, interrupts |
| PCI Local Bus Specification 2.3 | PCI-SIG | PCI protocol, electrical, configuration space |
| [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) | This KB | 5V→3.3V translation for all legacy buses |
| [Zorro Bus](../../amiga/01_hardware/common/zorro_bus.md) | Amiga KB | Amiga-specific Zorro implementation details |
