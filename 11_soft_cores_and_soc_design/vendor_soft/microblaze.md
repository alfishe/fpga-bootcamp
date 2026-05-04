[← 11 Soft Cores And Soc Design Home](../README.md) · [← Vendor Soft Home](README.md) · [← Project Home](../../../README.md)

# MicroBlaze & MicroBlaze V — Xilinx Soft Processors

MicroBlaze is Xilinx's soft processor — first shipped in 2001 and now in its second generation. The classic MicroBlaze uses a proprietary ISA, while the new **MicroBlaze V** (Vivado 2024.1+) uses the RISC-V ISA. Both are free to use on Xilinx/AMD FPGAs and deeply integrated with Vivado/Vitis.

---

## Classic MicroBlaze vs MicroBlaze V

| Aspect | MicroBlaze (Classic) | MicroBlaze V (2024+) |
|---|---|---|
| **ISA** | Proprietary (Xilinx custom) | RV32IM (RISC-V) |
| **Pipeline** | 3-stage or 5-stage | 5-stage |
| **LUTs (minimal)** | ~900 | ~1,200 |
| **LUTs (Linux)** | ~3,000 | ~3,500 |
| **fmax (7-series)** | 200+ MHz | 200+ MHz |
| **fmax (UltraScale+)** | 300+ MHz | 300+ MHz |
| **MMU** | Optional (for Linux) | Planned |
| **FPU** | Optional (single/double) | Optional (F extension) |
| **Debug** | MDM via JTAG | RISC-V Debug (JTAG) |
| **Toolchain** | Xilinx GCC (mb-gcc) | Standard RISC-V GCC |
| **Vivado integration** | Block design IP | Block design IP |
| **Software ecosystem** | Xilinx SDK/Vitis | Open-source RISC-V + Vitis |
| **License** | Free on Xilinx FPGAs | Free on AMD FPGAs |

**Key insight:** MicroBlaze V is AMD's transition path from proprietary ISA to RISC-V. Your C code works on both; your assembly doesn't.

---

## Classic MicroBlaze Architecture

| Parameter | Options |
|---|---|
| **ISA** | 32-bit RISC (custom, not RISC-V) |
| **Pipeline** | 3-stage (area-optimized) or 5-stage (performance) |
| **LUTs** | ~900 (microcontroller) to ~3,000 (Linux-capable MMU) |
| **fmax** | 200+ MHz on 7-series, 300+ MHz on UltraScale+ |
| **MMU** | Optional (for Linux) |
| **FPU** | Optional (single or double precision) |
| **Debug** | MDM (MicroBlaze Debug Module) via JTAG |

### Variants

| Variant | Pipeline | LUTs | Features |
|---|---|---|---|
| **Microcontroller** | 3-stage | ~900 | Minimal, no cache, bare-metal |
| **Real-time** | 5-stage | ~2,000 | I/D cache, FPU optional |
| **Linux** | 5-stage + MMU | ~3,000 | Virtual memory, runs Linux |

### Classic MicroBlaze Register Set

| Register | Purpose |
|---|---|
| R0 | Always zero (like RISC-V x0) |
| R1 | Stack pointer (convention) |
| R2–R13 | General purpose (callee-saved: R19–R31) |
| R14 | Return address (from `rtsd`) |
| R15 | Bit-aligned offset return |
| R16–R31 | General purpose |
| PC | Program counter |
| MSR | Machine Status Register |
| EAR | Exception Address Register |
| ESR | Exception Status Register |

### Classic MicroBlaze Interrupt Handling

```
Interrupt → Save MSR, PC → Jump to handler at 0x10 (hardware vector)
                                  or at interrupt vector address (if configured)

Handler:
    1. Save registers (sw r2, r19-r31 to stack)
    2. Read MSR to determine interrupt source
    3. Service interrupt (clear source, process data)
    4. Restore registers
    5. RTID r14, 0  (return from interrupt, enable interrupts)
```

---

## MicroBlaze V (RISC-V) Architecture

MicroBlaze V implements the RV32IM ISA profile:

- **RV32I**: Base integer instructions (40 instructions)
- **M extension**: Multiply/divide (maps to DSP48 slices)
- **C extension**: Compressed instructions (optional, saves ~30% code size)
- **Zicsr**: CSR access instructions
- **Machine mode only** (no S-mode/MMU yet — bare-metal or RTOS)

### MicroBlaze V Configuration in Vivado

```tcl
# Create MicroBlaze V in Vivado block design
create_ip -name microblaze_v -vendor xilinx.com -library ip \
    -module_name mbv_0

# Configure: enable M extension, C extension, 32KB I/D cache
set_property -dict [list \
    CONFIG.C_USE_M_EXT {1}  \
    CONFIG.C_USE_C_EXT {1}  \
    CONFIG.C_ICACHE_SIZE {32768} \
    CONFIG.C_DCACHE_SIZE {32768} \
] [get_ips mbv_0]
```

---

## AXI Integration

Both MicroBlaze variants use AXI4 natively:
- **AXI4** for DDR memory (cache line fills, DMA)
- **AXI4-Stream** for FIFO-attached accelerators
- **AXI4-Lite** for GPIO, UART, I2C, SPI

