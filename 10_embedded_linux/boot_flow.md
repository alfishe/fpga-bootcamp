[← Section Home](README.md) · [← Project Home](../README.md)

# FPGA SoC Boot Flow — From Power-On to Userspace

> [!IMPORTANT]
> The FPGA SoC boot is fundamentally asymmetric: the hard processor (HPS/PS/MSS) boots first as a conventional embedded Linux system, and the FPGA fabric is configured as a peripheral — either pre-boot (by the bootloader) or post-boot (by the kernel or userspace). Understanding this ordering is critical to writing correct drivers and avoiding "FPGA not ready yet" bugs.

This article covers the **vendor-agnostic common boot flow**: what is invariant across all FPGA SoCs, boot media options, SD card formatting, when to configure the FPGA, physical strapping, secure boot fundamentals, and common failure modes. For per-vendor, per-family deep dives, see the linked sub-articles at the end.

---

## The Universal Boot Sequence

Every FPGA SoC boots through the same five canonical stages. The names change per vendor, but the function is invariant.

```
    T+0ms           T+20–100ms              T+200ms–1s          T+1–3s        T+3–10s
    │                │                         │                  │              │
    ▼                ▼                         ▼                  ▼              ▼
[Boot ROM]  →  [SPL / FSBL / HSS]  →  [U-Boot / SSBL]  →  [Kernel]  →  [Userspace]
    │                │                         │                  │              │
    │                │                         │                  │              │
    ├─ Mask ROM      ├─ First user code        ├─ Full bootloader ├─ Linux       ├─ init + apps
    ├─ ~32–256 KB    ├─ Initializes DDR        ├─ Filesystems     ├─ Drivers     ├─ FPGA access
    ├─ Fixed clock   ├─ Pin mux + PLLs         ├─ Network boot    ├─ Device tree ├─ Dynamic config
    ├─ Loads SPL     ├─ MAY configure FPGA     ├─ Shell + script  ├─ FPGA Manager└─ via UIO/mmap
    └─ Jumps to it   └─ Loads U-Boot           └─ Loads kernel    └─ Mounts root
```

### What Is Invariant Across All Vendors

| Invariant | Why It Never Changes |
|---|---|
| **Boot ROM is read-only silicon** | Masked at manufacturing — vendor provides the first stage. You cannot patch bugs in Boot ROM |
| **Boot ROM runs from internal SRAM/OCM** | No external DRAM is initialized yet. The Boot ROM operates from on-chip memory at a slow clock (typically 10–50 MHz) |
| **SPL/FSBL initializes DDR before anything large runs** | DDR calibration (DQ/DQS deskew, write leveling) is the first hardware-dependent step. Wrong parameters = silent boot hang |
| **U-Boot (or equivalent) is the last bootloader before the kernel** | Vendor-specific first-stage loaders always hand off to a common second-stage like U-Boot, which then loads Linux |
| **FPGA fabric is optional at every stage before the kernel** | The processor subsystem can boot Linux without the FPGA ever being configured. The FPGA is always a peripheral, never a boot dependency |
| **Device tree describes the hardware the kernel will see** | Whether the FPGA is pre-configured or not, the device tree must match the actual hardware state at kernel probe time |

---

## Boot Media — Complete Options Matrix

FPGA SoCs support multiple boot media. The Boot ROM's supported media list is fixed in silicon — you cannot add new media types after the chip is manufactured.

