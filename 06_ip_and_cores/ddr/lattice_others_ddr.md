[← 06 IP & Cores Home](../README.md) · [← DDR Home](README.md) · [← Project Home](../../../README.md)

# Lattice, Microchip & Gowin DDR Controllers

Beyond the Intel/Xilinx duopoly, three other FPGA vendors offer DDR memory controllers with their own architectures, capabilities, and limitations. This article catalogs the options for non-duopoly designs.

---

## Lattice — ECP5 / MachXO / CrossLink

### ECP5 DDR3 Controller

The ECP5 family has a dedicated hard DDR3 PHY (PDDR, or Programmable DDR) capable of up to DDR3-800 (400 MHz clock):

| Parameter | ECP5-UM / ECP5-5G |
|---|---|
| **Max speed** | DDR3-800 (400 MHz) |
| **Data width** | 8/16/32-bit |
| **PHY type** | Hard PHY (DQSDLL per byte lane) |
| **Interface** | Wishbone or custom parallel |
| **Tool** | Lattice Diamond (Clarity Designer) |
| **ECC** | Not available |
| **Banks** | Fixed per side; DQS pins are predefined |

```
ECP5 DDR Architecture:
                    ┌── ECP5 DDR IP ──┐
Wishbone / Parallel ──→│ Controller ──→│ Hard DQSDLL ──→ DDR3
                       │ (soft logic)  │  (hard PHY)     up to 400 MHz
                       └─────────────────────────────────┘
```

The ECP5 DDR PHY uses **DQSDLL** blocks (one per byte lane) for read capture centering. Write leveling is NOT supported (no fly-by topology on ECP5), so the board must use T-branch topology with matched trace lengths.

### MachXO2/MachXO3 — LPDDR/DDR2

The MachXO families support simpler memory interfaces through hardened IP:

| Family | Max Type | Max Speed | Notes |
|---|---|---|---|
| **MachXO2** | LPDDR, DDR, DDR2 | 200 MHz (DDR2-400) | Hardened I2C/SPI/DDR block |
| **MachXO3** | LPDDR, DDR, DDR2 | 200 MHz | Similar to XO2; simplified pinout |
| **CrossLink-NX** | LPDDR2/3, DDR3 | DDR3-800 | Hard D-PHY + DDR PHY (nexus platform) |

> Lattice's DDR controllers are simpler than Xilinx/Intel equivalents. For designs needing high DDR throughput, ECP5 is the minimum viable Lattice platform. MachXO is suitable only for frame-buffer or small scratchpad memory.

---

## Microchip (formerly Microsemi/Actel) — PolarFire / SmartFusion2

### PolarFire DDR Controller

PolarFire uses a **hardened DDR PHY** (FDDR) integrated into the PolarFire MPF fabric:

| Parameter | PolarFire |
|---|---|
| **Max speed** | DDR4-1600, DDR3-1333, LPDDR3-1066 |
| **Data width** | 16/32/64-bit |
| **PHY type** | Hard PHY (MPF FDDR subsystem) |
| **Interface** | AXI4 slave (via CoreAXI or direct) |
| **Tool** | Libero SoC (System Builder) |
| **ECC** | Supported (64+8) |
| **DDR4 support** | Yes (PolarFire only; IGLOO2/SmartFusion2 are DDR3 max) |

PolarFire's FDDR subsystem includes dedicated PLLs, DLLs, and hard calibration logic. The calibration sequence is similar to Xilinx MIG but entirely hardware-controlled (no soft calibration state machine).

### SmartFusion2 / IGLOO2 — MDDR

| Family | Max Type | Max Speed | Notes |
|---|---|---|---|
| **SmartFusion2** | DDR3, LPDDR2 | 333 MHz (DDR3-667) | Hard MDDR controller; shares with ARM Cortex-M3 HPDMA |
| **IGLOO2** | DDR3, LPDDR2 | 333 MHz | Same MDDR block as SF2, no CPU |
| **RTG4** | DDR3 | 333 MHz | Radiation-tolerant; same MDDR block |

