[← Section Home](../README.md) · [← Project Home](../../README.md)

# 12-D — Open Source Memory Controllers

External memory is the first hard problem in any real FPGA design. This folder catalogs the open-source SDRAM, DDR, HyperRAM, and SRAM controller cores available — with comparison data on which FPGAs they target and what performance you can expect.

## Index

| File | Topic |
|---|---|
| [sdram_controllers.md](sdram_controllers.md) | Open SDRAM controllers: stffrdhrn/sdram-controller, MiSTer SDRAM controller, **LiteDRAM** (cross-platform, part of LiteX) — comparison: supported FPGAs, max frequency, bus width, burst support |
| [ddr_controllers.md](ddr_controllers.md) | Open DDR1/2/3/4 controllers: WangXuan95/FPGA-DDR-SDRAM (AXI DDR1), ultraembedded/core_ddr3_controller, oprecomp/DDR4_controller — comparison: max clock, data width, FPGA families tested, interface protocol |
| [specialized_memory.md](specialized_memory.md) | HyperRAM, QSPI PSRAM, async SRAM controllers — for designs where a full DDR PHY is overkill |
