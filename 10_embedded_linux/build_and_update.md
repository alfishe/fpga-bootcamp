[← Section Home](README.md) · [← Project Home](../README.md)

# Build Systems & OTA Updates — Buildroot, Yocto & Field Upgrades

Getting Linux onto an FPGA SoC requires more than just a kernel — you need a root filesystem, bootloader, device tree, and FPGA bitstream all coordinated. This article covers the two dominant build systems and the strategies for updating bitstreams in the field.

---

## The FPGA SoC Build Artifacts

A deployable FPGA SoC image consists of six components that must all be compatible:

| Artifact | Produced By | Format | Typical Location |
|---|---|---|---|
| **Preloader / SPL** | U-Boot build (SPL target) | `u-boot-with-spl.sfp` | Raw offset in SD/QSPI |
| **U-Boot proper** | U-Boot build | `u-boot.img` | FAT partition `/boot/` |
| **Linux kernel** | Kernel build | `zImage` or `uImage` | FAT partition `/boot/` |
| **Device tree blob** | `dtc` from `.dts` | `.dtb` | FAT partition `/boot/` |
| **FPGA bitstream** | Quartus/Vivado | `.rbf` (raw binary) or `.bit` | FAT `/boot/` or dedicated flash partition |
| **Root filesystem** | Buildroot/Yocto | `rootfs.ext4` or UBIFS | ext4 partition or NAND |

---

## Buildroot — Fast, Simple, Single Config

Buildroot is the pragmatic choice for FPGA SoC development. One `make menuconfig`, one build command, and you get a complete bootable SD card image in ~20 minutes (after the first full build).

### Adding FPGA Support — Key Config Options

```
# Buildroot configuration (make menuconfig)
Target options ->
  Target Architecture = ARM (little endian)
  Target Architecture Variant = cortex-A9
  Enable NEON SIMD = yes

Toolchain ->
  C library = glibc (for full Linux userspace compatibility)

System configuration ->
  /dev management = Dynamic using devtmpfs + mdev
  Root filesystem overlay directories = board/myboard/rootfs_overlay/

Bootloaders ->
  U-Boot = yes
  U-Boot board name = socfpga_de10_nano
  U-Boot SPL = yes

Kernel ->
  Linux kernel = yes
  Defconfig name = socfpga
  Device tree source = socfpga_cyclone5_de10_nano
  [*] Build a Device Tree Blob (DTB)

Target packages ->
  [*] Hardware handling -> fpga-manager-utils (custom package)
  [*] Interpreter languages -> python3 (for MiSTer-style scripts)
```

### Build and Deploy

```bash
make BR2_EXTERNAL=../my-fpga-bsp

# Output at output/images/:
#   sdcard.img       <- DD this to SD card, boots immediately
#   zImage           <- kernel
#   socfpga_cyclone5_de10_nano.dtb  <- device tree
#   u-boot-with-spl.sfp  <- preloader + U-Boot
#   rootfs.ext4      <- root filesystem
```

**Buildroot strengths for FPGA:**
- Single `defconfig` captures the entire build
- Fast iteration: `make linux-rebuild` for kernel-only changes
- Small rootfs: 20 MB minimal, 100 MB with full userspace
- Ideal for solo developers and small teams

---

## Yocto / OpenEmbedded — Distribution-Scale, Reproducible

Yocto is the right choice for team-scale production FPGA SoC projects. It provides layer-based reproducibility, package feeds (opkg/dnf), and SDK generation for application developers.

### Key Layers for FPGA SoCs

| Layer | Provides |
|---|---|
| `meta-altera` / `meta-intel-fpga` | Cyclone V SoC, Arria 10, Agilex machine configs, U-Boot recipes, kernel |
| `meta-xilinx` + `meta-xilinx-tools` | Zynq-7000, Zynq MPSoC, Versal machines. Includes `device-tree.bbclass` and `xsdt` for HDF -> DTS flow |
| `meta-lattice` (community) | ECP5, iCE40 BSP support |
| `meta-riscv` | PolarFire SoC, Microchip Icicle Kit |
| `meta-openembedded` | General embedded packages (required by vendor layers) |

### Yocto Machine Configuration Example (DE10-Nano)

```bitbake
# conf/machine/de10-nano.conf
#@TYPE: Machine
#@NAME: Terasic DE10-Nano
#@DESCRIPTION: Machine configuration for Terasic DE10-Nano (Cyclone V SoC)

require conf/machine/include/socfpga.inc

MACHINE_FEATURES = "usbhost ext2 vfat"

UBOOT_MACHINE = "socfpga_de10_nano_defconfig"
UBOOT_CONFIG = "spl"

KERNEL_DEVICETREE = "socfpga_cyclone5_de10_nano.dtb"

# FPGA bitstream: placed in /boot/ by a custom recipe
FPGA_BITSTREAM ?= "de10_nano_default.rbf"
```

### Yocto SDK — For Application Developers

