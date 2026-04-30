[← 06 IP & Cores Home](../README.md) · [← Project Home](../../README.md)

# 06-H — External Interfaces & Buses

FPGAs do not exist in a vacuum. They must talk to sensors, memories, displays, storage, and other chips. This section covers the **external buses and interfaces** that connect an FPGA to the outside world — from simple 400 kHz I2C sensors to 128 Gbps PCIe Gen6 links.

The articles progress from the simplest, slowest buses upward to the bleeding edge of chip-to-chip interconnect.

## Index

| File | Topic | Speed Range | Typical FPGA Implementation |
|---|---|---|---|
| [low_speed_serial_interfaces.md](low_speed_serial_interfaces.md) | I2C, SPI, UART, CAN, 1-Wire, SMBus | 100 Hz – 10 MHz | Soft core in fabric; some SoC FPGAs have hard I2C/SPI/CAN |
| [parallel_buses.md](parallel_buses.md) | 68000, Zorro II/III, ISA, PCI 2.3, VME | 3.5–66 MHz | Soft cores in fabric; level translation required for 5V TTL; retro-computing focus |
| [high_speed_serial_interfaces.md](high_speed_serial_interfaces.md) | USB 1.1/2.0/3.0/4 — soft IP and hardened controllers | 12 Mbps – 40 Gbps | Soft MAC + ULPI PHY on any FPGA; hard USB 2.0/3.0 on SoC FPGAs only |
| [usb_and_storage_interfaces.md](usb_and_storage_interfaces.md) | SATA, NVMe, SD/SDIO/eMMC | 1.5 Gbps – 64 Gbps | NVMe over PCIe hard block; SATA soft core + SerDes; SD/eMMC soft or hard |
| [display_and_camera_interfaces.md](display_and_camera_interfaces.md) | HDMI, DisplayPort, MIPI D-PHY/CSI-2/DSI, LVDS panels | 250 Mbps – 80 Gbps | Hard HDMI/DP on high-end FPGAs; MIPI hard on Lattice CrossLink-NX; LVDS on most |
| [chip_to_chip_interfaces.md](chip_to_chip_interfaces.md) | PCIe Gen1–6, CXL, CCIX, UCIe, Interlaken, Aurora | 2.5 GT/s – 256 GT/s | Hard PCIe blocks on mid-range+; CXL emerging on Intel Agilex/AMD Versal; UCIe future |

## Speed Spectrum Overview

```
Speed (log scale)
│
├─ 100 Gbps ─── PCIe Gen6 x16, UCIe
├─  10 Gbps ─── PCIe Gen4 x4, USB4, DisplayPort 2.0
├─   1 Gbps ─── PCIe Gen3 x1, SATA 6G, USB 3.0, MIPI D-PHY v2
├─ 100 Mbps ─── USB 2.0 HS, Fast Ethernet, CAN-FD, SD UHS-I
├─  10 Mbps ─── SPI @ 10 MHz, UART, USB 1.1 FS
├─   1 Mbps ─── I2C Fast-mode, CAN classic
├─ 100 kbps ─── I2C Standard-mode, 1-Wire, SMBus
├─  10 MHz ─── ISA bus, Zorro II, 68000 @ 8 MHz
├─   1 MHz ─── Zorro II (slow access), 68000 byte cycle
```

## Key Concepts Across All Articles

| Concept | Relevance |
|---|---|
| **Hard IP vs. Soft Core** | Hard IP = dedicated silicon (low power, guaranteed timing). Soft core = RTL in fabric (flexible, consumes LUTs/FFs) |
| **PHY vs. Controller** | PHY = physical layer (analog front-end, SerDes). Controller = digital protocol logic (packet handling, state machines) |
| **Voltage Translation** | External buses often use different voltages than the FPGA IO bank. See [IO Voltage Levels & Level Translation](../../09_board_design/io_voltage_levels.md) |
| **Pin Count** | Parallel buses (MIPI, LVDS, DDR) need many pins. Serial buses (PCIe, USB3) need fewer pins but dedicated transceivers |
| **IP Licensing** | Vendor IP for complex protocols (PCIe, HDMI, MIPI) often requires separate license fees beyond the FPGA tool license |

---

| ← Prev | Next → |
|---|---|
| [Other Hard IP](../other_hard_ip/README.md) (Ethernet MAC, video/audio, DSP) | [Low-Speed Serial Interfaces](low_speed_serial_interfaces.md) (I2C, SPI, UART, CAN) |
