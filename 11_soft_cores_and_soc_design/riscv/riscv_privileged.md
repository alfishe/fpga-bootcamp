[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Home](README.md) · [← Project Home](../../../README.md)

# RISC-V Privileged Architecture — Modes, MMU, and Protection

The privileged spec is what separates a bare-metal microcontroller from a Linux-capable processor. For FPGA SoC designers, this is where architectural decisions have the biggest impact: M-mode-only = RTOS/bare-metal; M+S+U = Linux.

This article covers privilege levels, trap delegation, virtual memory (Sv32/Sv39/Sv48), page table walking, PMP, CLINT/PLIC/CLIC, and SBI.

---

## Privilege Levels

| Level | Name | Encoding | Use | Typical FPGA Core |
|---|---|---|---|---|
| **M-mode** | Machine | 11 | Always present, firmware/RTOS, full CSR access | Every RISC-V core |
| **S-mode** | Supervisor | 01 | OS kernel (Linux), page tables, virtual memory | VexRiscv, Rocket, CVA6 |
| **U-mode** | User | 00 | Application code, isolated from kernel | Linux-capable cores |
| **H-mode** | Hypervisor | — | Virtual machine monitor (KVM-like) | Rare in FPGA (Rocket + H ext) |

### Mode Transitions

```
                    ecall
    U-mode ──────────────────► S-mode
                               │ ecall
                               └──────────────────► M-mode
                                                      │
    U-mode ◄── sret ─────── S-mode ◄── mret ──────── M-mode
                               │                         │
                          Trap from U                  Trap from S
                          (timer, IRQ,                (timer, IRQ,
                           exception)                  exception)
```

### mstatus Register — The Key Control Register

```
 31        25  24  23  22  21  20    19  18   17   16  15  14   13   12 11  8  7  6  5  4  3  0
┌───┬──┬─┬─┬─┬───┬───┬───┬────┬───┬────┬────┬────┬───┬────┬───┬────┬───┬───┬───┬───┐
│SD │..│TS│FS│MPP│...│SPP│MPIE│...│SPIE│UPIE│MIE │...│SIE │...│UIE │...│   │   |   |
└───┴──┴─┴─┴─┴───┴───┴───┴────┴───┴────┴────┴────┴───┴────┴───┴────┴───┴───┴───┴───┘

Key fields for FPGA SoC:
  MPP[12:11] = Previous privilege mode (saved on trap entry)
  MIE     [3] = M-mode interrupt enable
  MPIE    [7] = Previous MIE (saved on trap entry)
```

---

## Trap Delegation

By default, all traps go to M-mode. For Linux-capable SoCs, you delegate most traps to S-mode so the kernel handles them directly:

```c
// Delegate most interrupts and exceptions to S-mode
// (OpenSBI does this during initialization)
csrw mideleg, (1 << 5) | (1 << 9) | (1 << 1);  // STI, SEI, SSI
csrw medeleg, 0xFFFFBFFF;  // Delegate all exceptions except ecall from M-mode
```

### What to Delegate

| Trap | Delegate to S-mode? | Why |
|---|---|---|
| Timer interrupt (STI) | Yes | Linux scheduler handles timers |
| External interrupt (SEI) | Yes | Linux IRQ handling via PLIC |
| Software interrupt (SSI) | Yes | IPI between CPU cores |
| Instruction page fault | Yes | Linux page fault handler |
| Load/Store page fault | Yes | Linux page fault handler |
| ECALL from U-mode | Yes | Linux syscall handler |
| ECALL from M-mode | No | M-mode should never ecall to itself |
| Machine timer (MTI) | No | M-mode firmware handles (OpenSBI) |
| Machine external (MEI) | No | M-mode handles platform-level IRQs |

---

## Virtual Memory (MMU)

### MMU Modes

| Scheme | Address Space | Page Sizes | Levels | FPGA Core |
|---|---|---|---|---|
| **Bare** | Physical only | N/A | 0 | PicoRV32, SERV, NEORV32 (bare-metal) |
| **Sv32** | 32-bit (4 GB) | 4 KB, 4 MB | 2 | VexRiscv (Linux config) |
| **Sv39** | 39-bit (512 GB) | 4 KB, 2 MB, 1 GB | 3 | Rocket, CVA6 |
| **Sv48** | 48-bit (256 TB) | 4 KB, 2 MB, 1 GB, 512 GB | 4 | Rocket (optional), server-class |

