[← 11 Soft Cores And Soc Design Home](../README.md) · [← RISC-V Cores Home](README.md) · [← Project Home](../../../README.md)]

# PicoRV32 — Minimal RISC-V in Pure Verilog

PicoRV32 is a size-optimized RV32IMC implementation in a single Verilog file (~1,300 lines) — the easiest RISC-V core to read, modify, and integrate into any FPGA project. It trades IPC for area using a multicycle state machine instead of a pipeline, achieving a functional RISC-V processor in ~750 LUTs.

---

## Architecture

| Parameter | Value |
|---|---|
| **ISA** | RV32I + M + C (configurable) |
| **Pipeline** | None (multicycle state machine, ~1 IPC in 3–4 cycles) |
| **LUTs** | ~750 (RV32I) to ~2,000 (RV32IMC) on Artix-7 |
| **FFs** | ~350 to ~900 |
| **fmax** | 150+ MHz on iCE40, 200+ MHz on Artix-7, ECP5 |
| **CPI** | ~3.5 for RV32I (ALU ops), ~6 for RV32IM (multiply) |
| **Performance** | ~1.0 DMIPS/MHz (RV32I), ~0.7 DMIPS/MHz (RV32IM with fast mul) |
| **Bus** | Simple memory interface (valid/ready handshake, no standard bus) |
| **Interrupts** | Basic IRQ + optional fast IRQ with separate vector |
| **Debug** | None built-in (use UART-based monitor or external debug) |

---

## Why PicoRV32 Is Unique

### Single-File Verilog

The entire CPU is in one file — `picorv32.v`. No includes, no dependencies, no build system. This makes it:

- **Auditable** — One person can read the entire core in an afternoon
- **Portable** — Copy one file into any project; no IP packaging needed
- **Modifiable** — Edit the Verilog directly; no generator toolchain required

### Multicycle State Machine (Not a Pipeline)

```
Traditional 5-stage pipeline:
  F → D → E → M → WB   (1 IPC, with forwarding/hazard logic)

PicoRV32 multicycle:
  FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK
  (Each phase takes 1 clock; total 3-6 clocks per instruction)
```

**Consequences of no pipeline:**
- No forwarding logic → saves ~200 LUTs
- No hazard detection → saves ~100 LUTs
- No branch prediction → no misprediction penalty (branch = 3 cycles, always)
- Result: 1 DMIPS/MHz (vs ~1.6 for a 3-stage pipeline) — 37% slower per MHz, but 50% smaller

---

## Memory Interface

PicoRV32 uses a **simple valid/ready handshake** — not Wishbone, not AXI, not Avalon. This is both a strength (minimal interface logic) and a weakness (requires a wrapper for standard bus interconnects).

### Signal Interface

| Signal | Direction | Width | Description |
|---|---|---|---|
| `mem_valid` | Output | 1 | Memory request valid |
| `mem_instr` | Output | 1 | 1 = instruction fetch, 0 = data access |
| `mem_ready` | Input | 1 | Memory response ready |
| `mem_addr` | Output | 32 | Byte address |
| `mem_wdata` | Output | 32 | Write data |
| `mem_wstrb` | Output | 4 | Write byte strobe |
| `mem_rdata` | Input | 32 | Read data |

### Timing Diagram — Read Access

```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
clk     │   │   │   │   │   │   │   │
     ───┘   └───┘   └───┘   └───┘   └───

        ┌───────────────────────────────
mem_valid
     ───┘

                ┌───────────────────────
mem_ready
     ───────────┘

                ┌───────────────────────
mem_rdata
     ───────────┘ valid data
```

The CPU stalls until `mem_ready` goes high. There is no burst support — every memory access is a single-word transaction.

### Wishbone Adapter

```verilog
// Simple PicoRV32 → Wishbone adapter
always @(posedge clk) begin
    wb_cyc <= mem_valid;
    wb_stb <= mem_valid;
    wb_adr <= mem_addr;
    wb_dat_wr <= mem_wdata;
    wb_we <= |mem_wstrb;
    wb_sel <= mem_wstrb;
    mem_ready <= wb_ack;
    mem_rdata <= wb_dat_rd;
end
```

---

## Integration

### Minimal Instantiation

