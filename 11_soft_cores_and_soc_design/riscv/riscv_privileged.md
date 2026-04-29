[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Home](README.md) · [← Project Home](../../../README.md)

# RISC-V Privileged Architecture — Supervisor Mode & Virtual Memory

The privileged spec is what separates a bare-metal microcontroller from a Linux-capable processor. For FPGA SoC designers, this is where architectural decisions have the biggest impact.

---

## Privilege Levels

| Level | Name | Use | Typical FPGA Core |
|---|---|---|---|
| **M-mode** | Machine | Always present, firmware/RTOS, CSR access | Every RISC-V core |
| **S-mode** | Supervisor | OS kernel (Linux), page tables, virtual memory | Rocket, CVA6, VexRiscv (Linux) |
| **U-mode** | User | Application code, isolated from kernel | Linux-capable cores |
| **H-mode** | Hypervisor | Virtual machine monitor (KVM-like) | Rare in FPGA (Rocket with H extension) |

## SBI — Supervisor Binary Interface

The SBI is the API between S-mode (Linux kernel) and M-mode (OpenSBI firmware):

```
User App → Linux Kernel (S-mode) → OpenSBI (M-mode) → Hardware
              │                         │
         system calls          ecall to M-mode for
                               timer, IPI, console, reboot
```

OpenSBI is the de-facto firmware for RISC-V Linux — every Linux-on-FPGA project uses it.

## Virtual Memory (MMU)

| Scheme | Address Space | Page Sizes | FPGA Core |
|---|---|---|---|
| **Sv32** | 32-bit (4 GB) | 4 KB, 4 MB | VexRiscv (Linux), PicoRV32 (no MMU) |
| **Sv39** | 39-bit (512 GB) | 4 KB, 2 MB, 1 GB | Rocket, CVA6 |
| **Sv48** | 48-bit (256 TB) | 4 KB, 2 MB, 1 GB, 512 GB | Rocket (optional), server-class only |

## PMP — Physical Memory Protection

PMP is RISC-V's lightweight alternative to a full MMU:
- **No virtual memory** — physical addresses only
- **Configurable regions** (typically 8–16)
- **Per-region permissions**: R, W, X
- **Lock bit**: Region becomes immutable until reset (security)

PMP is what makes **Ibex suitable for OpenTitan** — it provides memory isolation without the cost of a full MMU.

---

## Original Stub Description

RISC-V privileged architecture: supervisor mode, SBI (Supervisor Binary Interface), virtual memory (Sv32/Sv39/Sv48), Physical Memory Protection (PMP), external interrupt controllers (PLIC/CLINT/CLIC/AIA)

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
