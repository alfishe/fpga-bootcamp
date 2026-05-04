[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Home](README.md) · [← Project Home](../../../README.md)

# RISC-V ISA — Base & Standard Extensions

A pragmatic reference for FPGA developers — what each RISC-V extension provides, how much it costs in LUTs, and when to enable it. RISC-V's modular ISA means you only pay for what you need.

---

## Extensions at a Glance

| Extension | Name | Adds | LUT Cost | Enable When |
|---|---|---|---|---|
| **RV32I** | Base Integer | 40 instructions, 32 registers | Baseline | Always (mandatory) |
| **RV64I** | 64-bit Base | 64-bit registers, addw/subw/etc. | +30% over RV32I | Need >4 GB addressing or 64-bit arithmetic |
| **M** | Multiply/Divide | mul, div, rem (signed/unsigned) | +300–1,500 LUTs | DSP, crypto, any math-heavy code |
| **A** | Atomic | lr/sc, amoswap/add/and/or/xor/min/max | +500–1,000 LUTs | Multi-core, shared memory synchronization |
| **F** | Single FP | 32-bit FPU, 32 FP registers | +2,000–4,000 LUTs | Sensor fusion, DSP with floating-point |
| **D** | Double FP | 64-bit FPU | +4,000–8,000 LUTs | Scientific computing, avoid on FPGA |
| **C** | Compressed | 16-bit instruction forms | +200–500 LUTs | Always (saves ~30% code size) |
| **B** | Bit Manipulation | clz, ctz, pcnt, rotate, bfp | +300–800 LUTs | Cryptography, networking, bit processing |
| **V** | Vector | Configurable-width SIMD | +5,000–50,000+ LUTs | ML/DSP acceleration, large FPGAs only |
| **Zicsr** | CSR Access | csrr, csrw, csrs, csrrc | Included in I | Always (needed for traps) |
| **Zifencei** | Fence.I | Instruction cache flush | ~50 LUTs | Self-modifying code, JIT |
| **Zba** | Address Gen | sh2add, sh3add, sh4add | ~100 LUTs | Array indexing acceleration |
| **Zbb** | Basic Bitmanip | clz, ctz, pcnt, rev, orc | ~300 LUTs | Most useful B sub-extension |
| **Zbs** | Single-bit | bset, bclr, binv, bext | ~200 LUTs | Bitfield manipulation |
| **Zicbom** | Cache Mgmt | cbo.clean, cbo.flush, cbo.inval | ~100 LUTs | Multi-core cache coherency |

### Recommended Configurations for FPGA

| Config | ISA String | LUTs (approx.) | Use Case |
|---|---|---|---|
| **Minimal bare-metal** | RV32I | 2,000–3,000 | Simple control logic, PicoRV32-class |
| **Bare-metal + MUL** | RV32IM | 3,000–4,500 | Most soft cores (NEORV32, SERV) |
| **Linux-capable** | RV32IMAC | 5,000–8,000 | VexRiscv Linux, Ibex + MMU |
| **Linux + FPU** | RV32IMAFDC | 8,000–15,000 | Full Linux with floating-point apps |
| **64-bit Linux** | RV64IMAFDC | 12,000–25,000 | BOOM, CVA6-class |
| **Vector accelerator** | RV32IMCV | 10,000–50,000+ | ML inference, DSP pipeline |

---

## Instruction Formats

All RISC-V instructions are 32-bit (or 16-bit with C extension), with 6 formats:

```
R-type: [funct7][rs2   ][rs1   ][funct3][rd    ][opcode ]  — Register-register (add, sub)
I-type: [imm11:0        ][rs1   ][funct3][rd    ][opcode ]  — Immediate (addi, lw, csrr)
S-type: [imm11:5][rs2   ][rs1   ][funct3][imm4:0][opcode ]  — Store (sw, sh, sb)
B-type: [imm12|10:5][rs2][rs1   ][funct3][imm4:1|11][opcode] — Branch (beq, bne, blt)
U-type: [imm31:12                            ][rd    ][opcode] — Upper immediate (lui, auipc)
J-type: [imm20|10:1|11|19:12               ][rd    ][opcode] — Jump (jal)

Bit positions: 31              25 24   20 19   15 14  12 11    7 6       0
```

### Compressed Instruction Formats (C Extension)

16-bit encodings of the most common 32-bit instructions:

```
CR-type: [funct4][rd/rs1][rs2   ][op]  — Register (c.mv, c.add)
CI-type: [funct3][imm   ][rd/rs1][op]  — Immediate (c.li, c.addi)
CSS-type:[funct3][imm   ][rs2   ][op]  — Stack-relative store (c.swsp)
CL-type: [funct3][imm  ][rs1 ][rd  ][op] — Load (c.lw)
CS-type: [funct3][imm  ][rs1 ][rs2 ][op] — Store (c.sw)
CB-type: [funct3][imm      ][rs1 ][op]  — Branch (c.beqz)
CJ-type: [funct3][imm              ][op]  — Jump (c.j, c.jal)
```

**Code size impact:** C extension reduces code size by 25–30%, which means:
- Less instruction memory (BRAM savings)
- Better I-cache hit rate
- Less fetch bandwidth → lower power

---

## RV32I Base Integer — Complete Instruction Set

### Computational Instructions

| Instruction | Format | Description |
|---|---|---|
| `add rd, rs1, rs2` | R | rd = rs1 + rs2 |
| `sub rd, rs1, rs2` | R | rd = rs1 - rs2 |
| `and rd, rs1, rs2` | R | rd = rs1 & rs2 |
| `or rd, rs1, rs2` | R | rd = rs1 \| rs2 |
| `xor rd, rs1, rs2` | R | rd = rs1 ^ rs2 |
| `sll rd, rs1, rs2` | R | rd = rs1 << rs2[4:0] |
| `srl rd, rs1, rs2` | R | rd = rs1 >> rs2[4:0] (logical) |
| `sra rd, rs1, rs2` | R | rd = rs1 >>> rs2[4:0] (arithmetic) |
| `slt rd, rs1, rs2` | R | rd = (rs1 < rs2) ? 1 : 0 (signed) |
| `sltu rd, rs1, rs2` | R | rd = (rs1 < rs2) ? 1 : 0 (unsigned) |
| `addi rd, rs1, imm` | I | rd = rs1 + imm |
| `andi rd, rs1, imm` | I | rd = rs1 & imm |
| `ori rd, rs1, imm` | I | rd = rs1 \| imm |
| `xori rd, rs1, imm` | I | rd = rs1 ^ imm |
| `slti rd, rs1, imm` | I | rd = (rs1 < imm) ? 1 : 0 (signed) |
| `sltiu rd, rs1, imm` | I | rd = (rs1 < imm) ? 1 : 0 (unsigned) |
| `slli rd, rs1, shamt` | I | rd = rs1 << shamt |
| `srli rd, rs1, shamt` | I | rd = rs1 >> shamt (logical) |
| `srai rd, rs1, shamt` | I | rd = rs1 >>> shamt (arithmetic) |
| `lui rd, imm` | U | rd = imm << 12 (load upper immediate) |
| `auipc rd, imm` | U | rd = PC + (imm << 12) |

### Load/Store Instructions

| Instruction | Width | Description |
|---|---|---|
| `lb rd, offset(rs1)` | 8-bit | Load byte (sign-extended) |
| `lbu rd, offset(rs1)` | 8-bit | Load byte (zero-extended) |
| `lh rd, offset(rs1)` | 16-bit | Load halfword (sign-extended) |
| `lhu rd, offset(rs1)` | 16-bit | Load halfword (zero-extended) |
| `lw rd, offset(rs1)` | 32-bit | Load word |
| `sb rs2, offset(rs1)` | 8-bit | Store byte |
| `sh rs2, offset(rs1)` | 16-bit | Store halfword |
| `sw rs2, offset(rs1)` | 32-bit | Store word |

### Branch and Jump Instructions

| Instruction | Description |
|---|---|
| `beq rs1, rs2, offset` | Branch if rs1 == rs2 |
| `bne rs1, rs2, offset` | Branch if rs1 != rs2 |
| `blt rs1, rs2, offset` | Branch if rs1 < rs2 (signed) |
| `bge rs1, rs2, offset` | Branch if rs1 >= rs2 (signed) |
| `bltu rs1, rs2, offset` | Branch if rs1 < rs2 (unsigned) |
| `bgeu rs1, rs2, offset` | Branch if rs1 >= rs2 (unsigned) |
| `jal rd, offset` | Jump and link: rd = PC+4, PC += offset |
| `jalr rd, rs1, offset` | Jump and link register: rd = PC+4, PC = rs1+offset |

### System Instructions

| Instruction | Description |
|---|---|
| `ecall` | Environment call (syscall to OS) |
| `ebreak` | Environment break (debugger breakpoint) |
| `mret` | Return from M-mode trap handler |
| `fence` | Memory fence (ordering) |
| `fence.i` | Instruction cache flush |

