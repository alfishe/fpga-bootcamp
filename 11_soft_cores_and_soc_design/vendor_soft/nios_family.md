[← 11 Soft Cores And Soc Design Home](../README.md) · [← Vendor Soft Home](README.md) · [← Project Home](../../../README.md)

# Nios II & Nios V — Intel's Soft Processor Family

Intel's Nios II is the legacy 32-bit RISC soft core for Intel FPGAs (2004–present), while Nios V is its RISC-V-based successor (2021+). Both are free with Quartus and integrate natively with Platform Designer.

---

## Nios II Variants

| Variant | Pipeline | LUTs | fmax | DMIPS/MHz | Use |
|---|---|---|---|---|---|
| **Nios II/e** (Economy) | 1-stage (state machine) | ~600–700 | 200 MHz | ~0.15 | Smallest, slowest, debug console |
| **Nios II/s** (Standard) | 5-stage, static branch prediction | ~1,200–1,400 | 180 MHz | ~0.74 | Balanced, most common |
| **Nios II/f** (Fast) | 6-stage, dynamic branch prediction | ~1,400–1,800 | 200+ MHz | ~1.17 | Highest performance |

### Nios II Architecture

| Feature | Detail |
|---|---|
| **ISA** | 32-bit RISC (proprietary, not RISC-V) |
| **Registers** | 32 general-purpose (r0=zero, r1=at, r27=sp), plus et, bt, status |
| **Addressing** | Up to 4 GB (32-bit), big-endian or little-endian |
| **Exceptions** | 32 hardware interrupts + 32 exception types |
| **Custom instructions** | User-defined combinational or multi-cycle instructions |
| **JTAG debug** | JTAG Debug Module (JDM) — breakpoints, trace, trigger |
| **MMU** | No (uses MPU for memory protection) |
| **FPU** | Optional (single-precision, floating-point custom instruction) |

### Nios II Register Set

| Register | Name | Purpose |
|---|---|---|
| r0 | zero | Always 0 |
| r1 | at | Assembler temporary |
| r2–r3 | return value | Function return values |
| r4–r7 | argument | Function arguments |
| r8–r15 | caller-saved | Temporary registers |
| r16–r23 | callee-saved | Saved across function calls |
| r24 | et | Exception temporary |
| r25 | bt | Break temporary |
| r26 | gp | Global pointer |
| r27 | sp | Stack pointer |
| r28 | fp | Frame pointer |
| r29 | ea | Exception return address |
| r30 | ba | Break return address |
| r31 | ra | Return address |

### Nios II Custom Instructions

One of Nios II's unique features is hardware custom instructions — RTL modules that the CPU invokes as single instructions:

```tcl
# Add a custom instruction in Qsys:
# 1. Create a component with:
#    - dataa[31:0], datab[31:0] inputs
#    - result[31:0] output
#    - clk, reset, clk_en
#    - start, done signals (multi-cycle)

# 2. In Nios II settings, add the custom instruction
# 3. Use in C code:
#   int result = ALT_CI_MY_CUSTOM_INST(dataa, datab);
```

```c
// Example: CRC32 custom instruction (combinational)
// In C:
uint32_t crc = ALT_CI_CRC32_0(data, 0xFFFFFFFF);

// The Nios II GCC generates a single instruction:
//   custom 0, rResult, rDataA, rDataB
```

---

## Nios V — RISC-V Transition

| Variant | ISA | LUTs | fmax | Key Trait |
|---|---|---|---|---|
| **Nios V/m** (Microcontroller) | RV32IMC | ~1,200 | 150+ MHz | RISC-V, bare-metal |
| **Nios V/g** (General) | RV32IMAFDC | ~5,000 | 150+ MHz | Linux-capable, MMU, FPU |

### Nios V/m — Bare-Metal RISC-V

- RV32IMC ISA (base integer + multiply + compressed)
- Machine mode only (no S-mode / MMU)
- Integrates natively with Platform Designer via Avalon-MM
- Debug via Ashling RiscFree IDE or OpenOCD
- Best for: new Intel FPGA designs that don't need Linux

### Nios V/g — Linux-Capable RISC-V

- RV32IMAFDC ISA (full feature set including FPU)
- M + S + U privilege modes with Sv32 MMU
- Runs Linux (Yocto/OpenSBI)
- Larger LUT budget but full OS support
- Best for: Intel FPGA designs that need Linux

### Nios V Configuration in Platform Designer

```tcl
# Add Nios V/m to Platform Designer
add_instance niosv_m_0 intel_niosv_m

# Configure
set_instance_parameter_value niosv_m_0 {ARCH} {RV32IMC}
set_instance_parameter_value niosv_m_0 {ICACHE_SIZE} {32768}
set_instance_parameter_value niosv_m_0 {DCACHE_SIZE} {32768}

# Connect to Avalon peripherals
add_instance jtag_uart_0 altera_avalon_jtag_uart
add_instance sysid_qsys_0 altera_avalon_sysid
add_instance onchip_ram_0 altera_avalon_onchip_memory2
```

