[← 11 Soft Cores And Soc Design Home](../README.md) · [← Other ISA Home](README.md) · [← Project Home](../../../README.md)

# Non-RISC-V Soft Cores — OpenRISC, SPARC, POWER, MIPS, MSP430, ZPU

While RISC-V dominates new soft core development, several mature non-RISC-V architectures remain relevant for FPGA — each with unique advantages and deep toolchain history. The LEON3/4 (SPARC V8) is the only ESA-qualified processor for space applications. The mor1kx (OpenRISC) offers the most mature Linux-capable non-RISC-V option. The Microwatt brings IBM's POWER ISA to the FPGA world. And the ZPU holds the record for the smallest FPGA CPU. This article provides deep technical coverage of each core: architecture, toolchain, FPGA resource requirements, Linux support, and when to choose each one.

> [!NOTE]
> For RISC-V cores, see [RISC-V Cores](../riscv_cores/README.md). For the full catalog including retro ISA soft cores, see [Non-RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md).

---

## Core Comparison

| Core | ISA | Bits | LUTs | fMAX | MMU | Linux | Language | License | Key Trait |
|------|-----|------|------|------|-----|-------|----------|---------|-----------|
| **mor1kx** | OpenRISC 1000 | 32 | 2,500–4,000 | 150+ MHz | Yes | ✅ 4.x | Verilog | LGPL | Mature GCC/binutils toolchain |
| **LEON3** | SPARC V8 | 32 | 15,000+ | 100+ MHz | Yes | ✅ (RTEMS, Linux) | VHDL | GPL + commercial | ESA-qualified, fault-tolerant |
| **LEON4** | SPARC V8 | 32 | 25,000+ | 150+ MHz | Yes | ✅ | VHDL | GPL + commercial | Multi-core, faster LEON3 |
| **Microwatt** | POWER (64-bit) | 64 | 20,000+ | 50+ MHz | Yes | ✅ ppc64le | VHDL | Apache 2.0 | IBM POWER ISA, mainline Linux |
| **Plasma** | MIPS I | 32 | 2,000–3,000 | 100+ MHz | No | ❌ (RTOS) | VHDL | MIT | Educational MIPS |
| **ZPU** | Custom stack | 32 | 500–1,000 | 100+ MHz | No | ❌ | VHDL | BSD | Smallest non-RV core |
| **NEO430** | MSP430 | 16 | 1,500–2,500 | 100+ MHz | No | ❌ | VHDL | BSD-3 | 16-bit, best docs after NEORV32 |

---

## OpenRISC — mor1kx

### Architecture

- **ISA:** OpenRISC 1000 (OR1K), 32-bit load/store, delayed branch slot
- **Pipeline:** 5-stage (mor1kx Cappuccino), 6-stage (mor1kx Pronteau), or 1-stage (mor1kx Espresso)
- **MMU:** Optional — Linux requires DMMU + IMMU
- **Cache:** Configurable I-cache and D-cache (direct-mapped or 2-way)
- **Interrupts:** 32 interrupt lines, programmable priority

### Variants

| Variant | Pipeline | Area | Performance | Use Case |
|---------|----------|------|-------------|----------|
| **Espresso** | 1-stage | ~1,500 LUTs | 0.5 DMIPS/MHz | Smallest, microcontroller |
| **Cappuccino** | 5-stage | ~3,500 LUTs | 1.0 DMIPS/MHz | General purpose, Linux |
| **Pronteau** | 6-stage (FPU) | ~5,000 LUTs | 1.2 DMIPS/MHz | FPU-intensive workloads |

### Toolchain

```bash
# Install OpenRISC toolchain
git clone https://github.com/openrisc/or1k-gcc
cd or1k-gcc
./configure --target=or1k-elf --enable-languages=c,c++
make && sudo make install

# Compile for OpenRISC
or1k-elf-gcc -mor1kx -O2 -o hello hello.c

# Linux: use openrisc/linux kernel
git clone https://github.com/openrisc/linux
make ARCH=openrisc CROSS_COMPILE=or1k-linux- defconfig
make ARCH=openrisc CROSS_COMPILE=or1k-linux- -j$(nproc)
```

### FPGA Integration

