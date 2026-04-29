[← Section Home](../../README.md) · [Embedded Linux](../README.md)

# Buildroot for FPGA SoCs

Buildroot is a simple, efficient tool for generating embedded Linux systems through cross-compilation. Unlike Yocto's complex dependency graph and layer model, Buildroot uses standard GNU Make and Kconfig — the same configuration system used by the Linux kernel. For FPGA SoC projects that need a quick, reproducible root filesystem without Yocto's learning curve and disk requirements, Buildroot is the pragmatic choice.

---

## Buildroot vs Yocto: When to Use Which

| Criterion | Buildroot | Yocto |
|---|---|---|
| **Learning curve** | Low — `make menuconfig`, `make` | High — BitBake, layers, recipes, tasks |
| **Build speed** | Fast (monolithic, single-pass) | Slower (per-package builds) |
| **Incremental builds** | Limited (rebuilds affected packages) | Full (per-task sstate-cache) |
| **Package management** | None — monolithic rootfs | `.ipk`/`.rpm` — OTA-updatable |
| **Disk space** | ~15 GB | 80–120 GB |
| **Customization depth** | Moderate — config fragments, patches | Deep — `.bbappend`, overlays, distro policies |
| **CI/CD friendliness** | Excellent — just `make` | Good — with sstate mirror setup |
| **Best for** | Fixed-function embedded FPGA systems | Products needing OTA updates, package management |

**Rule of thumb:** If your FPGA SoC runs one application and never needs remote package updates, use Buildroot. If it needs a Debian-like package ecosystem with OTA updates, use Yocto.

---

## Buildroot Architecture

```
┌──────────── Buildroot ────────────┐
│  make menuconfig                  │
│  ┌────────────────────────────┐   │
│  │  Kconfig (.config)          │   │
│  │  - Target arch (ARM, RISC-V)│   │
│  │  - Toolchain (internal/BSP) │   │
│  │  - Packages (dropbear, etc) │   │
│  │  - Filesystem type (ext4)   │   │
│  └───────────┬────────────────┘   │
│              │                    │
│  make        ▼                    │
│  ┌────────────────────────────┐   │
│  │  Single-Pass Build          │   │
│  │  1. Download sources        │   │
│  │  2. Build host tools        │   │
│  │  3. Build cross-toolchain   │   │
│  │  4. Build target packages   │   │
│  │  5. Assemble rootfs          │   │
│  │  6. Create image (ext4/cpio)│   │
│  └───────────┬────────────────┘   │
│              ▼                    │
│  output/images/                   │
│  ├── rootfs.ext4                  │
│  ├── rootfs.tar                   │
│  ├── zImage / uImage              │
│  └── *.dtb                        │
└───────────────────────────────────┘
```

---

## BR2_EXTERNAL: Keeping Your Board Config Separate

The `BR2_EXTERNAL` mechanism lets you maintain your FPGA board's Buildroot configuration outside the main Buildroot tree — essential for version control and reproducibility.

```bash
# First use: create external tree
git clone https://git.buildroot.net/buildroot
make BR2_EXTERNAL=../my-fpga-boards myboard_defconfig

# Subsequent builds: Buildroot remembers the BR2_EXTERNAL path
cd buildroot
make myboard_defconfig
make
```

External tree structure:
```
my-fpga-boards/
├── external.mk           # Extra make targets
├── external.desc         # Name + description
├── configs/
│   └── myboard_defconfig # Board default config
├── board/
│   └── myboard/
│       ├── linux.config       # Kernel config fragment
│       ├── u-boot.fragment    # U-Boot config fragment
│       ├── genimage.cfg       # SD card layout
│       └── post-build.sh      # Post-build hook
├── package/
│   └── my-fpga-app/           # Custom FPGA application package
└── patches/
    └── linux/                 # Kernel patches
```

---

## FPGA-Specific Configuration

### Toolchain for ARM SoCs (Zynq-7000, Cyclone V)

```
Target options → Target Architecture: ARM (little endian)
Target options → Target Architecture Variant: cortex-A9
Target options → Enable VFP extension: yes
Target options → Enable NEON SIMD: yes
Toolchain → C library: glibc (or musl for smaller footprint)
```

### Toolchain for RISC-V SoCs (PolarFire SoC)

```
Target options → Target Architecture: RISCV
Target options → Target Architecture Variant: RV64IMAFDC
Target options → MMU support: yes
```

### Kernel Configuration

```
Kernel → Linux Kernel: yes
Kernel → Defconfig name: xilinx_zynq (or multi_v7 for broader support)
Kernel → Kernel binary format: uImage
Kernel → Load address: 0x00008000 (Zynq-7000)
Kernel → Device Tree Source file paths:
    board/myboard/zynq-myboard.dts
```

### FPGA Bitstream Loading

