[← CPLD Home](README.md) · [← Architecture Home](../README.md) · [← Project Home](../../README.md)

# CPLD vs FPGA: When to Use Which

CPLDs and FPGAs solve different problems. The choice is not about "better" — it is about matching the device architecture to the design requirements.

> **For detailed workflow-level use cases** (power sequencing, safety interlocks, bus bridging, battery-powered designs, hybrid architectures), see [`cpld_architecture.md`](cpld_architecture.md). This document focuses on the high-level decision framework, power/cost comparisons, and a summary flowchart.

---

## Architectural Comparison

```
CPLD: Coarse-Grained, Deterministic
┌─────────────────────────────────────────┐
│  AND-OR Array → Macrocell → I/O Pin     │
│  (predictable 5-15 ns pin-to-pin)       │
└─────────────────────────────────────────┘

FPGA: Fine-Grained, Flexible
┌─────────────────────────────────────────┐
│  LUT → Carry Chain → DSP → RAM → I/O    │
│  (routing-dependent timing)             │
└─────────────────────────────────────────┘
```

### Core Differences

| Aspect | CPLD | FPGA |
|---|---|---|
| **Logic unit** | Macrocell (AND-OR + FF) | LUT (4–6 input lookup table) |
| **Granularity** | Coarse (1 macrocell ≈ 1 output) | Fine (1 LUT ≈ 1 logic function) |
| **Interconnect** | Central switch matrix | Segmented routing channels |
| **Timing** | Deterministic, predictable | Routing-dependent, requires STA |
| **Density** | 32–2,000 macrocells | 1,000–3,500,000+ LUTs |
| **Configuration** | Non-volatile (flash/EEPROM) | Volatile (SRAM) or flash-based |
| **Power-on** | Instant-on (0 ms) | Requires bitstream load (10 ms–2 s) |
| **Power** | Very low static current | Higher static (especially large FPGAs) |
| **Clocking** | Limited or no PLLs | Rich PLL/DLL/clock tree |
| **DSP/RAM** | None or minimal | Hard DSP blocks, block RAM |
| **SerDes** | None | Up to 112 Gbps transceivers |
| **Price (small)** | $1–$10 | $5–$50 |
| **Price (large)** | N/A (no large CPLDs) | $100–$20,000+ |

---

## Decision Matrix

### Use a CPLD When...

| Requirement | Why CPLD Wins |
|---|---|
| **Always-on, battery-powered** | 10–300 µA static current vs. 10–500 mA for FPGA |
| **Instant boot** | No configuration delay; logic active at power-on |
| **Glue logic / bus bridging** | Small state machines, level shifters, address decoders |
| **Deterministic latency** | Pin-to-pin delay is fixed ±0 ns; no routing surprises |
| **No external config memory** | Flash is on-chip; BOM reduced by 1–2 components |
| **Security (no bitstream)** | No external SPI flash to read and clone |
| **5V tolerance** | Many CPLDs tolerate 5V I/O (e.g., MAX V, ATF15) |
| **Small package (QFN/TQFP)** | Available in 2×2 mm WLCSP and 32-pin TQFP |

### Use an FPGA When...

| Requirement | Why FPGA Wins |
|---|---|
| **High logic density** | >2,000 LUT-equivalents; CPLDs top out around 1,270 LEs |
| **DSP / math acceleration** | Hard multiplier-accumulators, floating-point DSP |
| **Memory buffers** | Block RAM (10s–1000s of Kb) for FIFOs, frame buffers |
| **High-speed I/O** | SerDes, PCIe, DDR memory controllers |
| **Complex algorithms** | Parallel pipelines, systolic arrays, video processing |
| **Soft processors** | Nios II, MicroBlaze, RISC-V need 5K+ LUTs minimum |
| **Reconfigurable logic** | Partial reconfiguration, dynamic function swapping |
| **Prototyping / research** | Rapid iteration with SRAM reprogramming |

---

## Overlap Zone: Flash-Based FPGAs

The distinction blurs with **non-volatile FPGA** families that borrow CPLD traits:

| Device Type | Examples | CPLD Traits | FPGA Traits |
|---|---|---|---|
| **Flash FPGA** | Intel MAX 10, Lattice MachXO3 | Instant-on, no external config, low power | LUT fabric, DSP, PLLs |
| **SRAM+flash FPGA** | Xilinx Spartan-3AN, Lattice XP2 | On-chip config flash | LUT fabric, block RAM |
| **Antifuse FPGA** | Microchip RTAX-S, ProASIC3 | Non-volatile, radiation-tolerant | LUT fabric, higher density |

**Rule of thumb:** If your design fits in a CPLD macrocell count but you need a PLL or DSP block, use a flash-based FPGA like MAX 10 or MachXO3.

---

## Power Comparison by Sleep State

| State | CPLD (MAX V) | FPGA (Cyclone V) | FPGA (Zynq-7000) |
|---|---|---|---|
| Active (typical) | 5–50 mA | 100–500 mA | 200–1,000 mA |
| Static / idle | 25–300 µA | 50–300 mA | 100–500 mA |
| Power-on delay | 0 µs | 50–200 ms (config from QSPI) | 500 ms–2 s (boot Linux) |
| Config reprogram | JTAG, ~1 s | JTAG or SPI, ~1 s | JTAG or SPI, ~1 s |

**CPLDs win decisively** in always-on, low-duty-cycle applications where the device must be ready instantly but draws power 24/7.

---

## Cost Comparison at Equivalent Functionality

| Function | CPLD Solution | FPGA Solution | Cost Winner |
|---|---|---|---|
| 16-bit address decoder + LEDs | MAX V 5M40Z ($2) | Smallest FPGA ($5+) | CPLD |
| SPI-to-parallel bridge | MAX V 5M80Z ($3) | FPGA overkill | CPLD |
| Simple motor controller | MAX 10 10M02 ($8) | Cyclone V ($25+) | CPLD/MAX 10 |
| 720p video scaler | MAX 10 10M50 ($25) — tight | Cyclone V ($40) | FPGA |
| 1080p H.264 encode | Not possible | Zynq ($200+) | FPGA only |
| 100G Ethernet NIC | Not possible | Stratix 10 ($5,000+) | FPGA only |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Using FPGA for simple glue logic | BOM bloat, power waste, config complexity | Use CPLD or MAX 10 |
| Using CPLD for DSP pipeline | Insufficient density, no multipliers | Use FPGA with DSP blocks |
| Ignoring power-on delay | System hangs waiting for FPGA config | Use CPLD for critical boot logic |
| Assuming all non-volatile logic is CPLD | MAX 10 is FPGA architecturally | Verify LUT vs. macrocell architecture |
| Choosing CPLD for high-speed SerDes | No CPLD has transceivers | Use FPGA (even small Artix-7) |

---

## Summary Flowchart

```
Start
  │
  ├── Logic density > 2,000 LEs? ──► FPGA
  │
  ├── Need DSP / block RAM / SerDes? ──► FPGA
  │
  ├── Need instant-on + very low power? ──► CPLD or MAX 10
  │
  ├── Simple glue / bus / state machine? ──► CPLD
  │
  ├── Need ADC + FPGA fabric in one chip? ──► MAX 10
  │
  └── Need 5V-tolerant I/O on a budget? ──► CPLD (MAX V, ATF15)
```

---

## Further Reading

| Document | Source |
|---|---|
| CPLD Architecture and Macrocells | This knowledge base |
| Intel MAX Family | This knowledge base |
| Non-Volatile Programmable Logic | This knowledge base |
| FPGA Fabric Architecture | `../fabric/README.md` |
