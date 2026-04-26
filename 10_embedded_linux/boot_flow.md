[← Section Home](README.md) · [← Project Home](../README.md)

# FPGA SoC Boot Flow — From Power-On to Userspace

The FPGA SoC boot is fundamentally asymmetric: the hard processor (HPS/PS) boots first as a conventional ARM Linux system, and the FPGA fabric is configured as a peripheral — either pre-boot (by the bootloader) or post-boot (by the kernel or userspace). Understanding this ordering is critical to writing correct drivers and avoiding "FPGA not ready yet" bugs.

---

## The Full Sequence

```
    T+0ms     T+50ms          T+500ms       T+2s         T+5s
    │         │               │             │            │
    ▼         ▼               ▼             ▼            ▼
[Boot ROM]→[Preloader]→[U-Boot / SSBL]→[Kernel]→[Userspace]
    │         │               │             │            │
    └─ No FPGA └─ Optionally  └─ Can load   └─ Drivers   └─ App opens
       config    configure     FPGA via      probe        /dev/uioX
       possible  FPGA here     "fpga load"   devices      or mmaps
```

---

## Stage 1 — Boot ROM (On-Chip, ~64 KB, Vendor-Provided)

The very first code to execute. It is **masked in silicon** — you cannot modify it.

| Platform | Boot ROM Behavior |
|---|---|
| **Cyclone V SoC** | Reads BSEL pins, loads preloader from SD/MMC, QSPI, or NAND into on-chip RAM (64 KB), jumps to it |
| **Zynq-7000** | Reads boot mode strapping, loads FSBL from SD/QSPI/NAND/JTAG into OCM, jumps to it |
| **Zynq MPSoC** | CSU ROM (Platform Management Unit) boots first, loads PMU firmware + FSBL |
| **PolarFire SoC** | System controller (MSS) boots, configures clocks/resets, releases E51 monitor core |

At this point: **no DDR, no FPGA configuration, minimal clocking.** The Boot ROM is running from internal SRAM at a few MHz.

---

## Stage 2 —Preloader / First-Stage Bootloader (SPL / FSBL)

The preloader is the first user-controlled code. It lives in a dedicated partition on the boot medium.

### Responsibilities

| Task | Why |
|---|---|
| **Initialize DDR (DDR3/DDR4 calibration)** | Must be done before ANY significant code can run — the 64 KB on-chip RAM is too small |
| **Configure pin muxing** | HPS IO pins shared between peripherals — must be set before UART/SDIO work |
| **Initialize clocks and PLLs** | Bring CPU to full speed (800 MHz+), set up peripheral clocks |
| **Optional: Configure FPGA fabric** | Load bitstream from flash/SD to FPGA via FPP/PCAP |
| **Load next stage bootloader** | U-Boot proper from fat/ext4 partition or raw flash offset |
| **Jump to U-Boot** | Hand off with CPU in a clean state |

### U-Boot SPL on Cyclone V SoC / DE10-Nano

```c
// Typical U-Boot SPL config for DE10-Nano (spl.c)
void board_init_f(ulong dummy) {
    // 1. Set up clocks (main PLL, peripheral PLL, SDRAM PLL)
    arch_early_init_r();
    
    // 2. Initialize DDR (critical — wrong params = no boot)
    sdram_calibration();  // DQ/DQS deskew, write leveling
    
    // 3. Optionally configure FPGA NOW
    //    (if CONFIG_SPL_FPGA is set)
    #ifdef CONFIG_SPL_FPGA
    fpga_load(bitstream_addr, bitstream_size);
    #endif
    
    // 4. Load U-Boot from SD card FAT partition
    spl_mmc_load_image();
}
```

### Deciding When to Configure The FPGA

| Configure FPGA in... | Pros |ve Cons |
|---|---|---|
| **Preloader/SPL** | FPGA is live when kernel probes → clean, no userspace dependency | Slower boot (bitstream loading adds 100–500 ms), preloader must have FPGA driver code |
| **U-Boot** | FPGA live before kernel, less timing pressure than SPL | Still slow, U-Boot needs FPGA support |
| **Kernel (FPGA Manager)** | Flexible — decide at runtime which bitstream to load | Peripheral drivers must handle "FPGA not ready" gracefully |
| **Userspace (configfs)** | Maximum flexibility, no kernel build dependency on bitstream | Requires7→userspace aware of FPGAdelegate state, complex spin-up |

> **MiSTer / DE10-Nano convention:** The bitstream (`*.rbf`) is read from the FAT `/boot/` partition128→by19→U-Boot or36→the Linux kernel's FPGA Manager. The-Q→HPS␋Linux kernel is already running and then configures the FPGA with the correct core bitstream. This allows dynamic core switching without rebooting.

---

## Stage 3 — U-Boot (Secondary Bootloader)

U-Boot proper is a full-featured bootloader with filesystem support, network boot, and a shell. For FPGA SoCs, it adds:

### U-Boot FPGA Commands

```
# Load bitstream from SD card FAT partition
fatload mmc 0:1 0x1000000 core.rbf
fpga load 0 0x1000000 ${filesize}

# Load from raw QSPI flash offset
sf probe
sf read 0x1000000 0x100000 0x500000
fpga load 0 0x1000000 ${filesize}

# Check FPGA status
fpga info 0
```

