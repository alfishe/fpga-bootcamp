[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Memory Map Design — Planning Address Spaces

The memory map is the contract between hardware and software — get it wrong and your device tree won't match your RTL, leading to silent data corruption or boot failures. A well-designed memory map simplifies address decoding, enables efficient AXI interconnect routing, and makes software development predictable.

This article covers address map principles, aperture sizing, AXI address decoding, Zynq/UltraScale+ address spaces, device tree binding, and common mistakes.

---

## Memory Map Principles

| Principle | Why It Matters |
|---|---|
| **Power-of-2 aperture sizing** | Simplifies address decoding → fewer LUTs, simpler comparators |
| **Reserve gaps between regions** | Prevents address collision when expanding later |
| **Keep boot ROM at reset vector** | CPU reset vector is hard-coded (0x0000_0000 for RISC-V, 0x0000_0000 for ARM AArch64) |
| **MMIO above DRAM** | DRAM starts at lowest address for zero-offset access; MMIO at high addresses |
| **Align apertures to their size** | A 4 KB peripheral at 0x4000_1000 (aligned) decodes with 20-bit comparison; at 0x4000_1800 it can't be decoded efficiently |
| **Document every address in one place** | Single header file / device tree that is the source of truth |

---

## Address Decoder Design

### Simple Address Decoder (Power-of-2 Aperture)

For a 4 KB peripheral at address 0x4000_0000, the decoder compares only the upper address bits:

```verilog
// Address decoder: 4 KB peripheral at 0x4000_0000
// Only need to compare bits [31:12] = 0x40000
assign periph_sel = (axi_awaddr[31:12] == 20'h40000);

// Internal offset within peripheral
assign periph_offset = axi_awaddr[11:0];  // 12 bits = 4 KB space
```

This costs **1 comparator + 1 mux** — trivial in LUTs.

### Misaligned Address Decoder (Expensive)

For a 4 KB peripheral at 0x4000_1800 (NOT aligned to 4 KB):

```verilog
// Must compare ALL 32 bits — much more expensive
assign periph_sel = (axi_awaddr[31:0] >= 32'h40001800) &&
                    (axi_awaddr[31:0] <  32'h40002800);
// This requires a 32-bit magnitude comparator → many more LUTs
```

**Rule:** Always place peripherals at addresses aligned to their aperture size. A 4 KB peripheral goes at `0xNNNN_N000`, a 64 KB peripheral at `0xNNNN_0000`.

### AXI Address Decoder with Multiple Slaves

```verilog
// Typical SoC with 4 slaves
localparam DDR_BASE   = 32'h0000_0000;
localparam UART_BASE  = 32'h4000_0000;
localparam SPI_BASE   = 32'h4000_1000;
localparam GPIO_BASE  = 32'h4000_2000;

// Decode top bits for slave selection
always @(*) begin
    ddr_sel   = 0; uart_sel = 0; spi_sel = 0; gpio_sel = 0;
    case (axi_awaddr[31:28])
        4'h0: ddr_sel  = 1;   // 0x0000_0000 – 0x0FFF_FFFF
        4'h4: begin
            case (axi_awaddr[15:12])
                4'h0: uart_sel = 1;  // 0x4000_0000
                4'h1: spi_sel  = 1;  // 0x4000_1000
                4'h2: gpio_sel = 1;  // 0x4000_2000
                default: ;  // Decode error
            endcase
        end
        default: ;  // Decode error
    endcase
end
```

This two-level decode (outer: 256 MB regions; inner: 4 KB peripherals) is the standard pattern for FPGA SoCs.

---

## Zynq UltraScale+ Address Space

Zynq UltraScale+ has a complex address map with multiple address regions for PS (Processing System) and PL (Programmable Logic):

### PS Address Map (CPU View)

| Start | End | Size | Region |
|---|---|---|---|
| 0x0000_0000 | 0x7FFF_FFFF | 2 GB | DDR Low (via LPD) |
| 0x0000_0000 | 0x7FFF_FFFF | 2 GB | DDR Low (via FPD, alias) |
| 0x8000_0000 | 0xBFFF_FFFF | 1 GB | PL AXI LPD (M_AXI_HPM0_LPD) |
| 0xC000_0000 | 0xFFFF_FFFF | 1 GB | PL AXI FPD (M_AXI_HPM0_FPD) |
| 0xFF00_0000 | 0xFFFF_FFFF | 16 MB | PS I/O Peripherals (UART, SPI, I2C, etc.) |
| 0xFFE0_0000 | 0xFFE0_FFFF | 64 KB | OCM (On-Chip Memory) |
| 0xFD00_0000 | 0xFDFF_FFFF | 16 MB | GIC-400 (Interrupt Controller) |

### PL Address Map (FPGA View)

| Start | End | Size | Region |
|---|---|---|---|
| 0x0000_0000_0000 | 0x0000_07FF_FFFF | 128 MB | DDR Low (via HPC0) |
| 0x0000_0800_0000 | 0x0000_0FFF_FFFF | 128 MB | DDR Low (via HPC1) |
| 0x0004_0000_0000 | 0x0004_7FFF_FFFF | 2 GB | DDR High (via HPC0/1) |
| 0x00FF_F000_0000 | 0x00FF_FFFF_FFFF | 4 GB | PS I/O Peripherals |
| 0x00FF_FE00_0000 | 0x00FF_FE00_FFFF | 64 KB | OCM |

> **Key point:** The PL and PS have **different address maps** for the same physical DDR. The address translation is done by the SMMU (System Memory Management Unit) in the interconnect. This is a common source of bugs: the CPU accesses DDR at `0x0000_0000` but the FPGA accesses the same DDR at `0x0004_0000_0000`.

---

## Aperture Sizing Guide

| Peripheral Type | Typical Register Count | Recommended Aperture | Alignment |
|---|---|---|---|
| UART (16550) | 8 registers | 4 KB | 4 KB |
| SPI controller | 16 registers | 4 KB | 4 KB |
| I2C controller | 16 registers | 4 KB | 4 KB |
| GPIO | 8 registers | 4 KB | 4 KB |
| DMA engine (AXI DMA) | 64 registers | 4 KB | 4 KB |
| Interrupt controller (PLIC) | ~1K registers | 4 MB | 4 MB |
| GIC-400 (ARM) | ~8K registers | 64 KB | 64 KB |
| DDR controller | Large | 256 MB – 4 GB | Size of region |
| Boot ROM | 8–64 KB | 64 KB | 64 KB |
| BRAM/OCM | 64 KB – 1 MB | 1 MB | 1 MB |

**Why 4 KB for small peripherals?** It's the smallest ARM page size. Anything smaller than 4 KB can't be independently mapped in the MMU, which means Linux can't give different processes different access permissions.

---

## Device Tree Binding

The device tree is the software's view of the memory map. Every `reg` property must match the RTL address decoder exactly.

### Complete Device Tree Example (RISC-V SoC)

```dts
/dts-v1/;

/ {
    #address-cells = <1>;
    #size-cells = <1>;

    memory@0 {
        device_type = "memory";
        reg = <0x00000000 0x10000000>;  /* 256 MB DDR at 0x0 */
    };

    chosen {
        stdout-path = &uart0;
    };

    cpus {
        #address-cells = <1>;
        #size-cells = <0>;
        cpu0: cpu@0 {
            compatible = "riscv";
            reg = <0>;
        };
    };

    soc {
        #address-cells = <1>;
        #size-cells = <1>;
        compatible = "simple-bus";
        ranges;

        uart0: serial@40000000 {
            compatible = "ns16550a";
            reg = <0x40000000 0x1000>;
            interrupt-parent = <&plic>;
            interrupts = <1>;
            clock-frequency = <100000000>;
        };

        spi0: spi@40001000 {
            compatible = "xlnx,xps-spi-2.00.a";
            reg = <0x40001000 0x1000>;
            interrupt-parent = <&plic>;
            interrupts = <2>;
        };

        gpio0: gpio@40002000 {
            compatible = "xlnx,xps-gpio-1.00.a";
            reg = <0x40002000 0x1000>;
            #gpio-cells = <2>;
        };

        plic: interrupt-controller@40003000 {
            compatible = "riscv,plic0";
            reg = <0x40003000 0x400000>;
            interrupt-controller;
            #interrupt-cells = <1>;
            riscv,ndev = <32>;
        };
    };
};
```

### Zynq UltraScale+ Device Tree (PS + PL)

```dts
// PL peripheral added to base Zynq MP device tree
&axi_dma_0 {
    compatible = "xlnx,axi-dma-1.00.a";
    reg = <0x0 0xa0000000 0x0 0x1000>;  // Must match Vivado address editor
    interrupts = <0 89 4>, <0 90 4>;
};

// Custom PL IP
fpga_accel: accel@a0010000 {
    compatible = "mycompany,fpga-accel-1.0";
    reg = <0x0 0xa0010000 0x0 0x1000>,
          <0x0 0xa0020000 0x0 0x10000>;  /* Control + BRAM buffer */
    interrupt-parent = <&gic>;
    interrupts = <0 91 4>;
};
```

---

## Reserved Regions

Some memory regions must be excluded from the OS memory allocator:

```dts
reserved-memory {
    #address-cells = <2>;
    #size-cells = <2>;
    ranges;

    /* DMA coherent buffer — not cached, used by FPGA */
    dma_buf: buffer@70000000 {
        reg = <0x0 0x70000000 0x0 0x01000000>;  /* 16 MB */
        no-map;  /* OS cannot map this region */
    };

    /* FPGA shared mailbox — cacheable, shared with PL */
    mailbox: buffer@71000000 {
        reg = <0x0 0x71000000 0x0 0x1000>;  /* 4 KB */
        compatible = "shared-dma-pool";
        reusable;  /* OS can reclaim when not in use */
    };

    /* RPU (Cortex-R5) private memory */
    rpu_memory: rpu@7e000000 {
        reg = <0x0 0x7e000000 0x0 0x02000000>;  /* 32 MB */
        no-map;
    };
};
```

---

## AXI Interconnect Address Filtering

Xilinx AXI Interconnect IP supports address filtering to route transactions to the correct slave based on address ranges. This is configured in Vivado's Address Editor.

### Address Editor Configuration

```
Master: M_AXI_HPM0_FPD (PS → PL, 0xC000_0000 base)
  ├── Slave: axi_dma_0    @ 0xC000_0000, size 4K
  ├── Slave: axi_uart_0   @ 0xC000_1000, size 4K
  ├── Slave: fpga_accel   @ 0xC001_0000, size 4K
  └── Slave: bram_ctrl_0  @ 0xC100_0000, size 8K

Master: M_AXI_HPM0_LPD (PS → PL, 0x8000_0000 base)
  └── Slave: gpio_0       @ 0x8000_0000, size 4K
```

**Critical:** The base addresses in the Address Editor define the actual address decode in the interconnect. If you change a base address in the Address Editor, you MUST update the device tree `reg` property to match.

---

## Memory Protection

### ARM AArch64 Memory Attributes

| Memory Type | MAIR Value | Use For | Attributes |
|---|---|---|---|
| **Normal, Cacheable, WB** | 0xFF | DDR, BRAM | Read/write allocate, cacheable |
| **Device, nGnRnE** | 0x00 | Most MMIO | Non-gathering, non-reordering, no early write ack |
| **Device, nGnRE** | 0x04 | DMA registers | Non-gathering, non-reordering, early write ack |
| **Normal, Non-Cacheable** | 0x44 | Shared buffers (non-coherent) | No caching, no allocation |

```c
// Linux: ioremap() vs ioremap_wc() vs memremap()
void __iomem *regs = ioremap(0x40000000, 0x1000);      // Device memory (nGnRnE)
void __iomem *buf  = ioremap_wc(0x70000000, 0x1000000); // Write-combining (DMA buffer)
void *mem = memremap(0x0, 0x10000000, MEMREMAP_WB);     // Normal cacheable (DDR)
```

**Rule:** Never use `ioremap()` for DDR (it marks it as Device memory → uncached → extremely slow). Use `memremap()` or `ioremap_cache()` for normal memory.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Device tree reg ≠ RTL address** | Driver probes but reads wrong registers | Cross-check DT `reg` with Vivado Address Editor after every build |
| **PL vs PS address mismatch** | FPGA writes wrong DDR location | PL sees DDR at different base than PS; use `dma_set_mask()` correctly |
| **Peripheral at misaligned address** | Address decode costs excess LUTs | Align every aperture to its size |
| **No reserved region for DMA** | DMA corrupts kernel memory | Add `reserved-memory` node with `no-map` |
| **ioremap on DDR** | 100× slower access from CPU | Use `ioremap_cache()` or `memremap()` for DDR |
| **Aperture too small** | Peripheral registers alias into next device | Size apertures to 4 KB minimum (ARM page size) |
| **Missing `ranges` in DT** | PL peripherals not visible to CPU | Add `ranges` property in soc node for address translation |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [DMA Architecture](dma_architecture.md) | This KB | DMA engines, register maps, coherency |
| [Multi-Core Coherency](multi_core_coherency.md) | This KB | ACP, ACE, CCI, cache stashing |
| [Interrupt Routing](interrupt_routing.md) | This KB | GIC, PLIC, NVIC, FPGA IRQ mapping |
| [HPS-FPGA Bridges](../../10_embedded_linux/03_hps_fpga_bridges/hps_fpga_bridges_xilinx_zynq.md) | This KB | Zynq AXI port selection, address translation |
