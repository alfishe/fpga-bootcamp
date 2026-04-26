[← Lattice Home](../README.md) · [← Section Home](../../README.md)

# Lattice CrossLink-NX — 28nm FD-SOI with Hard MIPI

CrossLink-NX is Lattice's newer FPGA fabric on a 28nm Fully Depleted Silicon-On-Insulator (FD-SOI) process. Delivers **3× lower soft error rate** than bulk CMOS and **2× lower static power** vs equivalent ECP5. Purpose-built for embedded vision and MIPI video pipelines.

---

## Specifications

| Feature | CrossLink-NX | CrossLinkU-NX |
|---|---|---|
| **LUTs** | 17K–39.5K | 17K–39K |
| **BRAM** | 1.4–4.2 Mb | 1.4–4.2 Mb |
| **DSP** | up to 56 (18×18) | up to 56 |
| **SERDES** | None | None |
| **MIPI D-PHY** | 2× 4-lane (2.5 Gbps/lane) + CSI/DSI hard IP | 3× 4-lane + USB 3.0 PHY |
| **PCIe** | None | None |
| **DDR** | LPDDR4/DDR3 (1,600 Mbps) | LPDDR4 (1,067 Mbps) |
| **Process** | 28nm FD-SOI | 28nm FD-SOI |

---

## CrossLink-NX vs ECP5

| When to use... | Pick |
|---|---|
| MIPI CSI/DSI video pipelines | **CrossLink-NX** — hard MIPI + LPDDR4, purpose-built |
| General-purpose FPGA | **ECP5** — more mature open tools, wider board choices, lower cost |
| Needs open-source flow | ECP5 for now — CrossLink-NX tools are early-stage (Project Oxide) |
| Commercial product, power matters | **CrossLink-NX** — FD-SOI yields 2× lower static power |

---

## Development Boards

### Lattice (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **CrossLink-NX EVN** | LIFCL-40 | 39K | MIPI CSI/DSI ×2 (4-lane), LPDDR4, USB, GPIO headers | ~$199 | MIPI video pipeline eval |
| CrossLinkU-NX EVN | LIFCL-40U | 39K | MIPI ×3 + USB 3.0 PHY, LPDDR4 | ~$249 | USB 3.0 + MIPI combo eval |

### Choosing a Board

| You want... | Get... |
|---|---|
| MIPI CSI/DSI video pipeline | CrossLink-NX EVN (~$199) |
| MIPI + USB 3.0 combo | CrossLinkU-NX EVN (~$249) |

---

## References

| Source | Path |
|---|---|
| CrossLink-NX Data Sheet | FPGA-DS-02047 |
| CrossLink-NX EVN Board | Lattice evaluation kits |
