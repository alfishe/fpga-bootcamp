[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# OpenOCD & JTAG — FPGA Debug Access

OpenOCD (Open On-Chip Debugger) is the Swiss Army knife of hardware debugging. For FPGA developers, it provides JTAG bitstream programming, flash writing, boundary scan testing, and ARM/RISC-V CPU debugging — all through a single tool that works across vendors.

---

## What OpenOCD Does for FPGA Workflows

| Task | How | Vendor Tools Equivalent |
|---|---|---|
| **Load bitstream via JTAG** | `program foo.bit` or SVF/XSVF playback | Vivado Hardware Manager, Quartus Programmer |
| **Program external SPI flash** | Flash driver + bitstream write | Vivado/Quartus flash programmer |
| **Debug ARM Cortex-A9 (HPS)** | GDB server via JTAG → DAP → Cortex-A9 | ARM DS-5 Debugger |
| **Debug RISC-V soft core** | GDB server via JTAG → RISC-V Debug Module | Vendor-specific |
| **Boundary scan test** | `xsvf` command with IEEE 1149.1 vectors | Vendor boundary scan tools |
| **Monitor FPGA temperature/voltage** | JTAG DR access to SYSMON/XADC | Vendor hardware monitor |

---

## Configuration Files

### DE10-Nano (Cyclone V SoC)

```tcl
# openocd_de10_nano.cfg
interface ftdi
ftdi_vid_pid 0x0403 0x6010
ftdi_channel 0
ftdi_layout_init 0x0008 0x000b
transport select jtag
adapter speed 25000

# Cyclone V SoC has two TAPs in the JTAG chain:
#  - TAP 0: FPGA fabric (sld_hub → SignalTap, etc.)
#  - TAP 1: HPS (Cortex-A9 DAP)

# Set IR length for each TAP
jtag newtap cv_soc tap -irlen 10 -expected-id 0x02D020DD
jtag newtap cv_hps tap -irlen 4  -expected-id 0x4BA00477

target create cv_soc.cpu cortex_a -chain-position cv_hps.tap -dbgbase 0x80110000
```

### Xilinx 7-Series (Zynq)

```tcl
# openocd_zybo.cfg
interface ftdi
ftdi_vid_pid 0x0403 0x6010
adapter speed 15000
transport select jtag

# Zynq-7000 JTAG chain: DAP (ARM) + PL TAP
jtag newtap zynq_pl  tap -irlen 6  -expected-id 0x03722093
jtag newtap zynq_dap tap -irlen 4  -expected-id 0x4BA00477

target create zynq.cpu0 cortex_a -chain-position zynq_dap.tap -dbgbase 0x80090000
target create zynq.cpu1 cortex_a -chain-position zynq_dap.tap -dbgbase 0x80092000
```

---

## Common Commands

### Bitstream Loading

```bash
# Load .sof/.bit file via JTAG (SVF playback)
openocd -f board/de10_nano.cfg -c "init; svf soc_system.svf; exit"

# Program SPI flash (indirect via FPGA bridge)
openocd -f board/de10_nano.cfg -c "init; flash write_image erase unlock bitstream.jic 0x00000000; exit"
```

### ARM HPS Debugging

```bash
# Start OpenOCD as GDB server
openocd -f board/de10_nano.cfg

# In another terminal:
arm-none-eabi-gdb vmlinux
(gdb) target remote :3333
(gdb) monitor reset halt
(gdb) load
(gdb) continue
```

### Boundary Scan

```bash
# Run boundary scan test vectors
openocd -f board/de10_nano.cfg -c "init; xsvf bscan_test.xsvf; exit"
```

---

## JTAG Chain Topology

Understanding the JTAG chain is critical for debugging "can't connect" problems:

```
TDI → [FPGA TAP (IR=10)] → [HPS DAP (IR=4)] → TDO
        ↑ 0x02D020DD             ↑ 0x4BA00477
```

If the chain has unexpected length or wrong IDCODE, check:
1. JTAG pull-up/pull-down resistors on TCK, TMS, TDI (4.7kΩ typical)
2. Power rail sequencing — JTAG TAPs need VCCIO/VCORE before they respond
3. Multi-FPGA chains — add TAPs in order of TDI→TDO

---

## Best Practices

1. **Use a dedicated JTAG adapter** — FTDI FT2232H/FT4232H is the gold standard. Avoid the cheap Altera USB Blaster clones (unreliable at speeds >6 MHz).
2. **Set adapter speed cautiously** — start at 500 kHz, increase to 25 MHz only after confirming stable connection.
3. **Power the board before connecting JTAG** — some adapters back-power the JTAG TAP, causing partial initialization that prevents detection.
4. **Keep a known-good SVF file** — export SVF from vendor tools as a fallback if OpenOCD bitstream loading fails.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **"JTAG scan chain interrogation failed"** | All ones (0xFFFFFFFF) | Check power to FPGA; verify adapter wiring (TDI→TDI, TDO→TDO, not crossed) |
| **IDCODE mismatch** | Wrong device detected | JTAG chain length is wrong (forgot to account for all TAPs); check `-irlen` |
| **GDB can't halt CPU** | "Target not examined yet" | Missing `-dbgbase` address in `target create`; check TRM for debug base |
| **SVF playback fails at ~50%** | SVF error mid-bitstream | Flash timing in SVF too aggressive; regenerate SVF with slower TCK |
