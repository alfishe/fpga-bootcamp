[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# Clock Domain Crossing (CDC) — Coding Patterns

Clock Domain Crossing is the transfer of a signal from a register clocked by one clock to a register clocked by another, asynchronous clock. CDC is the single most common source of **intermittent, unreproducible** FPGA bugs because metastability behaves statistically — a design can work for millions of cycles and then fail.

---

## Metastability: The Root Cause

When a flip-flop's data input changes within its setup-and-hold window relative to the clock edge, the output enters a **metastable** state: neither valid `0` nor valid `1`. The output oscillates or hovers at an intermediate voltage before eventually settling — or not — to a valid logic level.

The probability of failure follows:

```
MTBF = e^(T_resolution / τ) / (f_clock × f_data × T_window)
```

Where `T_resolution` is the time allowed for the signal to settle (typically one clock period) and `τ` is the device-specific metastability resolution time constant.

**Every additional synchronizer flip-flop exponentially increases MTBF.** Two flip-flops in series is the industry standard minimum; three for safety-critical designs.

---

## Pattern 1: 2-FF Synchronizer (Single-Bit)

The simplest and most fundamental CDC pattern. Works only for **single-bit signals**.

**Verilog:**
```verilog
(* ASYNC_REG = "TRUE" *) reg [1:0] sync_ff;

always @(posedge dst_clk) begin
    sync_ff <= {sync_ff[0], async_signal};
end

wire sync_out = sync_ff[1]; // Safe to use in dst_clk domain
```

**VHDL:**
```vhdl
signal sync_ff : std_logic_vector(1 downto 0);
attribute ASYNC_REG : string;
attribute ASYNC_REG of sync_ff : signal is "TRUE";

process(dst_clk)
begin
    if rising_edge(dst_clk) then
        sync_ff <= sync_ff(0) & async_signal;
    end if;
end process;

signal sync_out : std_logic := sync_ff(1);
```

### Critical Rules

1. The `ASYNC_REG` attribute is **mandatory** — without it, the tool may optimize away or replicate the registers
2. Place the two FFs **physically adjacent** — inform the tool via attributes so it doesn't separate them across the chip
3. Fan-out only from the **second** flip-flop — never use the first FF's output for logic
4. No combinational logic between the synchronizer stages — no gates, no LUTs, just wire

### 3-FF Variant (Safety-Critical)

For high-reliability applications (automotive, medical, aerospace), add a third flip-flop:

```verilog
(* ASYNC_REG = "TRUE" *) reg [2:0] sync_ff; // 3-stage for safety
```

---

## Pattern 2: Multi-Bit Bus Crossing (Gray Code + 2-FF)

**Never apply the 2-FF pattern to a multi-bit bus.** Each bit settles independently, so different bits resolve on different clock cycles — the destination sees a corrupt, transient value that never existed in the source domain.

The solution: **Gray code encoding** + 2-FF synchronizer.

Gray code changes only **one bit at a time** when incrementing. Even if that single bit is metastable, the destination sees either the old value or the new value — never an intermediate, multi-bit corrupted state.

### Verilog: Binary-to-Gray Converter

```verilog
// Binary to Gray
wire [WIDTH-1:0] gray_ptr = bin_ptr ^ (bin_ptr >> 1);

// Synchronize each Gray bit independently
(* ASYNC_REG = "TRUE" *) reg [WIDTH-1:0] gray_sync [0:1];
always @(posedge dst_clk) begin
    gray_sync[0] <= gray_ptr;
    gray_sync[1] <= gray_sync[0];
end

// Gray to Binary (in destination domain)
function [WIDTH-1:0] gray2bin;
    input [WIDTH-1:0] g;
    integer i;
    begin
        gray2bin[WIDTH-1] = g[WIDTH-1];
        for (i = WIDTH-2; i >= 0; i = i - 1)
            gray2bin[i] = gray2bin[i+1] ^ g[i];
    end
endfunction

wire [WIDTH-1:0] safe_ptr = gray2bin(gray_sync[1]);
```

### When Gray Code Works

Gray code is safe for CDC when:
- The multi-bit value **increments by exactly 1** (counters, FIFO pointers)
- The destination clock is **at least 1.5× faster** than the source clock (ensures at least one destination edge between source transitions)

Gray code does **NOT** work for arbitrary data buses. For that, use an async FIFO.

---

## Pattern 3: Asynchronous FIFO

The async FIFO is the workhorse of multi-bit CDC. It uses **dual-clock Block RAM** with independently clocked read and write ports, plus Gray-coded pointer synchronization.

### Architecture

```
Source Domain (wr_clk)              Destination Domain (rd_clk)
┌──────────────────┐                ┌──────────────────┐
│ wr_data ──► Dual  │                │ Dual ◄── rd_data │
│ wr_addr ◄── Port  │◄── DATA ──────►│ Port  ◄── rd_addr│
│           BRAM   │                │       BRAM       │
└──────────────────┘                └──────────────────┘
        │                                    │
   wr_ptr (bin)                         rd_ptr (bin)
        │                                    │
   bin2gray                             bin2gray
        │                                    │
   ┌────▼─────────────────────────────────▼────┐
   │  2-FF Synchronizer (each Gray bit)        │
   │  wr_ptr_gray  ────►  rd_ptr_gray_sync     │
   │  rd_ptr_gray  ◄────  wr_ptr_gray_sync     │
   └───────────────────────────────────────────┘
```

The FIFO status flags (`empty`, `full`, `almost_empty`, `almost_full`) are derived from the synchronized pointers. Because pointers are Gray-coded, the comparison never sees invalid intermediate states.

### Verilog Instantiation (Vendor Primitive)

```verilog
// Xilinx: XPM FIFO
xpm_fifo_async #(
    .FIFO_WRITE_DEPTH(512),
    .WRITE_DATA_WIDTH(32),
    .READ_DATA_WIDTH(32)
) fifo_inst (
    .wr_clk(wr_clk),
    .rd_clk(rd_clk),
    .din(wr_data),
    .wr_en(wr_en),
    .rd_en(rd_en),
    .dout(rd_data),
    .full(full),
    .empty(empty)
);
```

For Intel devices, use the FIFO IP core or `scfifo`/`dcfifo` megafunction. For open-source flows, LiteX and other frameworks provide parametric async FIFO implementations.

---

## Pattern 4: Handshake Synchronizer

For occasional, low-bandwidth multi-bit data crossings where a FIFO is overkill, use a request/acknowledge handshake.

```
Source Domain                      Destination Domain
┌──────────┐                       ┌──────────┐
│ req ─────│──── 2-FF ────► data   │          │
│          │       ack ◄──── 2-FF  │          │
│ data ────│───────────────────────│──► latch │
└──────────┘                       └──────────┘
```

### Verilog Implementation

```verilog
// Source domain
reg req;
always @(posedge src_clk) begin
    if (start && !ack_sync)
        req <= 1;
    else if (ack_sync)
        req <= 0;
end

// Destination domain — synchronize req, latch data, generate ack
(* ASYNC_REG = "TRUE" *) reg [1:0] req_sync;
reg ack;
always @(posedge dst_clk) begin
    req_sync <= {req_sync[0], req};
    if (req_sync[1])
        latched_data <= src_data;
    ack <= req_sync[1];
end

// Source domain — synchronize ack back
(* ASYNC_REG = "TRUE" *) reg [1:0] ack_sync;
always @(posedge src_clk)
    ack_sync <= {ack_sync[0], ack};
```

Each transfer takes at least **4–6 clock cycles** (2 for req sync, 1 for data latch, 2 for ack return). Throughput is inherently limited — this pattern is for configuration registers, not streaming data.

---

## Pattern 5: MCP (Multi-Cycle Path with Synchronizer)

When a signal changes slowly relative to the destination clock (e.g., a configuration register that changes once per millisecond while the destination runs at 200 MHz), the signal is effectively static from the destination's perspective.

**Rule:** If the signal changes less than once per 1000 destination clock cycles, a single 2-FF synchronizer is sufficient, and you can declare the input path as a **false path** or **multi-cycle path** in timing constraints:

```tcl
# XDC: exclude the input synchronizer from timing analysis
set_false_path -from [get_ports async_config_reg*] -to [get_cells sync_ff_reg[0]]
```

This prevents the timing tool from trying to close timing on the intentionally metastable first stage.

---

## Common CDC Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Synchronizing a bus with 2-FF on each bit | Intermittent data corruption | Use Gray code or async FIFO |
| No `ASYNC_REG` attribute on synchronizer | Tool optimizes away or replicates FFs; MTBF collapses | Add attribute |
| Combinational logic between sync stages | Glitch propagates through | Pure wire connection between sync FFs |
| Using first sync FF output for logic | Metastability sampled by downstream logic | Only use second (or third) FF output |
| Missing timing exceptions on sync path | Tool reports timing violation; wastes effort | `set_false_path` on first stage |
| Clock gating on synchronizer clock | Missing clock edges → metastability persists longer | No gating on synchronizer's clock |
| CDC on a derived (gated/divided) clock | Unpredictable phase relationship | Treat as full CDC; use proper pattern |

---

## Choosing the Right CDC Pattern

| Signal Type | Throughput | Pattern | Complexity |
|---|---|---|---|
| Single-bit control | Low | 2-FF synchronizer | Minimal |
| Single-bit (safety) | Low | 3-FF synchronizer | Minimal |
| Multi-bit counter/pointer | Medium | Gray code + 2-FF | Low |
| Multi-bit streaming data | High | Async FIFO | Medium |
| Multi-bit occasional data | Low | Handshake | Medium |
| Slow-changing multi-bit | Low | 2-FF + false path timing exception | Minimal |

---

## Further Reading

| Resource | Description |
|---|---|
| [Cliff Cummings: CDC Design & Verification Using SystemVerilog (SNUG 2008)](http://www.sunburst-design.com/papers/) | The canonical reference on CDC |
| [Xilinx UG903: Timing Closure](https://docs.amd.com/) | XDC constraints for CDC paths |
| [ASYNC_REG pragma](vendor_pragmas.md#asynchronous-register-chain-async_reg) | Vendor attribute reference |
| [State Machines](state_machines.md) | FSM design — CDC-safe state encoding |
