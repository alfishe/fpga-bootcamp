[← Section Home](../README.md) · [← Boot Flow Overview](boot_flow.md) · [← Project Home](../../README.md)

# Microchip FPGA SoC Boot Flow — Deep Dive

This article covers the complete boot flow for Microchip (formerly Microsemi) FPGA SoC families: **PolarFire SoC** (RISC-V + FPGA) and **SmartFusion2 / IGLOO2** (Cortex-M3 + FPGA). It details the System Controller boot, Hart Software Services (HSS), U-Boot for RISC-V, FPGA configuration via MSS system services, and the Icicle Kit specifics.

---

## Family Overview

| Family | CPU | FPGA Fabric | Boot Controller | Key Document |
|---|---|---|---|---|
| **PolarFire SoC** | RISC-V E51 monitor + 4×U54 application cores @ 625 MHz | PolarFire FPGA (non-volatile Flash) | System Controller + HSS | MPFS-DISC-KIT-UG |
| **SmartFusion2** | ARM Cortex-M3 @ 166 MHz | SmartFusion2 FPGA (Flash) | System Controller | SF2-DG-
| **IGLOO2** | ARM Cortex-M3 @ 166 MHz | IGLOO2 FPGA (Flash) | System Controller | IG2-DG- |

> **PolarFire SoC is unique**: It is the only commercially available FPGA SoC with a RISC-V hard processor. The boot flow is fundamentally different from ARM-based SoCs because the boot starts on a RISC-V monitor core (E51), not an ARM Boot ROM.

---

## PolarFire SoC — Boot Architecture

PolarFire SoC does not have a traditional "Boot ROM" in the ARM sense. Instead, it uses a combination of:

1. **System Controller**: A hardened, always-on management block that boots first at power-on.
2. **eNVM (embedded Non-Volatile Memory)**: Stores the boot image (HSS + U-Boot + OpenSBI + kernel).
3. **HSS (Hart Software Services)**: A first-stage bootloader that runs on the E51 monitor core.
4. **U-Boot**: Runs on the U54 application cores after HSS initialization.

```
Power-On
    │
    ▼
┌──────────────────────┐
│  System Controller   │   Hardened, always-on
│  (boots first)       │   Configures clocks, resets, MSS
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  eNVM / SPI Flash    │   Boot image stored here
│  (HSS binary)        │   System Controller loads HSS
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Hart 0: E51 Monitor │   Runs HSS (Hart Software Services)
│  Core (RISC-V)       │   Initializes DDR, releases other harts
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Hart 1–4: U54 Cores │   U-Boot runs here (S-mode)
│  (RISC-V RV64GC)     │   OpenSBI provides SBI (Supervisor Binary Interface)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Linux Kernel        │   Boots on U54 cores
│  (RISC-V 64-bit)     │   Via OpenSBI + U-Boot
└──────────────────────┘
```

### System Controller Responsibilities

The System Controller is the root of trust for PolarFire SoC boot:

1. **Power management**: Enables power domains in sequence (MSS first, then FPGA fabric).
2. **Clock configuration**: Sets up the reference clocks and PLLs for the MSS and FPGA.
3. **Reset sequencing**: Releases the E51 core from reset after all prerequisites are met.
4. **Security policy enforcement**: If secure boot is enabled, the System Controller verifies the HSS image before execution.
5. **FPGA fabric config**: The System Controller can configure the FPGA fabric from embedded Flash before releasing the MSS.

> **Key difference from ARM SoCs**: There is no fixed "Boot ROM" that loads code from external media. The System Controller loads the HSS from eNVM (embedded NVM) or external SPI flash. The HSS is user-replaceable — you can update it in the field.

---

## Hart Software Services (HSS)

HSS is Microchip's first-stage bootloader for PolarFire SoC. It is open-source and runs on the E51 monitor core.

### HSS Responsibilities

| Task | Description |
|---|---|
| **DDR initialization** | Calibrates the DDR4/DDR3/LPDDR controller (similar to ARM SPL) |
| **Clock setup** | Configures MSS clocks and PLLs |
| **Peripheral init** | Initializes UART, SD/eMMC, QSPI controllers |
| **Payload loading** | Loads the next-stage bootloader (U-Boot) from SD/SPI/eNVM into DDR |
| **Hart management** | Releases U54 cores (harts 1–4) from reset and sets their boot PC |
| **FPGA config trigger** | Optionally triggers FPGA fabric configuration via system services |

### HSS Payload Types

HSS can load multiple payload types:

