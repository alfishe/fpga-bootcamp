[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Memory Map Design — Planning Address Spaces

The memory map is the contract between hardware and software — get it wrong and your device tree won't match your RTL, leading to silent data corruption or boot failures.

---

## Memory Map Principles

| Principle | Why It Matters |
|---|---|
| **Power-of-2 aperture sizing** | Simplifies address decoding → fewer LUTs |
| **Reserve gaps between regions** | Prevents address collision when expanding later |
| **Keep boot ROM at fixed address** | CPU reset vector is hard-coded (0x0000_0000 for RISC-V, varies for ARM) |
| **MMIO above DRAM** | DRAM starts at lowest address for zero-offset access |
| **Alias vs dedicate** | Aliasing saves decode logic; dedicated regions prevent accidental access |

## Typical SoC Memory Map

| Start Addr | End Addr | Size | Region |
|---|---|---|---|
| 0x0000_0000 | 0x0FFF_FFFF | 256 MB | DDR (low alias) |
| 0x1000_0000 | 0x1000_0FFF | 4 KB | Boot ROM |
| 0x2000_0000 | 0x2000_1FFF | 8 KB | On-chip SRAM |
| 0x4000_0000 | 0x4000_0FFF | 4 KB | UART0 |
| 0x4000_1000 | 0x4000_1FFF | 4 KB | SPI Controller |
| 0x4000_2000 | 0x4000_2FFF | 4 KB | GPIO |
| 0x4000_3000 | 0x4000_3FFF | 4 KB | PLIC |
| 0x8000_0000 | 0xFFFF_FFFF | 2 GB | DDR (high alias) |

## Device Tree Binding

```dts
uart0: serial@40000000 {
    compatible = "ns16550a";
    reg = <0x40000000 0x1000>;
    interrupt-parent = <&plic>;
    interrupts = <1>;
};
```

The `reg` field MUST match the actual address decode in RTL. Mismatches cause undefined behavior — the #1 cause of "kernel boots but driver doesn't work".

---

## Original Stub Description

Memory map planning: base address assignment, aperture sizing, aliasing, MMIO vs memory regions, Linux device tree binding, reserved regions, memory protection

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../../README.md)
- [README.md](README.md)