```verilog
picorv32 #(
    .ENABLE_MUL(1),           // M extension
    .ENABLE_DIV(1),           // Division (part of M)
    .ENABLE_FAST_MUL(1),      // Use DSP slices for multiply
    .ENABLE_COMPRESSED(1),    // C extension (16-bit instructions)
    .STACKADDR(32'h0000_4000),     // Stack top address
    .PROGADDR_RESET(32'h0000_0000),// Reset vector
    .PROGADDR_IRQ(32'h0000_0010)   // IRQ handler address
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

### Configuration Options

| Parameter | Default | Description |
|---|---|---|
| `ENABLE_MUL` | 0 | Enable M extension (multiply) — adds ~300 LUTs |
| `ENABLE_DIV` | 0 | Enable division — adds ~200 LUTs |
| `ENABLE_FAST_MUL` | 0 | Use DSP slices for 1-cycle multiply — adds ~100 LUTs + 1 DSP |
| `ENABLE_COMPRESSED` | 0 | Enable C extension (16-bit instructions) — adds ~400 LUTs |
| `ENABLE_IRQ` | 0 | Enable basic interrupt — adds ~100 LUTs |
| `ENABLE_IRQ_QREGS` | 0 | Fast IRQ with separate register set — adds ~500 LUTs |
| `TWO_STAGE_SHIFT` | 1 | 2-cycle barrel shifter (smaller) vs 1-cycle (faster) |
| `BARREL_SHIFTER` | 0 | Full barrel shifter (1-cycle, larger) |
| `CATCH_MISALIGN` | 1 | Trap on misaligned access |
| `CATCH_ILLINSN` | 1 | Trap on illegal instruction |
| `STACKADDR` | 0 | Stack pointer initialization address |
| `PROGADDR_RESET` | 0 | Reset vector (PC after reset) |
| `PROGADDR_IRQ` | 0 | IRQ handler entry point |

---

## PicoSoC — Reference SoC

PicoRV32 is commonly used with **PicoSoC** — a minimal SoC that pairs PicoRV32 with a simple memory subsystem:

```
PicoSoC Architecture
┌─────────────────────────────────────┐
│ PicoRV32 CPU                        │
│ ├─ RV32IMC (configurable)           │
│ └─ Simple memory interface          │
│                                     │
│ Memory Subsystem                    │
│ ├─ 32 KB BRAM (instruction + data)  │
│ ├─ SPI flash controller (boot ROM)  │
│ └─ Simple UART (console)            │
│                                     │
│ GPIO (optional)                     │
│ └─ 32-bit output pins               │
└─────────────────────────────────────┘
```

PicoSoC boots from SPI flash: the CPU fetches instructions directly from flash (slow but functional), then copies critical code to BRAM for faster execution.

---

## Interrupt Handling

PicoRV32 supports two interrupt modes:

### Basic IRQ

```verilog
// Single IRQ input, vector to PROGADDR_IRQ
assign irq = timer_irq | uart_irq | gpio_irq;