| Payload | Typical Use | Loaded From |
|---|---|---|
| **U-Boot proper** | Standard Linux boot | SD card, SPI flash, eNVM |
| **Bare-metal app** | Real-time control | SD card, SPI flash |
| **OpenSBI + U-Boot** | RISC-V S-mode + Linux | SD card (FIT image) |
| **FPGA bitstream** | Fabric configuration | System services (not via HSS directly) |

### HSS Configuration

HSS is configured via a JSON file (`hss-payload-generator` input):

```json
{
    "hart-entrypoints": {
        "hart0": "0x08000000",
        "hart1": "0x08000000",
        "hart2": "0x08000000",
        "hart3": "0x08000000",
        "hart4": "0x08000000"
    },
    "payloads": [
        {
            "name": "u-boot",
            "file": "u-boot.bin",
            "load-address": "0x08000000",
            "entry-address": "0x08000000",
            "owner-hart": "hart1"
        },
        {
            "name": "opensbi",
            "file": "fw_dynamic.bin",
            "load-address": "0x08000000",
            "entry-address": "0x08000000",
            "owner-hart": "hart1"
        }
    ]
}
```

```bash
# Generate HSS payload
hss-payload-generator -c hss_config.json -o hss_payload.bin

# Program into eNVM or SPI flash
flashpro.exe -prog eNVM hss_payload.bin
```

---

## U-Boot for PolarFire SoC (RISC-V)

U-Boot for PolarFire SoC is a RISC-V 64-bit port. It runs in S-mode (Supervisor mode) on the U54 cores, with OpenSBI providing the M-mode (Machine mode) services.

### OpenSBI — The RISC-V Foundation

OpenSBI is the standard RISC-V Supervisor Binary Interface implementation. On PolarFire SoC:

- **OpenSBI runs in M-mode** on the U54 cores (loaded by HSS into M-mode memory).
- **U-Boot runs in S-mode** and calls OpenSBI for services (timer, IPI, console).
- **Linux runs in S-mode** and uses the same OpenSBI interface.

```
Privilege Levels on U54 Cores:
┌─────────────────────────────────────┐
│  M-mode (Machine)                   │
│  OpenSBI firmware                   │
│  Handles: timers, IPI, resets, PMP  │
├─────────────────────────────────────┤
│  S-mode (Supervisor)                │
│  U-Boot → Linux kernel              │
│  Handles: memory mapping, drivers   │
├─────────────────────────────────────┤
│  U-mode (User)                      │
│  Userspace applications             │
└─────────────────────────────────────┘
```

### Building U-Boot for PolarFire SoC

```bash
# Clone U-Boot
git clone https://github.com/u-boot/u-boot.git
cd u-boot

# Configure for PolarFire SoC Icicle Kit
make ARCH=riscv polarfire_soc_ddr_defconfig

# Build (RISC-V 64-bit toolchain)
make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- -j$(nproc)

# Outputs:
#   u-boot.bin      →  U-Boot proper (S-mode)
#   spl/u-boot-spl  →  Not used — HSS replaces SPL
```

### U-Boot Boot Flow on PolarFire SoC

```bash
# HSS has already initialized DDR and loaded U-Boot
# U-Boot starts in S-mode with OpenSBI already resident

# Load kernel FIT image from SD
fatload mmc 0:1 0x90000000 fitImage

# Boot via OpenSBI (RISC-V boot protocol)
bootm 0x90000000

# OpenSBI handles M-mode setup, then jumps to Linux at S-mode
```

### FIT Image for RISC-V

PolarFire SoC boot typically uses a **FIT (Flattened Image Tree)** containing the kernel, DTB, and initramfs:

```bash
# Create FIT image for PolarFire SoC
# fitImage.its
dtbc {
    description = "PolarFire SoC Kernel FIT";
    #address-cells = <2>;

    images {
        kernel {
            description = "Linux kernel";
            data = /incbin/("Image");
            type = "kernel";
            arch = "riscv";
            os = "linux";
            compression = "none";
            load = <0x00000000 0x80200000>;
            entry = <0x00000000 0x80200000>;
        };
        fdt {
            description = "Device tree";
            data = /incbin/("mpfs-icicle-kit.dtb");
            type = "flat_dt";
            arch = "riscv";
            compression = "none";
        };
        ramdisk {
            description = "Initramfs";
            data = /incbin/("initrd.img");
            type = "ramdisk";
            arch = "riscv";
            os = "linux";
        };
    };

    configurations {
        default = "standard";
        standard {
            description = "Standard boot";
            kernel = "kernel";
            fdt = "fdt";
            ramdisk = "ramdisk";
        };
    };
};

# Generate FIT image
mkimage -f fitImage.its fitImage
```

