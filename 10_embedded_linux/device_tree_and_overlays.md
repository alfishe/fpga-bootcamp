[← Section Home](README.md) · [← Project Home](../README.md)

# Device Tree & FPGA Manager — Describing Hardware to Linux

The device tree is the data structure that tells Linux what peripherals exist and where they are mapped. For an FPGA SoC, the FPGA fabric itself and every IP core placed in it must be described in the device tree so the kernel can load the correct drivers. The Linux **FPGA Manager** subsystem handles the runtime loading of bitstreams and the associated device tree overlays.

---

## Device Tree Basics for FPGA SoCs

A device tree for an FPGA SoC has two portions: the **static** part (HPS/PS peripherals that are always present) and the **dynamic** part (FPGA fabric peripherals that depend on which bitstream is loaded).

### Static DT — The HPS Core

```dts
/dts-v1/;
#include "socfpga.dtsi"          // SoC-level definitions

/ {
    model = "Terasic DE10-Nano";
    compatible = "altr,socfpga-cyclone5", "altr,socfpga";

    memory@0 {
        device_type = "memory";
        reg = <0x0 0x40000000>;  // 1 GB DDR
    };
};

&uart0 {
    status = "okay";  // Enable UART0 (HPS -> FT232 -> USB)
};

&mmc0 {
    status = "okay";  // Enable SD/MMC (HPS -> Micro SD socket)
    bus-width = <4>;
};

&usb1 {
    status = "okay";  // Enable USB OTG
};
```

### Dynamic DT — FPGA Fabric Peripherals

FPGA IP cores appear in a `sopc@0` or `fpga-region` node that maps to the H2F bridge:

```dts
/ {
    // FPGA fabric configuration space
    soc {
        fpga_bridge0: fpga-bridge@ff200000 {
            compatible = "altr,socfpga-lwhps2fpga-bridge";
            reg = <0xff200000 0x00200000>;
        };
    };

    // An FPGA peripheral: custom GPIO expander at H2F
    fpga_peripherals: bridge@0xc0000000 {
        compatible = "simple-bus";
        #address-cells = <1>;
        #size-cells = <1>;
        ranges = <0 0xc0000000 0x40000000>;  // Map child addr 0 to H2F base 0xC000_0000

        my_gpio: gpio@10000000 {
            compatible = "mycorp,fpga-gpio-1.0";
            reg = <0x10000000 0x1000>;
            interrupts = <0 40 IRQ_TYPE_LEVEL_HIGH>;
            ngpios = <16>;
        };

        my_dma: dma@20000000 {
            compatible = "mycorp,axi-dma-1.0";
            reg = <0x20000000 0x1000>;
            interrupts = <0 41 IRQ_TYPE_LEVEL_HIGH>;
            dma-channels = <1>;
        };
    };
};
```

> **Address math note:** The `ranges` property maps child addresses starting from 0 to the H2F bridge base at `0xC000_0000`. So `gpio@10000000` in the DT corresponds to physical address `0xC000_0000 + 0x1000_0000 = 0xD000_0000`. In Qsys/Platform Designer, you assign addresses relative to the H2F bridge base (typically `0x0000_0000` in the Qsys address space), and the DT `ranges` property adds the bridge offset.

### Key DT Properties for FPGA Peripherals

| Property | Meaning |
|---|---|
| `compatible` | String matching a driver's `of_match_table`. The kernel uses this to decide which driver to probe |
| `reg` | `<base-address size>` — Where this IP core sits in the H2F bridge window. Must match what Qsys/Platform Designer or Vivado block design generated |
| `interrupts` | GIC interrupt specifier: `<irq-type irq-number irq-flags>`. On Cyclone V: IRQ type 0 = SPI; IRQ number = FPGA IRQ number + 72 (SPI offset) |
| `clocks` | Which clock drives this peripheral (for clock gating, rate configuration) |
| `interrupt-parent` | Which interrupt controller handles this device's IRQ (typically `&intc` or `&gic`) |
| `dmas` / `dma-names` | DMA channel binding if the IP uses the Linux DMA engine |