The MDDR controller exposes an AHB bus interface to the FPGA fabric or an internal AXI bus for the Cortex-M3 (SmartFusion2).

---

## Gowin — LittleBee / Arora

Gowin's DDR support is IP-based (soft controller with I/O SERDES):

| Family | Max Type | Max Speed | Notes |
|---|---|---|---|
| **GW1N (LittleBee)** | SDR SDRAM only | 200 MHz | No hard DDR PHY; SDRAM via GPIO |
| **GW2A (Arora)** | DDR3 | DDR3-800 | Soft controller + OSERDES/ISERDES |
| **GW2AR (Arora-II)** | DDR3 | DDR3-800 | Same; includes on-chip SDRAM option |
| **GW5AT (Arora-V)** | DDR3, DDR4 | DDR4-1333 | Hard PHY — major step up from GW2A |

The Gowin DDR3 IP generates a simple parallel interface (no Wishbone/AXI wrapper by default). You add a bus wrapper manually or use the Gowin EDA IP Generator to add an AXI/Wishbone bridge.

---

## Cross-Vendor DDR Capability Matrix

| Vendor | Family | DDR3 Max | DDR4 Max | LPDDR4 | Hard PHY | ECC |
|---|---|---|---|---|---|---|
| **Intel** | Cyclone V | 400 MHz | — | — | Yes (PHY) | No (UniPHY) |
| **Intel** | Arria 10 | 533 MHz (DDR4) | 1333 MHz | — | Yes (EMIF) | Yes (hard) |
| **Intel** | Agilex 7 | — | 1600 MHz | 2133 MHz | Yes (EMIF) | Yes (hard) |
| **Xilinx** | 7-series | 933 MHz | — | — | Half-hard | Yes (soft) |
| **Xilinx** | UltraScale+ | 933 MHz | 1600 MHz | 2133 MHz | Yes (PHASER) | Yes (hard) |
| **Lattice** | ECP5 | 400 MHz | — | — | Yes (DQSDLL) | No |
| **Lattice** | CrossLink-NX | 400 MHz | — | LPDDR3 only | Yes | No |
| **Microchip** | PolarFire | 667 MHz | 800 MHz | LPDDR3 | Yes (FDDR) | Yes |
| **Microchip** | SmartFusion2 | 333 MHz | — | LPDDR2 | Yes (MDDR) | No |
| **Gowin** | GW2A | 400 MHz | — | — | No (soft) | No |
| **Gowin** | GW5AT | 400 MHz | 667 MHz | — | Yes | No |

---

## Choosing a Non-Duopoly Controller

| Use Case | Recommendation |
|---|---|
| Low-power, simple frame buffer | Lattice ECP5 with DDR3-800 (Wishbone) |
| Mixed-signal + MCU + DDR | Microchip SmartFusion2 MDDR (Cortex-M3 direct) |
| High-reliability / radiation-tolerant | Microchip RTG4 MDDR |
| Lowest cost with DDR3 | Gowin GW2A (soft controller, works but limited speed) |
| Mid-range with DDR4 | Microchip PolarFire FDDR (only non-duopoly DDR4) |
| Open-source toolchain (Yosys/nextpnr) | Lattice ECP5 (strongest open-tool support) |

---

## Further Reading

| Article | Topic |
|---|---|
| [intel_ddr.md](intel_ddr.md) | Intel UniPHY/EMIF — full-featured controllers |
| [xilinx_ddr.md](xilinx_ddr.md) | Xilinx MIG — DDR3/DDR4/LPDDR4 across all series |
| [ddr_pin_planning.md](ddr_pin_planning.md) | PCB routing, fly-by topology, pin constraints |
| Lattice TN1295 | ECP5 DDR3 Memory Interface User Guide |
| Microchip UG0821 | PolarFire FPGA DDR Subsystem |
| Gowin SUG100 | Gowin DDR3 Memory Interface IP |
