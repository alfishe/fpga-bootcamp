[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# Inference Rules — HDL Pattern to Hardware Mapping

Synthesis tools don't "compile" HDL the way a C compiler compiles source code. They **recognize patterns** in your RTL and map them to specific hardware primitives: flip-flops, latches, RAM blocks, DSP slices, or multipliers. Writing HDL that infers the intended hardware — and doesn't accidentally infer something else — is the central skill of RTL design.

---

## The Synthesis Inference Engine

Every FPGA synthesis tool (Vivado, Quartus, Synplify, Yosys) follows the same logic:

```
HDL source → Parse → Elaborate → Pattern Match → Technology Map → Netlist
```

During **pattern matching**, the tool looks for specific code idioms. If it finds, for example, a `case` statement inside a `process(clock)` with a non-blocking assignment, it infers a flip-flop with clock enable and a multiplexer. If it finds an `always @*` block with an incomplete `if` (no `else`), it infers a latch — which may or may not be intentional.

The rules are remarkably consistent across vendors because they derive from the same IEEE synthesis subset (IEEE 1076.6 for VHDL, de-facto subset for Verilog).

---

## Flip-Flop vs Latch

This is the most fundamental inference distinction. The difference is **one missing `else`**.

### Flip-Flop Inference

**Verilog:**
```verilog
always @(posedge clk) begin
    if (rst)
        q <= 0;
    else
        q <= d;
end
```

**VHDL:**
```vhdl
process(clk)
begin
    if rising_edge(clk) then
        if rst = '1' then
            q <= '0';
        else
            q <= d;
        end if;
    end if;
end process;
```

**Rule:** All assignments inside a `posedge clk` / `rising_edge(clk)` block infer flip-flops. Both clock enable (CE) and synchronous/asynchronous reset are recognized by the surrounding `if` structure.

### Latch Inference (Accidental)

**Verilog (incomplete `if`):**
```verilog
always @(*) begin
    if (enable)
        q <= d;
    // Missing else → latch!
end
```

**VHDL (incomplete `if`):**
```vhdl
process(all)
begin
    if enable = '1' then
        q <= d;
    end if;  -- No else → latch!
end process;
```

**Rule:** Any combinational `always @*` / `process(all)` block where a variable is NOT assigned in every possible branch infers a **latch** to hold the previous value. This is the most common synthesis surprise.

> **`always_comb` / `always_latch` in SystemVerilog** catch this at compile time. `always_comb` prohibits latches — if you accidentally infer one, the tool errors. `always_latch` declares intent explicitly.

### Preventing Unintentional Latches

| Technique | Verilog | VHDL |
|---|---|---|
| Default assignment before `case`/`if` | `q = 0;` as first line of `always @*` | `q <= '0';` as first line of `process(all)` |
| Use defensive constructs | `always_comb` (SV) | `process(all)` with complete signal assignment check |
| Cover all `case` branches | Add `default:` | Add `when others =>` |

---

## RAM Inference (Block RAM / Distributed RAM)

BRAM inference requires a specific pattern: a memory array accessed with a clock. The synthesizer looks for:

1. An array declaration (reg/wire vector or VHDL array type)
2. A synchronous `always @(posedge clk)` or `process(clk)` that reads from it
3. Optionally, a write enable

### Single-Port RAM

**Verilog:**
```verilog
reg [7:0] mem [0:255];
always @(posedge clk) begin
    if (we)
        mem[addr] <= din;
    q <= mem[addr];
end
```

**VHDL:**
```vhdl
type mem_t is array (0 to 255) of std_logic_vector(7 downto 0);
signal mem : mem_t;
begin
process(clk)
begin
    if rising_edge(clk) then
        if we = '1' then
            mem(to_integer(unsigned(addr))) <= din;
        end if;
        q <= mem(to_integer(unsigned(addr)));
    end if;
end process;
```

**What gets inferred:** If the array depth exceeds the threshold for distributed RAM (typically 64–128 entries, vendor-dependent), the tool maps to **Block RAM** (BRAM/M9K/M20K). Below the threshold, it maps to **Distributed RAM** (LUT RAM).

### Dual-Port RAM

Adding a second read port (read address + data output) or a second write port produces dual-port Block RAM inference, provided both ports are synchronous.

### Vendor-Specific RAM Inference Attributes

| Vendor | Attribute | Effect |
|---|---|---|
| Xilinx | `(* ram_style = "block" *)` | Force BRAM |
| Xilinx | `(* ram_style = "distributed" *)` | Force LUT RAM |
| Intel | `(* ramstyle = "M9K" *)` | Force M9K/M20K/MLAB |
| Intel | `(* ramstyle = "logic" *)` | Force LUT RAM |

---

## ROM Inference

ROM is inferred when the data is initialized in the declaration and never written:

**Verilog:**
```verilog
reg [7:0] rom [0:255];
initial $readmemh("firmware.hex", rom);
// Or: assign directly in declaration
always @(posedge clk)
    q <= rom[addr];
```

**VHDL:**
```vhdl
type rom_t is array (0 to 255) of std_logic_vector(7 downto 0);
signal rom : rom_t := (
    0 => x"00", 1 => x"3F", 2 => x"6A", -- ...
    others => x"00"
);
begin
process(clk)
begin
    if rising_edge(clk) then
        q <= rom(to_integer(unsigned(addr)));
    end if;
end process;
```

Small ROMs (e.g., lookup tables for sine/cosine, state decoding) infer distributed LUT ROM. Larger ROMs infer Block ROM (BRAM configured as read-only).

---

## Multiplier and DSP Inference

The synthesis tool recognizes `*` (multiplication) and, when operands exceed a certain width, maps the operation to a hardware DSP slice (DSP48/DSP58 in Xilinx, variable-precision DSP in Intel).

| Operand Width | Typical Inference |
|---|---|
| ≤ 4 bits | LUT logic (no DSP) |
| 5–17 bits | DSP or LUT, vendor heuristic decides |
| ≥ 18 bits | DSP slice (almost always) |

### Force or Suppress DSP Inference

| Vendor | Attribute | Effect |
|---|---|---|
| Xilinx | `(* use_dsp = "yes" *)` | Force DSP |
| Xilinx | `(* use_dsp = "no" *)` | Suppress DSP, use LUTs |
| Intel | `(* multstyle = "dsp" *)` | Force DSP |
| Intel | `(* multstyle = "logic" *)` | Force LUT multiplier |

### Multiply-Accumulate (MAC)

A multiply followed by an add of the result (and optional register) infers a DSP slice with built-in accumulator:

```verilog
always @(posedge clk)
    acc <= acc + a * b;
```

This single line infers a complete MAC pipeline inside the DSP48 block — multiplier → adder → accumulator register — without consuming extra fabric logic.

---

## Shift Register Inference

### SRL (Shift Register LUT)

When you describe a shift register with a **fixed tap** (reading an intermediate stage), the Xilinx tool infers an SRL (Shift Register LUT) primitive that uses LUTs as an efficient shift register:

```verilog
reg [7:0] sr [0:15]; // 16-deep shift reg
always @(posedge clk) begin
    sr[0] <= din;
    for (i = 1; i < 16; i = i + 1)
        sr[i] <= sr[i-1];
end
assign q = sr[7]; // tap at stage 7
```

Without a tap, the tool infers flip-flops (or maps to SRL if the delay is long enough). The SRL threshold is vendor-specific.

---

## Priority Encoder vs Multiplexer

The `case` statement in RTL is actually a priority encoder, not a parallel multiplexer, unless modified:

| Construct | Infers | Notes |
|---|---|---|
| `case` (Verilog) / `case state is` (VHDL) | Priority encoder: first match wins | Synthesis adds priority logic (cascade of MUXes) |
| `unique case` (SV) / `case?` (SV) | Parallel MUX: all cases are mutually exclusive | Simpler hardware; simulation mismatch if cases overlap |
| `priority case` (SV) | Explicit priority encoder with assertion | Same hardware as `case`, but tool checks for unreachable branches |

The `if`/`elsif` chain also infers a priority encoder. A `case` statement with no overlaps infers the same hardware as a MUX, but only `unique case` tells the synthesizer to verify this at elaboration time.

---

## Quick Reference: Inference Cheat Sheet

| You Write | Synthesizer Infers | Gotcha |
|---|---|---|
| `always @(posedge clk)` with assignments | Flip-flops (registers) | Synchronous only |
| `always @(posedge clk)` with `if (rst)` before `else` | Flip-flop with **asynchronous reset** | Reset must be in sensitivity list for async |
| `always @(posedge clk)` with `if (rst)` after `else` | Flip-flop with **synchronous reset** | Order matters |
| `always @*` with `if` and no `else` | **Latch** (usually unintended!) | Use `always_comb` in SV |
| Array + `posedge clk` + write enable + read | BRAM or Distributed RAM | Depth determines which |
| Array + `posedge clk` + initialized + no write | ROM | `$readmemh` / aggregate init |
| `a * b` with wide operands | DSP slice multiplier | Narrow → LUTs |
| `acc <= acc + a * b` in `posedge clk` | DSP MAC (multiply-accumulate) | Zero extra fabric |
| `case` with non-overlapping cases | Parallel MUX | Use `unique case` to declare intent |
| `if`/`elsif` chain | Priority encoder | Highest-priority `if` wins |
| Shift register with tap | SRL (LUT-based shift reg) | Vendor SRL depth limits apply |
| Tri-state `assign bus = en ? data : 'bz` | IO pad tri-state buffer | Internal tri-state NOT supported in FPGAs |

---

## Further Reading

| Resource | Description |
|---|---|
| [Xilinx UG901: Vivado Synthesis Guide](https://docs.amd.com/r/en-US/ug901-vivado-synthesis) | Official coding examples and inference rules for AMD FPGAs |
| [Intel Quartus Design Recommendations](https://www.intel.com/programmable/technical-pdfs/683082.pdf) | Intel-specific HDL coding styles, RAM/ROM/DSP inference |
| [Yosys Documentation](https://yosyshq.readthedocs.io/) | Open-source synthesis inference behavior |
| [Verilog overview](verilog_sv/verilog.md) | The synthesis baseline language |
| [VHDL overview](vhdl/vhdl_basics.md) | Strongly-typed inference patterns |
| [Vendor pragmas](vendor_pragmas.md) | Attributes that control inference (`ram_style`, `use_dsp`, etc.) |
