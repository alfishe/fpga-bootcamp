[← SoC Home](README.md) · [← Section Home](../README.md) · [← Project Home](../../README.md)

# Boot Architecture — Multi-Stage SoC Bring-Up

The boot sequence is where FPGA SoCs diverge most from standalone FPGA design. The CPU always boots first, the FPGA is a configurable peripheral, and getting from power-on to a running Linux kernel with active FPGA bridges involves four distinct stages — each with vendor-specific tooling and pitfalls.

---

## Universal Boot Flow

```
┌───────────────────────────────────────────────────┐
│  1. Power-On Reset                                │
│     Internal oscillators start                    │
│     Reset vector: CPU Boot ROM                    │
└──────────────────────┬────────────────────────────┘
                       ▼
┌───────────────────────────────────────────────────┐
│  2. CPU Boot ROM (immutable, on-chip)             │
│     Reads boot-mode pins / BSEL                   │
│     Initializes minimal peripheral (SD/QSPI/NAND) │
│     Loads 1st-stage bootloader into on-chip RAM   │
└──────────────────────┬────────────────────────────┘
                       ▼
┌───────────────────────────────────────────────────┐
│  3. 1st-Stage Bootloader (FSBL / U-Boot SPL)      │
│     • Configures PLLs, clocks                     │
│     • Initializes DDR controller                  │
│     • Configures pin multiplexing                 │
│     • Optionally loads FPGA bitstream             │
│     • Loads 2nd-stage bootloader                  │
└──────────────────────┬────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────── ──┐
│  4. 2nd-Stage Bootloader (U-Boot / Linux)         │
│     • U-Boot: network, filesystem, scripting      │
│     • Loads kernel + device tree                  │
│     • Can load FPGA bitstream (FPGA Manager)      │
└──────────────────────┬────────────────────────────┘
                       ▼
┌───────────────────────────────────────────────────┐
│  5. Linux Kernel + Userspace                      │
│     • FPGA Manager driver active                  │
│     • FPGA bridges enumerated via device tree     │
│     • Applications use /dev/fpga0, UIO, or custom │
└───────────────────────────────────────────────────┘
```

---

## Vendor Boot Comparison

| Stage | Cyclone V SoC | Zynq-7000 | Zynq MPSoC | PolarFire SoC |
|---|---|---|---|---|
| **Boot ROM** | HPS Boot ROM (64 KB) | PS BootROM (128 KB) | CSU BootROM (PMU) | E51 monitor from eNVM |
| **Boot pins** | BSEL[2:0] — selects SD/QSPI/NAND | Boot mode straps (6 pins) | Boot mode straps | MSS config switches |
| **1st Stage** | U-Boot SPL (preloader) | FSBL (Xilinx SDK generated) | PMU firmware + FSBL | Hart Software Services (HSS) |
| **FPGA config** | Via HPS (FPP ×16): loads .rbf from SD→DDR→fabric | PCAP (Processor Config Access Port): FSBL or Linux | PCAP or CSU DMA: PMU controls | Auto-load from eNVM or SPI flash at power-on |
| **2nd Stage** | U-Boot (SSBL) | U-Boot (compiled with device tree) | ARM Trusted Firmware (ATF) + U-Boot | U-Boot (optional; HSS can boot Linux directly) |
| **OS** | Linux (from SD/eMMC/QSPI) | Linux (from SD/QSPI/NAND) | Linux + OpenAMP (R5 cores) | Linux (from eMMC/SD/QSPI) |
| **Power domains** | HPS + FPGA share power-on rail | PS powers first; PL power domain OFF — must enable | Multiple: low-power domain (LPD), full-power (FPD), PL | Single flash-based platform, instant-on |

---

## FPGA Configuration Paths

| Mode | How | Bandwidth | Who Uses | Notes |
|---|---|---|---|---|
| **FPP ×16 (via HPS)** | HPS loads .rbf from SD, pumps to fabric | 100 MHz × 16-bit = 200 MB/s | Cyclone V SoC (default) | FPGA configuration takes ~50–500 ms |
| **PCAP** | PS writes bitstream to PL config port | 200 MHz × 32-bit = 800 MB/s | Zynq-7000, MPSoC | Can be partial reconfiguration |
| **AS ×4 (Active Serial)** | FPGA reads from external QSPI flash directly | ~100 MHz × 4-bit | All Intel FPGA-only | No CPU involved |
| **eNVM (internal flash)** | Config stored on-die, instant-on | Instant (<1 ms) | PolarFire, SmartFusion2, MAX 10 | No external bitstream chip needed |
| **JTAG** | External debug probe | ~10–30 MHz | All devices (debug only) | Too slow for production |

---

## DE10-Nano Boot Walkthrough (Concrete Example)

```
Power-on
│
├─► HPS Boot ROM reads BSEL = 0x1 → SD/MMC
├─► Loads U-Boot SPL from SD card partition 3 (0xA2 type)
├─► U-Boot SPL: configures DDR3 (1 GB), HPS clocks (800 MHz)
│     Optional: loads socfpga.rbf → writes to FPGA Manager
├─► U-Boot SPL → U-Boot (from SD FAT partition)
├─► U-Boot: loads zImage + socfpga_cyclone5_de10_nano.dtb
├─► Boots Linux kernel
│
└─► Linux: FPGA Manager driver ready
      Bridge drivers probe AXI ports → /dev/fpga0
      Userspace can reconfigure FPGA via configfs
```

---

## Common Boot Pitfalls

| Pitfall | Symptom | Root Cause | Fix |
|---|---|---|---|
| **FPGA not configured before driver load** | Bridge driver probes fail | U-Boot SPL loaded kernel before FPGA config was written | Enable FPGA load in U-Boot pre-boot script |
| **DDR timing mismatch** | Kernel panics randomly under load | U-Boot SPL configured wrong DDR parameters for your board | Validate DDR timing against Terasic/Intel reference |
| **HPS hangs when FPGA toggles IO** | HPS freezes on FPGA config | FPGA IOs driven before HPS boot OK, causing contention on shared pins | Set FPGA IOs to weak pull-up during config |
| **Mismatched device trees** | Bridge addresses wrong, DMA crashes | Device tree compiled for different SoC variant | Use exact DTS for your device (not generic socfpga.dtsi) |

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS Boot Guide | Intel FPGA documentation |
| Zynq-7000 Boot and Configuration (UG585, Ch. 6) | Xilinx/AMD |
| MPSoC Boot and Configuration (UG1085, Ch. 11) | Xilinx/AMD |
| PolarFire SoC Boot Guide (UG0820) | Microchip |
| DE10-Nano User Manual | Terasic |