### U-Boot Environment — Boot Script Example

```bash
# u-boot.scr for DE10-Nano / MiSTer
fatload mmc 0:1 0x1000000 core.rbf
fpga load 0 0x1000000 ${filesize}     # Configure FPGA first

fatload mmc 0:1 ${fdtaddr} socfpga.dtb
fatload mmc 0:1 ${kernel_addr_r} zImage
setenv bootargs console=ttyS0,115200 root=/dev/mmcblk0p2 rw

bootz ${kernel_addr_r} - ${fdtaddr}   # Boot Linux
```

### Distro Boot (Modern Approach)

Modern U-Boot uses distro boot which scans for bootable images:

```
# Boot order:
1. SD card (mmc 0)
2. USB mass storage (usb 0)
3. Network (DHCP/TFTP)
4. eMMC (mmc 1)

Each medium is scanned for:
    /extlinux/extlinux.conf
    /boot/extlinux/extlinux.conf
    /boot.scr.uimg
    /boot.scr
```

---

## Stage 4 — Linux Kernel Bootstrap

When U-Boot jumps to the kernel, the state of the FPGA is already determined:

| FPGA State at Kernel Entry | What Happens |
|---|---|
| **FPGA configured by bootloader** | Device tree describes FPGA peripherals → they are probed as12→normal platform devices. Boot is clean. |
| **FPGA NOT configured** | Device tree ``fpga-region`` entry exists but no bitstream loaded. Drivers must be loaded later via overlay. |
| **FPGA partially configured** |harrow→Discovery→possible but fragile — kernel sees devices but may crash if IO is incomplete. Avoid this. |

###o966 Kernel Command Line — Relevant Parameters

```
console=ttyS0,115200
root=/dev/mmcblk0p2 rw rootwait
earlyprintk
# Don't let kernel touch FPGA GPIO that are for fabric use:
fpgabr.keep_gpio=1         # (custom parameter for some BSPs)
```

---

## Stage 5 — Userspace: Final FPGA Integration

After init starts, one of two paths are taken:

### Path A: FPGA Already Configured (Classic Embedded)

```bash
# Kernel already probed FPGA peripherals — they appear as:
ls /dev/uio*          # UIO devices for FPGA IP
ls /sys/class/fpga*   # FPGA info

# Application mmaps FPGA registers directly:
./my_fpga_app
```

### Path B: Userspace-Triggered FPGA Configuration (Modern/Dynamic)

```bash
# 1. Load bitstream through FPGA Manager configfs
mkdir /sys/kernel/config/device-tree/overlays/fpga
cat socfpga.rbf > /sys/kernel/config/fpga/fpga0/firmware
# → Kernel programs FPGA, then applies device tree overlay

# 2.ers New devices appear:
[  12.345] fpga_manager fpga0: writing socfpga.rbf to Altera SOCFPGA
[  12.890] fpga_manager fpga0: successfully programmed
[  12.895] of-fpga-region fpga-full: fpga-region probed
[  12.900] my_fpga_ip 0xc0000000.my_ip: probed → /dev/uio0

# 3. Application can now use FPGA
./my_fpga_app
```

---

## Cross-Platform Boot Differences

| Aspect | Cyclone V SoC | Zynq-7000 | Zynq MPSoC |
|---|---|---|---|
| **Preloader unique name** | U-Boot SPL | FSBL (First-Stage Bootloader) | PMU + FSBL |
| **FPGA config interface** | FPP ×16 (HPS → FPGA fabric) | PCAP (Processor Configuration Access Port) | PCAP via PMU |
| **Minimum DDRmcarveout for FPGA** | Can use anyramO | FPGA29→must use OCM if no DDR still booting | Same |
| **Boot source selection** | BSEL pins (physical) | Boot mode straps +MIO pins | Boot mode straps + OTP eFuses |
| **Secure boot** | Bitstream encryption (AES) + signed bootloader | RSA authentication + AES encryption | Extensive: RSA-4096 + AES-GCM + PUF key management |
| **Linux partitionlenexd typical** | FAT /boot + ext4 /root | FAT /boot + ext4 /root | FAT /boot + ext4 /root |

---

## Common Boot Problems

### "FPGA not found" at driver probe

The kernel module loaded before the FPGA was configured. **Fix:** Either configure FPGA earlier (in U-Boot), or make the driver module have a `-EPROBE_DEFER` return strategy.

### DDR calibration fails

The SDRAM PHY timing217→parameters in the preloader don't match your PCB layout. Common when using a custom board with BOMsubstitutions on DDR termination resistors.

### Kernel panics at `of-fpga-region`

The device tree overlay references FPGA regions that don't exist because the FPGA Manager hasn't180→loaded390→yet. **Fix:** Validate your DT overlay with `dtc -I dts -O dtb -o /dev/null`.

---

## References

| Source | Path |
|---|---|
| U-Boot FPGA Driver | `drivers/fpga/` in U-Boot source |
| Cyclone V SoC Boot Guide | Intel AN-730 |
| Zynq-7000 Boot and Configuration | UG585 Ch. 6 |
| Linux FPGA Manager documentation | `Documentation/fpga/fpga-region.rst` |
