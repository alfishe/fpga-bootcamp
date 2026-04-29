[← 15 Case Studies Home](README.md) · [← Project Home](../../README.md)

# Common FPGA Failures — Root Causes & Fixes

A catalog of frequently encountered FPGA failures organized by category: metastability, timing violations, power sequencing, configuration failures, and clocking issues. Each entry includes the symptom, root cause, and resolution.

---

## Metastability

| Symptom | Root Cause | Fix |
|---|---|---|
| Intermittent data corruption across clock domains | CDC crossing without synchronizer | 2-FF synchronizer on single-bit signals; async FIFO or handshake for multi-bit |
| Random CPU hangs in SoC | Unsynchronized external input to bus register | Add 2-FF sync + edge detection before CSR |
| MTBF violations (calculated failure rate) | Synchronizer chain too short | 3-FF chain for high-MTBF requirements (aero/med) |

**Golden rule:** Any signal crossing clock domains must pass through at least 2 flip-flops in the destination domain before use.

---

## Timing Violations

| Symptom | Root Cause | Fix |
|---|---|---|
| Setup time violation (negative slack) | Logic path too long between registers | Pipeline the path: insert register stage |
| Hold time violation | Clock skew > data path delay | Add delay to data path; check clock tree |
| `No routes possible` error | Congestion or over-constrained design | Reduce utilization, relax pblocks, add routing layers |
| Timing met in synth, failed in PAR | Synthesis estimate optimistic vs physical placement | Use physical-aware synthesis; check high-fanout nets |
| Negative slack on I/O paths | Missing `set_input_delay` / `set_output_delay` | Add I/O timing constraints referencing external device |

---

## Power Sequencing

| Symptom | Root Cause | Fix |
|---|---|---|
| FPGA doesn't configure after power-up | VCCINT ramp too slow — POR timer expires | Check PMIC soft-start; reduce VCCINT ramp time to <50ms |
| FPGA draws excessive current, no config | Incorrect power sequencing (e.g., VCCO before VCCINT) | Verify sequence: VCCINT → VCCAUX → VCCO |
| Transceivers fail to lock | MGTAVCC/MGTAVTT noisy or late | Dedicated LDO for transceiver rails; check PSRR |
| Random configuration failures at cold temp | PLL lock lost due to voltage droop | Add bulk capacitance (100µF+) near FPGA core supply |

---

## Configuration Failures

| Symptom | Root Cause | Fix |
|---|---|---|
| `INIT_B` stuck low | CRC check failed on bitstream | Rebuild bitstream; check flash integrity |
| `DONE` never goes high | Missing external pull-up on DONE pin | 330Ω to VCCO on DONE |
| `PROGRAM_B` keeps resetting | Floating PROGRAM_B pin | External 4.7kΩ pull-up to VCCO |
| JTAG IDCODE = `0xFFFFFFFF` | JTAG chain broken (TDI/TDO open) | Check JTAG header soldering; verify TCK continuity |
| Flash programming succeeds but FPGA doesn't boot | MSEL/M[2:0] wrong for flash mode | Verify strapping resistors match flash config mode |
| FPGA configures but bitstream wrong | Old .mcs / .pof in flash | Erase flash before reprogramming; old data can persist |

---

## Clocking Issues

| Symptom | Root Cause | Fix |
|---|---|---|
| PLL doesn't lock | Input clock outside PLL frequency range | Check PLL min/max input frequency in datasheet |
| High jitter on fabric clock | Clock on non-CC pin; PLL cascade | Route clock to MRCC/GC pin; avoid PLL→PLL cascading |
| `No clock defined` warning | Missing `create_clock` on input port | Add create_clock constraint on all primary inputs |
| Generated clock timing wrong | Missing `create_generated_clock` on PLL output | Define generated clocks at PLL outputs |
| PLL lock but system unstable | Reference clock jitter too high | Use dedicated oscillator, not FPGA-derived refclk |

---

## Quick Decision Tree

```
FPGA doesn't work?
    │
    ├─ No LEDs, no JTAG? → Power sequencing / rail short
    ├─ JTAG works, won't configure? → Configuration / MSEL / DONE pull-up
    ├─ Configures, behaves randomly? → Metastability / CDC / timing violation
    ├─ Configures, crashes under load? → Power integrity / IR drop
    └─ Works for seconds, then fails? → Thermal shutdown
```
