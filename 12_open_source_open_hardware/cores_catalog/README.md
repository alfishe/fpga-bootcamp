[← Section Home](../README.md) · [← Project Home](../../README.md)

# 12-C — Open Source CPU & Peripheral Core Catalogs

A shopping guide to the open-source core ecosystem. What CPUs can you drop into your design today? What peripheral cores are ready to wire up? These catalog files provide a high-level comparison — deep dives live in [Section 11](../../11_soft_cores_and_soc_design/README.md).

## CPU Core Catalogs

This project provides comprehensive coverage of FPGA CPU cores across three categories:

| Category | Catalog Article | Deep Dive Article | Coverage |
|---|---|---|---|
| **RISC-V cores** | [riscv_cores_catalog.md](riscv_cores_catalog.md) | [RISC-V Cores (Section 11)](../../11_soft_cores_and_soc_design/riscv_cores/README.md) | VexRiscv, PicoRV32, NEORV32, SERV, Ibex, Rocket, BOOM, CVA6, XiangShan, SweRV EH1 |
| **Other open ISA cores** | [other_isa_cores_catalog.md](other_isa_cores_catalog.md) | [Other ISA Cores (Section 11)](../../11_soft_cores_and_soc_design/other_isa/other_isa_cores.md) | OpenRISC (mor1kx), LEON3/4 (SPARC), Microwatt (POWER), NEO430 (MSP430), Plasma (MIPS), ZPU, retro cores (Z80, 6502, 68000), **plus Multi-ISA collections** (MicroCore Labs, OpenCores, ZipCPU) |
| **Vendor soft processors** | — | [Vendor Soft Processors (Section 11)](../../11_soft_cores_and_soc_design/vendor_soft/README.md) | MicroBlaze/MicroBlaze-V (Xilinx/AMD), Nios II/Nios V (Intel/Altera) — proprietary but widely used |

## Index

| File | Topic |
|---|---|
| [riscv_cores_catalog.md](riscv_cores_catalog.md) | **RISC-V core comparison table**: VexRiscv, PicoRV32, NEORV32, SERV, BOOM, Rocket, CVA6, Ibex, XiangShan — pipeline depth, ISA support (RV32/RV64, extensions), FPGA utilization (LUTs/FFs/BRAM/DSP), fmax, Linux capable? |
| [other_isa_cores_catalog.md](other_isa_cores_catalog.md) | Non-RISC-V inventory: OpenRISC (mor1kx), LEON3/4 (SPARC), Microwatt (POWER9), NEO430 (MSP430), Plasma (MIPS), ZPU, plus retro ISA soft cores (Z80, 6502, 68000) for vintage computing enthusiasts. **Includes Multi-ISA Core Collections** section covering MicroCore Labs (68000, 6502, 8086, Z80, 8051, RISC-V), OpenCores, and ZipCPU |
| [peripheral_cores_catalog.md](peripheral_cores_catalog.md) | Open peripheral repositories: Wishbone library, AXI infrastructure cores, standard protocol controllers (I2C/SPI/UART/GPIO/PWM), timers, watchdog |
