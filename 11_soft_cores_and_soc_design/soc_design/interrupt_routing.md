[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Interrupt Routing — PLIC, APIC, and Vectoring

Interrupt architecture determines how fast your SoC responds to hardware events. In open FPGA SoCs, the RISC-V PLIC (Platform-Level Interrupt Controller) is the emerging standard.

---

## Core Concepts

| Concept | Description |
|---|---|
| **Level-triggered** | Interrupt stays asserted until cleared by software |
| **Edge-triggered** | Interrupt fires on rising/falling edge only |
| **Vectoring** | CPU jumps to per-interrupt handler directly (vs shared handler) |
| **Priority** | Higher-numbered interrupt preempts lower |
| **Multi-core affinity** | Route interrupt to specific core or "any available" |

## RISC-V Interrupt Architecture

```
Peripherals           PLIC               CPU Core
┌──────────┐      ┌──────────┐      ┌──────────────┐
│ UART IRQ │─────►│          │      │              │
│ SPI IRQ  │─────►│  PLIC    │─────►│ MEIP (M-mode)│
│ GPIO IRQ │─────►│ (priority│      │ SEIP (S-mode)│
│ DMA Done │─────►│  + gate) │      │              │
│ Eth IRQ  │─────►│          │      │ claim/complete│
└──────────┘      └──────────┘      │ via MMIO     │
                                     └──────────────┘
```

## Design Decisions

| Decision | Options | Guidance |
|---|---|---|
| **Level vs Edge** | Level preferred for wire-OR; edge for pulse sources | Most FPGA peripherals → level with clear-on-ack |
| **Priority bits** | 3–8 bits | 8 levels (3 bits) sufficient for most SoCs |
| **Vectoring** | RISC-V does per-cause vectoring (mcause register) | Use mtvec.BASE + mcause × 4 for handler dispatch |
| **Priority inversion** | Higher-priority IRQ blocks lower | PLIC prevents this by design (only highest presented) |

---

## Original Stub Description

Interrupt architecture: PLIC/APIC design, vectoring, level vs edge, multi-core affinity, soft IRQs, priority inversion avoidance

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
