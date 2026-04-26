[← Cyclone V Home](../README.md) · [← Intel/Altera Home](../../README.md) · [← Section Home](../../../README.md)

# Cyclone V FPGA-Only (E/GX/GT) — Logic Without the Hard CPU

Identical 28nm FPGA fabric to the SoC variants, but **no HPS** (no hard ARM cores, no DDR controller, no USB/EMAC/SD peripheral block). Lower cost and simpler design for applications that don't need embedded Linux or a hard processor — or where the CPU lives on a separate chip.

---

## Variant Table

| Variant | Transceivers | PCIe | LEs range | DSP range | M10K | Key Differentiator |
|---|---|---|---|---|---|---|
| **Cyclone V E** | None | None | 25K–301K | 25–342 | 1.7–12.2 Mb | Pure logic, lowest cost, 15–30% cheaper than SE |
| **Cyclone V GX** | 4–8× 3.125 Gbps | Gen2 ×1 | 77K–301K | 150–342 | 4.2–12.2 Mb | Entry-level transceivers, PCIe x1 |
| **Cyclone V GT** | 4–8× 6.144 Gbps | Gen2 ×4 | 77K–301K | 150–342 | 4.2–12.2 Mb | Full-speed 6G transceivers, PCIe ×4 |

---

## SoC vs FPGA-Only — Decision Matrix

| Scenario | Pick |
|---|---|
| No CPU needed, pure datapath (DSP pipeline, protocol bridge, video passthrough) | **Cyclone V E** — cheaper, simpler board |
| Needs PCIe Gen2 ×1 | **Cyclone V GX** |
| Needs 6G transceiver + bare-metal soft CPU (Nios II) | **Cyclone V GT** |
| Needs Linux + hard CPU + DDR3 controller on-chip | **Cyclone V SoC** (SE/SX/ST) |
| Needs open-source toolchain | Neither — use **Lattice ECP5** |
| BOM cost is dominant factor, CPU is off-chip MCU on SPI/I2C | **Cyclone V E** |

---

## Key Architectural Differences from SoC

| Feature | Cyclone V SoC | Cyclone V FPGA-Only |
|---|---|---|
| **Die area** | ~60% HPS + ~40% fabric | ~100% fabric |
| **DDR controller** | Hard DDR3/DDR3L/LPDDR2 in HPS | Soft controller in fabric (consumes LEs) |
| **PCIe** | Hard IP in HPS (SE has none) | Hard IP in fabric (E has none) |
| **Configuration** | Via HPS (FPP ×16) or external | External only (AS ×1/×4, PS, JTAG, FPP) |
| **Boot** | HPS boots first, then configures FPGA | FPGA configures directly from external flash |
| **Linux** | Full Linux on hard Cortex-A9 | Soft CPU only (Nios II, ~2K–5K LEs consumed) |
| **Error correction** | HPS has ECC on L2/OCRAM/DDR | No ECC (unless soft IP added) |
| **Power sequencing** | Complex — 4+ rails, strict HPS power-up order | Simpler — 2–3 rails |

---

## Development Boards

| Board | Variant | FPGA (LEs) | Notable IO | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Cyclone V GX Starter Kit** | 5CGXFC5C6 (GX) | 77K | PCIe ×4 edge, HSMC, GbE, SDI video | ~$499 | Transceiver+PCIe development |
| Cyclone V GT Dev Kit | 5CGTFD9E5 (GT) | 301K | PCIe ×4, FMC, HSMC, 6G transceivers | ~$799 | High-speed 6G transceiver, large LEs |
| BeMicro CV | 5CEFA4 (E) | 40K | USB Blaster on-board, GPIO, accelerometer | ~$49 | Ultra-low-cost entry, bare-bones |
| C5G (QMTech) | 5CEFA2/5 (E) | 25K/77K | GPIO, DDR3 soft controller space | ~$30–60 | Low-cost FPGA-only hobbyist board |

---

## When FPGA-Only Wins Over SoC

1. **Pure acceleration card** — PCIe endpoint with DMA engine, no need for local CPU. Cyclone V GX/GT is ideal: PCIe hard block + fabric for DMA.
2. **Cost-sensitive consumer product** — MCU is already a $1 STM32 on the same PCB. Cyclone V E eliminates the HPS die area cost.
3. **Legacy replacement** — replacing an old Cyclone IV or Spartan-6 with no new CPU requirement.
4. **Board simplification** — fewer rails, no DDR routing, no USB PHY, smaller PCB.

---

## References

| Source | Path |
|---|---|
| Cyclone V Device Overview | Intel FPGA documentation |
