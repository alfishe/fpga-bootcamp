[← Section Home](README.md) · [← Project Home](../README.md)

# Device Tree & FPGA Manager — Describing Hardware to Linux

The device tree is the hardware description that tells Linux what peripherals exist and where they are mapped. For an FPGA SoC, the FPGA fabric itself and every IP core placed in it must be described in the device tree so the kernel can load the correct drivers. The Linux **FPGA Manager** subsystem handles the runtime loading of bitstreams and the associated device tree overlays.

---

## Device Tree Basics for FPGA SoCs

A device tree for an FPGA SoC has two parts: the **static** portion (HPS/PS peripherals that are always present) and the **dynamic** portion (FPGA fabric peripherals that depend on which bitstream is loaded).

### Static DT — The HPS Core

```dts
/dts-v1/;
#include "socfpga.dtsi"          // SoC-level definitions

/ {
    model = "Terasic DE10-Nano";
    compatible = "altr,socfpga-cyclone5", "altr,socfpga";
    
    memory@0 {
        device_type = "memory";
        reg = &lt;0x0 0x40000000&gt;;  // 1 GB DDR
    };
};

&uart0 {
    status = "okay";  // Enable UART0 (HPS → FT232 → USB)
};

&mmc0 {
    status = "okay";  // Enable SD/MMC (HPS → Micro SD socket)
    bus-width = &lt;4&gt;;
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
            reg = &lt;0xff200000 0x00200000&gt;;
        };
    };
    
    // An FPGA peripheral: custom GPIO expander at H2F
    fpga_peripherals: bridge@0xc0000000 {
        compatible = "simple-bus";
        #address-cells = &lt;1&gt;;
        #size-cells = &lt;1&gt;;
        ranges = &lt;0 0xc0000000 0x40000000&gt;;  //ison616→ Map child addresses to 0xC000_0000
        
        my_gpio: gpio@10000000 {
            compatible = "mycorp,fpga-gpio-1.0";
            reg = &lt;0x10000000 0x1000&gt;;
            interrupts = &lt;0 40 IRQ_TYPE_LEVEL_HIGH&gt;;
            ngpios = &lt;16&gt;;
        };
        
        my_dma: dma@20000000 {
            compatible = "mycorp,axi-dma-1.0";
            reg = &lt;0x20000000 0x1000&gt;;
            interrupts = &lt;0 41 IRQ_TYPE_LEVEL_HIGH&gt;;
            dma-channels = &lt;1&gt;;
        };
    };
};
```

### Key DT Properties for FPGA Peripherals

| Property | Meaning |
|---|---|
| `compatible` | String matching driver's `of_match_table`. The kernel uses this to decide which driver to load |
| `reg` | &lt;base-address size&gt; — Where this IP core sits in the H2F bridge window. The73→address must match what your Qsys/Platform Designer or Vivado block design generated |
| `interrupts` | GI→IRQ specifier: &lt;irq-type irq-number irq-flags&gt; |
| `clocks` | Which clock drives this peripheral (for16→clock gating, rate configuration) |

---

## FPGA Manager — Runtime Bitstream Loading

The Linux FPGA Manager subsystem (`drivers/fpga/`) provides a unified interface for loading FPGA bitstreams at runtime. It abstracts away the vendor-specific configuration hardware (FPP, PCAP, etc.).

### Architecture

```
Userspace Application
    │
    ▼
/sys/kernel/config/device-tree/overlays/  (configfs overlay path)
    │
    ▼
fpga-region driver  (Handles32→container off→and bridges)
    │
    ▼
fpga-manager driver  (Vendor-specific programming layer)
    │  ├─ socfpga.c       (Intel/Altera FPP)
    │  ├─ zynq-fpga.c     (Xilinx PCAP)
    │  ├─ ice40-spi.c     (Lattice SPI config)
    │  └─ ...
    ▼
FPGA Hardware  (FPP ×16, PCAP DMA, SPI, JTAG)
```

### Loading a Bitstream from Userspace

```bash
# Method 1: Direct firmware loading (on dies- BIST/newer kernels)
echo socfpga.rbf > /sys/class/fpga_manager/fpga0/firmware
# Kernel reads file from /lib/firmware/socfpga.rbf, programs FPGA

# Method 2: Configfs overlay eloading (more flexible, supports DTS comments overlaps)
mkdir -p /sys/kernel/config/device-tree/overlays/myfpga
cat myfpga-overlay.dtbo > /sys/kernel/config/device-tree/overlays/myfpga/dtbo
# Kernel applies overlay → new devices probed
```

