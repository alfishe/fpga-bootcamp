[← Section Home](../../README.md) · [Embedded Linux](../README.md)

# Yocto and PetaLinux Deep Dive

Yocto is the industry standard for building custom, reproducible embedded Linux distributions. For FPGA SoCs, it automates the compilation of U-Boot, the Linux kernel, and the root filesystem while ingesting the device tree and FPGA bitstream produced by Vivado/Quartus. **PetaLinux** is Xilinx's Yocto wrapper — it adds FPGA-aware workflows on top of standard Yocto, but understanding the underlying Yocto/BitBake system is essential for debugging when things go wrong.

---

## Why Yocto for FPGA SoCs?

| Alternative | Problem Yocto Solves |
|---|---|
| **Pre-built SD card image** | Inflexible — can't change kernel config, add packages, or update the bitstream |
| **Hand-built cross-compile** | Fragile, unreproducible — "works on my machine" syndrome |
| **Buildroot** | Simple but monolithic — no package management, no incremental builds |
| **Yocto** | Reproducible, layered, package-managed (.ipk/.rpm), incremental |

Yocto gives you a **software supply chain** for your FPGA SoC: you can track every source revision, every patch, every configuration option, and rebuild the entire system deterministically.

---

## Yocto Architecture

```
┌──────────── Yocto Build System ────────────┐
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  BitBake (Task Scheduler)            │   │
│  │  - Parses .bb recipes                │   │
│  │  - Resolves dependency graph         │   │
│  │  - Executes fetch → compile → pkg    │   │
│  └──────────┬───────────────────────────┘   │
│             │                                │
│  ┌──────────▼───────────────────────────┐   │
│  │  Metadata Layers                     │   │
│  │  ┌──────────────────────────────┐    │   │
│  │  │ meta-xilinx / meta-altera    │    │   │
│  │  │  - FPGA BSP: kernel, u-boot, │    │   │
│  │  │    device-tree, bitstream    │    │   │
│  │  ├──────────────────────────────┤    │   │
│  │  │ meta-openembedded            │    │   │
│  │  │  - Extra packages (python3,  │    │   │
│  │  │    opencv, gstreamer, etc.)  │    │   │
│  │  ├──────────────────────────────┤    │   │
│  │  │ poky / openembedded-core     │    │   │
│  │  │  - Base distro: glibc, bash, │    │   │
│  │  │    coreutils, busybox        │    │   │
│  │  └──────────────────────────────┘    │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Outputs:                                    │
│  ┌──────────┐ ┌────────┐ ┌──────────────┐   │
│  │ boot.bin │ │ uImage │ │ rootfs.tar.gz│   │
│  │ (FSBL +  │ │(kernel)│ │ (packages)   │   │
│  │  FPGA +  │ │        │ │              │   │
│  │  U-Boot) │ │        │ │              │   │
│  └──────────┘ └────────┘ └──────────────┘   │
└─────────────────────────────────────────────┘
```

---

## PetaLinux vs Pure Yocto

PetaLinux is Xilinx's tool that generates and wraps a Yocto build. It is NOT an alternative to Yocto — it IS Yocto, with Xilinx-specific templates and a simplified CLI.

| Aspect | Pure Yocto | PetaLinux |
|---|---|---|
| **Setup** | Clone poky + meta-xilinx, write `local.conf` + `bblayers.conf` | `petalinux-create -t project` |
| **Configuration** | Edit `local.conf`, run `bitbake -c menuconfig` | `petalinux-config` (ncurses menu) |
| **Kernel config** | `bitbake -c menuconfig virtual/kernel` | `petalinux-config -c kernel` |
| **Build** | `bitbake petalinux-image-minimal` | `petalinux-build` |
| **Package output** | `.ipk` / `.rpm` in `tmp/deploy/` | `petalinux-package --boot` |
| **Debugging** | Full Yocto visibility, can inspect task logs | Abstracts away Yocto internals — harder to debug |
| **CI/CD integration** | Native — just shell scripts calling `bitbake` | Awkward — PetaLinux expects interactive terminal |
| **Best for** | Production builds, CI/CD, multi-developer teams | Quick prototypes, single-developer exploration |

