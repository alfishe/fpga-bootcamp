[← 06 Ip And Cores Home](../README.md) · [← Vendor Ip Home](README.md) · [← Project Home](../../../README.md)

# Lattice IP Ecosystem — Diamond & Radiant

Lattice's IP tools have evolved from Diamond's IPexpress to Radiant's Clarity Designer. The catalog is smaller than Xilinx/Intel but well-suited to Lattice's target markets: low-power, small-form-factor, and interface-bridging applications.

---

## Tool Evolution

| Tool | IDE | IP Tool | Families | Status |
|---|---|---|---|---|
| **Diamond** | Diamond 3.x | IPexpress | ECP5, MachXO2/3, iCE40 (some) | Mature, legacy focus |
| **Radiant** | Radiant 2024.x | Clarity Designer | CertusPro-NX, CrossLink-NX, Avant | Active development |

---

## IP Catalog by Category

| Category | IP Blocks | Availability |
|---|---|---|
| **Clocking** | PLL, DCMA (Dynamic Clock Mux) | All families |
| **Memory** | DDR2/3 Controller (ECP5), LPDDR2/3 (CrossLink-NX) | Family-dependent |
| **High-Speed I/O** | MIPI D-PHY (hard on CrossLink-NX), HDMI/DVI TX, LVDS, SGMII | MIPI is Lattice's killer IP |
| **Bus Interfaces** | I2C, SPI, UART, Wishbone | All families |
| **Ethernet** | GigE MAC (soft), SGMII PCS (hard on ECP5 DCU) | ECP5 + CertusPro-NX |
| **DSP** | FIR, Multiply/Accumulate, Cordic | Limited vs Xilinx/Intel |
| **Processor** | LatticeMico8, LatticeMico32, RISC-V (third-party via VexRiscv) | Soft CPUs available |
| **PCIe** | PCIe Gen2 x1/x2/x4 (hard on ECP5-5G), Gen3 x4 (CertusPro-NX) | Hard IP free |

---

## Lattice's Differentiator: MIPI

Lattice dominates the MIPI bridging market. CrossLink-NX has hardened MIPI D-PHY:

- **MIPI CSI-2 RX** — 1–4 lanes, up to 2.5 Gbps/lane (camera input)
- **MIPI DSI TX** — 1–4 lanes (display output)
- **MIPI D-PHY** — hard IP, no LUTs consumed
- **Use case:** Camera → FPGA processing → Display (VR/AR, machine vision, drones)

---

## IPexpress vs Clarity Designer

| Feature | IPexpress (Diamond) | Clarity Designer (Radiant) |
|---|---|---|
| Interface | Standalone wizard per IP | Integrated module/IP block design |
| Bus connection | Manual | Drag-and-drop (simplified) |
| Parameter GUI | Text-based + tabbed | Modern GUI with preview |
| Simulation | Separate ModelSim project | Integrated with Radiant Sim |

---

## Best Practices

1. **Use hard MIPI D-PHY on CrossLink-NX** — don't try to implement MIPI in soft logic
2. **PCIe hard block on ECP5-5G is free** — no license fee, a differentiator vs Gowin
3. **LatticeMico32 is deprecated** — use VexRiscv or LiteX for new RISC-V designs
4. **DDR controller is family-specific** — verify availability before selecting FPGA

---

## References

- Lattice Diamond / Radiant Help → IP User Guides
- Lattice TN1278: ECP5 High-Speed I/O Interface
- Lattice CrossLink-NX MIPI D-PHY User Guide