| Media | Typical Bandwidth | Max Size (Boot ROM limit) | Supported By | Development? | Production? | Notes |
|---|---|---|---|---|---|---|
| **SD/MMC (SD card)** | 25 MB/s (SDR50) – 104 MB/s (SDR104) | 2–16 GB (no practical limit) | All vendors | Excellent | Good for low-volume | Most common for dev boards. Boot ROM reads raw blocks or FAT partition |
| **eMMC** | 200–400 MB/s (HS400) | 4–128 GB | Xilinx Zynq, Intel Agilex, some Microchip | Good | Excellent | Soldered-down, industrial temp range. Boot ROM reads from boot partition |
| **SPI NOR Flash** | 10–50 MB/s (QSPI) | 16–512 Mb (2–64 MB) | Intel Cyclone V/MAX 10, Microchip, Lattice | Good | Excellent for small bitstreams | Stores preloader + U-Boot + small bitstream. Too small for large Linux rootfs |
| **QSPI NOR Flash** | 50–133 MB/s (quad) | 128 Mb–2 Gb (16–256 MB) | Xilinx Zynq-7000/MPSoC, Intel Agilex | Good | Excellent | Most common production boot for Xilinx. `sf read` in U-Boot |
| **NAND Flash** | 20–40 MB/s | 1–8 GB (SLC/MLC) | Xilinx Zynq-7000, Intel (some families) | Poor | Good for cost-sensitive | Requires bad-block management. Boot ROM may skip BBT |
| **EEPROM / I2C** | 0.4–3.4 Mb/s | 256 Kb–4 Mb | Some CPLD+MCU devices (MAX 10) | N/A | N/A | Used for factory config or fallback, not primary Linux boot |
| **JTAG** | 1–10 MB/s (depends on adapter) | Unlimited (streamed) | All vendors | Excellent | N/A (manufacturing only) | Used for initial board bring-up and debugging. Boot ROM ignores JTAG unless explicitly selected |
| **USB (mass storage / RNDIS)** | 40 MB/s (USB 2.0) – 500 MB/s (USB 3.0) | Unlimited | Xilinx Zynq MPSoC, Intel Agilex | Good | Poor | USB boot is typically for recovery or manufacturing, not field deployment |
| **Network (TFTP / NFS / HTTP)** | 10–1000 Mb/s | Unlimited | All (via U-Boot, not Boot ROM) | Excellent | Poor (requires network infra) | U-Boot loads kernel/DTB over network. Boot ROM rarely supports direct network boot |

### Boot ROM vs U-Boot Media Support

| Stage | Cyclone V Boot ROM | Zynq-7000 Boot ROM | Zynq MPSoC Boot ROM | PolarFire SoC Boot ROM |
|---|---|---|---|---|
| **SD/MMC** | Yes (SDR25) | Yes (SDR25/SDR50) | Yes (SDR50/SDR104) | Yes |
| **eMMC** | No | Yes | Yes | Yes |
| **QSPI** | Yes | Yes | Yes | Yes |
| **NAND** | Yes | Yes | No | No |
| **USB** | No | No | Yes (USB 2.0/3.0) | No |
| **JTAG** | Yes | Yes | Yes | Yes |
| **Ethernet** | No | No | No | No (U-Boot only) |

> **Key insight**: The Boot ROM only needs to load the SPL/FSBL (typically 100–500 KB). U-Boot then takes over and can load from any medium U-Boot drivers support — including network, USB, NVMe, SATA, etc. This decouples Boot ROM limitations from actual boot flexibility.

---

## SD Card Formatting Deep Dive

SD card is the most common boot medium for development. Getting the partition layout right is critical — Boot ROMs are picky about partition types, alignment, and filesystems.

### Partition Layout — The "Standard" FPGA SoC SD Card

```
Disk: /dev/mmcblk0  (8–32 GB SD card)
┌─────────────────┬─────────────────┬─────────────────────────────────────┐
│  Partition 1    │  Partition 2    │  Partition 3 (optional)             │
│  FAT32 /boot    │  ext4 /root     │  ext4 /data or swap                 │
│  ~256–512 MB    │  Remainder      │  Remainder                          │
│                 │                 │                                     │
│  Files:         │  Files:         │                                     │
│  - preloader    │  - /bin, /lib   │                                     │
│  - u-boot.img   │  - /etc, /usr   │                                     │
│  - zImage/uImage│  - /home        │                                     │
│  - .dtb         │  - /var         │                                     │
│  - .rbf/.bit    │  - /tmp         │                                     │
│  - boot.scr     │                 │                                     │
│  - extlinux.conf│                 │                                     │
└─────────────────┴─────────────────┴─────────────────────────────────────┘
```

