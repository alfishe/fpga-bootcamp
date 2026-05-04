[← 12 Open Source Open Hardware Home](../README.md) · [← Memory Controllers Home](README.md) · [← Project Home](../../../README.md)

# Open SDRAM Controllers — Single Data Rate for FPGA

Single Data Rate SDRAM controllers — simpler than DDR, easier to implement on low-end FPGAs, and the memory backbone of virtually every retro computing and low-cost FPGA project. If your board has a 16-bit SDRAM chip soldered next to the FPGA (ULX3S, Colorlight, MiSTer add-on, DE10-Nano), you need one of these.

---

## Overview

SDRAM (Synchronous Dynamic Random Access Memory) is the simplest DRAM interface that provides reasonable bandwidth for FPGA designs. Unlike DDR, SDRAM transfers data on only the rising edge of the clock, uses single-ended (not differential) signaling, and requires no complex PHY calibration. This makes it ideal for low-cost boards, 2-layer PCBs, and FPGAs without fast I/O cells.

The trade-off: SDRAM tops out at ~166 MHz / 32-bit = ~667 MB/s, which is modest compared to DDR3 (1600 MT/s / 32-bit = ~6.4 GB/s). But for retro computing, audio/video buffers, and soft CPU memory, SDRAM is sufficient and far easier to get working.

---

## Controller Comparison

| Controller | Max Clock | Data Width | Bus Interface | FPGA Verified | Auto-Calibration | Repository |
|---|---|---|---|---|---|---|
| **sdram-controller** | 166 MHz | 8/16/32-bit | Native (Wishbone adapter available) | iCE40, ECP5, Artix-7 | No (manual timing) | stffrdhrn/sdram-controller |
| **MiSTer SDRAM** | 133 MHz | 16-bit | Native (parallel) | Cyclone V, Cyclone III | No (fixed timing per board) | MiSTer-devel/SDRAM_Controller |
| **LiteDRAM** | Up to 166 MHz | 8–32-bit | LiteX native (Wishbone + AXI adapters) | iCE40, ECP5, Artix-7, Cyclone V | ✅ Software-calibrated | enjoy-digital/litedram |
| **wb_sdram** | 133 MHz | 16-bit | Wishbone | ECP5, Artix-7 | No | olofk/wb_sdram |

---

## SDRAM Protocol Overview

SDRAM communicates through a command-based interface:

| Command | CS# | RAS# | CAS# | WE# | Description |
|---|---|---|---|---|---|
| **NOP** | H | X | X | X | No operation |
| **ACTIVATE** | L | L | H | H | Open a row (bank + row address) |
| **READ** | L | H | L | H | Read from open row (column address) |
| **WRITE** | L | H | L | L | Write to open row (column address) |
| **PRECHARGE** | L | L | H | L | Close a row |
| **REFRESH** | L | L | L | H | Refresh a row (required periodically) |
| **LOAD MODE** | L | L | L | L | Write to mode register |
| **BURST TERMINATE** | L | H | H | L | Stop current burst |

### SDRAM Timing Diagram (Read Burst)

```
CLK     ──┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
          └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘

CMD     ──< ACT >─< READ ────────── NOP ──────────────────

ADDR    ──< ROW >─< COL  >────────────────────────────────

DQ      ────────────────────< D0 >─< D1 >─< D2 >─< D3 >─  (CL=2)

                ┌─── tRCD ────┐
                │             │
         ACT    READ          DATA
```

| Timing Parameter | Typical Value (133 MHz) | Description |
|---|---|---|
| **tRCD** | 15 ns (2 cycles) | ACTIVATE to READ/WRITE delay |
| **CL** (CAS Latency) | 2 or 3 cycles | READ command to first data |
| **tRP** | 15 ns (2 cycles) | PRECHARGE to next ACTIVATE |
| **tRAS** | 37 ns (5 cycles) | ACTIVATE to PRECHARGE (min row open time) |
| **tRC** | 60 ns (8 cycles) | ACTIVATE to next ACTIVATE (same bank) |
| **tREFI** | 7.8125 μs | Refresh interval (8192 refreshes per 64 ms) |

---

## SDRAM Refresh: The Non-Negotiable Requirement