---

## Avalon-MM Integration

Both Nios II and Nios V use Intel's **Avalon Memory-Mapped** interface:

```
┌─────────────────┐
│   Nios II/V     │
│                 │
│  Avalon-MST ────┼──► Platform Designer ──┬──► DDR Ctrl (Avalon)
│  (data master)  │    Interconnect         ├──► On-chip RAM
│                 │                         ├──► JTAG UART
│  Avalon-MST ────┼──► (instruction)       ├──► SPI Master
│  (instr master) │                         └──► GPIO
│                 │
│  IRQ receiver ──┼──◄── Interrupts from peripherals
└─────────────────┘
```

### Avalon-MM vs AXI4

| Feature | Avalon-MM | AXI4 |
|---|---|---|
| **Channels** | Single (unified) | 5 separate channels |
| **Burst support** | Yes (Burst Count) | Yes (ARLEN/AWLEN) |
| **Waitrequest** | Slave holds ready low | Similar to AXI ready |
| **Pipeline** | Optional (latency=1) | Optional (register slices) |
| **Intel FPGA** | Native | Via AXI-Avalon adapter |
| **Xilinx FPGA** | Not available | Native |

---

## Toolchain and Software

### Nios II Software Build Tools (SBT)

```bash
# Build a Nios II project
nios2-bsp hal bsp.h --cpu-name nios2_qsys_0 \
    --script soc_system.sopcinfo

nios2-app-generate-makefile --app-name my_app \
    --src-dir src/ --bsp-dir bsp/

make
```

### Nios V — Standard RISC-V Toolchain

```bash
# Build with RISC-V GCC
riscv32-unknown-elf-gcc -O2 -march=rv32imc -mabi=ilp32 \
    -I${INTELFPGA}/niosv/software/include \
    main.c -o main.elf

# Program via Quartus programmer
quartus-program --niosv --sof my_design.sof --elf main.elf
```

### Debug with SignalTap + JTAG

```bash
# Nios II: debug via Nios II SBT
nios2-gdb main.elf
(gdb) target remote jtag_uart
(gdb) break main
(gdb) continue

# Nios V: debug via OpenOCD + GDB
openocd -f niosv.cfg
riscv32-unknown-elf-gdb main.elf
(gdb) target remote :3333
(gdb) break main
(gdb) continue
```

---

## Intel vs Open RISC-V

| Aspect | Nios II | Nios V | Open RISC-V (VexRiscv) |
|---|---|---|---|
| **Quartus integration** | Native Qsys/Platform Designer | Native | Manual RTL integration |
| **Avalon-MM** | Native | Native | Needs bridge IP |
| **AXI4** | Via adapter | Via adapter | Native |
| **License** | Free (Quartus) | Free (Quartus) | Free (open source) |
| **Cross-vendor** | Intel only | Intel only | Any FPGA family |
| **Debug** | SignalTap + Nios SBT | SignalTap + Ashling | OpenOCD + GDB |
| **Linux** | No (no MMU) | Yes (V/g) | Yes (VexRiscv Linux) |
| **Custom instructions** | Yes (unique feature) | No (use RISC-V I-ext) | No (use RoCC) |
| **Assembly portable** | No (proprietary) | Yes (RISC-V) | Yes (RISC-V) |

### When to Use What

| Scenario | Choice |
|---|---|
| Fastest SoC integration on Intel | **Nios II/f** — drag-and-drop in Platform Designer |
| Future-proofing for Intel RISC-V | **Nios V/m** — same Intel tooling, RISC-V ISA |
| Cross-vendor portability | **Open RISC-V** (VexRiscv) — same core on Xilinx, Intel, Lattice |
| Need custom instructions | **Nios II** — unique custom instruction feature |
| Need Linux on Intel FPGA | **Nios V/g** — only Intel RISC-V with MMU |
| Existing Nios II codebase | **Stay on Nios II** — Nios V is new, toolchain maturing |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [Nios II Processor Reference](https://www.intel.com/content/www/us/en/docs/programmable/683640/current/) | Intel | Nios II architecture, custom instructions, BSP |
| [Nios V Processor Reference](https://www.intel.com/content/www/us/en/docs/programmable/683913/current/) | Intel | Nios V RISC-V configuration, Platform Designer |
| [Hard Processor Integration](../../02_architecture/soc/hard_processor_integration.md) | This KB | Hard vs soft CPU trade-offs |
| [RISC-V ISA](../riscv/riscv_isa.md) | This KB | RV32I/M/A/F/D/C/B/V extensions |
| [MicroBlaze](microblaze.md) | This KB | Xilinx soft processor comparison |
