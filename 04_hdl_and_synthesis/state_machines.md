[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# State Machines — Safe FSM Design for FPGAs

Finite State Machines (FSMs) are the backbone of sequential control logic. A well-designed FSM is readable, synthesizes efficiently, and recovers gracefully from invalid states. A poorly designed one burns power, wastes resources, and can lock up irrecoverably in the field.

---

## Encoding: One-Hot vs Binary vs Gray

The encoding choice directly affects resource usage, timing, and power.

### One-Hot Encoding

One flip-flop per state. Exactly one bit is `1` at any time; all others are `0`. State transition logic is wide (looks at many bits) but shallow (one level of logic).

| Aspect | One-Hot |
|---|---|
| **Flip-flops** | N for N states |
| **Next-state logic** | Minimal — one-hot comparisons are trivial |
| **Timing** | Excellent — shallow logic depth per transition |
| **Power** | Higher — all FFs toggle on every state change |
| **Valid state check** | Simple: count ones → must equal exactly 1 |
| **Best for** | FPGA fabrics with abundant FFs; high-speed designs |

### Binary (Sequential) Encoding

States are enumerated as binary integers. N flip-flops encode 2^N states.

| Aspect | Binary |
|---|---|
| **Flip-flops** | ⌈log₂(N)⌉ |
| **Next-state logic** | More complex — full binary comparison needed |
| **Timing** | Potentially worse — deeper logic for wide state registers |
| **Power** | Lower — fewer FFs toggle |
| **Valid state check** | Must enumerate all valid states; `others`/`default` catches invalid |
| **Best for** | CPLDs with limited FFs; ASICs where FF count costs silicon |

### Gray Encoding

Adjacent states differ by exactly 1 bit. Combines some one-hot properties with binary density.

| Aspect | Gray |
|---|---|
| **Flip-flops** | ⌈log₂(N)⌉ |
| **Next-state logic** | Medium complexity |
| **Timing** | Medium |
| **Power** | Low — minimal simultaneous bit transitions between adjacent states |
| **Best for** | FSMs where consecutive states are the primary transition path; CDC pointer crossing |

### Auto / Tool-Determined

Most synthesis tools default to `"auto"`, which heuristically selects encoding based on FSM size, timing criticality, and device architecture. For small FSMs (≤ 8 states), one-hot is typical. For large FSMs (> 32 states), binary is typical in ASICs, one-hot still common in FPGAs.

---

## Two-Process vs One-Process FSM Style

### One-Process (Single always/proc)

All state register + next-state logic in a single block. Terser but mixes sequential and combinational logic in one scope.

```verilog
always @(posedge clk or posedge rst) begin
    if (rst) begin
        state <= IDLE;
    end else begin
        case (state)
            IDLE:   if (start) state <= RUN;
            RUN:    if (done)  state <= IDLE;
            default: state <= IDLE;
        endcase
    end
end
```

### Two-Process (Recommended)

Separates the state register (purely sequential) from next-state logic (purely combinational). Better matches the hardware. Use `always_ff` and `always_comb` in SystemVerilog for compile-time checking.

```verilog
// Sequential: state register
always_ff @(posedge clk or posedge rst) begin
    if (rst)
        state <= IDLE;
    else
        state <= next_state;
end

// Combinational: next-state logic
always_comb begin
    next_state = state; // Default: stay in current state (prevents latch!)
    case (state)
        IDLE: if (start) next_state = RUN;
        RUN:  if (done)  next_state = IDLE;
        default: next_state = IDLE;
    endcase
end
```

The two-process style is preferred because:
1. It makes latches impossible (the default assignment covers all branches)
2. It decouples the register inference from the transition logic
3. It produces cleaner timing reports — the state register is exactly one level of FFs

---

## Mealy vs Moore

| Aspect | Moore | Mealy |
|---|---|---|
| **Output depends on** | Current state only | Current state + inputs |
| **Output timing** | Synchronous to clock edge | Combinational — may glitch between clock edges |
| **State count** | May require more states | Fewer states possible (output encoded in transitions) |
| **Timing closure** | Easier — outputs are registered | Harder — outputs are combinational paths |
| **Best for** | Most FPGA designs | Tight latency requirements, protocol state machines |

**Modern consensus:** Use Moore machines by default. Outputs are clean, registered, and glitch-free. Use Mealy only when the extra state or latency of Moore is unacceptable.

### Registered Mealy (Hybrid)

A compromise: register the Mealy outputs by adding an output pipeline stage. This preserves the low-state-count advantage while eliminating combinational output glitches.

```verilog
// Mealy transition: output is combinational
assign grant = (state == ARB) & req;

// Registered Mealy: pipeline the output
always_ff @(posedge clk)
    grant_reg <= (next_state == ARB) & req; // next_state is combinational
```

---

## Reset Strategies

### Asynchronous Reset

```verilog
always @(posedge clk or posedge rst)
    if (rst) state <= IDLE;
```

**Pros:** Resets immediately without a free-running clock. Essential for startup before PLLs lock.
**Cons:** Asynchronous de-assertion can cause metastability if `rst` is released near a clock edge. De-assertion glitches may cause partial resets.

### Synchronous Reset

```verilog
always @(posedge clk)
    if (rst) state <= IDLE;
```

**Pros:** Clean timing — reset is sampled like any other synchronous input. No metastability on de-assertion.
**Cons:** Requires a free-running clock to assert reset. A truly dead clock = no reset possible.

### Asynchronous Assert, Synchronous De-Assert (Best Practice)

```verilog
// External async reset → synchronize internally
(* ASYNC_REG = "TRUE" *) reg [1:0] rst_sync;
always @(posedge clk or posedge ext_rst) begin
    if (ext_rst) begin
        rst_sync <= 2'b11;
    end else begin
        rst_sync <= {rst_sync[0], 1'b0};
    end
end
wire safe_rst = rst_sync[1]; // De-asserts synchronously

// FSM uses the synchronized reset
always @(posedge clk) begin
    if (safe_rst) state <= IDLE;
    else          state <= next_state;
end
```

---

## Safe State Recovery — The "Unreachable State" Problem

In binary encoding, N flip-flops can represent 2^N possible bit patterns. If the FSM has M states where M < 2^N, the unused patterns are **unreachable states**. If a cosmic ray, power glitch, or metastability event flips a bit, the FSM can land in one of these zombie states and **stay there forever**.

### Verilog: Default Case to Safe State

```verilog
always_comb begin
    next_state = IDLE; // Safe default BEFORE the case
    case (state)
        IDLE:  if (start)   next_state = RUN;
        RUN:   if (done)    next_state = IDLE;
        HALT:  if (restart) next_state = IDLE;
        // No default needed — the initial assignment already covers it
    endcase
end
```

### VHDL: When Others To Safe State

```vhdl
process(all)
begin
    next_state <= IDLE; -- Default to safe state
    case state is
        when IDLE => if start = '1' then next_state <= RUN; end if;
        when RUN  => if done = '1'  then next_state <= IDLE; end if;
        when others => next_state <= IDLE; -- Recovery from invalid
    end case;
end process;
```

### Vendor FSM Safe State Attributes

| Vendor | Attribute | Effect |
|---|---|---|
| Xilinx | `(* fsm_safe_state = "auto" *)` | Auto-generates recovery logic from invalid states |
| Xilinx | `(* fsm_safe_state = "reset" *)` | Invalid state → reset state |
| Intel | Handled inside Quartus FSM extraction | Tool detects FSM and adds recovery |
| Synplify | `syn_encoding = "safe"` | Adds recovery logic automatically |

> **Even with vendor-safe attributes, write the `default`/`when others` branch yourself.** The attribute is a safety net; the explicit code is the primary defense.

---

## FSM Coding Checklist

| Rule | Why |
|---|---|
| Use `always_ff`/`always_comb` (SV) or separate processes (VHDL) | Compile-time latch prevention |
| Default `next_state = state` at top of combinational process | Eliminates latch inference |
| Cover all cases — always have `default:` or `when others =>` | Safe recovery from invalid states |
| Use `enum` or `parameter`/`localparam` for state names | Readable, synthesis-friendly, type-safe |
| Use `unique case` / `priority case` (SV) to declare intent | Tool can verify FSM properties |
| Register outputs (Moore style) by default | Glitch-free outputs, easier timing |
| Synchronize external resets internally | Avoid metastability on reset de-assertion |
| Add `fsm_safe_state` / `syn_encoding = "safe"` | Hardware-level recovery for radiation-induced corruption |
| Prefer one-hot for FPGA fabrics | Abundant FFs, shallow logic → higher Fmax |

---

## Further Reading

| Resource | Description |
|---|---|
| [Cliff Cummings: FSM Design](http://www.sunburst-design.com/papers/) | Canonical papers on FSM coding styles |
| [Xilinx UG901: FSM Coding Examples](https://docs.amd.com/r/en-US/ug901-vivado-synthesis) | Vivado FSM extraction and safe state attributes |
| [Vendor pragmas — FSM encoding](vendor_pragmas.md#fsm-encoding) | Attribute reference for encoding control |
| [Inference Rules](inference_rules.md) | How FSMs map to flip-flops and LUTs |
| [CDC Coding Patterns](cdc_coding.md) | Crossing state machine signals between clock domains |
