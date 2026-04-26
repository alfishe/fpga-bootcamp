[← Intel/Altera Home](../README.md) · [← Section Home](../../README.md)

# Intel Stratix 10 — 14nm Tri-Gate Density & Bandwidth Peak

Stratix 10 was Intel's flagship throughout the late 2010s. It introduced the **HyperFlex** architecture (pipeline registers in every routing segment) and integrated HBM2 memory stacks directly on the FPGA package. The SoC variant upgrades to a quad Cortex-A53 (64-bit ARMv8-A).

---

## Specifications

| Feature | Specification |
|---|---|
| **Process** | 14nm Tri-Gate (Intel FinFET) |
| **LEs** | 378K–5,510K |
| **ALMs** | 143K–2,081K |
| **M20K blocks** | 1,170–11,721 (up to 229 Mb) |
| **DSP** | Up to 5,760 (18×19 + 27×27, hard FP32) |
| **Transceivers** | Up to 144× 28.3 Gbps (GX/SX) or 57.8 Gbps (TX/DX/GX) |
| **PCIe** | Gen3/Gen4 x16 hard IP |
| **HBM2** | Up to 8 GB integrated on package (MX/NX variants) |
| **100G Ethernet** | Hard MAC + PCS |
| **SoC** | Quad Cortex-A53 (64-bit ARMv8-A, 1.2 GHz) |

---

## HyperFlex Architecture

HyperFlex adds an optional pipeline register to **every routing segment** in the FPGA fabric. The toolchain automatically re-times critical paths by inserting these registers, which improves fmax without manual pipeline insertion. This is fundamentally different from conventional FPGA architectures where registers only exist in ALMs.

**Trade-off:** HyperFlex improves fmax but increases latency by 1 cycle per pipelined hop. Designs relying on low-latency paths (<5 cycles) may see latency penalties beyond acceptable limits.

---

## When Stratix 10 is Justified

You need Stratix 10 (over Arria 10) when you hit **any** of:
- Need >1.5M LEs (Arria 10 caps at 1.15M)
- Need HBM2 (Arria 10 has no HBM)
- Need >28 Gbps transceivers or 58G PAM4
- Need 64-bit ARM CPU (Arria 10's HPS is 32-bit Cortex-A9)
- FPGA fabric is the timing bottleneck and HyperFlex registers could close timing without manual pipelining

---

## Pitfall: HyperFlex Latency

The tool may insert dozens of pipeline stages across the fabric. If your design path includes a fixed-latency external interface (e.g., ADC DDR capture), validate that HyperFlex hasn't pushed latency beyond the allowed external window.

---

## Development Boards

### Intel (First-Party)

| Board | Stratix 10 Variant | LEs | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|---|
| **Stratix 10 GX Dev Kit** | 1SG280LU3F50 (GX) | 2,753K | 28 Gbps XCVR ×32, PCIe Gen3 ×16, DDR4, FMC+, QSFP28 ×4 | ~$7,995 | General Stratix 10 eval + 28G transceivers |
| **Stratix 10 MX Dev Kit** | 1SM21CHU2F55 (MX) | 2,100K | HBM2 8 GB integrated, 57.8 Gbps XCVR, PCIe Gen3 ×16, QSFP28 | ~$12,995 | HBM2 memory bandwidth dev (460 GB/s) |
| Stratix 10 TX Dev Kit | 1ST280EY2F55 (TX) | 2,753K | 57.8 Gbps PAM4 XCVR ×48, PCIe Gen3 ×16, QSFP-DD | ~$15,995 | PAM4 58G transceiver evaluation |
| Stratix 10 SoC Dev Kit | 1SX280LU2F50 (SoC) | 2,753K | Quad Cortex-A53, DDR4, PCIe Gen3 ×16, FMC+, 28G XCVR | ~$10,995 | 64-bit ARM SoC FPGA eval |

### Third-Party

| Board | Stratix 10 Variant | LEs | Key Feature | Approx. Price | Best For |
|---|---|---|---|---|---|
| **BittWare 520N-MX** | 1SM21B (MX) | 2,100K | PCIe ×16 card, HBM2 8 GB, QSFP28 ×4, 100G Eth-ready | ~$8,000+ | Datacenter HBM2 FPGA accelerator |
| BittWare IA-840F | 1SG280H (GX) | 2,753K | Dual QSFP28, DDR4, PCIe Gen3 ×16 | ~$6,000+ | Networking/telecom PCIe card |

### Choosing a Board

| You want... | Get... |
|---|---|
| HBM2 high-bandwidth memory | Stratix 10 MX Dev Kit or BittWare 520N-MX |
| PAM4 58G transceiver evaluation | Stratix 10 TX Dev Kit |
| General Stratix 10 development | Stratix 10 GX Dev Kit |
| 64-bit ARM SoC | Stratix 10 SoC Dev Kit |
| Production PCIe card | BittWare 520N-MX or IA-840F |

---

## References

| Source | Path |
|---|---|
| Stratix 10 Device Overview | Intel FPGA documentation |
| Stratix 10 HyperFlex Architecture | Intel FPGA documentation |