### Sv32 Page Table Walk

Sv32 uses a 2-level page table. The satp CSR holds the root page table address:

```
Virtual Address (32 bits):
┌──────────────────┬───────────────┬────────────────┐
│  VPN[1] (10 bits)│ VPN[0] (10bits)│ Offset (12bit)│
│  bits [31:22]    │ bits [21:12]   │ bits [11:0]   │
└────────┬─────────┴───────┬───────┴───────┬────────┘
         │                 │               │
         ▼                 ▼               ▼
   L1 Page Table    L2 Page Table    Physical Page
   (satp + VPN[1])  (+ VPN[0])       (+ offset)
```

### Page Table Entry (PTE) Format — Sv32

```
 31        20 19  18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
┌────────────┬─────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│  PPN[1]    │RSVD │D  │A  │G  │U  │X  │W  │R  │V  │   PPN[0]  │ RSVD  │ V │
└────────────┴─────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

V  = Valid
R/W/X = Read/Write/Execute permissions
U  = User-mode accessible
G  = Global (shared across address spaces)
A  = Accessed (set by hardware on first access)
D  = Dirty (set by hardware on first write)
PPN = Physical Page Number (physical address >> 12)
```

### Setting Up Virtual Memory (OpenSBI / U-Boot)

```c
// 1. Create page tables in DDR
// Identity map for M-mode firmware (0x0000_0000 – 0x7FFF_FFFF)
// Map DDR for Linux kernel at 0x8000_0000 (virtual = physical)
// Map device MMIO at 0x1000_0000 – 0x1FFF_FFFF

// 2. Set satp register to enable Sv32
uint32_t satp = (1 << 31) |        // MODE = Sv32
               (asid << 22) |      // Address Space ID
               (page_table_phys >> 12);  // PPN of root page table
csrw satp, satp;
// MMU is now active — all subsequent addresses are virtual
```

### MMU LUT Cost in FPGA

| Feature | LUTs | BRAM | Notes |
|---|---|---|---|
| Sv32 MMU (no TLB) | ~2,000 | 4 | Each access walks 2 page tables → slow |
| Sv32 MMU + ITLB + DTLB | ~4,000 | 4 | TLB: 32-entry I$, 32-entry D$ |
| Sv39 MMU + TLB | ~6,000 | 6 | 3-level walk; needed for Rocket |
| Sv48 MMU + TLB | ~8,000 | 8 | 4-level walk; server-class only |

---

## PMP — Physical Memory Protection

PMP is RISC-V's lightweight memory isolation mechanism — an alternative to a full MMU when you don't need virtual memory.

### PMP Architecture

```
┌─────────────────────────────────────────────┐
│ PMP Controller (M-mode only)                │
│                                             │
│  pmpcfg0: [R W X L] [R W X L] ... x 4       │  ← Per-region config
│  pmpcfg1: [R W X L] [R W X L] ... x 4       │
│  pmpaddr0-15: address/size registers        │  ← Region definitions
│                                             │
│  Check every U/S-mode memory access:        │
│    1. Find matching PMP region              │
│    2. If Locked (L=1): enforce permissions  │
│    3. If not matched: deny access           │
└─────────────────────────────────────────────┘
```

### PMP Configuration

| pmpcfg bits | Meaning |
|---|---|
| L (bit 7) | Lock — region is immutable until reset; also enforces in M-mode |
| R (bit 0) | Read permission |
| W (bit 1) | Write permission |
| X (bit 2) | Execute permission |
| A (bits 4:3) | Address mode: 00=OFF, 01=TOR, 10=NA4, 11=NAPOT |

### PMP Example: Protecting OpenTitan Regions

```c
// Region 0: ROM (execute-only for U-mode)
pmpaddr0 = 0x0000_8000 >> 2;  // Start at 0x0000_8000
pmpcfg0_byte0 = (1 << 5) | (1 << 2);  // NAPOT, L=1, X=1, R=0, W=0

// Region 1: RAM (read-write for U-mode)
pmpaddr1 = 0x0001_0000 >> 2;  // Start at 0x0001_0000
pmpcfg0_byte1 = (1 << 5) | (1 << 0) | (1 << 1);  // NAPOT, L=1, R=1, W=1

// Region 2: MMIO (no U-mode access)
pmpaddr2 = 0x4000_0000 >> 2;
pmpcfg0_byte2 = (1 << 7);  // L=1, R=0, W=0, X=0 (denied)
```

