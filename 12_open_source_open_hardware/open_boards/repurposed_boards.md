[← 12 Open Source Open Hardware Home](../README.md) · [← Open Boards Home](README.md) · [← Project Home](../../../README.md)

# Repurposed FPGA Boards

Commercial hardware repurposed for open FPGA development — getting 25K+ LUT FPGAs for under $20 by hacking LED controllers and thin clients.

---

## The Repurposed Boards

| Board | Original Purpose | FPGA | LUTs | RAM | Cost | Open Toolchain |
|---|---|---|---|---|---|---|
| **Colorlight i5** | LED display controller | Lattice ECP5 LFE5U-25F | 25K | 32 MB SDRAM | ~$15 | ✅ |
| **Colorlight i9** | LED display controller | Lattice ECP5 LFE5U-45F | 45K | 32 MB SDRAM | ~$30 | ✅ |
| **Colorlight 5A-75B** | LED display controller | Lattice ECP5 LFE5U-85F | 85K | 32–64 MB SDRAM | ~$50 | ✅ |
| **Pano Logic G2** | Zero client / thin client | Xilinx Spartan-6 XC6SLX150T | 150K | 128 MB DDR3 | ~$20 (ebay) | 🟡 (Xilinx ISE, no open flow) |

## Colorlight Deep Dive

The Colorlight boards are the **most popular open FPGA dev boards by volume** — not marketed as dev boards, but the ECP5 variants are fully supported by the open toolchain.

### What You Get
- **Gigabit Ethernet** (RTL8211 PHY) — already routed
- **Dual SDRAM** banks — independent memory channels
- **Standard Lattice JTAG** header — connect FT2232H for programming
- **5V barrel or terminal block power** — easy to power

### What You Need to Add
1. **External JTAG programmer** (FT2232H module, ~$10)
2. **A 3D-printed case** (open designs available)
3. **Pin mapping** — well-documented by the community

### Limitations
- No PMOD/Arduino-style headers — everything is through the original pin headers
- No USB UART built-in — add via GPIO pins
- SDRAM only (no DDR) — sufficient for most open projects, limiting for very high bandwidth

---

## Original Stub Description

**Colorlight i5/i9** (ECP5 LED controller repurposed for open FPGA), **Pano Logic G2** — recycling commercial hardware at \u003c$20, open toolchain compatible

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