```
┌────────────────┐
│  MicroBlaze/V  │
│                │
│  M_AXI_DP ─────┼──► AXI4-Lite ──► GPIO, UART, SPI
│  (data peripheral)                    │
│                │                       │
│  M_AXI_DC ─────┼──► AXI4 ────────► DDR Ctrl (cached)
│  (data cached)                        │
│                │                       │
│  M_AXI_IC ─────┼──► AXI4 ────────► DDR Ctrl (cached)
│  (instr cached)                       │
│                │                       │
│  M_AXI_IP ─────┼──► AXI4-Lite ──► Control registers
│  (instr peripheral)                   │
└────────────────┘
```

This tight AXI coupling is why MicroBlaze + Vivado IP Integrator is the fastest path to a working SoC on Xilinx.

### Vivado Block Design: Minimal MicroBlaze SoC

```tcl
# Create block design
create_block_design design_1

# Add MicroBlaze
startgroup
create_cell -type ip -vlnv xilinx.com:ip:microblaze:11.0 microblaze_0
endgroup

# Add MIG (DDR controller)
create_cell -type ip -vlnv xilinx.com:ip:mig_7series:4.2 mig_0

# Add AXI Interconnect
create_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_interconnect_0

# Add peripherals
create_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:2.0 axi_uartlite_0
create_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_0

# Connect everything via IP Integrator automation
apply_board_connection
```

---

## Toolchain and Software

### Classic MicroBlaze

| Tool | Purpose |
|---|---|
| `mb-gcc` | C compiler (Xilinx-modified GCC) |
| `mb-objdump` | Disassembler |
| `mb-size` | Binary size analysis |
| Xilinx SDK / Vitis | IDE with debug, BSP generation |
| `xsct` | Xilinx Software Command Tool (Tcl-based) |
| `xmd` | MicroBlaze Debug via JTAG (legacy) |

### MicroBlaze V

| Tool | Purpose |
|---|---|
| `riscv32-unknown-elf-gcc` | Standard RISC-V GCC toolchain |
| `riscv32-unknown-elf-objdump` | Disassembler |
| Vitis | IDE with RISC-V debug support |
| OpenOCD | Open-source JTAG debug (RISC-V debug spec) |

### Build Flow

```bash
# Classic MicroBlaze: build standalone application
mb-gcc -O2 -mcpu=v11.0 -mlittle-endian \
    -I${XILINX_VITIS}/include \
    -L${XILINX_VITIS}/lib \
    -T lscript.ld \
    main.c -o main.elf

# Generate .bin for flash / .mcs for PROM
mb-objcopy -O binary main.elf main.bin
bootutil -image main.bin -data_width 32 \
    -offset 0 -flash_type s25fl128s \
    -o main.mcs

# MicroBlaze V: use standard RISC-V toolchain
riscv32-unknown-elf-gcc -O2 -march=rv32im -mabi=ilp32 \
    main.c -o main.elf
```

---

## MicroBlaze vs RISC-V on Xilinx

| Aspect | MicroBlaze (Classic) | RISC-V (VexRiscv/etc.) | MicroBlaze V |
|---|---|---|---|
| **Vivado integration** | Native IP, drag-and-drop | Manual RTL integration | Native IP |
| **Performance** | 200–300 MHz | 100–200 MHz | 200–300 MHz |
| **Vendor lock-in** | Xilinx only | Any FPGA family | AMD only |
| **Software ecosystem** | Xilinx SDK/Vitis | Full open-source RISC-V | Open RISC-V + Vitis |
| **Linux support** | Yes (with MMU) | Yes (VexRiscv Linux) | Planned |
| **Assembly portable** | No (proprietary) | Yes (RISC-V standard) | Yes (RISC-V standard) |
| **Future-proof** | Maintenance mode | Growing ecosystem | AMD's future direction |

**When to use Classic MicroBlaze:** Existing projects with proprietary codebase, need Linux today.

**When to use MicroBlaze V:** New Xilinx designs — RISC-V ISA, same Vivado integration, forward-compatible.

**When to use open RISC-V (VexRiscv):** Multi-vendor designs, need S-mode/MMU features not yet in MicroBlaze V, or targeting non-Xilinx FPGAs.

---

## Debug with Vitis

```bash
# Launch Vitis debugger
vitis -debug -hw_target localhost:3121

# Or via xsct command line:
xsct> connect
xsct> targets
  1  MicroBlaze  #0
xsct> target 1
xsct> stop
xsct> reg pc          # Read program counter
xsct> mrd 0x40000000  # Read memory (UART register)
xsct> dow main.elf    # Download ELF
xsct> con             # Continue execution
```

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [UG1711 — MicroBlaze V Processor Reference](https://docs.amd.com/r/en-US/ug1711-microblaze-v-embedded-design) | AMD/Xilinx | MicroBlaze V configuration, RISC-V ISA, Vivado integration |
| [UG984 — MicroBlaze Reference Guide](https://docs.amd.com/r/en-US/ug984-vivado-microblaze) | AMD/Xilinx | Classic MicroBlaze architecture, register set, instruction set |
| [Hard Processor Integration](../../02_architecture/soc/hard_processor_integration.md) | This KB | Hard vs soft CPU trade-offs |
| [RISC-V ISA](../riscv/riscv_isa.md) | This KB | RV32I/M/A/F/D/C/B/V extensions |
| [AXI4 Family](../../06_ip_and_cores/bus_protocols/axi4_family.md) | This KB | AXI4/Lite/Stream protocol reference |