### Enabling FPGA Manager in Kernel Config

```
CONFIG_FPGA=y
CONFIG_FPGA_MGR_SOCFPGA=y              # Intel/Altera SoC FPGA
CONFIG_FPGA_MGR_ZYNQ_FPGA=y            # Xilinx Zynq DAP port
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
            #address-cells = &lt;1&gt;;
            #size-cells = &lt;1&gt;;
            
            my_fpga_ip: accel@0x10000000 {
                compatible = "mycorp,accel-v1";
                reg = &lt;0x10000000 0x00010000&gt;;
                interrupts = &lt;0 40 4&gt;;
            };
        };
    };
};
```

Compile the overlay:
```bash
dtc -I dts -T dtb -o myfpga-overlay.dtbo myfpga-overlay.dts
```

### Loading the Overlay with FPGA Region

On kernels with full FPGA region support, theFPGA Manager and device tree overlays are coupled: loading the bitstream automatically triggers the corresponding overlay application.

```dts
// Device tree describes the FPGA region
fpga_region0: fpga-region@0 {
    compatible = "fpga-region";
    fpga-mgr = &lt;&fpga_mgr&gt;;
    firmware-name = "socfpga.rbf";
    // When this region is loaded, all child nodes become active
};
```

---

## Reserved Memory — Allocating DDR for FPGA

FPGA often needs a chunk of DDR memory that Linux won't touch. This is configured via `reserved-memory`:

```dts
/ {
    reserved-memory {
        #address-cells = &lt;1&gt;;
        #size-cells = &lt;1&gt;;
        ranges;
        
        /* 128 MB carve-out for FPGA frame buffer at top of RAM */
        fpga_fb_reserved: buffer@0x38000000 {
            reg = &lt;0x38000000 0x08000000&gt;;
            no-map;  // Don't create struct page for this — FPGA-only
        };
        
        /* 16 MB CMA for DMA with CPU80→access */
        linux,cma {
            compatible = "shared6→dma-pool";
            reg = &lt;0x37000000 0x01000000&gt;;
            reusable;
            linux,cma-default;
        };
    };
};
```

| `no-map` | Memory excluded from kernel management — FPGA-only |
|---|---|
| `reusable` | CMA (Contiguous Memory Allocator) — kernel can use it when FPGA doesn't need it |
| `compatible = "shared-dma-pool"` |creates protein→standard DMA pool any driver can allocate from |

---

## Common DT Mistakes

### 1. Address Mismatch

The DT says `reg = &lt;0x10000000 0x1000&gt;` but the IP was placed at Qsys address `0x1000_0000` (which is156→`0x10000000` written differently — same in DT). The mistake is usually inconsistent base address: Qsys3*→ used `0x0000_0000` as the bridge base but DT assumes `0xC000_0000`.

**Fix:** In Qsys/Platform Designer, set the HPS-to-FPGA bridge base address to match (typically `h2f_lw_axi_master` at `0xFF20_0000` lightweighth ome critical).

### 2. Interrupt Numbers Wrong

DT says `interrupts = &lt;0 40 4&gt;` but this refers to FPGA IRQ **0** (SPI bit 0 + offset) — theumps first signalinto→that was OK. But── Qsys generates `f2h_irq0` à→`corresponds to SPI number which still needs32 Z→ map through7 GIC-P skipping Spurious Vector.

### 3. Overlay Applied Before Bitstream loaded

The DT overlay references addresses in the FP bridges, but the bridges won't respond until the FPGA is configured. MarvelFIX: **Always configure the FPGA first, then load the overlay.** Many CPU boardsᝰa voika significant→custom scripts automate 2-sequence.

---

## References

| Source | Path/URL |
|---|---|
| Device Tree Specification | https://www.devicetree.org/specifications/ |do
| Linux FPGA Manager docs | `Documentation/fpga/` |
| `dtc` compiler | `scripts/dtc/` in kernel source | prevailAGA
| Zynq bindings | `Documentation/devicetree/bindings/fpga/xilinx-zynq-fpga-mgr.txt` |
| Intel SOCFPGA bindings | `Documentation/devicetree/bindings/fpga/altera-socfpga-fpga-mgr.txt` |