### MBR vs GPT

| Scheme | Boot ROM Support | When to Use |
|---|---|---|
| **MBR** (Master Boot Record) | Universal — every FPGA Boot ROM understands MBR | Default choice. All legacy and current Boot ROMs parse MBR partition tables without issue |
| **GPT** (GUID Partition Table) | Zynq MPSoC, Intel Agilex, some newer families | Use if you need >4 primary partitions or >2 TB disks. Older Boot ROMs (Cyclone V, Zynq-7000) may fail to boot from GPT |

> **Cyclone V SoC caveat**: The Boot ROM reads the preloader from a **raw partition** (no filesystem) at a fixed offset or from a FAT partition. MBR is required. GPT is not supported by the Cyclone V Boot ROM.

### Creating a Bootable SD Card from Scratch

#### Linux

```bash
# 1. Identify the SD card device (BE CAREFUL — /dev/sdX not /dev/sda!)
lsblk
# Assume /dev/sdX

# 2. Create MBR partition table
sudo parted /dev/sdX --script -- mklabel msdos

# 3. Create FAT32 /boot partition (256 MB, aligned to 4 MB for erase block)
sudo parted /dev/sdX --script -- mkpart primary fat32 4MB 260MB

# 4. Create ext4 /root partition (remainder of disk)
sudo parted /dev/sdX --script -- mkpart primary ext4 260MB 100%

# 5. Format partitions
sudo mkfs.vfat -F 32 -n BOOT /dev/sdX1
sudo mkfs.ext4 -L rootfs /dev/sdX2

# 6. Verify partition alignment
sudo parted /dev/sdX align-check optimal 1
sudo parted /dev/sdX align-check optimal 2
```

#### Windows (using Rufus + manual steps)

