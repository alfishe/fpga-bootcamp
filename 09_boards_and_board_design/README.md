[← Home](../README.md)

# 09 — Boards & Board Design

The analog reality surrounding your digital design. Covers high-speed signal integrity, power distribution network (PDN) design, BGA escape routing, thermal management, and configuration interface selection for production FPGA boards. Also covers vendor-produced development and evaluation boards — the commercial hardware you design with before building your own.

## Index

| File | Topic |
|---|---|
| [high_speed_signals.md](high_speed_signals.md) | Signal integrity: impedance control, length matching, differential pairs, vias, insertion loss, crosstalk |
| [power_integrity.md](power_integrity.md) | Power rails & sequencing, decoupling capacitor selection, PDN design, IR drop, current transients |
| [bga_routing.md](bga_routing.md) | BGA escape routing strategies, layer stackup design, via types (through, blind, buried, microvia) |
| [thermal_design.md](thermal_design.md) | Junction temperature estimation, heat sink selection, airflow, power dissipation models, thermal vias |
| [configuration_interfaces.md](configuration_interfaces.md) | Flash selection (QSPI, eMMC, NAND), config pin strapping, fallback/multi-boot, remote update |
| [io_voltage_levels.md](io_voltage_levels.md) | IO bank voltages, 5V tolerance, level translation techniques, legacy system interfacing, multi-VCCO power design |
| [high_end_boards.md](high_end_boards.md) | **Alveo** data-center cards, **Zynq UltraScale+** dev kits, **KRIA** SOMs, **Intel Agilex 7/Stratix 10** DKs — PCIe, HBM, ARM SoC, $250–$8,000 |
| [arduino_fpga_boards.md](arduino_fpga_boards.md) | **MKR Vidor 4000**, **Alorium XLR8/Snō**, **Spartan Edge Accelerator**, **QuickLogic EOS S3** — MCU+FPGA hybrids, Arduino IDE programmable |
| [repurposed_boards.md](repurposed_boards.md) | **Colorlight i5/i9/5A-75B** (ECP5 LED controller repurposed), **EBAZ4205** (Zynq mining board), **Pano Logic G2**, **MS Catapult v2**, **Elgato Cam Link 4K** — commercial hardware at open-source prices |

> For community-designed open-hardware boards (ULX3S, OrangeCrab, iCEBreaker, etc.), see [Open Boards](../12_open_source_open_hardware/open_boards/README.md).
