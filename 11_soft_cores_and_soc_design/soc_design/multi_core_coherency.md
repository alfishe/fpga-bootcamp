[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Multi-Core Coherency on FPGA SoCs

Adding a second CPU core sounds simple, but cache coherency makes it one of the hardest problems in FPGA SoC design. Here's when multi-core makes sense — and when it doesn't.

---

## The Coherency Problem

```
Core 0 (L1: addr X = 42)     Core 1 (L1: addr X = 42)
        │                              │
        │ Core 0 writes X = 99         │
        │ (L1 updated, DDR still 42)   │ Core 1 reads X
        │                              │ (L1 hit → returns 42! WRONG!)
```

Without coherency, Core 1 sees stale data. Solutions:

| Solution | How | FPGA Cost | When |
|---|---|---|---|
| **Snooping (bus-based)** | Cores broadcast cache ops on shared bus | ~5,000 LUTs per core | ≤4 cores, shared bus |
| **Directory-based** | Central directory tracks cache line ownership | ~10,000 LUTs for directory | 4+ cores |
| **Software-managed** | Explicit cache flush/invalidate in code | Zero hardware cost | Bare-metal, deterministic workloads |
| **Don't share memory** | Each core has private memory region | Zero hardware cost | Independent tasks (AMP) |

## AXI Coherency Extensions

| Protocol | Coherency | Use Case |
|---|---|---|
| **AXI4 (standard)** | Non-coherent | Default |
| **AXI4 ACE-Lite** | I/O coherent (FPGA snoops CPU cache) | Accelerator reads CPU data |
| **AXI4 ACE** | Full coherent (FPGA participates in coherency) | Multi-master shared memory |

## When NOT to Use Multi-Core on FPGA

| Reason | Explanation |
|---|---|
| **LUT budget** | Each core = 3K–15K LUTs + coherency logic |
| **FPGA fmax** | Soft cores run 50–150 MHz, not 1+ GHz — diminishing returns |
| **Linux overhead** | SMP kernel adds complexity; AMP (bare-metal per-core) is more efficient |
| **Debug difficulty** | Multi-core race conditions are 10× harder to reproduce |

**Better alternative**: One fast core + DMA engines + hardware accelerators for parallel work.

---

## Original Stub Description

Multi-core SoCs on FPGA: SMP challenges, cache coherency (snooping, directory), AXI4 ACE-Lite, when NOT to go multi-core, practical FPGA resource limits

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