SDRAM cells leak charge and must be refreshed every 64 ms. With 8192 rows, that's a refresh every 7.8125 μs. If you miss a refresh deadline, data corruption is guaranteed.

| Refresh Strategy | Implementation | Latency Impact | Complexity |
|---|---|---|---|
| **Burst refresh** | Refresh all 8192 rows every 64 ms | Long pause (~160 μs) every 64 ms | Simple |
| **Distributed refresh** | One refresh every 7.8125 μs | 1–2 lost cycles per 7.8 μs window | Standard |
| **Auto-refresh with arbitration** | Controller inserts refresh between accesses | Transparent to user, variable latency | Best (most complex) |

> **Critical rule**: The refresh controller must have higher priority than any data access. Missing refresh deadlines causes silent data corruption.

---

## Controller Deep Dives

### sdram-controller (stffrdhrn)

The most widely-used standalone SDRAM controller. Clean Verilog, no dependencies, works out of the box on ECP5 and Artix-7.

```verilog
// Simplified instantiation
sdram_controller #(
    .SDRAM_ADDR_WIDTH(13),
    .SDRAM_COL_WIDTH(10),
    .SDRAM_ROW_WIDTH(13),
    .SDRAM_BANK_WIDTH(2),
    .SDRAM_DATA_WIDTH(16),
    .SDRAM_BURST_LENGTH(1),
    .SDRAM_CAS_LATENCY(3)
) sdram_inst (
    .clk(clk),
    .reset(reset),

    // User interface
    .req_addr(addr),
    .req_read(read_en),
    .req_write(write_en),
    .req_write_data(wr_data),
    .req_write_mask(wr_mask),
    .ack_data_valid(rd_valid),
    .ack_data(rd_data),

    // SDRAM pins
    .sdram_a(sdram_addr),
    .sdram_ba(sdram_bank),
    .sdram_dq(sdram_dq),
    .sdram_cke(sdram_cke),
    .sdram_cs_n(sdram_cs),
    .sdram_ras_n(sdram_ras),
    .sdram_cas_n(sdram_cas),
    .sdram_we_n(sdram_we),
    .sdram_dqm(sdram_dqm)
);
```

### MiSTer SDRAM Controller

The MiSTer retro platform uses a custom SDRAM controller for its 32 MB add-on board. Key features:

| Feature | Detail |
|---|---|
| **Clock** | 133 MHz (Cyclone V) |
| **Data width** | 16-bit |
| **Burst** | Full-page burst supported |
| **Arbiter** | Priority-based (video > CPU > DMA) |
| **Special** | Phase-shifted clock for read capture |

The MiSTer controller uses a phase-shifted clock (shifted ~2 ns from the SDRAM clock) to capture read data. This is essential for the Cyclone V's I/O timing but board-specific.

### LiteDRAM SDRAM Mode

LiteDRAM supports SDRAM (in addition to DDR) through its PHY abstraction. The key advantage: LiteDRAM performs **software calibration** at boot time, measuring the actual SDRAM timing and adjusting the PHY accordingly.

```python
# LiteX SoC with SDRAM on ECP5
soc = BaseSoC(platform=device)
soc.add_sdram("sdram",
    phy=sdram_module.phy_settings,
    module=sdram_module.geom_settings,
    size=0x4000000,  # 64 MB
)
```

---

## Resource Usage

| Controller | FPGA | LUTs | FFs | BRAM | fMax |
|---|---|---|---|---|---|
| sdram-controller | ECP5 25K | ~350 | ~250 | 0 | 133 MHz |
| sdram-controller | Artix-7 | ~300 | ~220 | 0 | 166 MHz |
| MiSTer SDRAM | Cyclone V | ~400 | ~300 | 0 | 133 MHz |
| LiteDRAM (SDRAM mode) | ECP5 25K | ~800 | ~500 | 2 | 133 MHz |

---

## When to Use SDRAM Instead of DDR

| SDRAM Advantage | DDR Disadvantage |
|---|---|
| Single-ended clock (no differential pair routing) | Needs differential DQS pairs |
| Simpler state machine (no DQS gating, no ODT) | Complex PHY calibration required |
| Works on 2-layer PCBs | Typically needs 4+ layers for impedance |
| Lower FPGA speed grade requirements | Needs fast I/O cells for DDR capture |
| Direct clocking from FPGA | Source-synchronous capture needed |