1. Use Rufus to create a bootable drive with "Non-bootable" option (Boot ROM doesn't need MBR boot code)
2. Create a 256 MB FAT32 partition for `/boot`
3. Create a second partition with remaining space (format as ext4 using WSL2 or Paragon extFS)

#### macOS

```bash
# 1. Identify disk (e.g., /dev/disk2)
diskutil list

# 2. Unmount and partition
diskutil unmountDisk /dev/disk2
sudo diskutil partitionDisk /dev/disk2 MBR \
  FAT32 BOOT 256M \
  ExFAT ROOT R

# Note: macOS cannot natively create ext4. Use a Linux VM or Docker:
docker run --rm -it --device=/dev/disk2:/dev/sdX alpine sh
# Then run the Linux mkfs.ext4 commands inside the container
```

### What Files Go Where

| File | Partition | Path | Description |
|---|---|---|---|
| **Preloader / SPL** | Raw offset or FAT | `/A2/` or raw LBA 0x8000 | First-stage bootloader. Cyclone V uses `preloader-mkpimage.bin` at raw offset. Xilinx Zynq uses `boot.bin` on FAT |
| **U-Boot proper** | FAT | `/u-boot.img` or `/boot/u-boot.img` | Second-stage bootloader. Loaded by SPL from FAT partition |
| **Device Tree Blob** | FAT | `/socfpga.dtb` or `/devicetree.dtb` | Hardware description for the kernel. Must match the configured FPGA |
| **Kernel** | FAT | `/zImage` or `/Image` | Compressed or uncompressed Linux kernel |
| **Bitstream** | FAT | `/core.rbf` or `/system.bit` | FPGA configuration file. Loaded by U-Boot or kernel FPGA Manager |
| **Boot script** | FAT | `/boot.scr` or `/extlinux/extlinux.conf` | U-Boot boot commands or distro boot configuration |
| **Root filesystem** | ext4 | `/bin`, `/lib`, `/etc`, ... | Full Linux rootfs — can be Buildroot, Yocto, or Debian |

### Verifying the SD Card

```bash
# Check partition table
sudo fdisk -l /dev/sdX

# Verify FAT partition contents
sudo mkdir -p /mnt/boot
sudo mount /dev/sdX1 /mnt/boot
ls -la /mnt/boot/

# Verify first few blocks for preloader signature (Cyclone V)
sudo dd if=/dev/sdX bs=512 skip=0 count=1 | hexdump -C | head

# Check ext4 filesystem
sudo e2fsck -n /dev/sdX2
```

---

## When to Configure The FPGA — Decision Framework

The single most important architectural decision in an FPGA SoC system is **when the FPGA fabric gets configured**. This choice affects boot time, driver complexity, and system flexibility.

```
Boot Time Impact:
┌──────────────────────────────────────────────────────────────┐
│ SPL config    ████████████████████  +100–500 ms              │
│ U-Boot config ████████████          +50–200 ms               │
│ Kernel config ██████                +20–100 ms               │
│ Userspace     ██                    +10–50 ms (but deferred) │
└──────────────────────────────────────────────────────────────┘
```

| Configure FPGA in... | Boot Time | Driver Complexity | Flexibility | Best For |
|---|---|---|---|---|
| **SPL / Preloader** | Slowest (+100–500 ms) | Simplest — kernel sees all devices at probe time | None — fixed bitstream at build time | Production systems with single known bitstream, fastest driver bring-up |
| **U-Boot** | Slow (+50–200 ms) | Simple — same as SPL but U-Boot has more FPGA loading tools | Low — bitstream chosen at U-Boot build time | Most common production choice. Balance of early availability and U-Boot tooling |
| **Kernel (FPGA Manager)** | Medium (+20–100 ms) | Moderate — drivers must handle `-EPROBE_DEFER` | High — bitstream can be chosen per-boot via DT overlay | Multi-personality systems (MiSTer), A/B bitstream updates, development |
| **Userspace (configfs)** | Fastest boot, deferred config | Highest — full hotplug handling required | Maximum — runtime bitstream swap without reboot | Dynamic reconfiguration (core switching), cloud-FPGA, adaptive workloads |

### Per-Vendor FPGA Configuration Interface

| Vendor | Interface | How It Works | Bitstream Format | Compression |
|---|---|---|---|---|
| **Intel/Altera** | FPP x16 (Cyclone V), HPS-to-FPGA bridge (Arria 10/Agilex), AVST (Agilex) | HPS writes bitstream bytes to a dedicated config port | `.rbf` (Raw Binary File), `.periph.rbf`, `.core.rbf` | Supported (RLE) |
| **Xilinx** | PCAP (Processor Configuration Access Port) | CPU writes to PCAP registers; PCAP DMA streams bitstream to config logic | `.bit` (with header), `.bin` (raw, no header) | Supported (GZIP) |
| **Microchip** | System services via MSS | System controller manages FPGA config via internal bus | `.job`, `.fpga_design.bin` | Supported |
| **Lattice** | SPI/JTAG via soft core or external flash | Typically external SPI flash boots FPGA; soft CPU may reconfig | `.bit`, `.jed` | Limited |

---

## Boot Source Selection — Physical Strapping

Every FPGA SoC has physical pins or switches that tell the Boot ROM where to look for the first-stage bootloader. These are sampled at power-on reset and cannot be changed without a power cycle.

### Intel/Altera — BSEL Pins

| BSEL[2:0] | Boot Source | Cyclone V | Arria 10 | Agilex |
|---|---|---|---|---|
| `000` | Reserved | — | — | — |
| `001` | FPGA (internal) | — | — | — |
| `010` | NAND flash | Yes | No | No |
| `011` | SD/MMC | Yes | Yes | Yes |
| `100` | QSPI flash | Yes | Yes | Yes |
| `101` | eMMC | No | Yes | Yes |
| `110` | JTAG / UART | Yes | Yes | Yes |
| `111` | External (FPGA-configured) | Yes | No | No |

> BSEL pins are typically on dedicated IO pins with internal pull-ups/pull-downs. Schematic review is critical — wrong BSEL = Boot ROM looks in the wrong place and hangs silently.

### Xilinx Zynq — Boot Mode Register

Zynq-7000 and Zynq MPSoC use a combination of **boot mode straps** (resistors on MIO pins) and **eFuse/OTP** settings.

| Mode | MIO[5:3] ( straps) | MIO[2] (width) | Description |
|---|---|---|---|
| JTAG | `000` | X | Debug only. Boot ROM enters JTAG mode |
| QSPI | `001` | 0=single, 1=quad | Boot from QSPI NOR flash |
| NOR | `010` | X | Boot from parallel NOR (rare) |
| NAND | `011` | X | Boot from NAND flash |
| SD0 | `100` | X | Boot from SD card (MIO 40–45) |
| SD1 | `101` | X | Boot from eMMC/SD (MIO 46–51) |
| USB | `110` | X | Boot from USB mass storage |
| Ethernet / PCIe | `111` | X | Network boot (MPSoC only) |

> On MPSoC, the **CSU ROM** also reads the **PMU_GLOBAL.BOOT_MODE** register, which can be overridden by the PMU firmware for secure boot flows.

### Microchip PolarFire SoC — System Controller

PolarFire SoC uses the **System Controller** (a dedicated hardened manager) to determine boot source:

| Source | Selection Method | Notes |
|---|---|---|
| **eNVM (embedded NVM)** | System controller default | Factory boot image stored in eNVM |
| **SPI Flash** | External SPI chip select | Most common for development |
| **SD/eMMC** | MSS IO configuration | Selected via Libero SoC design |
| **JTAG** | Debug tool forces mode | For recovery |

Unlike Intel/Xilinx, PolarFire SoC's boot source is partially determined by the **FPGA design itself** (Libero SoC project settings) and partially by external pins. The System Controller releases the E51 monitor core only after initializing clocks and MSS peripherals.

### Reading Current Boot Mode from Software

```bash
# Intel Cyclone V — read sysmgr bootinfo register
cat /sys/kernel/debug/socfpga/bootinfo

# Xilinx Zynq-7000 — read slcr.BOOT_MODE
devmem 0xF800025C  # SLCR BOOT_MODE register

# Xilinx Zynq MPSoC — read CSU boot mode
devmem 0xFF5E0200  # CSU_BOOT_MODE register

# PolarFire SoC — read system controller status via HSS
hss-payload-generator --status
```

---

## Secure Boot Overview

Secure boot on FPGA SoCs is more complex than on a plain processor because there are **two assets to protect**: the bootloader/software chain AND the FPGA bitstream (which may contain proprietary IP).

### Chain of Trust

```
Root of Trust (Hardware)
    │
    ▼
Boot ROM (hashes burned in eFuse)
    │ verifies
    ▼
SPL / FSBL (signed)
    │ verifies
    ▼
U-Boot (signed)
    │ verifies
    ▼
Kernel + DTB (signed)
    │ verifies
    ▼
Bitstream (encrypted + authenticated)
```

### Per-Vendor Secure Boot Feature Matrix

| Feature | Intel Cyclone V | Intel Agilex | Xilinx Zynq-7000 | Xilinx Zynq MPSoC | Microchip PolarFire SoC |
|---|---|---|---|---|---|
| **Bootloader authentication** | RSA-2048 | ECDSA P-384 | RSA-2048 | RSA-4096 | ECC P-384 |
| **Bitstream encryption** | AES-256 | AES-256-GCM | AES-256 | AES-256-GCM | AES-256 |
| **Bitstream authentication** | HMAC-SHA-256 | ECDSA P-384 | RSA-2048 | RSA-4096 | ECC P-384 |
| **Key storage** | eFuse | PUF + eFuse | eFuse | PUF + eFuse | eFuse + DSN binding |
| **Anti-rollback** | No | Yes (Agilex 7) | No | Yes (eFuse counter) | Yes |
| **Debug disable** | JTAG secure mode | Yes | JTAG disable | Full debug lock | Yes |
| **Secure boot doc** | Intel AN-689 | Agilex Security User Guide | UG821 | UG1137 | PolarFire SoC Security |

### Why Secure Boot Matters for FPGA SoCs

1. **Bitstream IP protection**: Your FPGA design is a binary asset. Encryption prevents cloning.
2. **Supply chain integrity**: Authentication ensures only your signed bitstream runs on your hardware.
3. **Root of trust for the system**: If the Boot ROM verifies the SPL, and the SPL verifies U-Boot, the entire system is trustworthy.
4. **Regulatory compliance**: Many industries (automotive, medical, defense) require secure boot.

> **Important**: Secure boot is a one-way door. Once eFuses are programmed, they cannot be reversed. Always test secure boot flows on development units before programming production units.

---

## Common Boot Problems & Diagnostics

### "Silence after power-on" — Boot ROM Hang

**Symptoms**: No UART output, no LEDs, JTAG chain may or may not respond.

| Cause | Diagnosis | Fix |
|---|---|---|
| **Wrong BSEL/boot mode straps** | Measure voltage on boot mode pins with DMM | Fix pull-up/pull-down resistors on schematic. Review `BSEL` truth table |
| **Boot medium not detected** | Logic analyzer on SD/QSPI signals. Check for clock activity | Verify SD card is inserted, QSPI flash is populated, NAND has valid bad block table |
| **Power sequencing failure** | Scope power rails — CPU core may not reach stable voltage before reset release | Check power sequencing IC. Add delay capacitors if needed |
| **Corrupted preloader/Boot ROM image** | `hexdump` first 64 KB of boot medium. Compare against known-good image | Re-write preloader/FSBL to boot medium. Check for flash write errors |

### DDR Calibration Failure

**Symptoms**: SPL starts, prints "DDR calibration..." then hangs or reboots.

| Cause | Diagnosis | Fix |
|---|---|---|
| **Wrong DDR parameters in SPL** | Compare `sdram_config` struct against PCB BOM and DDR datasheet | Regenerate preloader with correct DDR timing (Intel: handoff from QSys. Xilinx: update PS7 init in Vivado) |
| **Missing termination resistors** | Check RZQ and VREF pins on schematic | Populate termination resistors per JEDEC spec. Check for BOM substitutions |
| **Signal integrity issues** | Scope DQS/DQ lines during calibration. Look for reflections or insufficient drive | Adjust drive strength in SPL config. Review PCB layout (length matching, via stubs) |
| **Temperature drift** | Calibration passes at 25C but fails at 0C or 70C | Implement temperature-compensated calibration or use wider timing margins |

### "FPGA not found" at Driver Probe

**Symptoms**: Kernel boots, but `dmesg` shows `fpga-region: probe deferral` or custom driver fails with `-EPROBE_DEFER`.

| Cause | Diagnosis | Fix |
|---|---|---|
| **FPGA not configured yet** | Check `cat /sys/class/fpga_manager/fpga0/state` — shows `unknown` instead of `operating` | Configure FPGA earlier (U-Boot) or make driver handle deferred probe |
| **Device tree mismatch** | `dtc -I fs /proc/device-tree` shows FPGA regions but no compatible devices | Verify DTB matches actual bitstream. Re-compile DTB after bitstream changes |
| **Wrong FPGA Manager driver** | Check loaded modules: `lsmod | grep fpga` | Ensure correct vendor FPGA Manager driver is compiled into kernel or loaded as module |

### Kernel Panic at `of-fpga-region`

**Symptoms**: Kernel panic or oops during device tree overlay application.

| Cause | Fix |
|---|---|
| **Overlay references non-existent FPGA region** | Validate overlay with `dtc -I dts -O dtb -o /dev/null overlay.dts` before loading |
| **Bitstream loaded but region not declared in base DTB** | Add `fpga-region` node to base device tree |
| **Memory carveout conflict** | Check `reserved-memory` node. FPGA DMA buffers must not overlap with Linux memory |

### JTAG Recovery

When all else fails, JTAG is the universal recovery path:

```bash
# Connect JTAG adapter (USB-Blaster, Platform Cable, J-Link)
# Load SPL/U-Boot directly into SRAM via JTAG

# Intel — Quartus Programmer or openocd
openocd -f interface/altera-usb-blaster.cfg -f target/socfpga_cyclone5.cfg

# Xilinx — Vivado HW Manager or openocd
openocd -f interface/ftdi/digilent-hs1.cfg -f target/zynq_7000.cfg

# Microchip — FlashPro or openocd
openocd -f interface/ftdi/flashpro.cfg -f target/polarfire.cfg
```

---

## SoC Family Quick-Reference

| Family | CPU | Boot ROM | FPGA Config | Deep Dive |
|---|---|---|---|---|
| **Cyclone V SoC** | ARM Cortex-A9 dual-core @ 925 MHz | 64 KB, BSEL pins | FPP x16 (HPS → FPGA) | [boot_flow_intel_soc.md](boot_flow_intel_soc.md) |
| **MAX 10** | Nios II soft core or external MCU | 8 KB (config only) | Internal flash | [boot_flow_intel_soc.md](boot_flow_intel_soc.md) |
| **Arria 10 SoC** | ARM Cortex-A9 dual-core @ 1.2 GHz | 128 KB, BSEL pins | HPS-to-FPGA bridge | [boot_flow_intel_soc.md](boot_flow_intel_soc.md) |
| **Agilex 5 SoC** | Dual Cortex-A76 + Dual Cortex-A55 @ 1.8 GHz | 256 KB, BSEL + eFuse | AVST + HPS bridge | [boot_flow_intel_soc.md](boot_flow_intel_soc.md) |
| **Agilex 7 SoC** | Quad-core Cortex-A53 @ 1.5 GHz | 256 KB, BSEL + eFuse | AVST + HPS bridge | [boot_flow_intel_soc.md](boot_flow_intel_soc.md) |
| **Zynq-7000** | ARM Cortex-A9 dual-core @ 1 GHz | 128 KB OCM, mode straps | PCAP | [boot_flow_xilinx_zynq.md](boot_flow_xilinx_zynq.md) |
| **Zynq UltraScale+ MPSoC** | Cortex-A53 quad + R5F dual | 256 KB CSU ROM, mode straps | PCAP via PMU | [boot_flow_xilinx_zynq.md](boot_flow_xilinx_zynq.md) |
| **Versal ACAP** | Cortex-A72 dual + R5F dual | 512 KB PMC ROM | PLM + NoC config | [boot_flow_xilinx_zynq.md](boot_flow_xilinx_zynq.md) |
| **PolarFire SoC** | RISC-V E51 + 4×U54 @ 625 MHz | System controller | MSS system services | [boot_flow_microchip_soc.md](boot_flow_microchip_soc.md) |
| **SmartFusion2/IGLOO2** | Cortex-M3 @ 166 MHz | System controller | MSS system services | [boot_flow_microchip_soc.md](boot_flow_microchip_soc.md) |

---

## References

| Source | Document |
|---|---|
| Intel Cyclone V SoC Boot Guide | Intel AN-730 |
| Intel Arria 10 SoC Boot Guide | Intel AN-728 |
| Intel Agilex Security User Guide | Intel document |
| Xilinx Zynq-7000 Boot and Configuration | UG585, Chapter 6 |
| Xilinx Zynq MPSoC Boot Guide | UG1085, Chapter 11 |
| Xilinx Versal Boot Guide | AM011 |
| Microchip PolarFire SoC Boot | MPFS-DISC-KIT-UG |
| U-Boot FPGA Driver | `drivers/fpga/` in U-Boot source tree |
| Linux FPGA Manager | `Documentation/fpga/` in Linux kernel |
| [boot_flow_intel_soc.md](boot_flow_intel_soc.md) | Intel/Altera FPGA SoC boot deep dive |
| [boot_flow_xilinx_zynq.md](boot_flow_xilinx_zynq.md) | Xilinx Zynq boot deep dive |
| [boot_flow_microchip_soc.md](boot_flow_microchip_soc.md) | Microchip PolarFire/SmartFusion boot deep dive |
