[← Section Home](../README.md) · [← Project Home](../../README.md)

# 06-D — DDR Memory Controllers

DDR memory is196→in nearly every non-trivial FPGA design. This folder covers the vendor IP blocks that interface FPGAs to external DDR3/DDR4/LPDDR4 SDRAM, their calibration sequences, and the pin planning constraints they impose.

## Index

| File | Topic |
|---|---|
| [xilinx_ddr.md](xilinx_ddr.md) | Xilinx MIG: 7-series, UltraScale+, Versal; DDR3/DDR4/LPDDR4; PHY architecture, calibration (write leveling, read DQS centering, read/write training), AXI4 slave interface, pin planning |
| [intel_ddr.md](intel_ddr.md) | Intel UniPHY / EMIF: Cyclone V/10, Arria 10, Stratix 10, Agilex; hard vs soft memory controller, calibration stages, Avalon-MM interface |
| [lattice_others_ddr.md](lattice_others_ddr.md) | Lattice ECP5/MachXO DDR, Microchip PolarFire DDR, Gowin DDR — capability comparison: max frequency, data width, PHY availability |
| [ddr_pin_planning.md](ddr_pin_planning.md) | PCB & pin planning for DDR: byte lanes, DQS pairing, fly-by topology, bank/byte group constraints, recommended pinout patterns |
