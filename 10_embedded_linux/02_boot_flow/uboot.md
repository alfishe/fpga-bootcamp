[← Section Home](../README.md) · [← Project Home](../../README.md)

# U-Boot on FPGA SoCs — SSBL, FPGA Config, and Boot Scripting

U-Boot ("Das U-Boot") is the **second-stage bootloader (SSBL)** in every FPGA SoC boot chain. After the first-stage loader (SPL/FSBL/HSS) initializes DDR and loads U-Boot into RAM, U-Boot takes over — loading the Linux kernel, providing the device tree, and optionally configuring the FPGA fabric before the kernel ever sees the hardware.

> [!NOTE]
> This article focuses on U-Boot's **FPGA SoC-specific roles**: configuring the fabric, managing cross-domain bridge order, and automating board bring-up. For general U-Boot usage (environment, scripting, networking), see the [U-Boot official documentation](https://docs.u-boot.org/).

---

## U-Boot's Position in the Boot Chain

```
                    ┌──── SPL / FSBL ────┐
                    │  • Boot ROM loads  │
                    │  • Initializes DDR │
                    │  • MAY config FPGA │
                    │  • Loads U-Boot    │
                    └────────┬───────────┘
                             │
                             ▼
                    ┌──── U-Boot (SSBL) ──┐
                    │  • Full bootloader   │
                    │  • Filesystem access │
                    │  • Network (TFTP/NFS)│
                    │  • MAY config FPGA   │
                    │  • Loads kernel+DTB  │
                    └────────┬─────────────┘
                             │
                             ▼
                    ┌──── Linux Kernel ────┐
                    │  • Drivers probe     │
                    │  • FPGA bridges init │
                    │  • Mounts rootfs     │
                    └──────────────────────┘
```

U-Boot is the **last place** where the FPGA can be configured before Linux boots. This is strategically important: if the FPGA is configured in U-Boot, all FPGA bridges are ready when Linux probes them. If not, drivers must handle "FPGA not ready" gracefully.

---

## SPL vs Full U-Boot — What Runs Where

| Stage | Size | Runs From | Capabilities | FPGA Config? |
|---|---|---|---|---|
| **Boot ROM** | 32–256 KB | On-die Mask ROM | Minimal: load next stage from fixed media | No |
| **SPL / FSBL / HSS** | ~64–256 KB | On-chip RAM (OCRAM) | DDR init, pin mux, PLL setup, load U-Boot | **Yes** (some platforms) |
| **U-Boot (SSBL)** | ~400–800 KB | DDR SDRAM | Full: filesystems, network, shell, scripting | **Yes** (most common) |

**Key insight**: SPL runs from small on-chip RAM (typically 64 KB). U-Boot runs from DDR (hundreds of MB available). This is why complex operations — filesystem parsing, network boot, FPGA bitstream loading — happen in U-Boot, not SPL.

---

## FPGA Configuration from U-Boot

U-Boot has a built-in `fpga` command subsystem for loading bitstreams. This is the **most common and recommended** place to configure the FPGA.

### U-Boot FPGA Commands

```
# Load bitstream from FAT partition on SD card
fatload mmc 0:1 ${loadaddr} soc_system.rbf
fpga load 0 ${loadaddr} ${filesize}

# Load from raw SD card partition (no filesystem)
mmc read ${loadaddr} 0x1000 0x8000
fpga load 0 ${loadaddr} 0x1000000

# Load from QSPI flash
sf probe
sf read ${loadaddr} 0x100000 0x800000
fpga load 0 ${loadaddr} 0x800000

# Check FPGA status
fpga info 0
```

### Vendor-Specific FPGA Load

| Vendor / SoC | U-Boot Command | Driver | Notes |
|---|---|---|---|
| **Cyclone V / Arria 10** | `fpga load 0` | `drivers/fpga/socfpga.c` | Uses FPGA Manager bridge. Bitstream = `.rbf` (raw binary) |
| **Zynq-7000** | `fpga load 0` | `drivers/fpga/zynqpl.c` | Uses PCAP (Processor Configuration Access Port). Bitstream = `.bit` or `.bin` |
| **Zynq MPSoC** | `fpga load 0` | `drivers/fpga/zynqmp.c` | Uses PMU firmware for FPGA config. `.bit` or `.bin` |
| **PolarFire SoC** | Not in U-Boot | HSS (Hart Software Services) | FPGA is flash-based. Config happens in HSS stage, not U-Boot |

### When to Configure FPGA: Decision Matrix

| Scenario | Configure In | Reason |
|---|---|---|
| FPGA bridges needed by kernel drivers | **U-Boot** (pre-kernel) | Bridges ready when kernel probes |
| FPGA is optional / hot-pluggable | **Linux** (FPGA Manager) | Kernel handles graceful absence |
| Fastest boot time required | **SPL** (pre-U-Boot) | FPGA config overlaps with DDR training |
| FPGA bitstream too large for SPL OCRAM | **U-Boot** (has DDR) | SPL has 64 KB, bitstreams are MB |
| Secure boot enforced | **SPL** (authenticated) | SPL verifies before loading anything else |
| Multiple FPGA images (A/B) | **U-Boot** (script logic) | U-Boot env selects which bitstream |

