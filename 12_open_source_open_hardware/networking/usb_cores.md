[← 12 Open Source Open Hardware Home](../README.md) · [← Networking Home](README.md) · [← Project Home](../../../README.md)

# Open USB Cores

Open-source USB device and host controllers for FPGA — from FS (12 Mbps) through HS (480 Mbps) device-mode cores.

---

## Core Comparison

| Core | Mode | Speed | Interface | FPGA Verified | Repository |
|---|---|---|---|---|---|
| **usbcorev** | Device-only | FS (12 Mbps) | Native register interface | iCE40, ECP5, Artix-7 | avakar/usbcorev |
| **FPGA-USB-Device** | Device-only | FS + HS (480 Mbps) | Configurable (camera/audio/serial/HID) | Artix-7, Cyclone V, ECP5 | WangXuan95/FPGA-USB-Device |
| **core_usb_host** | Host-only | FS + HS | Wishbone | Artix-7, Cyclone V | ultraembedded/core_usb_host |
| **ULPI PHY** | PHY only | FS + HS | ULPI (12-pin) | Any FPGA with ULPI PHY chip | Various (used with USB3300, USB3320) |

## USB Device Classes Supported

| Class | FPGA-USB-Device | usbcorev | Notes |
|---|---|---|---|
| **HID (keyboard/mouse)** | ✅ | — | Most common use case |
| **CDC-ACM (serial)** | ✅ | — | Virtual COM port |
| **MSC (mass storage)** | ✅ | — | SD card via USB |
| **UVC (video/camera)** | ✅ (MJPEG) | — | FPGA camera streaming |
| **UAC (audio)** | ✅ | — | FPGA audio interface |
| **Custom bulk** | ✅ | ✅ (basic) | Raw data pipe |

## The ULPI Problem

Most FPGA boards lack a USB PHY chip (like USB3300). Without ULPI, you're stuck at FS (12 Mbps) using simple pull-up detection. Common workarounds:
- **PMOD-compatible ULPI boards** (e.g., Digilent PMOD USBUART)
- **FTDI FT232H in FIFO mode** (proprietary but ubiquitous hardware)
- **Use a microcontroller as USB bridge** (ESP32-S3, STM32 with USB FS)

---

## Original Stub Description

Open USB cores: **avakar/usbcorev** (FS device), **WangXuan95/FPGA-USB-Device** (camera/audio/serial/HID), **ultraembedded/core_usb_host** (host controller), ULPI PHY integration

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