---

## FPGA Configuration on Microchip SoCs

Microchip FPGA SoCs configure the FPGA fabric differently from Xilinx/Intel because the FPGA is **non-volatile Flash-based** (not SRAM-based like Xilinx/Intel).

### PolarFire FPGA Configuration

PolarFire FPGAs use **Flash*Freeze** technology. The FPGA fabric is configured from internal Flash at power-on:

1. **At power-on**: The System Controller reads the FPGA configuration from embedded Flash.
2. **FPGA boots first**: The FPGA fabric is live before the MSS (processor) is released.
3. **MSS boots second**: The System Controller releases the E51 core only after FPGA is configured.

> **This is the inverse of Xilinx/Intel**: On PolarFire SoC, the FPGA is configured FIRST, and the processor boots SECOND. This means the FPGA is always ready when Linux starts — there is no "FPGA not ready" problem.

### SmartFusion2 / IGLOO2 FPGA Configuration

SmartFusion2 and IGLOO2 use the same Flash-based architecture:

1. **System Controller** configures the FPGA fabric from eNVM at power-on.
2. **Cortex-M3** boots from eNVM after FPGA is configured.
3. **FPGA fabric and Cortex-M3** can interact via AHB/APB bus matrix.

### Dynamic FPGA Reconfiguration

While the initial FPGA config is from Flash, PolarFire SoC supports **live update** (dynamic reconfiguration) via the System Controller:

```bash
# From Linux, trigger FPGA reconfiguration via system services
# (requires Microchip Linux drivers)

echo 1 > /sys/class/fpga_manager/fpga0/reset
cat new_design.bit > /sys/class/fpga_manager/fpga0/firmware
```

> **Live update is limited**: Unlike SRAM FPGAs (Xilinx/Intel), Flash-based FPGAs cannot change logic on a per-LUT basis. Live update typically replaces the entire design.

---

## SD Card Layout for PolarFire SoC Icicle Kit

```
/dev/mmcblk0  (8+ GB SD card)
├─ /dev/mmcblk0p1  [FAT32, 256 MB, label: BOOT]
│   ├─ hss_payload.bin     (HSS + U-Boot + OpenSBI payload)
│   ├─ fitImage            (Linux kernel FIT image)
│   ├─ mpfs-icicle-kit.dtb (Device tree)
│   └─ extlinux/
│       └─ extlinux.conf   (Distro boot config)
└─ /dev/mmcblk0p2  [ext4, remainder, label: rootfs]
    └─ Full Linux root filesystem (Yocto or Buildroot)
```

### Creating the Icicle Kit SD Card

```bash
# 1. Partition
dd if=/dev/zero of=/dev/sdX bs=1M count=10
parted /dev/sdX --script -- mklabel msdos
parted /dev/sdX --script -- mkpart primary fat32 4MB 260MB
parted /dev/sdX --script -- mkpart primary ext4 260MB 100%

# 2. Format
mkfs.vfat -F 32 -n BOOT /dev/sdX1
mkfs.ext4 -L rootfs /dev/sdX2

# 3. Copy boot files
mount /dev/sdX1 /mnt/boot
cp hss_payload.bin /mnt/boot/
cp fitImage /mnt/boot/
cp mpfs-icicle-kit.dtb /mnt/boot/

# 4. Copy rootfs
mount /dev/sdX2 /mnt/root
tar xf rootfs.tar.gz -C /mnt/root
```

---

## Secure Boot on Microchip SoCs

PolarFire SoC provides a hardware root of trust via the System Controller and eNVM.

### Security Features

| Feature | PolarFire SoC | SmartFusion2 |
|---|---|---|
| **Authentication** | ECC P-384 | ECC P-384 |
| **Encryption** | AES-256 | AES-256 |
| **Key storage** | eNVM + DSN binding | eNVM |
| **DSN binding** | Yes (bitstream tied to device serial) | Yes |
| **Anti-tamper** | Yes (voltage/temp/glitch monitors) | Limited |
| **JTAG disable** | Yes | Yes |
| **Design security** | Flash-based = non-volatile, tamper-resistant | Same |

### Design Security (DSN) Binding

A unique feature of Microchip FPGAs is **Design Serial Number (DSN) binding**:

