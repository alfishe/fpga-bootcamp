[← 12 Open Source Open Hardware Home](../README.md) · [← Litex Home](README.md) · [← Project Home](../../../README.md)

# LiteX — Python-Based SoC Generation

LiteX is an open-source framework that generates complete FPGA SoCs from Python scripts. Instead of dragging blocks in Vivado IP Integrator or Platform Designer, you write a Python class that instantiates CPUs, buses, peripherals, and memory controllers — then LiteX generates the Verilog, compiles the BIOS, and produces a bitstream.

---

## Why LiteX Matters

| Traditional SoC Design | LiteX |
|---|---|
| GUI drag-and-drop (not reproducible) | Python script (version-controlled, diffable) |
| Vendor-locked IP (AXI = Xilinx, Avalon = Intel) | Wishbone bus (cross-vendor) |
| Manual address map assignment | Auto-calculated memory map |
| Write C headers by hand | Auto-generate `csr.h`, `sdram_phy.h`, `mem.h` |
| Days to port between FPGAs | Change one line: `platform = "arty"` → `platform = "de10nano"` |

---

## Architecture: Migen FHDL

LiteX is built on **Migen** (Milkymist Generator), a Python-based HDL that generates Verilog through Python metaprogramming:

```python
# Migen: a counter in Python that becomes Verilog
from migen import *

class Blinky(Module):
    def __init__(self, width=26):
        self.counter = Signal(width)
        self.led = Signal()
        self.sync += self.counter.eq(self.counter + 1)
        self.comb += self.led.eq(self.counter[width-1])
```

This generates synthesizable Verilog with proper clock domain handling.

---

## Supported Boards

| Board | FPGA | RAM | Ethernet | Open Toolchain? | LiteX Support |
|---|---|---|---|---|---|
| **ULX3S** | ECP5-85F | 32 MB SDRAM | Yes (RGMII) | ✅ Yosys+nextpnr | Excellent |
| **Arty A7** | Artix-7 35T | 256 MB DDR3 | Yes | ❌ Needs Vivado | Excellent |
| **DE10-Nano** | Cyclone V SoC | HPS DDR3 | Yes (HPS) | ❌ Needs Quartus | Good |
| **KC705** | Kintex-7 | 1 GB DDR3 | Yes | ❌ Needs Vivado | Good |
| **Terasic DE2-115** | Cyclone IV | 128 MB SDRAM | Yes | ❌ Needs Quartus | Good |
| **ButterStick** | ECP5-85F | None | Yes (RGMII) | ✅ Yosys+nextpnr | Good |
| **OrangeCrab** | ECP5-25F | 128 MB DDR3 | No | ✅ Yosys+nextpnr | Experimental |

---

## CPU Options

| CPU | ISA | Features | Linux? | Notes |
|---|---|---|---|---|
| **VexRiscv** | RV32IMAC | Configurable pipeline, MMU option | ✅ (with MMU) | Default. SpinalHDL-based, highly configurable. |
| **PicoRV32** | RV32IMC | Minimal, ~750 LUTs | ❌ | Best for tiny control CPUs |
| **Rocket** | RV64IMAFDC | 64-bit, FPU, MMU | ✅ | Berkeley's in-order core. Larger. |
| **Microwatt** | ppc64le | POWER ISA, MMU | ✅ | IBM's open-source POWER core |
| **SERV** | RV32I | Bit-serial, ~125 LUTs | ❌ | World's smallest RISC-V. For fun/education. |
| **BlackParrot** | RV64IMAFDC | Superscalar, multicore | ✅ | University of Washington. High-perf. |

---

## BIOS and Boot Flow

LiteX includes a built-in BIOS that:
1. Initializes LiteDRAM (runs calibration)
2. Prints board info to UART
3. Loads user payload from SD card, Ethernet (TFTP), or serial (XMODEM)
4. Jumps to payload (e.g., Linux kernel, bare-metal app)

---

## Best Practices

1. **Use `venv` for LiteX** — Python dependency isolation prevents breakage
2. **Start from board target** — `litex-boards` repo has pre-configured targets for 50+ boards
3. **Version-pin your LiteX commit** — main branch moves fast and can break
4. **LiteDRAM calibration is the first thing to verify** — if memtest fails, nothing else works

---

## References

- [LiteX GitHub](https://github.com/enjoy-digital/litex)
- [LiteX Wiki](https://github.com/enjoy-digital/litex/wiki)
- [LiteX Boards Repository](https://github.com/litex-hub/litex-boards)
- [Migen / Amaranth HDL](https://github.com/amaranth-lang/amaranth)
