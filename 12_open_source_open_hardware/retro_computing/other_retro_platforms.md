[← 12 Open Source Open Hardware Home](../README.md) · [← Retro Computing Home](README.md) · [← Project Home](../../../README.md)

# Other Retro FPGA Platforms

Beyond MiSTer and MiST, a rich ecosystem of alternative FPGA retro-hardware platforms exists — each with unique tradeoffs in cost, capability, and community support.

---

## Platform Comparison

| Platform | FPGA | LEs | RAM | Price | Cores | Status | Key Differentiator |
|---|---|---|---|---|---|---|---|
| **SiDi** | Cyclone IV EP4CE22 | 22K | 32 MB SDRAM | ~$80 | 40+ | Active | Cheapest Cyclone retro platform |
| **SiDi128** | Cyclone V (49K) | 49K | 128 MB SDRAM | ~$160 | 50+ | Active | Cyclone V + 128 MB, MiSTer-lite |
| **ZX-Uno** | Xilinx Spartan-6 LX9/LX16 | 9K/16K | 32 MB SDRAM | ~$60 | 30+ | Mature | Spectrum-focused, compact |
| **ZX-Uno Next** | Xilinx Artix-7 (35T) | 33K | 32 MB SDRAM | ~$130 | Growing | New | Spectrum Next compatibility |
| **FPGA Arcade Replay** | Xilinx Spartan-6 LX45 | 43K | 64 MB DDR2 | ~$200 (rare) | 20+ | Dormant | Daughterboard architecture |
| **MARS** | Xilinx Artix-7 (200T?) | 215K | DDR3 | TBD | TBD | In development | Ambitious MiSTer successor |
| **MiSTeX** | Multi-target (DE10-Nano, MiST, SiDi128) | Varies | Varies | Free (software) | 70+ | Active | Runs MiSTer cores on MiST/SiDi |
| **MultiComp** | Any FPGA (generic VHDL) | ~3K+ | None required | Free | 5+ | Educational | Generic VHDL computer-on-FPGA |

## Selection Guide

| I want... | Platform |
|---|---|
| MiSTer-like experience, lower cost | **SiDi128** — Cyclone V, 128 MB, MiSTeX compatible |
| Cheapest possible retro FPGA | **SiDi** — $80 for Cyclone IV + 32 MB |
| ZX Spectrum authenticity | **ZX-Uno** — Spectrum community, bespoke cores |
| The most future-proof retro FPGA | **MARS** (when released) — Artix-7 200T, designed as MiSTer successor |
| Run MiSTer cores on my existing MiST/SiDi | **MiSTeX** — software bridge, 70+ cores supported |
| Learn FPGA computing concepts | **MultiComp** — clean VHDL, runs on any dev board |

---

## Original Stub Description

Survey: **SiDi / SiDi128, ZX-Uno, FPGA Arcade Replay, MARS, MiSTeX, MultiComp** — comparison table: FPGA chip, core count, community size, price, active development status

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
