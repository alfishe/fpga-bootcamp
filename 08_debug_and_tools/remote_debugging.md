[← 08 Debug And Tools Home](README.md) · [← Project Home](../../README.md)

# Remote Debugging — Embedded Linux on SoC FPGAs

When your SoC FPGA runs Linux and something goes wrong in the FPGA fabric, you need to debug across the CPU-FPGA boundary. This covers kernel-space debugging (GDB via JTAG, kgdb), userspace access to FPGA peripherals (`/dev/mem`, UIO), and techniques for diagnosing bridge hangs and DMA stalls.

---

## The SoC Debugging Stack

```
┌─────────────────────────────────┐
│  Userspace App (your code)      │ ← gdb, strace, valgrind
├─────────────────────────────────┤
│  Kernel Driver (your driver)    │ ← kgdb, printk, ftrace
├─────────────────────────────────┤
│  HPS-FPGA Bridges (AXI)         │ ← /dev/mem peek, bridge status regs
├─────────────────────────────────┤
│  FPGA Fabric (your HDL)         │ ← ILA/SignalTap, external LA
└─────────────────────────────────┘
```

---

## GDB via JTAG — Kernel & Bare-Metal Debugging

### Setup (DE10-Nano / Cyclone V SoC)

```bash
# Terminal 1: Start OpenOCD as GDB server
openocd -f board/de10_nano.cfg
# Output: Listening on port 3333 for gdb connections

# Terminal 2: Connect GDB
arm-none-eabi-gdb vmlinux
(gdb) target remote localhost:3333
(gdb) monitor reset halt       # Halt both Cortex-A9 cores
(gdb) load                     # Load kernel image
(gdb) hbreak start_kernel      # Hardware breakpoint at kernel entry
(gdb) continue
```

### Useful GDB Commands for SoC Debug

| Command | What It Does |
|---|---|
| `info threads` | List both CPU cores (core 0 and core 1) |
| `thread 2` | Switch to core 1 context |
| `monitor reg` | Dump all ARM registers (via JTAG) |
| `x/16xw 0xFF200000` | Read 16 words from LWH2F bridge |
| `set {int}0xFF200000 = 0xDEAD` | Write to LWH2F register (poke FPGA) |
| `monitor arm semihosting enable` | Enable semihosting for printf-without-UART |

---

## kgdb — Kernel Debugging Without JTAG

kgdb lets you debug the running kernel over serial or Ethernet — no JTAG hardware needed:

```bash
# On target (DE10-Nano via UART):
echo ttyS0 > /sys/module/kgdboc/parameters/kgdboc
echo g > /proc/sysrq-trigger    # Enter kgdb — kernel freezes

# On host:
arm-none-eabi-gdb vmlinux
(gdb) target remote /dev/ttyUSB0
(gdb) hbreak fpga_bridge_probe
(gdb) continue
```

**kgdb limitations on SoC FPGAs:**
- Can't debug through FPGA reconfiguration (bridge resets kill kgdb transport)
- UART-based kgdb shares the same UART as console — kernel messages interfere
- Ethernet-based kgdb (`kgdboe`) survives bridge resets if EMAC is in HPS

---

## /dev/mem — Direct FPGA Register Access

`/dev/mem` maps physical addresses to userspace. Essential for quick FPGA register pokes:

```c
#include <fcntl.h>
#include <sys/mman.h>

int fd = open("/dev/mem", O_RDWR | O_SYNC);
volatile uint32_t *fpga_regs = mmap(
    NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED,
    fd, 0xFF200000  // LWH2F bridge base
);

// Read FPGA status register
uint32_t status = fpga_regs[0];

// Write control register
fpga_regs[1] = 0x00000001;

munmap(fpga_regs, 4096);
close(fd);
```

### devmem2 Quick Poke

```bash
# Read LWH2F register at offset 0x100
devmem2 0xFF200100 w
# Memory at 0xFF200100: 0x0000DEAD

# Write to LWH2F register
devmem2 0xFF200100 w 0xBEEF
```

---

## Diagnosing Bridge Hangs

### Symptom: CPU hangs when reading FPGA bridge

```bash
# Check if bridge is enabled (Cyclone V)
devmem2 0xFFD08050 w  # System Manager: FPGA bridge control
# Bit 0: H2F bridge enable
# Bit 1: LWH2F enable
# Bit 2: F2H enable

# If bridges are enabled but reads hang:
# 1. Check FPGA is configured (CONF_DONE)
# 2. Check FPGA AXI slave responds (no combinatorial loops, valid address decode)
# 3. Check clock to FPGA bridge domain is running
```

### Early Printk

For debugging before console is available:

```bash
# Kernel cmdline: earlyprintk
# Output appears on UART as soon as UART driver probes

# On Zynq:
earlyprintk=xuartps,0xE0001000

# On Cyclone V:
earlyprintk=uart8250,0xFFC02000
```

---

## FPGA Bridge Debug Checklist

When nothing works, verify in order:

1. **Power good?** — All rails present and sequenced (HPS VCC before FPGA VCCIO)
2. **Clocks running?** — HPS oscillator (25 MHz), bridge clock, FPGA clock
3. **FPGA configured?** — `CONF_DONE` high, no `CONF_ERROR`
4. **Bridges enabled?** — System Manager bridge control register bits set
5. **Address map correct?** — Device tree `ranges` matches Platform Designer/Vivado address map
6. **AXI protocol correct?** — No AXI-3 WID mismatch, write response sent, BVALID asserted

---

## Best Practices

1. **Always include a UART loopback path in FPGA** — a simple UART→FIFO→UART through FPGA fabric confirms bridges work.
2. **Use UIO for production drivers, /dev/mem for debug** — `/dev/mem` has no safety; UIO isolates crashes.
3. **Keep a known-good bitstream on SD card** — a minimal design that enables bridges and echoes a register; load it to isolate hardware vs HDL bugs.

---

## References

| Source | Path |
|---|---|
| OpenOCD User Guide | https://openocd.org/doc/html/ |
| Linux Kernel kgdb documentation | `Documentation/dev-tools/kgdb.rst` in kernel source |
| Cyclone V HPS TRM — System Manager | Intel FPGA Documentation |
| Zynq-7000 TRM — SLCR Registers | Xilinx UG585 |
