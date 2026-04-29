[← Section Home](../README.md) · [← Project Home](../../README.md)

# 01-D — Gowin Semiconductor

The ultra-low-cost challenger from China — Tang Nano boards start under $10 with the FPGA included. Founded in 2014, Gowin has rapidly captured the budget FPGA segment with the LittleBee (55nm) and Arora (55nm/22nm) families. Their free (but proprietary) Gowin EDA IDE works on Windows and Linux, and the open-source Project Apicula (Yosys+nextpnr) supports LittleBee devices. The GW1NSR variant includes a hard PicoRV32 RISC-V core — a $7 SoC FPGA.

---

## Why Gowin Matters

Gowin is the **price floor of functional FPGAs** — Tang Nano boards deliver a usable FPGA + programmer + USB for $6–15. This makes FPGA technology accessible to hobbyists, students, and cost-sensitive embedded products where even Lattice iCE40 is too expensive at scale. Gowin also has growing open-source toolchain support (Project Apicula), making them an alternative to Lattice for open-source-first designs.

| Advantage | Detail |
|---|---|
| **Lowest cost** | Tang Nano 1K: $6 (GW1NZ-1, 1,152 LUTs). Tang Nano 9K: $15 (GW1NR-9, 8,640 LUTs) |
| **Integrated flash+PSRAM** | GW1NR devices include on-package 64Mbit PSRAM — no external DRAM needed for small framebuffers |
| **Hard RISC-V SoC** | GW1NSR: PicoRV32 core at ~30 MHz + FPGA fabric on one die. $7 in volume |
| **Open-source progress** | Project Apicula: Yosys synthesis + nextpnr-himbaechel place-and-route for GW1N/GW1NZ/GW1NS |
| **Free IDE** | Gowin EDA is free (license file download, no cost) for all devices including GW2A and GW5A |

---

## Technology Platforms

| Platform | Process | Families | Key Features |
|---|---|---|---|
| **LittleBee** | 55nm | GW1N, GW1NR, GW1NSR, GW1NZ | 1K–9K LUTs, integrated flash, PSRAM (NR), hard PicoRV32 (NSR). Open-source Apicula flow |
| **Arora** | 55nm | GW2A | 18K–55K LUTs, DDR2/DDR3 hard controllers, 2.5–6.25 Gbps SERDES |
| **Arora-V** | 22nm | GW5A, GW5AT | 25K–138K LUTs, LPDDR4, PCIe Gen2 ×4, 6.25G SERDES, higher performance |

---

## Family Directories

| Directory | Coverage |
|---|---|
| [littlebee/](littlebee/README.md) | **LittleBee (55nm)** — GW1N-1 through GW1N-9C, GW1NR (integrated flash+PSRAM), GW1NSR (hard PicoRV32 SoC). $1.50–$10 chips, Tang Nano boards from $6. Project Apicula open-source flow |
| [arora/](arora/README.md) | **Arora GW2A (55nm) & Arora-V GW5A (22nm)** — DDR2/DDR3/LPDDR4 hard controllers, 2.5–6.25 Gbps SERDES, PCIe Gen2 ×4 (GW5A-25), Tang Primer boards ($40–50) |

---

## Family Comparison

| Family | Process | LUTs (max) | SERDES | Key Differentiator | Chip Price | Board Price |
|---|---|---|---|---|---|---|
| GW1NZ-1 (Tang Nano) | 55nm | 1,152 | None | Cheapest functional FPGA board | $1.50 | $6 |
| GW1N-9C | 55nm | 8,640 | None | Best open-source LittleBee, 8× DSP | $5 | N/A |
| GW1NR-9 | 55nm | 8,640 | None | 64Mbit PSRAM on-package | $5 | $15 (Tang Nano 9K) |
| **GW1NSR-4C** | 55nm | 4,608 | None | Hard PicoRV32 RISC-V SoC | $7 | $20 (Tang Nano 4K) |
| GW2A-18 | 55nm | 20,736 | 2.5 Gbps | DDR3 hard controller, Tang Primer | $10–15 | $40 |
| GW2A-55 | 55nm | 55,296 | 6.25 Gbps | Highest LittleBee/Arora density | $20–40 | $50+ |
| GW5A-25 (Arora-V) | 22nm | 25,344 | 6.25 Gbps | PCIe Gen2 ×4, LPDDR4, 22nm process | $30–60 | $100+ |
| GW5AT-138 | 22nm | 138K | 6.25 Gbps (×16) | Highest Gowin density, large SERDES count | $100+ | $500+ |

