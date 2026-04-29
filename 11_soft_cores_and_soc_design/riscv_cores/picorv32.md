[← 11 Soft Cores And Soc Design Home](../README.md) · [← Riscv Cores Home](README.md) · [← Project Home](../../../README.md)

# PicoRV32 — Minimal RISC-V in Pure Verilog

PicoRV32 is a size-optimized RV32IMC implementation — a single Verilog file with ~1,300 lines, making it the easiest RISC-V core to read, modify, and integrate into any FPGA project.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32I + M + C (configurable) |
| **Pipeline** | None (state machine, ~1 IPC in 3–4 cycles) |
| **LUTs** | ~750 (RV32I) to ~2,000 (RV32IMC) |
| **fmax** | 150+ MHz on iCE40, ECP5, Artix-7 |
| **Interrupts** | IRQ (basic), fast IRQ with separate vector |
| **Debug** | None built-in (use UART-based monitor) |

## What Makes It Unique

PicoRV32 uses a **multicycle state machine** instead of a pipeline, trading IPC for area:
- No pipeline hazards → no forwarding, no stalling logic
- Each instruction takes 3–4 cycles (CPI ~3.5 for RV32I, ~6 for RV32IM)
- Result: 1 DMIPS/MHz (vs ~1.6 for a 3-stage pipeline)

It's the wrong choice for performance but the right choice when:
- You need a CPU in \u003c1000 LUTs
- You want a single-file Verilog core you can fully understand
- You're targeting iCE40/ECP5 with limited resources

## Integration Example

```verilog
picorv32 #(
    .ENABLE_MUL(1),
    .ENABLE_DIV(1),
    .ENABLE_FAST_MUL(1),
    .ENABLE_COMPRESSED(1),
    .STACKADDR(32'h0000_4000),
    .PROGADDR_RESET(32'h0000_0000),
    .PROGADDR_IRQ(32'h0000_0010)
) cpu (
    .clk        (clk),
    .resetn     (!rst),
    .mem_valid  (mem_valid),
    .mem_instr  (mem_instr),
    .mem_ready  (mem_ready),
    .mem_addr   (mem_addr),
    .mem_wdata  (mem_wdata),
    .mem_wstrb  (mem_wstrb),
    .mem_rdata  (mem_rdata),
    .irq        (irq)
);
```

---

## Original Stub Description

Documentation for PicoRV32 deep dive.

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [hard_processor_integration.md](../../02_architecture/soc/hard_processor_integration.md)
- [README.md](README.md)