---

## U-Boot Device Tree Handling

U-Boot passes a **Device Tree Blob (DTB)** to the Linux kernel. This DTB describes the FPGA bridges, their addresses, and interrupt mappings. Getting it right is critical.

### Three DTB Strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| **Static DTB** | Compile DTB with kernel, always same | Simple, predictable | Can't handle runtime FPGA changes |
| **U-Boot DTB overlay** | U-Boot applies overlay after FPGA config | Flexible, supports multiple FPGA images | Requires U-Boot overlay support (`CONFIG_OF_LIBFDT_OVERLAY`) |
| **Linux device tree overlay** | Kernel loads overlay via configfs after FPGA config | Most flexible, hot-pluggable | Bridges not available during early kernel boot |

### U-Boot → Kernel DTB Handoff

```
U-Boot loads kernel + DTB into RAM:

  ┌─────────────────┐
  │  U-Boot in DDR  │
  │                 │
  │ 1. Load kernel  │──► zImage / Image at ${kernel_addr_r}
  │ 2. Load DTB     │──► .dtb at ${fdt_addr_r}
  │ 3. (Optional)   │──► Apply overlay if FPGA loaded
  │ 4. booti/bootz  │──► Jump to kernel with DTB pointer in r2/x0
  └─────────────────┘
```

**Critical gotcha**: If the DTB declares FPGA bridge nodes (`fpgabridge@ff200000`) but the FPGA hasn't been configured yet, the kernel bridge driver will probe and fail. The fix: either configure FPGA in U-Boot before passing DTB, or use `status = "disabled"` in DTB and enable via overlay after FPGA config.

---

## U-Boot Environment and Scripting

U-Boot stores persistent configuration in its **environment** — typically on SD card, QSPI flash, or eMMC.

### Essential FPGA SoC Environment Variables

```bash
# Boot command — what U-Boot runs automatically
bootcmd=run fpga_boot

# FPGA configuration sequence
fpga_boot=run fpga_load; run bridge_enable; run kernel_boot

# Load FPGA bitstream from SD card FAT partition
fpga_load=fatload mmc 0:1 ${loadaddr} soc_system.rbf; fpga load 0 ${loadaddr} ${filesize}

# Enable HPS-to-FPGA bridges (Intel SoC)
bridge_enable=bridge enable; echo "Bridges enabled"

# Load kernel and DTB, then boot
kernel_boot=fatload mmc 0:1 ${kernel_addr_r} zImage; fatload mmc 0:1 ${fdt_addr_r} socfpga.dtb; bootz ${kernel_addr_r} - ${fdt_addr_r}
```

### U-Boot Script (`boot.scr`)

For complex boot sequences, compile a script:
```bash
# On host: create boot.txt, then:
mkimage -A arm -T script -C none -n "Boot script" -d boot.txt boot.scr

# Place boot.scr on SD card FAT partition.
# U-Boot auto-executes it if found.
```

---

## Board-Specific U-Boot: DE10-Nano (Cyclone V SoC)

### Prebuilt U-Boot (from Terasic / Intel SoC EDS)

```bash
# Default U-Boot files on DE10-Nano SD card FAT partition:
#   u-boot.img          — U-Boot proper (SSBL)
#   u-boot-spl.bin      — Preloader (SPL, loaded by Boot ROM)
#   soc_system.rbf      — FPGA bitstream (optional, U-Boot loads it)
#   socfpga_cyclone5.dtb — Device tree
#   zImage              — Linux kernel
```

### Building U-Boot from Source (for DE10-Nano)

```bash
# Clone and configure
git clone https://github.com/u-boot/u-boot.git
cd u-boot
make socfpga_de10_nano_defconfig

# Customize (optional)
make menuconfig

# Build
make -j$(nproc)

# Output files:
#   spl/u-boot-spl-dtb.bin  → rename to u-boot-spl.bin (put on SD FAT)
#   u-boot.img              → U-Boot proper (put on SD FAT)
```

### DE10-Nano U-Boot Boot Log (Annotated)

```
U-Boot SPL 2024.01 (spl/u-boot-spl-dtb.bin)
DDR: 1 GiB                    ← SPL initialized DDR
Trying to boot from MMC1      ← Loading U-Boot from SD

U-Boot 2024.01
CPU: Altera SoCFPGA Platform
DRAM: 1 GiB
MMC: dwmmc0@ff704000: 0       ← SD card detected

reading soc_system.rbf         ← FPGA bitstream loading
6059620 bytes read in 326 ms (17.7 MiB/s)
FPGA: OK                       ← FPGA configured successfully

reading zImage                 ← Kernel loading
reading socfpga_cyclone5.dtb   ← Device tree
Kernel image @ 0x1000000
FDT image @ 0x2000000

Starting kernel ...            ← Handoff to Linux
```

