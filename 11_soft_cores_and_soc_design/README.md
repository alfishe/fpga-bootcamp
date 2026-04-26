[← Home](../README.md)

# 11 — Soft Cores & SoC Design

Embedding processors inside FPGA fabric — from selecting a soft CPU core to designing a complete system-on-chip. Covers RISC-V ISA fundamentals, vendor soft processors (MicroBlaze, Nios II/V), deep dives into open-source RISC-V cores, and SoC architecture: bus matrices, memory maps, interrupts, DMA, and multi-core coherency.

## Index

| Folder | Coverage |
|---|---|
| [riscv/](riscv/README.md) | RISC-V ISA (RV32I/RV64I, extensions), privileged architecture (M/S/U modes, CSRs, virtual memory, PMP, PLIC/CLINT) |
| [vendor_soft/](vendor_soft/README.md) | MicroBlaze / MicroBlaze-V (Xilinx), Nios II / Nios V (Intel/Altera) — configuration, buses, BSP, migration |
| [riscv_cores/](riscv_cores/README.md) | Open RISC-V deep dives: VexRiscv, PicoRV32, NEORV32, SERV, Ibex, BOOM, Rocket, CVA6, XiangShan |
| [other_isa/](other_isa/README.md) | OpenRISC (mor1kx), LEON3/4 (SPARC V8), Microwatt (POWER9), ZPU, Plasma (MIPS), NEO430 (MSP430) |
| [soc_design/](soc_design/README.md) | Bus matrix design, memory map planning, interrupt routing, DMA architecture, Rocket Chip / Chipyard, multi-core coherency |