---

## Interrupt Controllers

### CLINT — Core-Local Interruptor

The CLINT provides per-core timer and software interrupts:

| Register | Offset | Purpose |
|---|---|---|
| `msip` | 0x0000 | Software interrupt (write 1 → assert MSIP) |
| `mtimecmp` | 0x4000 | Timer compare (fires MTI when mtime >= mtimecmp) |
| `mtime` | 0xBFF8 | Current time counter (reads from RTC) |

```c
// Set a timer interrupt 1 second from now
volatile uint64_t *mtime = (uint64_t *)0x200BFF8;
volatile uint64_t *mtimecmp = (uint64_t *)0x2004000;
*mtimecmp = *mtime + 10000000;  // 10 MHz clock → 1 second
csrs mie, (1 << 7);  // Enable MTI
```

### PLIC — Platform-Level Interrupt Controller

See [Interrupt Routing](../soc_design/interrupt_routing.md) for full PLIC details. Key points:
- Routes external interrupts (UART, SPI, DMA, etc.) to cores
- Each interrupt has configurable priority
- Each core has enable bits and a priority threshold
- Claim/complete mechanism prevents lost interrupts

### CLIC — Core-Local Interrupt Controller

CLIC is a newer interrupt controller spec that replaces CLINT + PLIC for low-latency systems:

| Feature | CLINT + PLIC | CLIC |
|---|---|---|
| **Interrupt latency** | 20–40 cycles | 4–8 cycles |
| **Preemption** | Limited (threshold-based) | Full nested (level-based) |
| **Vectoring** | Via mtvec + software | Hardware automatic |
| **Max interrupts** | 1023 (PLIC) | 4096 |
| **FPGA adoption** | Standard (VexRiscv, Rocket) | Emerging (NEORV32 has CLIC support) |

---

## SBI — Supervisor Binary Interface

The SBI is the API between S-mode (Linux kernel) and M-mode (OpenSBI firmware):

```
User App → Linux Kernel (S-mode) → OpenSBI (M-mode) → Hardware
              │                         │
         system calls          ecall to M-mode for
                               timer, IPI, console, reboot
```

### Key SBI Functions

| SBI Call | EID | Purpose |
|---|---|---|
| `sbi_set_timer` | 0x00 | Set next timer interrupt |
| `sbi_console_putchar` | 0x01 | Output a character (early printk) |
| `sbi_console_getchar` | 0x02 | Read a character (early console) |
| `sbi_send_ipi` | 0x05 | Send inter-processor interrupt |
| `sbi_reset` | 0x09 | Reboot or shutdown |
| `sbi_dbcn_write_byte` | 0x44 | Debug console (SBI v1.0+) |

OpenSBI is the de-facto firmware for RISC-V Linux — every Linux-on-FPGA project uses it. The boot flow is: M-mode ROM → OpenSBI → U-Boot → Linux.

---

## Linux-Capable vs Bare-Metal Core Selection

| Requirement | ISA | MMU | LUTs | Example Core |
|---|---|---|---|---|
| Bare-metal, no OS | RV32I/M | None | 2K–5K | PicoRV32, SERV |
| RTOS (FreeRTOS/Zephyr) | RV32IM | None or MPU | 3K–8K | NEORV32, Ibex |
| Linux-capable SoC | RV32IMAC | Sv32 | 15K–30K | VexRiscv (Linux) |
| 64-bit Linux | RV64IMAFDC | Sv39 | 40K–100K | Rocket, CVA6 |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [RISC-V Privileged Spec](https://riscv.org/technical/specifications/) | RISC-V International | Official privileged architecture specification |
| [RISC-V ISA](riscv_isa.md) | This KB | Base ISA, extensions, instruction formats |
| [Interrupt Routing](../soc_design/interrupt_routing.md) | This KB | PLIC, GIC, NVIC, FPGA IRQ mapping |
| [DMA Architecture](../soc_design/dma_architecture.md) | This KB | DMA engines, descriptor chains |