---

## FPGA Manager — Runtime Bitstream Loading

The Linux FPGA Manager subsystem (`drivers/fpga/`) provides a unified interface for loading FPGA bitstreams at runtime. It abstracts away the vendor-specific configuration hardware (FPP, PCAP, SPI, JTAG).

### Architecture

```
Userspace Application
    │
    ▼
/sys/kernel/config/device-tree/overlays/  (configfs overlay path)
    │
    ▼
fpga-region driver  (Handles bus on/off and bridge enable/disable)
    │
    ▼
fpga-manager driver  (Vendor-specific programming layer)
    │  ├─ socfpga.c       (Intel/Altera FPP)
    │  ├─ zynq-fpga.c     (Xilinx PCAP)
    │  ├─ ice40-spi.c     (Lattice SPI config)
    │  ├─ machxo2-spi.c   (Lattice MachXO2 SPI)
    │  └─ ...
    ▼
FPGA Hardware  (FPP x16, PCAP DMA, SPI, JTAG)
```

### Loading a Bitstream from Userspace

```bash
# Method 1: Direct firmware loading (simplest, on most kernels)
echo socfpga.rbf > /sys/class/fpga_manager/fpga0/firmware
# Kernel reads the file from /lib/firmware/socfpga.rbf, programs FPGA

# Method 2: Configfs overlay loading (more flexible, supports overlays)
mkdir -p /sys/kernel/config/device-tree/overlays/myfpga
cat myfpga-overlay.dtbo > /sys/kernel/config/device-tree/overlays/myfpga/dtbo
# Kernel applies overlay -> new devices probed
```

### Enabling FPGA Manager in Kernel Config

```
CONFIG_FPGA=y
CONFIG_FPGA_MGR_SOCFPGA=y              # Intel/Altera SoC FPGA
CONFIG_FPGA_MGR_ZYNQ_FPGA=y            # Xilinx Zynq PCAP
CONFIG_FPGA_REGION=y
CONFIG_OF_OVERLAY=y                     # Device tree overlay support
```

---

## Device Tree Overlay — FPGA Configuration at Runtime

A device tree overlay is a **fragment** of device tree that is merged into the live tree after the FPGA bitstream is loaded. It describes the IP cores that the bitstream placed in the fabric.

### Building an Overlay

```dts
// myfpga-overlay.dts — Overlay that adds FPGA peripherals
/dts-v1/;
/plugin/;

/ {
    fragment@0 {
        target-path = "/soc/fpga_bridge0";

        __overlay__ {
            #address-cells = <1>;
            #size-cells = <1>;

            my_fpga_ip: accel@0x10000000 {
                compatible = "mycorp,accel-v1";
                reg = <0x10000000 0x00010000>;
                interrupts = <0 40 4>;
            };
        };
    };
};
```

Compile the overlay:

```bash
dtc -I dts -O dtb -o myfpga-overlay.dtbo myfpga-overlay.dts
```

### Loading the Overlay with FPGA Region

On kernels with full FPGA region support, the FPGA Manager and device tree overlays are coupled: loading the bitstream automatically triggers the corresponding overlay application.

```dts
// Device tree describes the FPGA region
fpga_region0: fpga-region@0 {
    compatible = "fpga-region";
    fpga-mgr = <&fpga_mgr>;
    firmware-name = "socfpga.rbf";
    // When this region is loaded, all child nodes become active
};
```

### The Overlay Loading Sequence

```
1. echo socfpga.rbf > /sys/class/fpga_manager/fpga0/firmware
2. FPGA Manager writes bitstream via FPP/PCAP
3. FPGA enters user mode (bridges enabled)
4. fpga-region driver detects configuration complete
5. fpga-region applies the overlay from firmware-name
6. Kernel probes drivers for devices in the overlay
7. New devices appear in /dev and sysfs
```

