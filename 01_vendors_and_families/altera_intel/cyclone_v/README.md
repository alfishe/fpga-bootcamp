[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel Cyclone V — 28nm FPGA Family

> **Anchor device for this knowledge base.** Available in two flavors: [SoC with hard ARM Cortex-A9](soc/README.md) and [FPGA-only logic](fpga_only/README.md). Both share the same 28nm fabric (ALM, M10K, DSP, PLLs).

The Cyclone V is a 28nm FPGA family that powers the MiSTer retro-computing platform, the DE10-Nano development board, and thousands of industrial embedded systems.

---

## Directory Structure

| Directory | Covers |
|---|---|
| **[soc/](soc/README.md)** | **★ SE/SX/ST variants** — HPS (dual Cortex-A9), AXI bridges, HPS peripherals, boot sequence, DE10-Nano/MiSTer specifics, address map |
| **[fpga_only/](fpga_only/README.md)** | **E/GX/GT variants** — transceiver details (3G/6G), PCIe Gen2, SoC vs FPGA-only decision matrix, when each wins |

## Quick Variant Reference

| Variant | Type | Transceivers | PCIe | Max LEs | Max DSP | Max M10K |
|---|---|---|---|---|---|---|
| **Cyclone V SE** | SoC | No | No | 40K–110K | 112–224 | 1.7–5.4 Mb |
| **Cyclone V SX** | SoC | 6× 3.125 Gbps | Gen2 ×1 | 40K–110K | 112–224 | 1.7–5.4 Mb |
| **Cyclone V ST** | SoC | 6× 6.144 Gbps | Gen2 ×4 | 85K–301K | 168–342 | 4.2–12.2 Mb |
| **Cyclone V E** | FPGA-only | No | No | 25K–301K | 25–342 | 1.7–12.2 Mb |
| **Cyclone V GX** | FPGA-only | 4–8× 3.125 Gbps | Gen2 ×1 | 77K–301K | 150–342 | 4.2–12.2 Mb |
| **Cyclone V GT** | FPGA-only | 4–8× 6.144 Gbps | Gen2 ×4 | 77K–301K | 150–342 | 4.2–12.2 Mb |

> **DE10-Nano / MiSTer:** 5CSEBA6U23I7 — SE variant, 110K LEs.

---

## Shared FPGA Fabric (common to all variants)

### Adaptive Logic Module (ALM)

Each ALM contains a fracturable 6-input LUT (can split into two smaller LUTs), two flip-flops, and a full adder with carry chain. 10 ALMs form a **Logic Array Block (LAB)**.

One ALM can implement:
- One 6-input function
- Two independent 4-input functions (shared inputs)
- A 4-input LUT + full adder (carry chain for arithmetic)

### M10K Memory Block

| Property | Value |
|---|---|
| **Size** | 10,240 bits (1,280 × 8 or 1,024 × 10) |
| **Ports** | Dual-port |
| **Modes** | Simple dual-port, true dual-port, ROM, FIFO |
| **FIFO** | Hard FIFO control logic (no ALM consumption) |
| **Cascade** | Can cascade for deeper FIFOs |

557 M10K blocks in a 5CSEA6 = 6.8 Mb of on-chip SRAM.

### Variable-Precision DSP

| Mode | Multipliers per block | Accumulator |
|---|---|---|
| 3× 9×9 | 3 | No accumulation |
| 2× 18×18 | 2 | 44-bit |
| 1× 27×27 | 1 | 64-bit |

5CSEA6 has 112 blocks = 224 18×18 multipliers or 112 27×27 multipliers.

### FPGA PLLs (6 total)

| PLL Type | Count | Use |
|---|---|---|
| **Fractional PLL (fPLL)** | 4 | General-purpose synthesis, DDR, spread-spectrum |
| **Integer PLL** | 2 | Low-jitter applications |

Each fPLL supports fractional-N multiplication (VCO: 600–1,600 MHz).

### Clocking Reference

The HPS (SoC only) requires a 25 MHz reference and generates:
- **MPU clock:** up to 925 MHz
- **L3/L4 clock:** 200/100 MHz
- **SDRAM clock:** up to 400 MHz (DDR3-800)

### Configuration Methods

| Method | SoC | FPGA-Only |
|---|---|---|
| **FPP ×16 (via HPS)** | ✓ Default | ✗ |
| **AS ×1/×4 (Active Serial)** | ✓ Fallback | ✓ Default |
| **PS (Passive Serial)** | ✓ | ✓ |
| **JTAG** | ✓ Debug | ✓ Debug |

---

## References

| Source | Path |
|---|---|
| Cyclone V Device Handbook (vol. 1–3) | Intel FPGA Documentation |
| DE10-Nano Manual | Terasic |
| MiSTer Wiki | https://github.com/MiSTer-devel/Wiki_MiSTer |
