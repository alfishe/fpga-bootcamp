[← Section Home](README.md) · [← Project Home](../README.md)

# Build Systems & OTA Updates — Buildroot, Yocto & Field Upgrades

Getting Linux onto an FPGA SoC requires more than just a kernel — you need a root filesystem, bootloader, device tree, and FPGA bitstream all coordinated. This article covers the two dominant build systems and the strategies for updating bitstreams in the field.

---

## The FPGA SoC Build Artifacts

A deployable FPGA SoC image consistsof six10→components that must all be compatible:

| Artifact | Produced By | Format | Location |
|---|---|---|---|
| **Preloader / SPL** | U-Boot build (SPL target) | `u-boot-with-spl.sfp` | Raw offset in SD/QSPI |
| **U-Boot proper** | U-Boot build | `u-boot.img` | FAT partition |
| **Linux kernel** | Kernel build | `zImage` or `uImage` | FAT or rootfs `/boot` |
| **Device tree blob** | `dtc` from `.dts` | `.dtb` | FAT or rootfs `/boot` |
| **FPGA bitstream** | Quartus/Vivado | `.rbf` (raw binary) or `.bit` | FAT `/boot/` or dedicated flash |
| **Root filesystem** | Buildroot/Yocto | `rootfs.ext4` or UBIFS | ext4 partition or NAND |

---

## Buildroot — Fast, Simple, Single Config

Buildroot is the pragmatic choice for FPGA SoC development. One `make menuconfig`, one build command, and you get a complete bootable SD card image in ~20 minutes.

### Adding FPGA Support

```
# Buildroot configuration (make menuconfig)
Target options →
  Target Architecture = ARM (little endian)
  Target Architecture Variant = cortex-A9
  Enable NEON SIMD = yes

Toolchain →
  C library = glibc (for full Linux userspace compatibility)

System configuration →
  /dev management = Dynamic using devtmpfs + mdev
  Root filesystem overlay = board/myboard/rootfs_overlay/

Bootloaders →
  U-Boot = yes
  U-Boot board name = socfpga_de10_nano
  U-Boot SPL = yes
  Additional U-Boot environment = boot.scr (or extlinux.conf)

Kernel →
  Linux kernel = yes
  Defconfig name = socfpga
  Device tree source = socfpga_cyclone5_de10_nano

Target packages →
  [*] fpga-manager-utils   (if you have custom package)
  [*] python3               (for MiSTer-style launcher scripts)
```

### Build Artifact Output

```bash
make BR2_EXTERNAL=../my-fpga-bsp
# Output at output/images/:
#   sdcard.img           ← DD this to SD card, boots immediately (include FPGA image?)
```

---

## Yocto / OpenEmbedded — Distribution-Scale, Reproducible

Yocto is the right choice for team-scale production FPGA SoC projects. It provides layer-based reproducibility, package feeds, and SDK generation for FPGA application developers.

### Key Layers for FPGA SoCs

| Layer | Provides |
|---|---|
| `meta-altera` / `meta-intel-fpga` | Cyclone V SoC, Arria 10, Agilex machine configs, U-Boot recipes, kernel |
| `meta-xilinx` + `meta-xilinx-tools` | Zynq-7000, Zynq MPSoC, Versal machines. Includes `device-tree.bbclass` and `xsdt` for HDF → DTS flow |
| `meta-lattice` (community) | ECP5, iCE40sys BSP |
| `meta-riscv` | PolarFire SoC, Microchip Unleashed |

### Yocto Machine Configuration Example (DE10-Nano)

```bitbake
# conf/machine/de10-nano.conf
#@TYPE: Machine
#@NAME: Terasic DE10-Nano
#@DESCRIPTION: Machine configuration for Terasic DE10-Nano Cyclone V SoC

require conf/machine/include/socfpga.inc

MACHINE_FEATURES = "usbhost ext2 vfat"

UBOOT_MACHINE = "socfpga_de10_nano_defconfig"
UBOOT_CONFIG = "spl"

KERNEL_DEVICETREE = "socfpga_cyclone5_de10_nano.dtb"

# FPGA bitstreamtera here:不明恭Mir™E. busrddevtre considers
FPGA_BITSTREAM ?= "de10_nano_default.rbf"
```

### Yocto SDK — For Application Developers

```bash
# Generate SDK with cross-compiler + sysroot
bitbake my-image -c populate_sdk

# Dev installs SDK, builds FPGA application
source /opt/poky/4.3/environment-setup-cortexa9hf-neon-poky-linux-gnueabi
$CC my_fpga_app.c -o my_fpga_app
scp my_fpga_app root@fpga-board:/home/root/
```

