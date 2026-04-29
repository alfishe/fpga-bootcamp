[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# VexRiscv — SpinalHDL's Configurable RISC-V

VexRiscv is the most flexible open-source RISC-V soft core — generated from SpinalHDL, not hand-written Verilog, allowing unprecedented runtime configuration of pipeline depth, ISA extensions, and cache topology.

---

## Architecture

| Parameter | Options |
|---|---|
| **ISA** | RV32I[M][A][F][D][C] — any combination |
| **Pipeline** | 2-stage (smallest) to 5-stage (highest fmax) |
| **LUT Usage** | ~1,200 (RV32I, 2-stage) to ~3,000 (RV32IMAC, 5-stage) |
| **fmax (FPGA)** | 200+ MHz on Artix-7, Cyclone V, ECP5 |
| **Debug** | JTAG (OpenOCD + GDB), full hardware breakpoints |
| **MMU** | Optional, Linux-capable with MMU enabled |

## Why SpinalHDL Matters

VexRiscv isn't written in Verilog — it's a **SpinalHDL software library** that generates Verilog at build time. This means:
- **Plugin architecture**: Add FPU, MMU, caches, or custom instructions by adding plugins, not modifying RTL
- **Single config file**: One `VexRiscvConfig` object defines the entire CPU
- **No forked code**: Everyone uses the same source; configuration handles variations

## Quick Integration (with LiteX)

```python
# LiteX SoC with VexRiscv CPU — single config file
from litex.soc.integration.soc_core import SoCCore
from litex.soc.cores.cpu.vexriscv import VexRiscv

class MySoC(SoCCore):
    def __init__(self):
        super().__init__(
            cpu=VexRiscv(
                variant="linux",  # or "standard", "minimal", "debug"
            ),
            l2_size=8192,
        )
```

## Use Cases

| Use Case | Variant | Why |
|---|---|---|
| LiteX SoC CPU (most common) | "standard" variant | Balanced performance/size |
| Linux on soft core | "linux" variant (MMU + FPU) | One of few soft cores that runs mainline Linux |
| Minimal controller | "minimal" variant | ~1,200 LUTs, bare-metal |

---

## Original Stub Description

Documentation for VexRiscv deep dive.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](README.md)