---

## M Extension — Multiply/Divide

| Instruction | Operation | Cycles (typical) |
|---|---|---|
| `mul rd, rs1, rs2` | rd = (rs1 × rs2)[31:0] | 1 (with DSP) |
| `mulh rd, rs1, rs2` | rd = (rs1 × rs2)[63:32] signed×signed | 3 |
| `mulhu rd, rs1, rs2` | rd = (rs1 × rs2)[63:32] unsigned×unsigned | 3 |
| `mulhsu rd, rs1, rs2` | rd = (rs1 × rs2)[63:32] signed×unsigned | 3 |
| `div rd, rs1, rs2` | rd = rs1 / rs2 (signed) | 8–32 (iterative) |
| `divu rd, rs1, rs2` | rd = rs1 / rs2 (unsigned) | 8–32 |
| `rem rd, rs1, rs2` | rd = rs1 % rs2 (signed) | 8–32 |
| `remu rd, rs1, rs2` | rd = rs1 % rs2 (unsigned) | 8–32 |

**FPGA implementation:** `mul` maps directly to DSP48/ECP5 DSP slices. `div` is typically iterative (1 bit/cycle) or table-based. Multi-cycle dividers use a state machine.

---

## A Extension — Atomic Memory Operations

| Instruction | Operation |
|---|---|
| `lr.w rd, (rs1)` | Load reserved — sets reservation set |
| `sc.w rd, rs2, (rs1)` | Store conditional — succeeds only if reservation valid |
| `amoswap.w rd, rs2, (rs1)` | Atomic swap: rd = *rs1, *rs1 = rs2 |
| `amoadd.w rd, rs2, (rs1)` | Atomic add: rd = *rs1, *rs1 += rs2 |
| `amoand.w rd, rs2, (rs1)` | Atomic AND |
| `amoor.w rd, rs2, (rs1)` | Atomic OR |
| `amoxor.w rd, rs2, (rs1)` | Atomic XOR |
| `amomin.w rd, rs2, (rs1)` | Atomic signed minimum |
| `amomax.w rd, rs2, (rs1)` | Atomic signed maximum |
| `amominu.w rd, rs2, (rs1)` | Atomic unsigned minimum |
| `amomaxu.w rd, rs2, (rs1)` | Atomic unsigned maximum |

**LR/SC usage — spinlock:**

```c
// RISC-V spinlock using LR/SC
void lock(volatile int *mutex) {
    int tmp;
    do {
        // Wait for lock to be free
        do {
            asm volatile("lw %0, 0(%1)" : "=r"(tmp) : "r"(mutex));
        } while (tmp != 0);
        // Try to acquire
        asm volatile(
            "li %0, 1\n"          // tmp = 1
            "lr.w %0, 0(%1)\n"    // tmp = *mutex (load reserved)
            "bne %0, zero, 1f\n"  // if not 0, retry
            "sc.w %0, %2, 0(%1)\n"// store conditional: *mutex = 1
            "1:"
            : "=r"(tmp)
            : "r"(mutex), "r"(1)
        );
    } while (tmp != 0);  // SC failed, retry
}

void unlock(volatile int *mutex) {
    *mutex = 0;
}
```

---

## C Extension — Compressed Instructions

The 16-bit compressed encodings map to the most frequently used 32-bit instructions:

| Compressed | Expanded | Description |
|---|---|---|
| `c.li rd, imm` | `addi rd, x0, imm` | Load small immediate |
| `c.lui rd, imm` | `lui rd, imm` | Load upper immediate |
| `c.addi rd, imm` | `addi rd, rd, imm` | Add small immediate |
| `c.addi4spn rd', imm` | `addi rd', sp, imm` | Add SP offset (stack frame) |
| `c.lw rd', offset(rs1')` | `lw rd', offset(rs1')` | Load word |
| `c.sw rs2', offset(rs1')` | `sw rs2', offset(rs1')` | Store word |
| `c.lwsp rd, offset(sp)` | `lw rd, offset(sp)` | Load from stack |
| `c.swsp rs2, offset(sp)` | `sw rs2, offset(sp)` | Store to stack |
| `c.mv rd, rs2` | `add rd, x0, rs2` | Register move |
| `c.add rd, rs2` | `add rd, rd, rs2` | Register add |
| `c.j offset` | `jal x0, offset` | Unconditional jump |
| `c.jal offset` | `jal x1, offset` | Jump and link (RV32 only) |
| `c.jr rs1` | `jalr x0, rs1, 0` | Jump register |
| `c.jalr rs1` | `jalr x1, rs1, 0` | Jump and link register |
| `c.beqz rs1', offset` | `beq rs1', x0, offset` | Branch if zero |
| `c.bnez rs1', offset` | `bne rs1', x0, offset` | Branch if not zero |

