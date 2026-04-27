[← Home](../README.md)

# 02 — Architecture: What's Inside an FPGA

The silicon fundamentals every FPGA shares, organized into four layers: **fabric** (programmable logic), **infrastructure** (support hardware), **SoC** (CPU+FPGA integration), and **hybrid** (specialized on-die compute + analog).

## Index

| Folder | Coverage |
|---|---|
| [fabric/](fabric/README.md) | LUTs & CLBs, BRAM & URAM, DSP slices, routing & interconnect |
| [infrastructure/](infrastructure/README.md) | Clocking, IO standards & SERDES, configuration & bitstream |
| [soc/](soc/README.md) | Hard CPU integration: ARM/RISC-V + FPGA, AXI bridges, shared memory, boot architecture |
| [hybrid/](hybrid/README.md) | Specialized integration: RF DAC/ADC (RFSoC), AI Engine arrays (Versal), HBM stacks |
| [cpld/](cpld/README.md) | CPLD & non-volatile logic: macrocells, flash/antifuse/SONOS, Intel MAX families, CPLD vs FPGA decision |
