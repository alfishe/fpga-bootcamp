[← 14 References Home](README.md) · [← Project Home](../../README.md)

# Common Package Pinout Patterns

Quick-reference for pinout patterns across popular FPGA packages — which pins are clock-capable, which banks support what I/O standards, and what to watch out for.

---

## Clock-Capable Pin Identification

Every FPGA has dedicated clock-capable (CC) or global clock (GC) pins. Using a non-CC pin for a clock forces the signal through general routing, causing high skew and poor timing.

| FPGA Family | Clock Pin Naming | Per Bank | Notes |
|---|---|---|---|
| **Xilinx 7-Series** | MRCC (Multi-Region), SRCC (Single-Region) | 4 per bank (2 MRCC + 2 SRCC) | MRCC can drive multiple clock regions |
| **Intel Cyclone V** | CLK[0..15][p,n] | 4–8 per side | Differential clock inputs on dedicated pins |
| **Lattice ECP5** | PCLK (Primary), SCLK (Secondary) | Varies per bank | Check pinout spreadsheet for PCLK pins |
| **Gowin GW1N** | GCLK (Global Clock) | 4–8 total | Very limited — plan clock pins early |

---

## Popular Package Ball Maps (Key Pins Only)

### Xilinx Artix-7 XC7A35T (CPG236)

| Pin | Function | Bank | Notes |
|---|---|---|---|
| R4 | CCLK (config) | 0 | Do not use as GPIO |
| P4 | DONE | 0 | Do not use as GPIO |
| L16 | MRCC (clock) | 34 | Clock-capable |
| M17 | MRCC (clock) | 34 | Clock-capable |
| G14 | JTAG TMS | — | Dedicated |
| G15 | JTAG TCK | — | Dedicated |
| H15 | JTAG TDO | — | Dedicated |
| H16 | JTAG TDI | — | Dedicated |

### Intel Cyclone V 5CSEMA5 (U672)

| Pin | Function | Bank | Notes |
|---|---|---|---|
| HPS_DDR_* | HPS DDR3 | HPS | Dedicated to HPS, not FPGA GPIO |
| FPGA_CLK1_p | FPGA clock | 5A | Dedicated FPGA clock input |
| MSEL[4:0] | Config mode | — | Strapped at boot, do not float |
| nCONFIG | Config start | — | External pull-up required |
| CONF_DONE | Config done | — | External pull-up required |

### Lattice ECP5-85K (CABGA381)

| Pin | Function | Bank | Notes |
|---|---|---|---|
| PCLK[1-4]_p | Primary clock | per bank | Best jitter for high-speed applications |
| SCLK_* | Secondary clock | per bank | Lower performance than PCLK |
| PROGRAMN | Config start | — | Active low |
| DONE | Config done | — | Open drain, needs pull-up |
| MCLK | Master config clock | — | SPI flash clock during config |

---

## I/O Bank Organization

| FPGA Family | Banks | VCCIO per Bank | Supports |
|---|---|---|---|
| **Artix-7** | 2–5 banks | 1.2V–3.3V | LVCMOS, LVDS (HR banks only) |
| **Cyclone V** | 8 I/O banks | 1.2V–3.3V | All banks support LVDS |
| **ECP5** | 8 I/O banks | 1.2V–3.3V | LVDS on differential pairs only |
| **Gowin GW1N-9** | 4 I/O banks | 1.5V–3.3V | LVDS on Bank 2 only |

**Bank sharing rule:** All I/Os in a bank share the same VCCIO voltage. Mixing 1.8V and 3.3V I/Os requires placing them in different banks.

---

## DCI (Digitally Controlled Impedance) Pins

| FPGA Family | DCI Support | Which Pins |
|---|---|---|
| **Xilinx 7-Series HP banks** | Yes | VRP/VRN reference resistors required per bank |
| **Xilinx 7-Series HR banks** | No (use external termination) | — |
| **Intel Cyclone V** | OCT (On-Chip Termination) | RUP/RDN pins per bank |
| **Lattice ECP5** | No DCI | External termination required |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Clock on non-CC pin | Poor timing, high skew | Move clock to MRCC/GC pin |
| VCCIO mismatch | Bank contention, damaged I/O | Verify all pins in bank use same VCCIO |
| Shared config pins as GPIO | Board won't configure | Check pin list in datasheet; some config pins are dual-purpose |
| Missing DONE pull-up | Configuration fails | 330 Ω to VCCO on DONE pin |
