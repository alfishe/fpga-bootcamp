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

## RISC-V Soft Core Debugging

OpenOCD supports RISC-V debug via the RISC-V Debug Specification (version 0.13 / 1.0):

```tcl
# openocd_riscv.cfg — VexRiscv / NEORV32 debug
adapter driver ftdi
ftdi_vid_pid 0x0403 0x6010
adapter speed 5000
transport select jtag

# RISC-V TAP (IR length varies by core)
jtag newtap riscv cpu -irlen 5 -expected-id 0x10001fff

# Create RISC-V target
set _TARGETNAME riscv.cpu
target create $_TARGETNAME riscv -chain-position riscv.cpu
```

```bash
# Debug session
openocd -f openocd_riscv.cfg

# In another terminal:
riscv-none-elf-gdb firmware.elf
(gdb) target remote :3333
(gdb) load
(gdb) break main
(gdb) continue
```

| RISC-V Core | Debug Module | GDB Features | Notes |
|---|---|---|---|
| **VexRiscv** | Custom JTAG debug module | Breakpoints, watchpoints, single-step | Requires OpenOCD riscv fork or mainline 0.12+ |
| **NEORV32** | External debug module (JTAG) | Breakpoints, single-step | Well-documented debug interface |
| **PicoRV32** | No hardware debug | Print statements only | Use $display / UART for debug |
| **PolarFire SoC (U54)** | SiFive debug module | Full GDB via OpenOCD | Supported in mainline OpenOCD |

---

## Flash Programming Workflows

### Xilinx 7-Series (S25FL128 SPI Flash)
```bash
# Program SPI flash via JTAG (indirect: FPGA acts as SPI bridge)
openocd -f board/zybo.cfg -c "
  init;
  reset halt;
  flash probe 0;
  flash erase_sector 0 0 last;
  flash write_image erase top.bit 0x000000;
  flash verify_image top.bit 0x000000;
  reset run;
  exit"
```

### Intel Cyclone V (EPCS/EPCQ Flash)
```bash
# Convert .sof to .jic (Intel flash format), then program
# Note: OpenOCD supports SVF playback for Intel FPGA programming
openocd -f board/de10_nano.cfg -c "
  init;
  svf top.svf progress;
  exit"
```

### Lattice iCE40 (SPI Flash via FPGA bridge)
```bash
# iCE40 uses direct SPI programming
openocd -f board/icestick.cfg -c "
  init;
  flash write_image erase top.bin 0x000000;
  exit"
```

---

## Multi-FPGA JTAG Chains

When multiple FPGAs are on the same JTAG chain, configure each TAP:

```tcl
# Multi-FPGA JTAG chain: Xilinx FPGA → Intel FPGA → RISC-V core
adapter driver ftdi
ftdi_vid_pid 0x0403 0x6014
adapter speed 10000
transport select jtag

# TAP order: TDI → Xilinx → Intel → RISC-V → TDO
jtag newtap xilinx tap -irlen 6  -expected-id 0x0362C093
jtag newtap intel   tap -irlen 10 -expected-id 0x02D020DD
jtag newtap riscv   cpu -irlen 5  -expected-id 0x10001FFF

# Create targets
target create xilinx.cpu cortex_a -chain-position xilinx.tap
target create riscv.cpu  riscv     -chain-position riscv.cpu
```

**Common multi-FPGA pitfall:** If you only want to debug one FPGA, you must still account for all TAPs in the chain. OpenOCD needs to know the total IR length to shift instructions correctly.

---

## OpenOCD vs Vendor Tools Decision Matrix

| Task | OpenOCD | Vendor Tool (Vivado HW Manager / Quartus Programmer) |
|---|---|---|
| **Bitstream load (JTAG)** | Supported (SVF playback) | Native, faster, more reliable |
| **SPI flash programming** | Supported (indirect) | Native with verification |
| **ARM Cortex-A/R/M debug** | Full GDB server | DS-5 / SVD-based debug |
| **RISC-V debug** | Full GDB server | Not supported by vendor tools |
| **ILA / SignalTap** | Not supported | Required for internal signal debug |
| **Boundary scan** | Supported | Supported |
| **Temperature/voltage monitor** | Limited | Full (XADC / SYSMON) |
| **Scriptability** | Excellent (Tcl + config files) | Good (Tcl) but vendor-locked |
| **Cost** | Free | Free (with device license) |

**Rule of thumb:** Use OpenOCD for ARM/RISC-V CPU debugging and CI/CD scripting. Use vendor tools for FPGA-internal signal debug (ILA/SignalTap) and flash programming reliability.

---

## Best Practices

1. **Use a dedicated JTAG adapter** — FTDI FT2232H/FT4232H is the gold standard. Avoid the cheap Altera USB Blaster clones (unreliable at speeds >6 MHz).
2. **Set adapter speed cautiously** — start at 500 kHz, increase to 25 MHz only after confirming stable connection.
3. **Power the board before connecting JTAG** — some adapters back-power the JTAG TAP, causing partial initialization that prevents detection.
4. **Keep a known-good SVF file** — export SVF from vendor tools as a fallback if OpenOCD bitstream loading fails.
5. **For RISC-V debug, use mainline OpenOCD 0.12+** — older versions require the riscv fork which is no longer maintained.
6. **In multi-FPGA chains, always specify all TAPs** — even if you only debug one device, OpenOCD needs the full chain description.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **"JTAG scan chain interrogation failed"** | All ones (0xFFFFFFFF) | Check power to FPGA; verify adapter wiring (TDI→TDI, TDO→TDO, not crossed) |
| **IDCODE mismatch** | Wrong device detected | JTAG chain length is wrong (forgot to account for all TAPs); check `-irlen` |
| **GDB can't halt CPU** | "Target not examined yet" | Missing `-dbgbase` address in `target create`; check TRM for debug base |
| **SVF playback fails at ~50%** | SVF error mid-bitstream | Flash timing in SVF too aggressive; regenerate SVF with slower TCK |
| **RISC-V: "target not examined"** | GDB connection but no register access | Add `-irtagvalue` to `jtag newtap`; check core's IR encoding |

---

## Cross-References

| Topic | Article |
|---|---|
| JTAG adapter hardware | [Commercial JTAG Tools](commercial_jtag_tools.md) |
| Board bring-up with JTAG | [Bring-Up Checklist](../../15_case_studies/bring_up_checklist.md) |
| Hard CPU debug (HPS) | [Hard Processor Integration](../../02_architecture/soc/hard_processor_integration.md) |
| FPGA configuration methods | [Configuration & Bitstream](../../02_architecture/infrastructure/configuration.md) |

---

## References

| Source | Path |
|---|---|
| OpenOCD Documentation | https://openocd.org/ |
| RISC-V Debug Specification 0.13 | https://github.com/riscv/riscv-debug-spec |
| FTDI MPSSE Application Note | FTDI Ltd |
| IEEE 1149.1 (JTAG) Standard | IEEE |
| ARM CoreSight Architecture TRM | ARM |