**Note:** Compressed instructions can only access 8 registers (x8–x15) in load/store forms, and have limited immediate ranges. The assembler automatically selects C encoding when possible.

---

## CSRs — Control and Status Registers

| CSR | Address | Purpose | FPGA Relevance |
|---|---|---|---|
| **mstatus** | 0x300 | Status (MIE, MPIE, MPP) | Nested interrupt control |
| **misa** | 0x301 | ISA extensions supported | Runtime ISA query |
| **mie** | 0x304 | Interrupt enable bits | Route peripheral IRQs |
| **mip** | 0x344 | Interrupt pending bits | Check which IRQ fired |
| **mtvec** | 0x305 | Trap vector base address | Set up interrupt/exception handlers |
| **mscratch** | 0x340 | Scratch register for trap handler | Save SP during trap entry |
| **mepc** | 0x341 | Exception PC | Return address after trap |
| **mcause** | 0x342 | Trap cause code | Exception dispatch (interrupt vs exception) |
| **mtval** | 0x343 | Trap value | Fault address for load/store exceptions |
| **mcounteren** | 0x306 | Counter enable for S-mode | Performance counter access control |
| **mcycle** | 0xB00 | Cycle counter | Performance measurement |
| **minstret** | 0xB02 | Instruction retire counter | IPC measurement |
| **pmpcfg0-3** | 0x3A0-3 | PMP configuration | Memory protection for secure SoC |
| **pmpaddr0-15** | 0x3B0-3F | PMP address registers | Memory protection regions |

### CSR Access Instructions

| Instruction | Operation |
|---|---|
| `csrr rd, csr` | rd = CSR[csr] (read) |
| `csrw csr, rs1` | CSR[csr] = rs1 (write) |
| `csrs csr, rs1` | CSR[csr] |= rs1 (set bits) |
| `csrc csr, rs1` | CSR[csr] &= ~rs1 (clear bits) |
| `csrrw rd, csr, rs1` | rd = CSR[csr]; CSR[csr] = rs1 (atomic read-write) |
| `csrrs rd, csr, rs1` | rd = CSR[csr]; CSR[csr] |= rs1 (atomic read-set) |
| `csrrc rd, csr, rs1` | rd = CSR[csr]; CSR[csr] &= ~rs1 (atomic read-clear) |

---

## Trap Handling

### Machine-Mode Trap Entry

```c
// Trap handler in C
void trap_handler(void) __attribute__((interrupt("machine")));

void trap_handler(void) {
    uint32_t cause = csrr(mcause);
    
    if (cause & 0x80000000) {
        // Interrupt
        uint32_t irq_id = cause & 0x3FF;
        switch (irq_id) {
            case 7:  uart_irq_handler(); break;  // MTIP (timer)
            case 11: plic_handler();     break;  // MEIP (external)
        }
    } else {
        // Exception
        switch (cause) {
            case 2:  // Illegal instruction
            case 11: // ECALL from M-mode
            case 8:  // ECALL from U-mode (syscall)
            default: break;
        }
    }
}
```

### Trap Cause Codes

| Code | Interrupt? | Cause |
|---|---|---|
| 0x80000007 | Yes | Machine Timer Interrupt (MTIP) |
| 0x8000000B | Yes | Machine External Interrupt (MEIP) |
| 0x80000003 | Yes | Machine Software Interrupt (MSIP) |
| 0 | No | Instruction address misaligned |
| 1 | No | Instruction access fault |
| 2 | No | Illegal instruction |
| 3 | No | Breakpoint |
| 5 | No | Load access fault |
| 7 | No | Store access fault |
| 8 | No | ECALL from U-mode |
| 11 | No | ECALL from M-mode |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [RISC-V Specifications](https://riscv.org/technical/specifications/) | RISC-V International | Official ISA and privileged architecture specs |
| [RISC-V Privileged](riscv_privileged.md) | This KB | M/S/U modes, virtual memory, PMP |
| [Interrupt Routing](../soc_design/interrupt_routing.md) | This KB | PLIC design, GIC, NVIC |
| [Memory Map Design](../soc_design/memory_map_design.md) | This KB | Address decoder, aperture sizing |
