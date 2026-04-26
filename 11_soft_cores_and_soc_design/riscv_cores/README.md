[← Section Home](../README.md) · [← Project Home](../../README.md)

# 11-C — Open-Source RISC-V Cores

Deep technical dives into the major open-source RISC-V soft cores. Each article covers architecture, pipeline design, FPGA resource utilization, configuration options, and when to use (or avoid) that core.

> For a quick comparison across all cores at once, see [Section 12 — RISC-V Core Catalog](../../12_open_source_open_hardware/cores_catalog/riscv_cores_catalog.md).

## Index

| File | Topic |
|---|---|
| [vexriscv.md](vexriscv.md) | VexRiscv: SpinalHDL, highly configurable 2–5 stage pipeline, optional MMU (Linux capable), caches, debug module, LiteX default CPU |
| [picorv32.md](picorv32.md) | PicoRV32: minimal RV32IMC, ~750–2000 LUTs, no pipeline, PCPI co-processor interface, when tiny footprint beats performance |
| [neorv32.md](neorv32.md) | NEORV32: best-in-class documentation, RV32, integrated SoC peripherals (UART/SPI/TWI/GPIO/PWM/WDT), bootloader, excellent for learning |
| [serv.md](serv.md) | SERV: bit-serial RV32I, world's smallest RISC-V (~125 LUTs on iCE40), 1 bit per cycle, when footprint is everything |
| [ibex_cv32e.md](ibex_cv32e.md) | Ibex / CV32E40P: OpenTitan's core, 2–3 stage, RV32IMCB, security features, OpenHW Group, formal verification status |
| [high_perf_riscv_cores.md](high_perf_riscv_cores.md) | High-perf survey: BOOM (Berkeley OoO, RV64GC), Rocket (in-order, Chisel generator), CVA6 (ex-Ariane, RV64GC), XiangShan — comparison: pipeline depth, branch prediction, multi-issue, Linux-ready |