---

## When to Use / When NOT to Use

### When to Use Open SDRAM Controllers

- **Retro computing** — original hardware used SDRAM; cycle-accurate recreation requires SDRAM timing
- **Low-cost FPGA boards** — ULX3S, Colorlight, SiDi, Tang Nano — these all have SDRAM
- **Audio/video buffers** — 32 MB at ~267 MB/s is plenty for 1080p framebuffer or audio sample FIFOs
- **LiteX SoCs** — LiteDRAM handles SDRAM natively with auto-calibration

### When NOT to Use Open SDRAM Controllers

- **Bandwidth > 667 MB/s** — DDR3/DDR4 is needed; see [DDR Controllers](ddr_controllers.md)
- **Large memory > 128 MB** — SDRAM density tops out; DDR3/4 provides 4–32 GB
- **Source-synchronous designs** — DDR interfaces capture data on both clock edges; SDRAM cannot compete

---

## Best Practices

1. **Use LiteDRAM for new designs** — auto-calibration eliminates the most common SDRAM bring-up failure (timing misconfiguration)
2. **Always implement refresh** — missing refresh deadlines causes silent data corruption; never "optimize" by skipping refresh
3. **Set CAS latency correctly** — CL=2 is faster but requires faster SDRAM chips; CL=3 is safer. Check your chip's speed grade.
4. **Use a PLL to generate the SDRAM clock** — the SDRAM clock must be clean and jitter-free; derive it from the system clock via PLL
5. **Match trace lengths** — SDRAM signal integrity degrades with unmatched trace lengths; keep CLK, CMD, and DATA traces within 5 mm of each other

---

## Antipatterns

- **The No-Refresh Shortcut** — disabling refresh to "save cycles"; this causes data corruption within milliseconds
- **The Asynchronous Interface** — treating SDRAM like async SRAM; SDRAM requires command-based access with proper timing
- **The Full-Bandwidth Assumption** — designing for 100% SDRAM bandwidth utilization; refresh overhead and row misses reduce real throughput to ~70%

---

## Pitfalls

1. **SDRAM clock phase** — the SDRAM clock must arrive at the chip slightly after the FPGA outputs change; a phase-shifted clock (via PLL) is often needed for reliable read capture
2. **tRCD and tRP timing** — these are minimum times, not suggestions; violating them causes incorrect data with no error indication
3. **Bank management** — keeping a row open across multiple accesses improves performance (page hit), but each bank can only have one row open at a time
4. **DQM (Data Mask) during writes** — partial-byte writes require setting the DQM mask; incorrect masking writes garbage to the unmasked bytes
5. **Power-up initialization** — SDRAM requires a specific initialization sequence (100 μs wait → PRECHARGE ALL → 2× AUTO REFRESH → LOAD MODE REGISTER); skipping it leaves the SDRAM in an undefined state

---

## Use Cases

- **Retro computing cores** — Amiga, Atari ST, C64, console cores (see [MiSTer](../retro_computing/mister.md))
- **LiteX SoC main memory** — VexRiscv + LiteDRAM on ULX3S, OrangeCrab, Colorlight
- **Video frame buffer** — 640×480 to 1280×720 framebuffer in 32 MB SDRAM
- **Audio sample buffer** — delay lines, reverb, multi-channel audio
- **Soft CPU program memory** — RISC-V core executing from SDRAM via cache

---

## References

- [sdram-controller (GitHub)](https://github.com/stffrdhrn/sdram-controller)
- [MiSTer SDRAM Controller (GitHub)](https://github.com/MiSTer-devel/SDRAM_Controller)
- [LiteDRAM (GitHub)](https://github.com/enjoy-digital/litedram)
- [SDRAM Specification (JEDEC)](https://www.jedec.org/)
- [MiSTer SDRAM Timing Theory](../../mister/06_fpga_subsystem/sdram_timing_theory.md) — deep dive into SDRAM timing for retro cores
- [DDR Controllers](ddr_controllers.md) — for higher bandwidth needs
- [Specialized Memory](specialized_memory.md) — HyperRAM, QSPI PSRAM, async SRAM