```verilog
// mor1kx instantiation (Cappuccino variant)
mor1kx #(
    .OPTION_OPERAND_WIDTH(32),
    .OPTION_RF_ADDR_WIDTH(5),
    .FEATURE_INSTRUCTIONCACHE("ENABLED"),
    .OPTION_ICACHE_BLOCK_WIDTH(4),
    .FEATURE_DATACACHE("ENABLED"),
    .OPTION_DCACHE_BLOCK_WIDTH(4),
    .FEATURE_MMU("ENABLED"),
    .FEATURE_SYSCALL("ENABLED")
) u_cpu (
    .clk(cpu_clk),
    .rst(rst),
    .irq_i(irq),
    // Wishbone instruction bus
    .iwbm_adr_o(iwb_adr),
    .iwbm_dat_i(iwb_dat_r),
    .iwbm_dat_o(iwb_dat_w),
    .iwbm_sel_o(iwb_sel),
    .iwbm_cyc_o(iwb_cyc),
    .iwbm_stb_o(iwb_stb),
    .iwbm_ack_i(iwb_ack),
    .iwbm_we_o(iwb_we),
    // Wishbone data bus
    .dwbm_adr_o(dwb_adr),
    // ...
);
```

---

## LEON3 / LEON4 — SPARC V8

### Architecture

- **ISA:** SPARC V8 (register windows: 8 global + 8×8-window register file)
- **Pipeline:** 7-stage (LEON3), 8-stage with FPU (LEON3FT)
- **Cache:** Configurable I/D cache (1–4 way, 1–256 KB)
- **Multi-core:** LEON4 supports 1–16 cores
- **Bus:** AMBA AHB/APB (GRLIB interconnect)

### LEON3 Fault-Tolerant (LEON3FT)

Critical for space applications:

| Feature | Implementation | Protection |
|---------|---------------|-----------|
| **Register file EDAC** | SECDED on each register word | Single-bit correction, double-bit detection |
| **Cache EDAC** | Parity or ECC on cache tags + data | Detects and corrects cache bit flips |
| **Scrubbing** | Background cache scrub | Prevents multi-bit accumulation |
| **TMR register file** | Optional triplication | Zero single-point-of-failure |

### GRLIB IP Library

LEON3/4 ships with the GRLIB IP library — a complete SoC building framework:

| IP Block | Function |
|----------|----------|
| `greth` | 10/100/1000 Ethernet MAC |
| `gptimer` | General-purpose timer unit |
| `apbuart` | UART |
| `spictrl` | SPI controller |
| `apbctrl` | APB bridge |
| `ahbctrl` | AHB arbiter / decoder |
| `mctrl` | Memory controller (SRAM/PROM) |
| `ddr2spa` | DDR2 controller |

### Toolchain

```bash
# SPARC bare-metal toolchain
sudo apt install gcc-sparc64-linux-gnu

# Or build from GRLIB
# LEON3 uses bare-c (RTEMS) or Linux
# RTEMS for LEON3:
git clone https://github.com/RTEMS/rtems
./waf configure --target=sparc-rtems5
./waf build install
```

### Licensing

| License | Terms | Use Case |
|---------|-------|----------|
| **GPL** | Must release modified source | Open-source projects, research |
| **Commercial (Cobham Gaisler)** | No GPL obligation, support contract | Space missions, defense, commercial |

---

## Microwatt — POWER ISA

### Architecture

- **ISA:** POWER (64-bit, little-endian), subset of Power ISA v3.0
- **Pipeline:** 4-stage simple in-order |
| **MMU:** Radix MMU (Linux-compatible) |
| **Cache:** 4 KB I-cache, 4 KB D-cache (default) |
| **Bus:** Wishbone 64-bit |

### Key Feature: Mainline Linux

Microwatt boots mainline Linux ppc64le — not a fork:

```bash
# Build Microwatt + Linux
git clone https://github.com/antonblanchard/microwatt
cd microwatt
make

# Build Linux for Microwatt
git clone https://github.com/linux/linux
make ARCH=powerpc CROSS_COMPILE=powerpc64le-linux-gnu- \
    microwatt_defconfig
make ARCH=powerpc CROSS_COMPILE=powerpc64le-linux-gnu- -j$(nproc)
```

### FPGA Targets