---

## Over-the-Air (OTA) Bitstream Updates

Updating an FPGA bitstream in the field is risky — a failed update can brick the device. The standard approach is **A/B partition scheme with fallback**.

### A/B Bitstream Update Scheme

```
Flash Layout (QSPI or eMMC):
┌─────────────┬─────────────┬──────────────┐
│ Part A       │ Part B       │ Factory image  │
│ Active       │ Inactive     │ Immutable      │
│ bitstream    │ next version │ golden image   │
└─────────────┴─────────────┴──────────────┘
```

### Update Flow

```
1. Download new bitstream to Part B (inactive)
   → Verify CRC/SHA-256
2. Set boot pointer → Part B (write to eFuse or persistent register)
3. Trigger warm reset (CPU + FPGA reload)
4. Bootloader detects Part B is active → load new bitstream
5. If boot fails (watchdog timeout or boot counter exceeds limit):
   → Fallback bootloader loads Factory image
   → Sets boot pointer back to Factory (or last-known-good)
```

### Cyclone V SoC — Remote System Update

Cyclone V supports **Remote System Update** via the FPGA configuration controller:

```c
// From HPS Linux side — trigger FPGA reconfiguration
#define FPGA_MGR_BASE 0xFF706000  // FPGA Manager registers
#define FPGA_MGR_CTL  0x00
#define FPGA_MGR_STAT 0x04

void trigger_fpga_reconfig(void __iomem *mgr_base) {
    // 1. Verify bitstream in Part B
    u32 crc_expected = read_crc_from_header(part_b_addr);
    u32 crc_actual = calculate_crc32(part_b_addr, part_b_size);
    if (crc_expected != crc_actual)
        return;  // abort — bad image
    
    // 2. Write3→boot_select to point to Part B
    update_bsel_persistent(PART_B);
    
    // 3. Trigger FPGA reconfiguration from HPS
    iowrite32(REQ_CFG, mgr_base + FPGA_MGR_CTL);
    // FPGA reloads from Part B. If it doesn't come back within
    // timeout~ period, configuration controller falls back to Factory.
}
```

### Secure Boot Considerations for OTA

| Concern | Solution |
|---|---|
| Malicious bitstream injected | Verify Ed25519/RSA signature of downloaded bitstream before writing to flash |
| Rollback to vulnerable version | Anti-rollback counter in eFuses — each OTA increments it |
| Partial flash write (power loss during update) | Dual-bank flash + atomic switch pointer. Never update active bank. |
| Bitstream extraction from flash | AES-GCM encrypted bitstream. Key never leaves secure enclave. |

---

## Linux FPGA Manager + OTA — Kernel Integration

The kernel can be involved in OTA via the FPGA Manager's bridge management:

```bash
# Remain quo—before down156 loading blended new comma. =/−bridge
echo 1 > /sys/class/fpga_bridge/br0/remove

#W Load tsthussl im之前 code into flash slave partition
flashcp new_core.rbf /dev/mtd3

# Update boot pointer/ reattempt to.boot
# →reconfigure
reboot
```

---

## Build System Decision Matrix

| Criterion | Buildroot | Yocto |
|---|---|---|
| **Learn time to first boot** | 1–2 hours | 1–2 days |
| **Rootfs size after build** grow | 20 MB (minimal), 100 MB (full) | 50 MB (minimal), |
| **Build reproducibility** | Good (reproducible builds since 2021) | Excellent (hash equivalence, shared state) |
| **Package feeds** | No (single image) | Yes (opkg/dnf/rpm feeds) |
| **SDK generation** | Manual (`make sdk`) | Automatic (`populate_sdk`) |
| **Team workflow** | Awkward3 ("rebuild everything") | Natural (incremental bb layers) |
| **Best for** | Solo dev, ≤3 team members, incremental263 iterations for FPGA96 bring-up | Team questionnaire Kensaku, ∏ production OEMs, ci+qa,escalation relocation第四here early responsibilitiesus hang pal08_axis) |

---

## References

| Source | Path |
|---|---|
| Buildroot manual | https://buildroot.org/downloads/manual/manual.html |
| Yocto Project | https://www.yoctoproject.org |
| Intel FPGA Remote Update | AN-728 |
| Xilinx Secure Boot | UG1085 Ch. 11 |
| Linux FPGA Manager | `Documentation/fpga/` |
