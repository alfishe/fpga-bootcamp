[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# JTAG Boundary Scan — Board-Level Interconnect Test

Boundary scan (IEEE 1149.1) is the industry-standard method for testing PCB interconnects without physical probes. Every FPGA supports it, and it's your first line of defense when a new board doesn't work — before you even load a bitstream.

---

## How Boundary Scan Works

Each I/O pin on the FPGA has a boundary-scan cell (BSC) between the pad and the core logic:

```
Normal mode:  Core Logic ←→ BSC (transparent) ←→ Pad → PCB trace

EXTEST mode:  Core Logic    BSC (controlled by JTAG) ←→ Pad → PCB trace
              (disconnected)      ↑
                            JTAG shifts in/out pin values
```

In EXTEST, the JTAG controller drives every FPGA pin — it can wiggle any pin high/low and read back what the connected device sees. This tests solder joints, PCB traces, and inter-device connections without a single line of HDL.

---

## Key JTAG Instructions

| Instruction | What It Does | Used For |
|---|---|---|
| **BYPASS** | Routes TDI→TDO through 1-bit bypass register | Skipping devices in chain |
| **IDCODE** | Reads 32-bit device ID | Verifying correct FPGA is on board |
| **SAMPLE/PRELOAD** | Captures pin states into BSCs (SAMPLE) or preloads BSCs (PRELOAD) | Snapshot of live system; setup before EXTEST |
| **EXTEST** | Drives BSC values to pins, captures from pins | Interconnect test — the main event |
| **INTEST** | Drives BSC values to core logic | Static test of internal logic (rarely used) |
| **USERCODE** | Reads 32-bit user-defined code | PCB revision tracking |
| **HIGHZ** | Tri-states all FPGA I/O pins | Safe board power-up, isolating FPGA |

---

## BSDL Files

BSDL (Boundary Scan Description Language) files are VHDL-format files that describe:
- Pin names, numbers, and types (input/output/bidirectional/power)
- Boundary-scan cell order and function (which BSC maps to which pin)
- Instruction register length and opcodes
- IDCODE value

**Where to find BSDL files:**
- Intel: Quartus installation → `quartus/libraries/misc/bsdl/`
- Xilinx: Vivado installation → `data/parts/bsdl/`
- Or: vendor website → device page → BSDL models

**BSDL example (excerpt):**
```vhdl
attribute INSTRUCTION_LENGTH of EP2C5 : entity is 10;
attribute IDCODE_REGISTER of EP2C5 : entity is "0010" & x"020D0DD";

"IO1(0)" : INOUT cell "1" ;  -- BSC cell 1 maps to pin IO1, bidirectional
```

---

## Common Test Patterns

### 1. Interconnect Test (EXTEST Walk-1)

Drive a "walking 1" through all FPGA outputs and verify the connected device reads the correct pin:

```
Step 1: Load PRELOAD with 0x0001 (pin 0 high, all others low)
Step 2: Issue EXTEST — FPGA drives pin 0 high
Step 3: Capture result via JTAG on receiving device
Step 4: Repeat for pin 1, 2, 3...
```

### 2. Short Circuit Detection

Drive one pin high, all others low. If any other pin reads high, there's a short.

### 3. Pull-Up / Pull-Down Verification

Set all pins to input (via BSC control cell). Measure each pin's state — if a pin reads '0' when it should have a pull-up, the resistor is missing.

---

## FPGA-Specific Notes

### Intel (Cyclone V, MAX 10)
- IR length: 10 bits
- IEEE 1149.1 compliant; also supports IEEE 1532 (in-system configuration)
- BSDL files include `CONFIG` and `HIGHZ` instruction opcodes
- After configuration, boundary scan still works — BSCs remain accessible

### Xilinx (7-Series, UltraScale+)
- IR length: 6 bits (7-series), 18 bits (UltraScale+)
- Pre-configuration: boundary scan works normally
- Post-configuration: BSCs are controlled by the configured design unless `BSCAN` primitive is instantiated
- Use `BSCANE2` primitive to access boundary scan from FPGA fabric

---

## Best Practices

1. **Run boundary scan as the first board bring-up step** — before loading any bitstream. Verifies power, JTAG chain, soldering.
2. **Keep BSDL files with your board design** — version-control them alongside schematics.
3. **Use a dedicated boundary scan tool for production** — XJTAG, Corelis, or JTAG Technologies for automated production test.
4. **Verify IDCODE first** — if JTAG chain IDCODE read fails, nothing else will work.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Wrong BSDL file** | BSC-to-pin mapping incorrect; test drives wrong pin | Verify BSDL matches exact FPGA package (e.g., F256 vs F484) |
| **Power rail not up during test** | All pins read as 'Z' or 'X' | Ensure VCCIO for the bank under test is powered |
| **Shared JTAG chain with other devices** | Boundary scan affects non-FPGA devices | Use BYPASS for non-target devices in chain |
| **Configured I/O standard mismatch** | EXTEST drives wrong voltage | FPGA I/O standards are configured by bitstream; pre-config EXTEST uses default LVCMOS |

---

## References

| Source | Path |
|---|---|
| IEEE 1149.1-2013 Standard for Test Access Port | IEEE |
| Intel BSDL Support Page | Intel FPGA Documentation |
| Xilinx BSDL and SVF File Generation (XAPP067) | Xilinx / AMD |
| OpenOCD Boundary Scan Guide | https://openocd.org/ |
| XJTAG Boundary Scan Tutorial | https://www.xjtag.com/ |
