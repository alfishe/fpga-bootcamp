[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Interrupt Routing — GIC, PLIC, NVIC, and FPGA IRQ Mapping

Interrupt architecture determines how fast your SoC responds to hardware events. A misrouted interrupt means your DMA completion never fires, your UART drops characters, or your accelerator hangs silently.

This article covers the three major interrupt controller architectures (ARM GIC, RISC-V PLIC, ARM NVIC), level vs edge triggering, FPGA-to-CPU interrupt routing, and Linux IRQ configuration.

---

## Core Concepts

| Concept | Description |
|---|---|
| **Level-triggered** | Interrupt line stays asserted until software clears the source. Safe for shared lines. |
| **Edge-triggered** | Interrupt fires on rising/falling edge only. Can miss interrupts if source pulses fast. |
| **Vectoring** | CPU jumps to a per-interrupt handler address directly (vs polling a shared status register) |
| **Priority** | Higher-priority interrupt preempts lower. Numeric convention varies by controller. |
| **Multi-core affinity** | Route interrupt to a specific core, all cores, or "any available" |
| **Claim/complete** | Software claims an IRQ (reads ID), handles it, then completes (writes ID back) |
| **IRQ chaining** | One IRQ handler demultiplexes into sub-handlers (cascade) |
| **MSI (Message-Signaled Interrupt)** | Write to address triggers interrupt (PCIe standard; no dedicated wire needed) |

### Level vs Edge — The Critical Choice

| Type | How It Works | Pros | Cons | Use When |
|---|---|---|---|---|
| **Level** | Line held high until cleared | Can't miss interrupts; safe for shared wires | Requires explicit clear in handler | Most FPGA peripherals (UART, DMA done, GPIO) |
| **Edge** | Fires on transition only | No need to clear; works with pulse sources | Can miss if another edge arrives before handler runs | Pulse sources (timer overflow, single-shot events) |

**FPGA rule of thumb:** Use level-triggered interrupts for almost everything. FPGA peripherals assert an IRQ line and hold it until the CPU reads a status register (which implicitly clears it). Edge-triggered interrupts on FPGA are risky because a second event during ISR execution is lost.

---

## ARM GIC (Zynq / Zynq UltraScale+)

The ARM GIC (Generic Interrupt Controller) is the interrupt controller in all Xilinx Zynq devices.

### GIC Architecture

```
                  ┌─────────────────────────────┐
  SPI 0–98 ──────►│                             │
  (PS peripherals)│       GIC-400               │
                  │  ┌───────────┐ ┌──────────┐ │
  SPI 121–128 ───►│  │Distributor│ │CPU iface │ │
  (PL→PS IRQ0-7)  │  │(priority, │ │(per-core)│ │
                  │  │ routing)  │ │          │ │
  SPI 136–143 ───►│  └───────────┘ └──────────┘ │
  (PL→PS IRQ8-15) │                             │
                  └─────────────────────────────┘
                        │             │
                   ┌────▼────┐   ┌────▼────┐
                   │ Core 0  │   │ Core 1  │
                   │ (A53)   │   │ (A53)   │
                   └─────────┘   └─────────┘
```

### GIC Interrupt Types

| Type | ID Range | Source | Notes |
|---|---|---|---|
| **SGI** (Software Generated) | 0–15 | Inter-processor IPI | CPU writes to GIC → triggers interrupt on target core |
| **PPI** (Private Peripheral) | 16–31 | Per-core: timer, watchdog, PMU | Each core has its own PPIs |
| **SPI** (Shared Peripheral) | 32–98 | PS peripherals (UART, ETH, SD, USB) | Shared among all cores |
| **SPI** (PL → PS) | 121–128, 136–143 | FPGA fabric interrupts | 16 PL→PS IRQ lines total |

### Zynq UltraScale+ PL→PS Interrupt Routing

The FPGA can send up to 16 interrupts to the PS:

| Signal | GIC SPI # | Direction |
|---|---|---|
| `pl_ps_irq0[0]` | SPI 121 | PL → PS |
| `pl_ps_irq0[1]` | SPI 122 | PL → PS |
| `pl_ps_irq0[2]` | SPI 123 | PL → PS |
| `pl_ps_irq0[3]` | SPI 124 | PL → PS |
| `pl_ps_irq0[4]` | SPI 125 | PL → PS |
| `pl_ps_irq0[5]` | SPI 126 | PL → PS |
| `pl_ps_irq0[6]` | SPI 127 | PL → PS |
| `pl_ps_irq0[7]` | SPI 128 | PL → PS |
| `pl_ps_irq1[0]` | SPI 136 | PL → PS |
| `pl_ps_irq1[1]` | SPI 137 | PL → PS |
| ... | ... | ... |
| `pl_ps_irq1[7]` | SPI 143 | PL → PS |

### Linux IRQ Number Mapping

Linux remaps hardware SPI IDs to Linux IRQ numbers:

```
Linux IRQ = SPI_ID - 32 + linux_irq_offset

For Zynq US+: SPI 121 → Linux IRQ 89 (typically)
Check: cat /proc/interrupts
```

### Device Tree: PL Interrupt to GIC

```dts
// FPGA peripheral with interrupt routed to GIC
fpga_accel: accel@a0010000 {
    compatible = "mycompany,fpga-accel-1.0";
    reg = <0x0 0xa0010000 0x0 0x1000>;
    interrupt-parent = <&gic>;
    interrupts = <0 89 4>;  // GIC SPI 121 = (121-32) = 89 in Linux
    // Format: <GIC_type SPI_number trigger_type>
    //   GIC_type: 0 = SPI, 1 = PPI
    //   SPI_number: hardware SPI ID - 32
    //   trigger_type: 4 = level-sensitive high
};
```

### Multi-Core Affinity (GIC)

Route an interrupt to a specific CPU core:

```c
// Linux kernel: set interrupt affinity
irq_set_affinity(irq_num, cpumask_of(1));  // Route to CPU 1 only

// Or from userspace:
echo 2 > /proc/irq/89/smp_affinity  // CPU 1 only (bit mask: 0b0010)
echo f > /proc/irq/89/smp_affinity  // Any CPU (bit mask: 0b1111)
```

**Why affinity matters:** If DMA completion interrupts go to CPU 0 (which is also handling network and timer interrupts), the DMA handler may be delayed. Pin DMA IRQs to a dedicated core.

---

## RISC-V PLIC (Platform-Level Interrupt Controller)

The PLIC is the standard interrupt controller for RISC-V FPGA SoCs.

### PLIC Architecture

```
Peripherals           PLIC               CPU Core
┌──────────┐      ┌──────────┐      ┌────────────────┐
│ UART IRQ │─────►│          │      │                │
│ SPI IRQ  │─────►│  PLIC    │─────►│ MEIP (M-mode)  │
│ GPIO IRQ │─────►│ (priority│      │ SEIP (S-mode)  │
│ DMA Done │─────►│  + gate) │      │                │
│ Eth IRQ  │─────►│          │      │ claim/complete │
└──────────┘      └──────────┘      │ via MMIO       │
                                    └────────────────┘
```

### PLIC Register Map

| Address Offset | Register | Description |
|---|---|---|
| 0x0000–0x003F | Priority thresholds | Per-interrupt priority (0=disabled, 1–7=active) |
| 0x1000–0x107F | Pending bits | Bit N = 1 if interrupt N is pending |
| 0x2000–0x207F | Enable bits (Hart 0) | Bit N = 1 if interrupt N is enabled for Hart 0 |
| 0x2080–0x20FF | Enable bits (Hart 1) | Per-hart enable registers |
| 0x200000 | Priority threshold (Hart 0) | Min priority to reach Hart 0 |
| 0x200004 | Claim/Complete (Hart 0) | Read = claim (returns IRQ ID); Write = complete |

### PLIC Handler Flow

```c
// RISC-V PLIC interrupt handler (M-mode)
void handle_trap(void) {
    uint32_t irq_id;

    // 1. Claim: read claim register → returns highest-priority pending IRQ
    irq_id = *(volatile uint32_t *)PLIC_CLAIM;

    if (irq_id == 0) return;  // Spurious

    // 2. Dispatch to handler
    switch (irq_id) {
        case 1: uart_handler(); break;
        case 2: spi_handler();  break;
        case 3: dma_handler();  break;
        // ...
    }

    // 3. Complete: write IRQ ID back
    *(volatile uint32_t *)PLIC_CLAIM = irq_id;
}
```

### PLIC Multi-Hart Routing

The PLIC supports routing interrupts to specific harts (CPU cores):

```verilog
// PLIC with 2 harts, 32 IRQ sources
plic #(
    .N_IRQ(32),
    .N_HARTS(2)
) plic_inst (
    .irq_i    (irq_sources[31:0]),  // 32 interrupt inputs
    .meip_o   (meip[1:0]),          // Per-hart M-mode external interrupt
    .seip_o   (seip[1:0])           // Per-hart S-mode external interrupt
);
```

Each hart has its own enable and threshold registers. To route UART to Hart 0 only: set UART's enable bit in Hart 0's enable array, clear it in Hart 1's.

---

## ARM NVIC (Cortex-M in FPGA SoCs)

The NVIC (Nested Vectored Interrupt Controller) is used with ARM Cortex-M processors (Cortex-M0/M3/M33), which appear in some FPGA SoCs as the RPU (Real-Time Processing Unit) in Zynq UltraScale+.

### NVIC Key Features

| Feature | Detail |
|---|---|
| **Interrupt count** | 1–240 (configurable; Zynq US+ RPU has ~96) |
| **Priority levels** | 8 (3-bit) to 256 (8-bit); most implementations: 8 or 16 |
| **Vector table** | At VTOR address; each entry = 4-byte handler address |
| **Tail-chaining** | Back-to-back ISR without returning to thread mode |
| **Latency** | 12 cycles (deterministic, guaranteed) |

### Zynq UltraScale+ RPU Interrupt Map

| Source | RPU IRQ # | Notes |
|---|---|---|
| R5 Private Timer | 0 | Per-core |
| R5 WDT | 1 | Watchdog |
| PL → RPU (via IPI) | Varies | Inter-Processor Interrupt from PL |
| PMU | 4 | Power Management Unit |
| IPI (A53 → R5) | 15 | Inter-Processor Interrupt |

The RPU (Cortex-R5) uses the GIC indirectly through the IPI (Inter-Processor Interrupt) mechanism — it doesn't share the A53's GIC SPI numbers directly.

---

## FPGA Interrupt Design Patterns

### Pattern 1: Status Register Clear (Level-Triggered)

```verilog
// FPGA peripheral with level-triggered IRQ
// IRQ stays high until CPU reads status register

reg irq_pending;
reg [7:0] status_reg;

// Assert IRQ when event occurs
always @(posedge clk) begin
    if (event_occurs)
        irq_pending <= 1;
end

// Clear IRQ when CPU reads status
always @(posedge clk) begin
    if (axi_arvalid && axi_arready && (axi_araddr[11:0] == 12'h000))
        irq_pending <= 0;  // Read of status clears IRQ
end

assign irq_out = irq_pending;  // Level-triggered output
```

### Pattern 2: Pulse-to-Level Converter

If your FPGA source produces pulses (1-cycle wide), convert to level for the GIC:

```verilog
// Convert edge/pulse to level for GIC (level-sensitive)
reg irq_latched;

always @(posedge clk) begin
    if (pulse_event)
        irq_latched <= 1'b1;       // Latch the event
    else if (irq_clear)
        irq_latched <= 1'b0;       // Software clears via register write
end

assign pl_ps_irq = irq_latched;    // GIC sees level
```

### Pattern 3: Interrupt Aggregator (Shared IRQ Line)

When you have more FPGA interrupt sources than PL→PS IRQ lines:

```verilog
// 16 FPGA IRQ sources → 1 PL→PS IRQ line + status register
reg [15:0] irq_sources;
reg [15:0] irq_enabled;

// OR-reduce: any enabled and active source asserts the shared IRQ
assign pl_ps_irq = |(irq_sources & irq_enabled);

// CPU reads status register to find which source fired
assign status_read = irq_sources & irq_enabled;

// CPU writes clear register to acknowledge
always @(posedge clk) begin
    if (clear_write)
        irq_sources <= irq_sources & ~clear_data;
end
```

The CPU's ISR reads the status register, handles all pending sources, then writes the clear register.

---

## Linux Interrupt Configuration

### Kernel Driver: Request IRQ

```c
#include <linux/interrupt.h>

static irqreturn_t fpga_irq_handler(int irq, void *dev_id)
{
    struct my_dev *dev = dev_id;
    uint32_t status = readl(dev->regs + STATUS_REG);

    if (status & DMA_DONE_BIT)
        complete(&dev->dma_complete);

    if (status & ERROR_BIT)
        dev_err(dev->dev, "FPGA error: 0x%x\n", status);

    // Clear interrupt source
    writel(status, dev->regs + CLEAR_REG);
    return IRQ_HANDLED;
}

// Probe:
ret = devm_request_irq(dev, irq_num, fpga_irq_handler,
                        IRQF_TRIGGER_HIGH,  // Level, active-high
                        "fpga-accel", dev);
if (ret) return ret;
```

### Device Tree: Trigger Type Encoding

| Value | ARM GIC | Meaning |
|---|---|---|
| `1` | Edge rising | Edge-triggered, rising edge |
| `2` | Edge falling | Edge-triggered, falling edge |
| `4` | Level high | Level-triggered, active high (**most FPGA interrupts**) |
| `8` | Level low | Level-triggered, active low |

```dts
// Level-high (standard for FPGA → GIC)
interrupts = <0 89 4>;

// Edge-rising (for pulse sources)
interrupts = <0 89 1>;
```

### /proc/interrupts Debugging

```bash
cat /proc/interrupts
# Output:
#            CPU0  CPU1
#  27:     1024     0  GIC  89  fpga-accel    ← Routed to CPU0 only
#  28:        0  2048  GIC  90  fpga-dma      ← Routed to CPU1 only
#  32:    50000 50000  GIC  94  eth0           ← Shared across cores
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Edge-triggered on level source** | Interrupt fires once, then never again | Use level-triggered (type 4) for FPGA peripherals |
| **No IRQ clear in handler** | Interrupt fires repeatedly (infinite ISR loop) | Always clear source before returning from handler |
| **Wrong SPI number in DT** | Handler never fires, or fires for wrong device | Cross-check `interrupts = <0 N 4>` with Vivado PL→PS mapping |
| **PL→PS line not connected** | `cat /proc/interrupts` shows 0 events | Check Vivado block design: `pl_ps_irq` ports connected? |
| **Affinity on wrong core** | High latency on ISR | Pin time-critical IRQs to dedicated core |
| **PLIC claim without complete** | No further interrupts delivered | Always write IRQ ID back to claim/complete register |
| **Shared IRQ without status** | Can't determine which device fired | Add IRQ status register; OR-aggregate sources |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [UG1137 — Zynq MPSoC Software Developer Guide](https://www.xilinx.com/support/documents/sw_manuals/xilinx2022_2/ug1137-zynq-ultrascale-mpsoc-swdev.pdf) | AMD/Xilinx | GIC interrupt routing, PL→PS mapping |
| [DMA Architecture](dma_architecture.md) | This KB | DMA completion interrupts, descriptor IRQ flags |
| [Multi-Core Coherency](multi_core_coherency.md) | This KB | ACP, ACE, CCI, cache stashing |
| [Memory Map Design](memory_map_design.md) | This KB | Address decoder, device tree binding |
