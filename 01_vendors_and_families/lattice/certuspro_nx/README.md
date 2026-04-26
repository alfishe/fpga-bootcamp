[← Lattice Home](../README.md) · [← Section Home](../../README.md)

# Lattice CertusPro-NX — 28nm FD-SOI with PCIe & SERDES

CertusPro-NX scales the CrossLink-NX FD-SOI architecture to 96K LUTs and adds PCIe Gen3 ×4, 10.3 Gbps SERDES, and larger block RAM. Positioned as Lattice's mid-range workhorse with FD-SOI radiation and power advantages.

---

## Specifications

| Feature | CertusPro-NX |
|---|---|
| **LUTs** | 96K |
| **BRAM** | 7.3 Mb + large RAM blocks (LRAM) |
| **DSP** | up to 156 (18×18 + pre-adder) |
| **SERDES** | Up to 8× 10.3 Gbps |
| **PCIe** | Gen3 ×4 hard IP |
| **MIPI D-PHY** | 2× 4-lane |
| **DDR** | DDR3/LPDDR4 (1,600 Mbps) |
| **Process** | 28nm FD-SOI |

---

## Position vs ECP5 and CrossLink-NX

- More logic than CrossLink-NX (96K vs 39K LUTs)
- Adds PCIe Gen3 and SERDES (CrossLink-NX has neither)
- FD-SOI advantages over ECP5's bulk 40nm (radiation tolerance, lower static power)
- Open-source tooling is nonexistent — Radiant proprietary toolchain only

---

## Development Boards

### Lattice (First-Party)

| Board | FPGA | LUTs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **CertusPro-NX EVB** | LFCPNX-100 | 96K | PCIe Gen3 ×4, 10.3G SERDES ×8, MIPI D-PHY ×2, DDR3, FMC | ~$599 | FD-SOI PCIe + SERDES evaluation |

### Choosing a Board

| You want... | Get... |
|---|---|
| FD-SOI PCIe + SERDES mid-range | CertusPro-NX EVB (~$599) |
| Cheaper PCIe + SERDES alternative | ECP5 Versa (~$499) or Cyclone 10 GX (~$549) |

---

## References

| Source | Path |
|---|---|
| CertusPro-NX Data Sheet | Lattice documentation |