**Recommendation:** Start with PetaLinux to get a working system fast, then graduate to pure Yocto for production. PetaLinux's abstraction becomes a liability when you need to customize deeply or integrate with CI.

---

## FPGA Bitstream Integration

Both Yocto and PetaLinux need the FPGA bitstream (`.bit`) and hardware handoff (`.xsa` / `.hdf`) from Vivado to generate:
- **First Stage Bootloader (FSBL)** — initializes PS clocks, DDR, loads bitstream
- **Device Tree Blob (DTB)** — describes AXI peripherals in the PL
- **U-Boot** — with FPGA manager support for post-boot reconfiguration

```
Vivado Export (.xsa)
      │
      ├─→ PetaLinux: petalinux-config --get-hw-description=../hw/export.xsa
      │   → generates: FSBL, device-tree, U-Boot config
      │
      └─→ Pure Yocto: meta-xilinx-tools layer extracts .xsa into DTG (Device Tree Generator)
          → bitbake virtual/bootloader, bitbake virtual/kernel
```

---

## Minimal .bb Recipe Example

```bitbake
# recipes-myapp/myapp/myapp_1.0.bb
SUMMARY = "FPGA register reader"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ada698e0bcf0836ecb27c94fc14d"

SRC_URI = "file://fpga_reader.c \
           file://Makefile"

S = "${WORKDIR}"

do_compile() {
    oe_runmake
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 fpga_reader ${D}${bindir}
}
```

This compiles a C program (`fpga_reader`) and installs it into `/usr/bin` on the root filesystem.

---

## Best Practices

1. **Pin all layer revisions with `repo` manifests** — Yocto layers move fast. Without pinned SHAs, your build will break when upstream updates.
2. **Use `meta-xilinx-tools` for hardware handoff** — it automates the `.xsa` → FSBL/DT/PMUFW generation that's error-prone to do manually.
3. **Separate your customizations into `meta-<project>`** — never modify `meta-xilinx` or `poky` directly. Your custom layer contains `.bbappend` files, patches, and config fragments.
4. **Use `INHERIT += "rm_work"` to save disk space** — Yocto's `tmp/work/` directory can exceed 100 GB. `rm_work` deletes intermediate build artifacts after packaging.
5. **Cache the `downloads/` and `sstate-cache/` directories** — they contain all source tarballs and shared-state objects. A cold build is 4+ hours; a warm build with cached sstate is 15 minutes.

## Pitfalls

1. **sstate-cache invalidation.** Modifying a recipe's source without bumping `PR` (package revision) means Yocto uses the old cached output. Symptom: your code changes don't appear on the target. Fix: `bitbake -c cleansstate <recipe>`.
2. **`petalinux-build` is not `bitbake`.** PetaLinux wraps `bitbake` but doesn't expose all options. When a PetaLinux build fails with a cryptic error, drop into the `build/` directory and run `bitbake` directly to see the real error.
3. **Layer compatibility.** `meta-xilinx` has branches matching Yocto releases (honister, kirkstone, langdale, mickledore...). Mismatched layer branches produce opaque parse errors. Always match the branch to your `poky` release.
4. **Bitstream version drift.** If you update the FPGA design but forget to re-export the `.xsa` and rebuild FSBL/DT, the device tree will describe peripherals that don't exist (or miss ones that do). Linux will boot but PL drivers will probe-fail silently.
5. **Disk space.** A full Yocto build with `meta-xilinx` needs 80–120 GB. Build on a machine with at least 200 GB free and 16 GB RAM.

---

## References

| Source | Description |
|---|---|
| Yocto Project Documentation | https://docs.yoctoproject.org |
| PetaLinux User Guide (UG1144) | https://docs.xilinx.com/r/en-US/ug1144-petalinux-tools-reference-guide |
| meta-xilinx layer | https://github.com/Xilinx/meta-xilinx |
| meta-altera layer | https://github.com/altera-opensource/meta-intel-fpga |
| BitBake User Manual | https://docs.yoctoproject.org/bitbake/ |