Buildroot doesn't directly ingest `.xsa` like PetaLinux. Instead, include the bitstream as an overlay file and load it via U-Boot or the Linux FPGA Manager:

```bash
# In board/myboard/post-build.sh
cp ${BINARIES_DIR}/../hw/design_1_wrapper.bit ${BINARIES_DIR}/
```

---

## Minimal defconfig Example (Zynq-7000)

```makefile
# Architecture
BR2_arm=y
BR2_cortex_a9=y
BR2_ARM_ENABLE_VFP=y
BR2_ARM_ENABLE_NEON=y

# Toolchain
BR2_TOOLCHAIN_BUILDROOT_GLIBC=y
BR2_TOOLCHAIN_BUILDROOT_CXX=y

# System
BR2_TARGET_GENERIC_HOSTNAME="zynq-fpga"
BR2_TARGET_GENERIC_ISSUE="Welcome to Zynq FPGA"
BR2_ROOTFS_OVERLAY="board/myboard/overlay"
BR2_ROOTFS_POST_BUILD_SCRIPT="board/myboard/post-build.sh"

# Kernel
BR2_LINUX_KERNEL=y
BR2_LINUX_KERNEL_CUSTOM_VERSION=y
BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.1.70"
BR2_LINUX_KERNEL_DEFCONFIG="xilinx_zynq"
BR2_LINUX_KERNEL_UIMAGE=y
BR2_LINUX_KERNEL_UIMAGE_LOADADDR="0x00008000"
BR2_LINUX_KERNEL_DTS_SUPPORT=y
BR2_LINUX_KERNEL_INTREE_DTS_NAME="zynq-zybo-z7"

# U-Boot
BR2_TARGET_UBOOT=y
BR2_TARGET_UBOOT_BUILD_SYSTEM_KCONFIG=y
BR2_TARGET_UBOOT_BOARD_DEFCONFIG="zynq_zybo_z7"
BR2_TARGET_UBOOT_FORMAT_IMG=y
BR2_TARGET_UBOOT_SPL=y

# Packages
BR2_PACKAGE_DROPBEAR=y
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_I2C_TOOLS=y
BR2_PACKAGE_ETHTOOL=y

# Filesystem
BR2_TARGET_ROOTFS_EXT2=y
BR2_TARGET_ROOTFS_EXT2_4=y
BR2_TARGET_ROOTFS_EXT2_SIZE="512M"
BR2_TARGET_ROOTFS_TAR=y
```

---

## Best Practices

1. **Use `BR2_EXTERNAL` from day one** — never modify the Buildroot tree directly. Your external tree is your board's entire build definition in version control.
2. **Pin the Buildroot version** — Buildroot has quarterly releases (2024.02, 2024.05...). Use a tagged release, not `master`, for reproducible builds.
3. **Use `BR2_ROOTFS_OVERLAY` for FPGA bitstream and startup scripts** — drop your `.bit` file and `/etc/init.d/` scripts into the overlay directory instead of creating packages.
4. **Enable `BR2_CCACHE=y`** — ccache dramatically speeds up rebuilds after `make clean`. Only the first build is slow.
5. **Buildroot for fixed-function, Yocto for products with OTA** — if your FPGA SoC ships to customers who'll install updates, Yocto's package management is worth the complexity.

## Pitfalls

1. **No package manager = no OTA updates.** Buildroot produces a monolithic root filesystem. To update a single package in the field, you must replace the entire rootfs. For products needing incremental updates, use Yocto.
2. **`make clean` is destructive.** It wipes the entire `output/` directory including the downloaded sources. Use `make <package>-reconfigure` for targeted rebuilds.
3. **Kernel and U-Boot version coupling.** Buildroot's default kernel and U-Boot versions may not match your FPGA vendor's BSP. Always pin specific versions (e.g., `BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="6.1.70"`).
4. **Device tree mismatch.** Buildroot uses the kernel's in-tree DTS by default. If your board has a custom PL design, you must provide an out-of-tree DTS (`BR2_LINUX_KERNEL_CUSTOM_DTS_PATH`).
5. **No hardware handoff integration.** Unlike PetaLinux/Yocto with `meta-xilinx-tools`, Buildroot doesn't auto-generate FSBL or PMUFW from `.xsa`. You must build these externally (via XSCT or pre-built binaries) and include them manually.

---

## References

| Source | Description |
|---|---|
| Buildroot User Manual | https://buildroot.org/downloads/manual/manual.html |
| Buildroot BR2_EXTERNAL guide | https://buildroot.org/downloads/manual/manual.html#outside-br-custom |
| Zynq Buildroot example | https://github.com/buildroot/buildroot/tree/master/configs/zynq_zybo_z7_defconfig |
| PolarFire SoC Buildroot | https://github.com/linux4microchip/buildroot-external-microchip |
| genimage (SD card layout) | https://github.com/pengutronix/genimage |