```bash
# Generate SDK with cross-compiler + sysroot
bitbake my-image -c populate_sdk

# Developer installs SDK, builds FPGA application
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
┌─────────────┬─────────────┬──────────────────┐
│  Partition A  │  Partition B  │  Factory (golden) │
│  Active       │  Inactive     │  Immutable        │
│  bitstream    │  next version │  fallback image   │
└─────────────┴─────────────┴──────────────────┘
```

### Update Flow

```
1. Download new bitstream to Partition B (inactive)
   -> Verify CRC32 or SHA-256
2. Set boot pointer -> Partition B (persistent register or eFuse)
3. Trigger warm reset (CPU + FPGA reload)
4. Bootloader detects Partition B is active -> load new bitstream
5. If boot fails (watchdog timeout or boot counter exceeds limit):
   -> Fallback bootloader loads Factory image
   -> Sets boot pointer back to Factory (or last-known-good)
```

### Cyclone V SoC — Remote System Update

Cyclone V supports **Remote System Update** via the FPGA configuration controller:

```c
// From HPS Linux side — trigger FPGA reconfiguration
#define FPGA_MGR_BASE 0xFF706000  // FPGA Manager registers

void trigger_fpga_reconfig(void __iomem *mgr_base) {
    // 1. Verify bitstream integrity in Partition B
    u32 crc_expected = read_crc_from_rbf_header(part_b_addr);
    u32 crc_actual   = calculate_crc32(part_b_addr, part_b_size);
    if (crc_expected != crc_actual)
        return;  // abort — corrupted image

    // 2. Write boot_select to point to Partition B
    update_boot_select_persistent(PART_B);

    // 3. Trigger FPGA reconfiguration from HPS
    iowrite32(CFG_REQ, mgr_base + FPGA_MGR_CTL);
    // FPGA reloads from Partition B. If it doesn't come back within
    // the watchdog timeout, configuration controller falls back
    // to the Factory (golden) image.
}
```

### Xilinx Zynq — MultiBoot and Fallback

Zynq-7000 uses **MultiBoot** for A/B updates. The boot ROM reads the MultiBoot register to determine which bitstream to load:

```bash
# Program the MultiBoot register to point to the golden image
# This is set once during manufacturing and never changed
program_flash -offset 0x00000000 -file golden.bin

# Update image is written to a separate flash offset
program_flash -offset 0x01000000 -file update_v2.bin
# The MultiBoot register is updated to point here for the next boot
```

### Secure Boot Considerations for OTA

| Concern | Solution |
|---|---|
| Malicious bitstream injected | Verify Ed25519/RSA signature before writing to flash. Reject unsigned or bad-signature images. |
| Rollback to vulnerable version | Anti-rollback counter in eFuses — each OTA increments it. Bootloader refuses to load images with counter below the eFuse value. |
| Partial flash write (power loss) | Dual-bank flash + atomic switch pointer. Never update the active bank — write to inactive, verify, then switch. |
| Bitstream extraction from flash | AES-GCM encrypted bitstream. Decryption key never leaves secure enclave (HPS secure RAM or TPM). |

---

## Linux FPGA Manager + OTA — Kernel Integration

The kernel's FPGA Manager subsystem supports OTA workflows via bridge control and status reporting:

```bash
# 1. Disable FPGA bridges before reconfiguration
echo 1 > /sys/class/fpga_bridge/hps2fpga/remove
echo 1 > /sys/class/fpga_bridge/fpga2hps/remove

# 2. Write new bitstream to inactive flash partition
flashcp new_core.rbf /dev/mtd3

# 3. Update boot pointer and reboot into new FPGA image
fw_setenv boot_part B
reboot
```

---

## Build System Decision Matrix

| Criterion | Buildroot | Yocto |
|---|---|---|
| **Time to first boot** | 1–2 hours | 1–2 days |
| **Rootfs size** | 20 MB (minimal), 100 MB (full) | 50 MB (minimal), 200 MB+ (full) |
| **Build reproducibility** | Good (reproducible builds since 2021) | Excellent (hash equivalence, shared state cache) |
| **Package feeds** | No (single image) | Yes (opkg / dnf / rpm feeds) |
| **SDK generation** | Manual (`make sdk`) | Automatic (`populate_sdk` with sysroot) |
| **Team workflow** | "Rebuild everything" per change | Incremental per-layer builds; multiple machines from one tree |
| **Best for** | Solo dev, ≤3 team members, fast FPGA bring-up iterations | Production teams, CI/CD pipelines, multi-product OEMs, long-term maintenance |

---

## References

| Source | Target |
|---|---|
| Buildroot manual | https://buildroot.org/downloads/manual/manual.html |
| Yocto Project | https://www.yoctoproject.org |
| Intel FPGA Remote Update | AN-728: Remote System Update for Intel FPGAs |
| Xilinx MultiBoot | UG585 Chapter 6: Boot and Configuration |
| Xilinx Secure Boot | UG1085 Chapter 11: Security |
| Linux FPGA Manager | `Documentation/fpga/` in kernel source |
| [boot_flow.md](boot_flow.md) | Boot sequence — where build artifacts fit in the boot chain |
| [device_tree_and_overlays.md](device_tree_and_overlays.md) | DT overlays for runtime FPGA reconfiguration |