---

## Reserved Memory — Allocating DDR for FPGA

FPGA often needs a chunk of DDR memory that Linux won't touch. This is configured via `reserved-memory`:

```dts
/ {
    reserved-memory {
        #address-cells = <1>;
        #size-cells = <1>;
        ranges;

        /* 128 MB carve-out for FPGA frame buffer at top of RAM */
        fpga_fb_reserved: buffer@0x38000000 {
            reg = <0x38000000 0x08000000>;
            no-map;  // Don't create struct page for this — FPGA-only
        };

        /* 16 MB CMA for DMA with CPU access */
        linux,cma {
            compatible = "shared-dma-pool";
            reg = <0x37000000 0x01000000>;
            reusable;
            linux,cma-default;
        };
    };
};
```

| Property | Meaning |
|---|---|
| `no-map` | Memory excluded from kernel management entirely — no struct page, no CPU mapping. FPGA-only access through F2S bridge. |
| `reusable` | CMA (Contiguous Memory Allocator) — kernel can use it when FPGA doesn't need it; allocated on demand for DMA |
| `compatible = "shared-dma-pool"` | Creates a standard DMA pool any driver can allocate from via `dma_alloc_coherent()` |

---

## Vendor-Specific DT Bindings

### Intel (Cyclone V / Arria 10 / Stratix 10 / Agilex)

```dts
// FPGA Manager node
fpga_mgr: fpga-mgr@ff706000 {
    compatible = "altr,socfpga-fpga-mgr";
    reg = <0xff706000 0x1000>,         // Configuration registers
          <0xffb90000 0x1000>;         // FPGA Manager registers
    interrupts = <0 175 IRQ_TYPE_LEVEL_HIGH>;
};

// HPS-to-FPGA bridges
hps_bridges: bridge@ff200000 {
    compatible = "altr,socfpga-hps2fpga-bridge";
    // Individual bridges
    fpga2hps: fpga-bridge@0 { ... };
    hps2fpga: fpga-bridge@1 { ... };
    lwhps2fpga: fpga-bridge@2 { ... };
};
```

Key Intel bindings:
- `altr,socfpga-fpga-mgr` — FPGA Manager
- `altr,socfpga-fpga2sdram-bridge` — F2S bridge
- `altr,socfpga-lwhps2fpga-bridge` — Lightweight H2F
- FPGA interrupt offset: Cyclone V SPI 72–135; Stratix 10 SPI 128–255

### Xilinx (Zynq-7000 / Zynq MPSoC)

```dts
// FPGA Manager (PCAP)
fpga_mgr: fpga-region {
    compatible = "fpga-region";
    fpga-mgr = <&devcfg>;
    #address-cells = <1>;
    #size-cells = <1>;
};

// Device Configuration Interface
devcfg: devcfg@f8007000 {
    compatible = "xlnx,zynq-devcfg-1.0";
    reg = <0xf8007000 0x100>;
    interrupt-parent = <&intc>;
    interrupts = <0 8 4>;
};

// ACP port for cache-coherent FPGA access
axi_acp: axi@f800b000 {
    compatible = "xlnx,zynq-7000-acp";
    reg = <0xf800b000 0x1000>;
};
```

Key Xilinx bindings:
- `xlnx,zynq-devcfg-1.0` — PCAP configuration interface
- `fpga-region` — standard FPGA region with firmware-name
- AXI ports appear as `simple-bus` children
- FPGA IRQs route through the GIC PL-to-PS interrupt lines (Zynq-7000: IRQ 61–68 from PL)

### Microchip (PolarFire SoC)

```dts
fpga_mgr: fpga-region {
    compatible = "fpga-region";
    fpga-mgr = <&fpga_mgr_system_controller>;
    firmware-name = "polarfire.rbf";
};
```

PolarFire SoC uses the System Controller (MSS) for FPGA configuration. DT bindings are simpler because the flash-based FPGA fabric is a simpler programming model.