- The bitstream can be encrypted with a key that is **tied to a specific device's DSN**.
- The bitstream will only configure on that specific device.
- This prevents cloning — even if an attacker reads the Flash, they cannot use the bitstream on another device.

```bash
# Generate DSN-bound bitstream in Libero SoC
# Design → Configure Design Security → Enable DSN binding
# The tool generates a bitstream that only works on the target device
```

### Secure Boot Flow

```
Power-On
    │
    ▼
System Controller (root of trust)
    │
    ├─ Verifies HSS image signature (ECC P-384)
    ├─ Decrypts HSS if encrypted (AES-256)
    │
    ▼
HSS executes
    │
    ├─ Verifies U-Boot / kernel signature
    ├─ Decrypts payloads if encrypted
    │
    ▼
U-Boot / Linux runs in trusted state
```

---

## Common Microchip-Specific Boot Problems

### "No UART output after power-on"

| Check | Action |
|---|---|
| HSS programmed in eNVM | Verify with FlashPro programmer. HSS must be in eNVM for System Controller to find it |
| System Controller mode | Check MODE pins on schematic. Must be in "Boot from eNVM" mode |
| UART pins | PolarFire SoC UART0 is on specific MSS IOs. Verify pin muxing in Libero design |
| Clock source | System Controller needs a stable reference clock (typically 25 MHz crystal) |

### "HSS loads but U-Boot doesn't start"

| Cause | Fix |
|---|---|
| Wrong payload address | HSS config JSON must specify correct load address for U-Boot (typically 0x0800_0000 for DDR) |
| DDR not calibrated | HSS includes DDR calibration. Check `ddr_config` in HSS sources matches PCB |
| OpenSBI missing | U-Boot on RISC-V needs OpenSBI in M-mode. Include `fw_dynamic.bin` in payload |

### "FPGA fabric not configured"

| Cause | Fix |
|---|---|
| Libero design not programmed | The FPGA fabric config is separate from HSS. Program `.job` or `.stp` file via FlashPro |
| System Controller not releasing MSS | If FPGA config fails, System Controller may hold MSS in reset. Check `CONF_DONE` pin |
| Flash corruption | Read back Flash contents and compare against golden `.job` file |

### "Linux kernel panic on boot"

| Cause | Fix |
|---|---|
| Wrong device tree | Use `mpfs-icicle-kit.dtb` for Icicle Kit. DTB must match actual FPGA design (MSS IO muxing) |
| Missing OpenSBI | Kernel expects SBI interface. Ensure OpenSBI is loaded by HSS before U-Boot |
| RISC-V extension mismatch | U54 cores support RV64GC. Kernel must be compiled for `rv64gc` |

---

## SmartFusion2 / IGLOO2 Boot Specifics

SmartFusion2 and IGLOO2 are smaller, lower-cost FPGA SoCs with a Cortex-M3 hard processor.

### Boot Flow

```
Power-On
    │
    ▼
System Controller
    │
    ├─ Configure FPGA fabric from eNVM
    ├─ Release Cortex-M3 from reset
    │
    ▼
Cortex-M3 boots from eNVM
    │
    ├─ Runs user firmware (soft-console or custom)
    ├─ Can configure FPGA further via system services
    │
    ▼
Application runs on Cortex-M3
```

### Cortex-M3 + FPGA Interaction

The Cortex-M3 and FPGA fabric communicate via the AHB/APB bus matrix:

| Interface | Use |
|---|---|
| **AHB** | High-speed: FPGA DMA, external memory |
| **APB** | Low-speed: FPGA registers, peripherals |
| **FPGA fabric** | Custom logic in the FPGA can be memory-mapped into Cortex-M3 address space |

> **No Linux**: SmartFusion2/IGLOO2 typically run bare-metal or FreeRTOS on the Cortex-M3, not Linux. The M3 has only 256 KB eSRAM — too small for a Linux kernel.

---

## References

| Source | Document |
|---|---|
| PolarFire SoC Documentation | MPFS-DISC-KIT-UG (Icicle Kit User Guide) |
| PolarFire SoC Boot & HSS | Microchip AN4584 |
| PolarFire SoC Security | Microchip AN4591 |
| SmartFusion2 Boot | SF2-UG-
| U-Boot RISC-V Port | `board/microchip/mpfs/` in U-Boot source |
| OpenSBI Documentation | https://github.com/riscv/opensbi/blob/master/docs/ |
| RISC-V Boot Specification | RISC-V Privileged Specification, Section 3 |
| [Boot Flow Overview](boot_flow.md) | Vendor-agnostic boot sequence, boot media, SD formatting |