| Board | FPGA | Status |
|-------|------|--------|
| **Digilent Arty A7** | Artix-7 35T | Main target, well-tested |
| **Nexys A7** | Artix-7 100T | Works |
| **OrangeCrab** | ECP5 25F | Experimental |
| **QEMU** | — | Functional simulation |

---

## ZPU — The Smallest Soft Core

### Architecture

- **ISA:** Custom stack-based (no register file — operands come from a stack)
- **Size:** ~500 LUTs (smallest 32-bit CPU available)
- **Pipeline:** Single-stage
- **Performance:** Very low (~0.1 DMIPS/MHz), but tiny

### When to Use ZPU

| Scenario | Why ZPU |
|----------|---------|
| Bootloader on a tiny CPLD/FPGA | Fits in < 500 LUTs |
| Simple control state machine replacement | Stack machine → simple code |
| Space-constrained co-processor | When even PicoRV32 (700 LUTs) is too big |

### Toolchain

```bash
# ZPU toolchain (zpu toolchain)
git clone https://github.com/zylin/zpu
cd zpu/zpu/sw
make
```

---

## NEO430 — MSP430 on FPGA

### Architecture

- **ISA:** MSP430 (16-bit, von Neumann, 16 general-purpose registers)
- **Size:** ~1,500–2,500 LUTs |
| **Peripherals:** UART, SPI, I²C, timer, PWM, GPIO, CRC16 — all built-in |
| **Memory:** Internal instruction ROM + data RAM (BRAM-based) |

### Key Advantage: Documentation

NEO430 has some of the best documentation in the open-source FPGA core space — comparable to NEORV32. The [NEO430 manual](https://github.com/stnolm/neo430) is a model for core documentation.

### Peripheral Map

| Address | Peripheral |
|---------|-----------|
| 0x0000–0x00FF | Internal ROM (bootloader) |
| 0x0100–0x01FF | Control Status Registers |
| 0x0200 | GPIO |
| 0x0300 | UART |
| 0x0400 | SPI |
| 0x0500 | I²C |
| 0x0600 | Timer |
| 0x0700 | CRC16 |
| 0x8000–0xFFFF | External memory (Wishbone) |

---

## When to Choose Non-RISC-V

| Scenario | Core | Why Over RISC-V |
|----------|------|-----------------|
| Space-qualified FPGA processor | **LEON3/4** | ESA qualification, EDAC, flight heritage (Vega, Sentinel) |
| Learn POWER architecture | **Microwatt** | IBM-supported, boots mainline Linux ppc64le |
| Smallest possible CPU | **ZPU** | ~500 LUTs; even SERV (RISC-V) is 300 LUTs but much slower |
| 16-bit ultra-low-power | **NEO430** | MSP430 compatibility, 16-bit efficiency |
| Existing SPARC codebase | **LEON3/4** | GRLIB ecosystem, RTEMS certified |
| Legacy OpenRISC project | **mor1kx** | Stable GCC/binutils, Linux 4.x support |
| Educational MIPS | **Plasma** | Simple MIPS I, MIT license, easy to modify |

### When NOT to Choose Non-RISC-V

| Scenario | Why Not | Better Option |
|----------|---------|---------------|
| New project, greenfield | RISC-V ecosystem is larger and growing faster | VexRiscv, NEORV32, PicoRV32 |
| Need commercial support | Most non-RV cores have limited commercial support | MicroBlaze V (RISC-V) or Nios V |
| Want smallest Linux core | PicoRV32 or VexRiscv are smaller and faster | See [RISC-V Cores](../riscv_cores/README.md) |
| Need industry-standard verification | RISC-V has the most formal verification work | Ibex / CV32E40P |

---

## Cross-References

| Topic | Article |
|-------|---------|
| RISC-V cores deep dives | [RISC-V Cores](../riscv_cores/README.md) |
| Vendor soft cores (MicroBlaze, Nios) | [Vendor Soft Cores](../vendor_soft/README.md) |
| RISC-V ISA reference | [RISC-V ISA](../riscv/riscv_isa.md) |
| SoC bus design | [Bus Matrix Design](../soc_design/bus_matrix_design.md) |
| Open-source cores catalog | [Other ISA Cores Catalog](../../12_open_source_open_hardware/cores_catalog/other_isa_cores_catalog.md) |