---

## Development Board Highlights

| Board | Family | Key Spec | Price | Best For |
|---|---|---|---|---|
| **Tang Nano 9K** | GW1NR-9 | 8,640 LUTs, PSRAM, HDMI, USB-C, RGB LED | ~$15 | Best value LittleBee board |
| Tang Nano 4K | GW1NSR-4C | 4,608 LUTs, hard RISC-V, HDMI, USB-C | ~$20 | Cheapest RISC-V SoC FPGA |
| Tang Nano 1K | GW1NZ-1 | 1,152 LUTs, 1× PLL, USB-C | ~$6 | Absolute cheapest FPGA entry |
| Tang Nano 20K | GW2A-18 | 20,736 LUTs, DDR3, HDMI, USB-C | ~$27 | Best value Arora entry |
| **Tang Primer 25K** | GW5A-25 | 25,344 LUTs, PCIe Gen2 ×4, LPDDR4, PMOD | ~$50 | PCIe on a budget, 22nm |
| Sipeed Tang Mega 138K | GW5AT-138 | 138K LUTs, 16× 6.25G SERDES, PCIe, DDR4 | ~$100+ | Highest Gowin density board |

---

## Best Practices

1. **Tang Nano 9K for learning and simple projects** — $15 gets you 8,640 LUTs + PSRAM + HDMI + USB-C programmer. The best price-to-capability ratio in FPGAs, period.
2. **GW1NSR-4C for embedded RISC-V + FPGA** — a $7 chip with a hard RISC-V core and 4,608 LUTs. Ideal for adding custom peripherals to a microcontroller-class CPU.
3. **GW5A-25 for PCIe on a budget** — the cheapest FPGA with a hard PCIe Gen2 ×4 block. Good for low-cost PCIe accelerators.
4. **Use open-source Apicula for LittleBee** — Yosys+nextpnr flow works for GW1N/GW1NR/GW1NSR. Gowin EDA as fallback for features Apicula doesn't yet cover.
5. **Gowin EDA for Arora/GW5A** — open-source tools don't yet support Arora-V. The free Gowin IDE is the only option, but it works.

## Pitfalls

1. **LittleBee routing is tight above 80% utilization** — the 55nm process node limits routing resources. Expect timing closure challenges at high utilization.
2. **GW1NSR PicoRV32 is NOT Linux-capable** — no MMU, no FPU, ~30 MHz. It's a microcontroller replacement, not an application processor.
3. **Gowin EDA is Windows-centric** — the Linux build exists but has quirks. The Windows version is the primary development target.
4. **SERDES on GW2A is limited (2.5–6.25 Gbps)** — fine for SATA, PCIe Gen1, but not for modern high-speed protocols.
5. **Documentation quality varies** — Gowin datasheets and user guides have improved but may have translation gaps. Cross-reference with community resources (Tang wiki, Sipeed docs).
6. **Chip availability outside China** — distributors like Seeed and Mouser carry Tang boards, but bare chips and less popular models may have lead time issues.

---

## References

| Source | Description |
|---|---|
| Gowin Semiconductor | https://www.gowinsemi.com — official site, datasheets, Gowin EDA download |
| Sipeed Tang Wiki | https://wiki.sipeed.com/hardware/en/tang/ — Tang Nano/Primer/Mega board documentation |
| Project Apicula | https://github.com/YosysHQ/apicula — open-source Gowin bitstream documentation |
| nextpnr-himbaechel | https://github.com/YosysHQ/nextpnr — open-source P&R with Gowin support |
| Gowin EDA License | https://www.gowinsemi.com/en/support/license/ — free license request |
