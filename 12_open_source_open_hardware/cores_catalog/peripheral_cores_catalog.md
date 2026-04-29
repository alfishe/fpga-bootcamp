[← 12 Open Source Open Hardware Home](../README.md) · [← Cores Catalog Home](README.md) · [← Project Home](../../../README.md)

# Peripheral Core Catalog

A catalog of open-source FPGA peripheral cores: common serial protocols, timers, GPIO, memory interfaces, and utility cores used in virtually every FPGA design.

---

## Communication Protocols

| Core | Interface | Key Trait | Repository |
|---|---|---|---|
| **wishbone-i2c** | I²C master/slave | Wishbone attachable | opencores.org |
| **simple-spi** | SPI master | Configurable CPOL/CPHA | many variants on GitHub |
| **uart2bus** | UART-to-Wishbone bridge | Exposes register map over serial | LiteX ecosystem |
| **jtag_vpi** | JTAG-to-AXI | Virtual JTAG for FPGA debug | Project F |
| **WB2AXI** | Wishbone ↔ AXI bridge | IP integration glue logic | Alex Forencich |

## Timer & System Peripherals

| Core | Function | Notes |
|---|---|---|
| **RISC-V MTIME** | 64-bit mtime/mtimecmp | Standard RISC-V machine timer |
| **APB Timer** | ARM-compatible timer | Used in ARM-based SoCs |
| **Watchdog Timer** | Simple countdown watchdog | Available in most open libraries |
| **PWM Generator** | Multi-channel PWM | LED/servo/motor control |

## GPIO & Interface

| Core | Function | Notes |
|---|---|---|
| **Wishbone GPIO** | Configurable-width GPIO | Input/output/tri-state per pin |
| **I²S/PCM** | Audio serial interface | Stereo, configurable sample rates |
| **PS/2 Host/Device** | Keyboard/mouse interface | Still used in retro and industrial |
| **SD Card SPI** | FAT32 over SPI | Common in retro computing cores |

## Where to Find More

- **Wishbone Library**: opencores.org/projects/wishbone — largest collection of Wishbone peripherals
- **LiteX Library**: litex-hub — LiteX-compatible peripheral cores (Python/Migen)
- **Alex Forencich**: github.com/alexforencich — AXI infrastructure cores
- **Project F**: projectf.io — well-documented Verilog peripherals (display, I²C, SPI)

---

## Original Stub Description

Open peripheral repositories: Wishbone library, AXI infrastructure cores, standard protocol controllers (I2C/SPI/UART/GPIO/PWM), timers, watchdog

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