---

## Common DT Mistakes

### 1. Address Mismatch Between Qsys and DT

**The mistake:** The DT says `reg = <0x10000000 0x1000>` but Qsys/Platform Designer placed the IP at a different offset from the bridge base.

**Why it fails:** The kernel driver accesses the wrong physical address. Reads return `0xFFFFFFFF` (unmapped bus) and writes silently fail.

**Fix:** In Qsys/Platform Designer, check the **Base Address** column in the Address Map tab. The address is relative to the bridge base. If your H2F bridge maps to `0xC000_0000` and Qsys shows `0x0001_0000`, the DT `ranges` must add the bridge offset: `ranges = <0 0xc0000000 0x40000000>` and then peripheral `reg = <0x00010000 0x1000>`.

### 2. Incorrect Interrupt Numbers

**The mistake:** DT says `interrupts = <0 40 4>` but the FPGA IRQ signal number doesn't match what the FPGA designer connected in Qsys/Vivado.

**Why it fails:** The wrong interrupt fires (or no interrupt fires), and the driver hangs waiting for a signal.

**Fix:** On Cyclone V, FPGA IRQ 0 → SPI 72 ; FPGA IRQ 1 → SPI 73; ..., FPGA IRQ N → SPI 72+N. On Zynq-7000, IRQs from PL use the PL-to-PS interrupt lines (typically 61–68 for IRQ_F2P). Verify both the FPGA-side IRQ number AND the GIC mapping.

### 3. Overlay Applied Before Bitstream Is Loaded

**The mistake:** Loading the DT overlay first, then programming the FPGA.

**Why it fails:** The overlay references addresses in FPGA bridges. The bridges don't respond (or respond with bus errors) until the FPGA is configured.

**Fix:** Always configure the FPGA first, then load the overlay. On recent kernels with `fpga-region`, this ordering is automatic — the region driver handles it. For manual scripts: `echo bitstream > fpga_manager` BEFORE `cat overlay.dtbo > configfs`.

### 4. Missing `no-map` on FPGA-Only Memory

**The mistake:** Reserving memory without `no-map` for an F2S DDR buffer that only the FPGA accesses.

**Why it fails:** The kernel creates struct pages for this memory and may allocate it to other users (page cache, slab allocator). When the FPGA writes to it, it corrupts kernel data structures — a catastrophic system crash.

**Fix:** Use `no-map` for FPGA-exclusive memory. Use `reusable` (CMA) only for memory that both CPU and FPGA access, and only with proper cache synchronization.

### 5. Wrong `compatible` String

**The mistake:** Typo in the `compatible` string, or using a generic string when a specific driver binding exists.

**Why it fails:** No driver matches. The device is silently ignored — no error, no warning, just no `/dev` entry.

**Fix:** Check `Documentation/devicetree/bindings/` in the kernel source for the exact compatible string. Use `grep -r "your-driver" drivers/` to find the `of_match_table` in the driver source and match it exactly.

---

## References

| Source | Target |
|---|---|
| Device Tree Specification | https://www.devicetree.org/specifications/ |
| Linux FPGA Manager docs | `Documentation/fpga/` in kernel source |
| Kernel DT bindings (FPGA) | `Documentation/devicetree/bindings/fpga/` |
| Intel SOCFPGA DT binding | `altr,socfpga-fpga-mgr.txt` in kernel bindings |
| Xilinx Zynq DT binding | `xlnx,zynq-devcfg-1.0` binding in kernel source |
| `dtc` compiler source | `scripts/dtc/` in kernel source, or install `device-tree-compiler` |
| [soc_linux_architecture.md](soc_linux_architecture.md) | SoC architecture overview — memory maps, bridge topology |
| [boot_flow.md](boot_flow.md) | Boot sequence — where FPGA config and DT loading fit in |
| [hps_fpga_bridges.md](hps_fpga_bridges.md) | Bridge programming from Linux — the driver side of DT devices |