// In firmware (C):
void irq_handler(void) __attribute__((interrupt));
void irq_handler(void) {
    // Check IRQ source, handle, return
}
```

- Single vector for all interrupts
- Software must determine the source
- No nesting — interrupts are disabled during handler
- Saving/restoring registers is manual

### Fast IRQ (with QREGS)

When `ENABLE_IRQ_QREGS` is enabled, PicoRV32 provides **alternate registers** for the IRQ handler — no register save/restore needed:

- 4 alternate registers (`q0`–`q3`) available only in IRQ mode
- Entry/exit is 2 cycles each (vs 20+ for register save/restore)
- Best for latency-critical handlers (e.g., UART character receive)

---

## Performance Analysis

### CPI Breakdown

| Instruction Type | Cycles | Notes |
|---|---|---|
| ALU (ADD, SUB, AND, OR, XOR, SLT) | 3 | Fetch → Decode → Execute |
| LUI, AUIPC | 3 | No memory access |
| Load (LW, LH, LB) | 3–5 | Depends on memory latency |
| Store (SW, SH, SB) | 3–5 | Depends on memory latency |
| Branch (BEQ, BNE, BLT, BGE) | 3 | No prediction penalty (always 3) |
| Jump (JAL, JALR) | 3 | No prediction penalty |
| Shift (SLL, SRL, SRA) | 3 (2-stage) or 1 (barrel) | Depends on `TWO_STAGE_SHIFT`/`BARREL_SHIFTER` |
| Multiply (MUL) | 3 (fast) or 33 (iterative) | Depends on `ENABLE_FAST_MUL` |
| Divide (DIV) | 33 | Always iterative |
| Compressed (C.XXX) | 3 | Same as expanded instruction |

### DMIPS/MHz by Configuration

| Configuration | DMIPS/MHz | LUTs (Artix-7) | Notes |
|---|---|---|---|
| RV32I (minimal) | ~1.0 | ~750 | Baseline |
| RV32IM (fast mul) | ~1.0 | ~1,100 | Multiply is same speed, but enables M extension |
| RV32IMC (fast mul, compressed) | ~0.9 | ~1,500 | Compressed saves code size but CPI doesn't improve much |
| RV32IMC + barrel shifter | ~1.1 | ~1,700 | 1-cycle shifts add performance but cost area |

---

## When to Use / When NOT to Use

### When to Use

- **You need < 1,000 LUTs** — PicoRV32 is the smallest practical RISC-V (SERV at ~125 LUTs is too slow for most applications)
- **Single-file Verilog integration** — Copy one file into any project; no build system dependencies
- **You need to modify the CPU** — Simple state machine is easy to understand and modify
- **iCE40 / ECP5 targets** — PicoRV32 runs well on Lattice FPGAs with open toolchains

### When NOT to Use

- **You need high IPC** — 1 DMIPS/MHz is low; VexRiscv achieves 1.4+ with similar resources
- **You need a standard bus interface** — The custom valid/ready interface requires adapters for Wishbone/AXI
- **You need cache** — No cache support; all memory accesses go to external RAM
- **You need debug** — No JTAG debug module; use UART or LED-based debugging

---

## Best Practices

1. **Enable `ENABLE_FAST_MUL`** — If your FPGA has DSP slices (Artix-7, ECP5), use them; fast multiply costs 1 DSP but saves 30 cycles per MUL instruction
2. **Use `TWO_STAGE_SHIFT` for area savings** — The 2-stage shifter costs 1 extra cycle but saves ~100 LUTs vs the barrel shifter
3. **Write a Wishbone/AXI adapter** — Don't connect PicoRV32 directly to your memory system; use a small adapter to bridge to a standard bus
4. **Use the PicoSoC as a starting point** — Don't build a SoC from scratch; modify PicoSoC's memory map and peripherals

## Antipatterns

| Antipattern | Why It Fails | Correct Approach |
|---|---|---|
| **Adding pipeline stages to PicoRV32** | The state machine is not designed for pipelining; adding stages requires a complete rewrite | Switch to VexRiscv if you need pipeline performance |
| **Using iterative multiply in DSP-rich designs** | Iterative MUL takes 33 cycles and uses LUTs; DSP slices are free | Enable `ENABLE_FAST_MUL` on any FPGA with DSP48/ALM DSP |
| **Connecting PicoRV32 directly to DDR memory** | The simple memory interface cannot handle DDR latency and burst requirements | Use a Wishbone adapter → LiteDRAM or vendor DDR controller |
| **Ignoring `mem_ready` latency** | PicoRV32 stalls on every wait state; slow memory directly reduces throughput | Use BRAM for time-critical code; use SPI flash only for boot |

---

## Pitfalls

### 1. No Standard Bus Interface

PicoRV32's memory interface is intentionally simple but incompatible with Wishbone, AXI, or Avalon. Every integration requires a small adapter:

- **To Wishbone**: ~30 lines of Verilog (shown above)
- **To AXI4-Lite**: ~100 lines (requires response channel handling)
- **To AXI4**: ~200 lines (requires burst support which PicoRV32 doesn't generate)

### 2. IRQ Handler Overhead

Basic IRQ handling requires saving all 32 registers to the stack on entry and restoring on exit — ~64 memory operations at 3–5 cycles each = ~200 cycles of pure overhead. For frequent interrupts, this is a significant performance penalty.

**Fix:** Enable `ENABLE_IRQ_QREGS` for fast IRQ with alternate registers, reducing entry/exit to ~4 cycles total.

### 3. Memory Latency Sensitivity

PicoRV32 has no cache — every memory access goes directly to the bus. If your memory has wait states (SDRAM, SPI flash), CPI increases proportionally:

- BRAM (0 wait states): CPI = 3.5
- SDRAM (2 wait states): CPI = 5.5
- SPI flash (10+ wait states): CPI = 13+

**Fix:** Use tightly-coupled BRAM for code and data. Use SPI flash only for boot loading.

---

## Use Cases

| Use Case | Configuration | Why PicoRV32 |
|---|---|---|
| **Small FPGA control CPU** | RV32I minimal (~750 LUTs) | Smallest practical RISC-V with full ISA |
| **PicoSoC-based design** | RV32IMC with SPI flash | Reference SoC provides complete working system |
| **iCE40 open-source projects** | Any | Well-tested with Yosys + nextpnr |
| **Custom instruction experimentation** | Modified Verilog | Simple state machine is easy to modify |
| **Soft MCU in vendor-agnostic design** | Any | Pure Verilog, no vendor primitives |

---

## References

- [PicoRV32 GitHub Repository](https://github.com/YosysHQ/picorv32) — source code, PicoSoC, documentation
- [PicoSoC Reference Design](https://github.com/YosysHQ/picorv32/tree/master/picosoc) — minimal SoC with SPI flash boot
- [SERV](serv.md) — even smaller (~125 LUTs) but much slower bit-serial RISC-V
- [NEORV32](neorv32.md) — similar size, VHDL, better documentation, more peripherals
- [VexRiscv](vexriscv.md) — more features, SpinalHDL-based, plugin architecture
- [LiteX Overview](../../12_open_source_open_hardware/litex/litex_overview.md) — SoC builder with PicoRV32 support
