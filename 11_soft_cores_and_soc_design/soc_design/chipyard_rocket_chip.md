[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Rocket Chip / Chipyard — Chisel SoC Generation

Chipyard is Berkeley's open-source SoC design framework built around the Rocket Chip generator — a Scala/Chisel library that produces complete RISC-V SoCs from configuration files.

---

## What Rocket Chip / Chipyard Provides

| Component | What It Generates |
|---|---|
| **Rocket Core** | RV64IMAFDC, 5-stage in-order CPU |
| **BOOM Core** | RV64IMAFDC, out-of-order (optional) |
| **TileLink Interconnect** | Coherent on-chip network (Berkeley's alternative to AXI/ACE) |
| **L1/L2 Caches** | Configurable size, inclusive/exclusive |
| **Peripherals** | UART, SPI, GPIO, JTAG debug |
| **RoCC Interface** | Rocket Custom Coprocessor — attach FPGA accelerators |

## Diplomacy Parameter Negotiation

Chipyard's killer feature is **Diplomacy** — a Chisel-embedded type system that negotiates parameters between blocks at elaboration time:

```scala
// Two blocks negotiate bus width automatically
val master = LazyModule(new MyMaster())
val slave  = LazyModule(new MySlave())
slave.node := master.node  // Diplomacy checks compatibility
```

This means the bus width, address map, and cache coherence policy are all resolved before any Verilog is emitted — eliminating parameter mismatch bugs at the source.

## FPGA Mapping

| Target | Works? | Notes |
|---|---|---|
| **Kintex-7 (325T+)** | ✅ | Rocket single-core fits, BOOM needs 325T+ |
| **Zynq Ultrascale+** | ✅ | Can co-exist with hard ARM cores |
| **ECP5 / iCE40** | ❌ | Too small |
| **Cyclone V (110K)** | 🟡 | Rocket fits, tight |

## When to Use Chipyard

| Scenario | Chipyard | LiteX |
|---|---|---|
| I need a configurable RV64 Linux SoC | ✅ | ❌ (LiteX = RV32 mostly) |
| I want to attach custom accelerators | ✅ RoCC interface | ✅ Wishbone/AXI |
| I need fast iteration (minutes) | ❌ Chisel compile = slow | ✅ Python config = fast |
| I'm targeting small FPGAs | ❌ | ✅ ECP5/iCE40 OK |

---

## Original Stub Description

Rocket Chip / Chipyard: Scala/Chisel SoC generation framework, TileLink protocol, Diplomacy parameter negotiation, connecting custom accelerators (RoCC), FPGA mapping flow

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](README.md)
