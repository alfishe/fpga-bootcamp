[← CPLD Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# CPLD Architecture and Macrocells

Complex Programmable Logic Devices (CPLDs) evolved from PAL (Programmable Array Logic) and GAL (Generic Array Logic) devices. Unlike FPGAs, which use LUT-based fine-grained logic, CPLDs use a **coarse-grained architecture** built around macrocells and deterministic interconnect.

---

## The PAL Heritage: AND-OR Array

CPLDs retain the fundamental PAL structure: a programmable **AND array** feeding a fixed **OR array**.

```
                    Inputs (n)
                       │
                       ▼
            ┌─────────────────────┐
            │   Programmable AND  │
            │      Array          |
            │  (product terms)    │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │      Fixed OR       │
            │      Array          │
            └──────────┬──────────┘
                       │
                       ▼
                 Macrocell
```

**Key difference from FPGA:**
- CPLD: AND-OR sum-of-products logic, deterministic timing
- FPGA: LUTs implement any N-input Boolean function, routing-dependent timing

---

## Macrocell: The Atomic Unit

A macrocell is the smallest programmable logic unit in a CPLD. It combines:

| Component | Function |
|---|---|
| **Product Term Array** | 5-33 AND terms feeding an OR gate |
| **XOR Gate** | Optional polarity inversion (active-high/low) |
| **D/T/JK Flip-Flop** | Registered output with clock, preset, clear |
| **Bypass MUX** | Combinatorial or registered output selection |
| **Output Enable** | Tristate control for I/O pin |
| **Feedback Path** | Output routed back to the AND array |

### Macrocell Structure

```
    Product Terms (from AND array)
         │ │ │ │ │
         ▼ ▼ ▼ ▼ ▼
    ┌─────────────────┐
    │   OR Gate       │
    │  (sum of prod)  │
    └────────┬────────┘
             │
        ┌────┴────┐
        ▼         ▼
    ┌──────┐   ┌──────┐
    │ XOR  │   │Bypass│
    │Inv   │   │ MUX  │
    └──┬───┘   └──┬───┘
       │          │
       ▼          ▼
    ┌──────┐   ┌──────┐
    │  FF  │   │Comb. │
    │D/T/JK│   │ Out  │
    └──┬───┘   └──┬───┘
       │          │
       └────┬─────┘
            ▼
       I/O Pin
       (tristate)
```

**Typical macrocell capacity:**
- 5 to 33 product terms per macrocell
- 1 flip-flop per macrocell
- 1 output pin per macrocell (with feedback)

---

## Interconnect Architecture

CPLDs use a **deterministic, non-segmented interconnect** — a central switch matrix connects logic blocks. This is fundamentally different from FPGA island-style routing.

### CPLD Interconnect

```
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │  LAB 0  │◄───►│  LAB 1  │◄───►│  LAB 2  │
        │32 MCs   │     │32 MCs   │     │32 MCs   │
        └────┬────┘     └────┬────┘     └────┬────┘
             │               │               │
             └───────────────┼───────────────┘
                             │
                    ┌─────────┴─────────┐
                    │  Global Switch    │
                    │     Matrix        │
                    └───────────────────┘
```

**Logic Array Block (LAB):** A cluster of 16-36 macrocells sharing a local AND array.

**Characteristics:**
- All paths through the switch matrix have **predictable delay**
- Pin-to-pin delay is typically **5-15 ns** and does not vary with routing
- No place-and-route timing closure needed — if it fits, it meets timing

---

## CPLD Configuration Technology

CPLDs are inherently **non-volatile**. Configuration is stored in on-chip flash or EEPROM.

| Technology | Characteristic |
|---|---|
| **Flash-based** | Reprogrammable, retains config at power-off, modern standard |
| **EEPROM-based** | Older CPLDs (e.g., Altera MAX 7000S), slower erase |
| **One-Time Programmable (OTP)** | Fuses or antifuses, cannot be erased |

**Advantage:** Instant-on at power-up. No external configuration PROM, no bitstream loading delay.

---

## Modern CPLD Families

| Vendor | Family | Density | Voltage | Key Feature |
|---|---|---|---|---|
| **Intel/Altera** | MAX V | 40–1,270 LEs | 1.8V core | On-chip flash, internal oscillator |
| **Intel/Altera** | MAX 10 | 2K–50K LEs | 3.3V / 1.2V | Flash + SRAM hybrid, ADC, dual config |
| **Lattice** | MachXO2/XO3 | 256–9K LUTs | 1.2–3.3V | Instant-on, embedded flash, small form factor |
| **Lattice** | ispMACH 4000 | 32–512 macrocells | 1.8–3.3V | Ultra-low power, CPLD classic |
| **Microchip/Atmel** | ATF15 | 32–128 macrocells | 3.3–5V | 5V tolerant, industrial temp |
| **Xilinx** | XC9500XL | 36–288 macrocells | 3.3V | Obsolete; last Xilinx CPLD line |

> **Note:** Xilinx exited the CPLD market. The XC9500XL and CoolRunner-II families are obsolete with no direct successors. For Xilinx non-volatile needs, users must look to flash-based FPGAs (Spartan-3AN historically, or partner with Lattice/Microchip for true CPLDs).

---

## CPLD Power and Timing

### Power Characteristics

| Parameter | Typical CPLD | Comparison |
|---|---|---|
| Static current | 10–300 µA | 10–100× lower than FPGA |
| Dynamic power | Low (no clock tree) | No PLL/DCM overhead |
| Wake time | 0 µs (instant-on) | FPGA needs 10 ms–2 s config |
| I/O banks | 2–4 | Mixed-voltage support |

### Timing Characteristics

| Parameter | Value | Notes |
|---|---|---|
| Pin-to-pin (combinatorial) | 5–15 ns | Routing-independent |
| Pin-to-pin (registered) | 3–10 ns | Includes FF clock-to-out |
| Max clock frequency | 100–400 MHz | Limited by macrocell FF speed |
| Propagation consistency | ±0 ns | Same delay for all paths through switch matrix |

---

## When CPLDs Are Best: Real-World Use Cases

### 1. Power Sequencing and Reset Management

CPLDs are the industry standard for power-rail sequencing in complex SoC boards. A typical ARM SoC requires 5–10 power rails to come up in a specific order with millisecond delays.

```
Power Input (3.3V, 1.8V, 1.2V, 0.85V)
         │
         ▼
    ┌──────────┐
    │  CPLD    │──► En_3V3  ──► [wait 10ms] ──► En_1V8
    │ Sequencer│──► En_1V2  ──► [wait 5ms]  ──► En_0V85
    │          │──► POR_n   ──► [wait 20ms] ──► SoC_RESET_n
    └──────────┘
         ▲
         └── Reads PG (Power Good) from each regulator
```

**Why CPLD:** Instant-on means the sequencer is ready before any regulator stabilizes. Deterministic timing ensures reset de-assertion happens exactly when required. A 5M40Z ($2) handles this comfortably.

### 2. Bus Bridging and Protocol Translation

Translating between legacy and modern buses is a classic CPLD sweet spot.

| Translation | CPLD Fit | Why |
|---|---|---|
| **I2C ↔ SPI** | Excellent | Small state machine, < 50 macrocells |
| **8-bit parallel ↔ SPI** | Excellent | Shift register + control logic |
| **5V ↔ 3.3V level shift** | Excellent | Many CPLDs have 5V-tolerant I/O |
| **AXI-Lite ↔ Avalon-MM** | Poor | Too wide, needs FIFO/bridge IP |
| **PCIe ↔ anything** | Impossible | No SerDes |

### 3. Safety-Critical I/O and Interlocks

Industrial motor drives, medical devices, and automotive subsystems require deterministic interlock logic.

**Example: Emergency Stop Chain**
```
E-Stop Button ──► CPLD ──► Motor Drive Enable
                    │
                    ├──► Light Curtain Input
                    ├──► Door Switch Input
                    └──► Delayed Brake Release (exact 50ms)
```

**Why CPLD:** The 7.5 ns pin-to-pin delay through the switch matrix is guaranteed by the datasheet — no timing closure, no corner-case routing analysis. The same logic in an FPGA would require post-route STA and constraints.

### 4. Battery-Powered Always-On Logic

Wearables, IoT sensors, and portable medical devices need logic that consumes microamps.

| Scenario | CPLD | FPGA |
|---|---|---|
| **Door sensor (open/close detect)** | 25 µA standby, instant response | 50 mA standby, 100 ms boot |
| **Smart meter event logging** | 50 µA, wake on GPIO edge | 200 mA, unacceptable for battery |
| **Key fob button decoder** | 10 µA, < 1 µs response | Not viable |

---

## When NOT to Use a CPLD

### 1. Designs Exceeding ~1,000 Macrocell Equivalents

CPLDs simply do not scale. The largest MAX V (5M1270Z) offers 980 equivalent macrocells. If your design needs:

- Soft processor (Nios II needs ~3,000 LEs minimum)
- Video pipeline (even simple scaling needs FIFOs + line buffers)
- Digital signal processing (FIR filters need multiply-accumulate)

**Use an FPGA instead.** The cost crossover happens around 500–1,000 LEs, where a small Cyclone or Artix-7 becomes cheaper per logic gate.

### 2. Algorithms Needing DSP or Block RAM

CPLDs have **no hard DSP blocks** and **no block RAM**. A 16-tap FIR filter in a CPLD would consume hundreds of macrocells for multipliers and shift registers. In an FPGA, this is one DSP48 slice.

| Function | CPLD Cost | FPGA Cost |
|---|---|---|
| 16-tap FIR filter | 400+ macrocells (entire device) | 1 DSP48 slice |
| 1 KB FIFO | 64 macrocells + external SRAM | 1 block RAM (free in fabric) |
| FFT (256-point) | Impossible | ~2,000 LUTs + DSPs |

### 3. High-Speed Serial I/O

No CPLD family includes SerDes transceivers. If you need:

- Gigabit Ethernet (PCS/PMA)
- PCIe (any generation)
- USB 3.0/3.1
- DisplayPort / HDMI 2.0
- JESD204B ADC/DAC interfaces

**Use an FPGA** — even the smallest Artix-7 has GTP transceivers.

### 4. Designs Requiring Frequent In-Field Reconfiguration

Flash-based CPLDs are rated for **10,000 program/erase cycles**. If your application needs:

- Daily firmware updates over-the-air
- Dynamic function swapping based on user mode
- Bitstream encryption key rotation

**Use an SRAM FPGA** with external encrypted flash. SRAM FPGAs have unlimited reconfigurations (the external flash wears, but it's replaceable and cheap).

### 5. Complex Clocking Requirements

CPLDs lack PLLs and have limited clock distribution. If you need:

- Clock multiplication / division
- Dynamic phase shifting
- Multiple clock domains with CDC
- Spread-spectrum clocking

**Use an FPGA** (or MAX 10 / MachXO3 flash FPGA, which have PLLs).

---

## CPLD Pros and Cons

| Aspect | Pro | Con |
|---|---|---|
| **Power-on behavior** | Instant-on — logic active at power-up, no config delay | — |
| **Static power** | Ultra-low: 10–300 µA standby vs. 50–500 mA for typical FPGAs | — |
| **Timing predictability** | Pin-to-pin delay fixed by datasheet; no routing variance | — |
| **BOM simplicity** | No external config memory; flash is on-chip | — |
| **Package size** | 2×2 mm WLCSP, 32-pin TQFP, 44-pin QFP available | — |
| **Legacy I/O** | 5V-tolerant I/O in MAX V, ATF15 for direct legacy interfacing | — |
| **Security** | No external bitstream to intercept or clone | — |
| **Tool flow** | No timing constraints or place-and-route closure needed | — |
| **Unit cost** | $1–$10 for typical glue-logic densities | Higher **per-gate cost at scale** — above ~1,000 LEs, FPGAs win |
| **Harsh environments** | No SRAM cells susceptible to SEU/soft errors | — |
| **Logic density** | — | Hard ceiling at ~1,000–2,000 macrocell equivalents; no path to large designs |
| **DSP / math** | — | No hard DSP blocks; FIR/FFT built from macrocells — inefficient |
| **On-chip memory** | — | No block RAM; FIFOs need external SRAM or consume macrocells |
| **High-speed I/O** | — | No SerDes; cannot do PCIe, GigE, USB 3.0, or JESD204B |
| **Clocking** | — | No PLLs; cannot multiply/divide clocks or phase-shift dynamically |
| **Reconfigurability** | — | Flash wears after ~10,000 program/erase cycles |
| **Granularity** | — | One macrocell ≈ one output; inefficient for wide data-path logic |
| **Soft processors** | — | Nios II / MicroBlaze / RISC-V need 3,000+ LEs — far beyond CPLD capacity |
| **Vendor ecosystem** | — | Xilinx exited; Intel MAX V is last-gen; only Lattice and Microchip actively invest |

---

## CPLD + FPGA Hybrid Designs

Many systems use **both** — a CPLD for instant-on tasks and an FPGA for heavy lifting.

```
┌─────────────────────────────────────────┐
│           System Power-On               │
│                                         │
│  3.3V ──► CPLD ──► Power sequencing    │
│              │                          │
│              ├──► Config FPGA flash      │
│              │    (bitstream validator) │
│              ├──► Safety interlocks      │
│              │    (always active)        │
│              └──► Boot mode select       │
│                                         │
│  After boot:                            │
│  CPLD ──► FPGA via SPI/I2C (status)    │
│  FPGA ──► CPLD via GPIO (commands)     │
└─────────────────────────────────────────┘
```

**Example:** High-end industrial PLCs use a MAX V CPLD for E-stop, watchdog, and power sequencing, while a Cyclone V FPGA runs the motion control algorithms. The CPLD can hold the system in safe state even if the FPGA crashes or is being reconfigured.

> **See also:** [`cpld_vs_fpga.md`](cpld_vs_fpga.md) for a complete decision matrix, power comparison tables, cost analysis, and a summary flowchart.

---

## Further Reading

| Document | Source |
|---|---|
| MAX V Device Handbook | Intel (altera.com) |
| ispMACH 4000ZE Family Data Sheet | Lattice Semiconductor |
| MachXO2 Family Data Sheet | Lattice Semiconductor |
| Architecture of FPGAs and CPLDs: A Tutorial | Brown & Rose, IEEE Survey |
