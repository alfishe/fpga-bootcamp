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

## Device Tree & FPGA Manager (Linux)

When Linux boots on a SoC FPGA, two mechanisms control FPGA interaction:

### FPGA Manager Subsystem
The Linux kernel FPGA Manager provides a unified API for loading bitstreams from userspace:

```bash
# Load bitstream via configfs (Linux 5.10+)
configfs_dir=/sys/kernel/config/device-tree/overlays/fpga
echo -n "soc_system.rbf" > $configfs_dir/path
```

### Device Tree Overlay Pattern
```dts
/* fpga_overlay.dts — loads bitstream + enumerates FPGA peripherals */
/dts-v1/;/plugin/;

/ {
  fragment@0 {
    target-path = "/fpga_full";
    __overlay__ {
      firmware-name = "soc_system.rbf";
    };
  };
  fragment@1 {
    target-path = "/soc";
    __overlay__ {
      my_accel: accel@0x40000000 {
        compatible = "mycorp,accel-1.0";
        reg = <0x40000000 0x1000>;
        interrupts = <0 29 4>;  /* PL→PS IRQ 29 */
      };
    };
  };
};
```

**Key point:** The overlay loads the bitstream first (fragment@0), then enumerates the FPGA peripheral (fragment@1). If you reverse the order, the driver probes before the FPGA is configured.

### Bridge Control
```bash
# Cyclone V SoC: enable bridges before loading FPGA
echo 1 > /sys/class/fpga-bridge/fpga2hps/enable
echo 1 > /sys/class/fpga-bridge/hps2fpga/enable
echo 1 > /sys/class/fpga-bridge/lwhps2fpga/enable
```

---

## U-Boot Scripting for FPGA Load

### Cyclone V SoC (DE10-Nano)
```bash
# U-Boot commands to load FPGA before Linux
fatload mmc 0:1 ${loadaddr} soc_system.rbf
fpga load 0 ${loadaddr} ${filesize}
# Then boot Linux
fatload mmc 0:1 ${loadaddr} zImage
fatload mmc 0:1 ${fdt_addr} socfpga_cyclone5_de10_nano.dtb
bootz ${loadaddr} - ${fdt_addr}
```

### Zynq-7000
```bash
# FSBL can load PL, but if not, do it from U-Boot
load mmc 0:1 ${loadaddr} system.bit
fpga loadb 0 ${loadaddr} ${filesize}
# Boot Linux
load mmc 0:1 ${kernel_addr} zImage
load mmc 0:1 ${fdt_addr} system.dtb
bootz ${kernel_addr} - ${fdt_addr}
```

### Zynq MPSoC (Multi-Stage)
```bash
# PMU firmware + ATF + U-Boot chain
# FSBL loads PMU firmware and PL (if specified in bif file)
# boot.bif example:
# the_image: {
#   [fsbl_config] a53_x64
#   [bootloader] fsbl.elf
#   [pmufw_image] pmufw.elf
#   [destination_cpu=a53-0, destination_device=pl] system.bit
#   [destination_cpu=a53-0] bl31.elf
#   [destination_cpu=a53-0] u-boot.elf
# }
```

---

## Secure Boot Considerations

| Device | Secure Boot Mechanism | Key Storage | Chain of Trust |
|---|---|---|---|
| **Zynq MPSoC** | RSA + SHA-256 (boot header authentication) | BBRAM or eFUSE | FSBL verifies PMU + PL bitstream + ATF |
| **Cyclone V SoC** | No native secure boot | N/A | Add AES-encrypted .rbf in software |
| **PolarFire SoC** | eNVM + digital signature | Flash (locked) | HSS verifies Linux image before boot |
| **Agilex 7** | Root of Trust (RoT) + AES-GCM | eFUSE or QSPI | FSBL authenticates each stage |

**Best practice:** If your design includes proprietary IP in the FPGA fabric, enable bitstream encryption. An unencrypted bitstream on an SD card can be reverse-engineered to extract the RTL netlist.

---

## Common Boot Pitfalls

| Pitfall | Symptom | Root Cause | Fix |
|---|---|---|---|
| **FPGA not configured before driver load** | Bridge driver probes fail | U-Boot SPL loaded kernel before FPGA config was written | Enable FPGA load in U-Boot pre-boot script |
| **DDR timing mismatch** | Kernel panics randomly under load | U-Boot SPL configured wrong DDR parameters for your board | Validate DDR timing against Terasic/Intel reference |
| **HPS hangs when FPGA toggles IO** | HPS freezes on FPGA config | FPGA IOs driven before HPS boot OK, causing contention on shared pins | Set FPGA IOs to weak pull-up during config |
| **Mismatched device trees** | Bridge addresses wrong, DMA crashes | Device tree compiled for different SoC variant | Use exact DTS for your device (not generic socfpga.dtsi) |
| **Bitstream too large for SPI flash** | FPGA fails to configure from flash | Bitstream exceeds flash capacity after compression | Enable bitstream compression in vendor tools |
| **Boot ROM can't find bootloader** | No output on serial console | BSEL/boot pins misconfigured or SD card not partitioned correctly | Verify BSEL strap values; use fdisk to check boot partition type |

---

## Boot Time Optimization

| Technique | Savings | Applies To |
|---|---|---|
| QSPI ×4 flash (vs ×1) | 300→50 ms FPGA config | All Intel SoC FPGAs |
| Bitstream compression | 30–50% size reduction | Xilinx 7-series, UltraScale+ |
| Tandem configuration (PCIe) | Meets 100ms PERST# window | Zynq MPSoC, UltraScale+ |
| Skip DDR training (warm boot) | 100→5 ms if previously calibrated | Intel EMIF fast boot mode |
| HPS early IO release | FPGA can use shared pins sooner | Cyclone V SoC |
| PolarFire instant-on | <1 ms fabric ready | PolarFire, SmartFusion2 |

---

## Cross-References

| Topic | Article |
|---|---|
| Hard CPU coupling models | [Hard Processor Integration](hard_processor_integration.md) |
| AXI bridge initialization | [AXI Bridges & Interconnect](axi_bridges_and_interconnect.md) |
| Memory topology & DDR | [Memory Hierarchy](memory_hierarchy.md) |
| FPGA configuration & bitstream | [Configuration & Bitstream](../infrastructure/configuration.md) |
| PCIe 100ms boot requirement | [PCIe Bringup](../../15_case_studies/pcie_bringup.md) |

---

## References

| Source | Path |
|---|---|
| Cyclone V HPS Boot Guide | Intel FPGA documentation |
| Zynq-7000 Boot and Configuration (UG585, Ch. 6) | Xilinx/AMD |
| MPSoC Boot and Configuration (UG1085, Ch. 11) | Xilinx/AMD |
| PolarFire SoC Boot Guide (UG0820) | Microchip |
| DE10-Nano User Manual | Terasic |
| Linux FPGA Manager Documentation | kernel.org |
| U-Boot README.fpga | U-Boot source tree |