---

## Cross-Vendor U-Boot Comparison

| Feature | Intel SoCFPGA | Xilinx Zynq-7000 | Xilinx Zynq MPSoC | Microchip PolarFire SoC |
|---|---|---|---|---|
| **SPL name** | U-Boot SPL | FSBL (Xilinx, not U-Boot) | PMU + FSBL | HSS (Hart Software Services) |
| **U-Boot loads** | From SD/eMMC/QSPI | From SD/QSPI/NAND | From SD/eMMC/QSPI | From eMMC/SD (after HSS) |
| **FPGA config** | `fpga load 0` | `fpga load 0` (zynqpl) | `fpga load 0` (zynqmp) | Pre-configured (flash-based FPGA) |
| **Bridge enable** | `bridge enable` | Automatic (AXI) | Automatic (AXI via PMU) | Automatic (coherent matrix) |
| **DTB handoff** | r2 register | r2 register | x0 register | Device tree in HSS |
| **Defconfig prefix** | `socfpga_` | `zynq_` | `xilinx_zynqmp_` | `microchip_mpfs_` |

---

## U-Boot Build Configuration for FPGA SoCs

### Must-Enable Configs

```
# FPGA Manager support
CONFIG_FPGA=y
CONFIG_FPGA_SOCFPGA=y         # Intel
CONFIG_FPGA_ZYNQPL=y          # Zynq-7000
CONFIG_FPGA_ZYNQMPPL=y        # Zynq MPSoC

# Device tree overlays (optional)
CONFIG_OF_LIBFDT_OVERLAY=y

# Environment on SD card FAT
CONFIG_ENV_IS_IN_FAT=y
CONFIG_ENV_FAT_INTERFACE="mmc"
CONFIG_ENV_FAT_DEVICE_AND_PART="0:1"

# Networking for TFTP/NFS boot
CONFIG_NET=y
CONFIG_CMD_DHCP=y
CONFIG_CMD_TFTPBOOT=y
```

---

## Best Practices

1. **Configure FPGA in U-Boot, not SPL** — Unless boot time is the absolute #1 priority. U-Boot has DDR, filesystem access, and better error handling. SPL failures are hard to debug (no serial output).
2. **Use U-Boot script (`boot.scr`), not hardcoded `bootcmd`** — Scripts can be updated on the SD card without recompiling U-Boot. Much faster iteration.
3. **Always have a fallback boot path** — If FPGA config fails in U-Boot, boot Linux anyway with `status = "disabled"` bridges. A board that doesn't boot at all is worse than a board with a missing FPGA bridge.
4. **Store U-Boot env on FAT partition, not raw sectors** — Easier to read/modify from Linux with `fw_printenv`/`fw_setenv`.
5. **Use `CONFIG_DISTRO_DEFAULTS`** — Enables standard boot flow (scan USB, SD, network), making your board compatible with generic distro images.
6. **Test FPGA load timeout** — U-Boot's `fpga load` blocks until done. Test how long your bitstream takes and set `CONFIG_FPGA_LOAD_TIMEOUT` appropriately.

## Common Pitfalls

| Pitfall | Symptom | Root Cause | Fix |
|---|---|---|---|
| **FPGA not configured before kernel** | Kernel bridge probe fails | U-Boot skipped `fpga load` | Add FPGA load to U-Boot `bootcmd` script |
| **Wrong DTB passed to kernel** | Bridges don't work, no interrupts | DTB doesn't match FPGA image | Compile DTB after Platform Designer / Vivado block design export |
| **U-Boot can't find bitstream** | `fatload` fails, "File not found" | Wrong partition or filename | Check FAT partition with `fatls mmc 0:1` in U-Boot shell |
| **SPL too large** | Build fails with overflow error | OCRAM is only 64 KB | Disable unused SPL features (`CONFIG_SPL_FS_EXT4=n` if not needed) |
| **U-Boot env corruption** | Board boots with wrong settings | Power loss during env write | Use redundant env (`CONFIG_ENV_OFFSET_REDUND`) or store on read-mostly partition |

---

## References

- [U-Boot Official Documentation](https://docs.u-boot.org/)
- [Intel SoC EDS — U-Boot User Guide](https://www.intel.com/content/www/us/en/docs/programmable/683472/)
- [Xilinx Wiki — U-Boot](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842316/U-Boot)
- [PolarFire SoC — HSS and U-Boot](https://github.com/polarfire-soc/hart-software-services)
- [DE10-Nano U-Boot Sources](https://github.com/terasic-socfpga/u-boot-socfpga)

> **Next:** [Device Tree & Overlays](../04_drivers_and_dma/device_tree_and_overlays.md) — how the DTB U-Boot passes to the kernel describes FPGA bridges, reserved memory, and interrupt routing across vendors.
