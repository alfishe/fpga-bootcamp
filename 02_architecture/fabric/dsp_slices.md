[← Home](../../README.md) · [Architecture](../README.md) · [Fabric](README.md)

# DSP Slices — Hardened Multiply-Accumulate Engines

When an FPGA needs to run at hundreds of MHz and multiply numbers, LUT-based multipliers are the wrong answer. A 25×18 multiply implemented in LUTs consumes ~400 LUTs and struggles to hit 100 MHz. A single DSP48 slice does the same operation at 450+ MHz while burning one hardened silicon block. This article covers the DSP primitive architectures across all major vendors — their operating modes, cascading, SIMD capabilities, and how to make synthesis infer them correctly.

---

## Overview

A **DSP slice** is a hardened arithmetic unit containing at least one multiplier, an adder/accumulator, and configurable pipeline registers. Modern DSP slices (Xilinx DSP48E2, Intel Variable-Precision DSP, Lattice sysDSP) handle not just multiply-accumulate but also pattern detection, rounding, saturation, barrel shifting, and SIMD operations (packing multiple narrow operations into one wide slice). The critical design decisions are: **whether your operation fits a DSP** (bit widths matter), **how many pipeline stages you need** (under-pipelining kills fMAX), and **how to cascade slices** for wider or deeper operations without routing through the general fabric (dedicated cascade paths are ~3× faster than fabric routing).

---

## Vendor-by-Vendor Comparison

| Parameter | Xilinx DSP48E2 | Intel Cyclone V | Intel Agilex | Lattice sysDSP (ECP5) | Gowin DSP | Microchip Math |
|---|---|---|---|---|---|---|
| **Multiplier size** | 27×18 | 27×27 (var) | 18×19 (dual) | 18×18 | 18×18 | 18×18 |
| **Accumulator** | 48-bit | 64-bit | 64-bit | 36-bit | 48-bit | 44-bit |
| **Pre-adder** | Yes (25-bit) | No | No | No | No | No |
| **SIMD modes** | 2× 12-bit, 4× 7-bit | 2× 18×18, 3× 9×9 | 2× 18, 4× 7-bit | No | No | No |
| **Pattern detect** | Yes | No | No | No | No | No |
| **Cascade (column)** | Yes (48-bit) | Yes (44-bit) | Yes | Yes (36-bit) | Yes | Yes |
| **Max fMAX (slowest speed)** | 450 MHz (7-series) | 350 MHz | 500+ MHz | 200 MHz | 180 MHz | 300 MHz |
| **Pipeline stages** | 3 (M, P, A) + input regs | 3 | 3+ | 3 | 2 | 3 |
| **Hard pre-adder** | Yes (25-bit, for symmetric FIR) | No | No | No | No | No |

---

## Xilinx DSP48E2 — The Reference Design

The DSP48E2 (7-series) and DSP58 (UltraScale+) are the most feature-rich DSP blocks in the FPGA industry. One slice contains:

```
┌────────────── DSP48E2 ──────────────┐
│  A (30 bits) ──┐                     │
│                ├── Pre-Adder (25b)──┐│
│  D (25 bits) ──┘                   ││
│                                     ↓│
│  B (18 bits) ──────────→ [ 27×18 ] ─┤
│                                      ││
│  C (48 bits) ────────────────────→ [+]──→ P (48 bits)
│                                       │
│  Pattern Detect ←────────────────────┘
│  (overflow, underflow, ==C, ==0)
│
│  Pipeline: A1→A2→M→P→  (all optional)
│  Cascade: PCIN → PCOUT (dedicated 48b)
└──────────────────────────────────────┘
```

**SIMD Modes:**
| Mode | Operations per Slice | Widths |
|---|---|---|
| ONE48 | 1× (27×18 + 48) | 48-bit result |
| TWO24 | 2× (12×18 + 24) | Two independent 24-bit results |
| FOUR12 | 4× (7×18 + 12) | Four independent 12-bit results |

The SIMD mode splits the 48-bit adder into 2× 24-bit or 4× 12-bit units, enabling INT8 convolution (4 MACs/slice) and INT16 (2 MACs/slice). This is how Xilinx FPGAs achieve competitive AI inference throughput without dedicated AI engines.

**The Pre-Adder:** A 25-bit adder before the multiplier (A ± D → multiplier input). This is the killer feature for symmetric FIR filters: compute `(h[k] × (x[n-k] + x[n-2N+k]))` in one slice instead of two.

**Pattern Detect:** Hardware comparison against C register or zero. Detects overflow/underflow, saturation boundary crossing, and counter thresholds — all without consuming fabric LUTs.

### DSP58 (UltraScale+) Upgrades
- 27×24 multiplier (wider B-input)
- 96-bit cascade (vs 48-bit in DSP48E2)
- Optional pipeline at every stage
- Enhanced pattern detection

---

## Intel Variable-Precision DSP

### Cyclone V — 3-Mode DSP

Each Cyclone V DSP block can be configured three ways:

| Mode | Multipliers | Accumulator | Notes |
|---|---|---|---|
| 3× 9×9 | 3 independent | No | Best for narrow filters |
| 2× 18×18 | 2 independent | 44-bit shared | Dual MAC or complex multiply |
| 1× 27×27 | 1 | 64-bit | Wide multiply, single result |

The 27×27 mode supports full 24-bit mantissa × 24-bit mantissa with room for exponent — enough for single-precision floating-point emulation in fixed-point.

### Arria 10 / Stratix 10 — 2× 18×19

Arria 10 and Stratix 10 use a refined design: two 18×19 multipliers per block, each with independent 64-bit accumulator. This matches the 2× 18×18 mode from Cyclone V but with independent accumulators (previously shared).

### Agilex — AI Tensor DSP

Agilex introduces **AI Tensor DSP** blocks that support:
- **INT8**: 20 TOPS (tera-operations per second) across 1,500+ blocks
- **BF16 (Brain Float 16)**: 10 TFLOPS
- **FP16**: 5 TFLOPS
- **Block FP**: Shared exponent for mixed-precision

Each tensor block performs matrix-vector products natively. This is the direct Intel competitor to Xilinx Versal AI Engines, but integrated into the DSP column rather than a separate compute tile.

---

## Lattice sysDSP — Clean and Predictable

### ECP5 sysDSP

ECP5 uses a straightforward 18×18 multiplier with 36-bit accumulator and 3 pipeline stages:

| Feature | ECP5 sysDSP |
|---|---|
| Multiplier | 18×18 signed/unsigned |
| Accumulator | 36-bit |
| Cascade | Dedicated 36-bit chain |
| SIMD | No |
| Pre-adder | No |
| Input registers | 3 stages (configurable) |

No SIMD, no pattern detect, no pre-adder — but the clean design makes inference predictable and timing reliable at 200 MHz. For most mid-range DSP (FIR, FFT, NCO), this is more than enough.

### CertusPro-NX sysDSP

Upgrades to 18×18 with 44-bit accumulator and improved cascade speed. Adds single-instruction multiple data (SIMD) for 2× 9×9 operations.

---

## Gowin DSP and Microchip Math

### Gowin DSP

18×18 multiplier with 48-bit accumulator and 2 pipeline stages. No SIMD, no pre-adder. At 180 MHz fMAX, sufficient for cost-sensitive designs but limited for high-throughput DSP pipelines. Works well for simple IIR/FIR filters, control loops, and CORDIC.

### Microchip Math Block (PolarFire)

18×18 multiplier with 44-bit accumulator. Supports dot-product mode (sum of two 18×18s). No SIMD or pre-adder. Designed for low-power arithmetic rather than peak throughput — consistent with PolarFire's flash-based, power-conscious positioning.

---

## DSP Inference: Writing HDL That Actually Maps to DSPs

Synthesis tools are good at inferring DSP usage from simple patterns but fail silently on complex ones:

### Patterns That Infer DSP

```verilog
// ✅ Simple multiply — infers DSP reliably
assign product = a * b;

// ✅ Multiply-accumulate — infers DSP with accumulator
always @(posedge clk)
    acc <= acc + a * b;

// ✅ Multiply-add — infers DSP with pre-adder (Xilinx)
assign result = a * (b + c);  // Pre-adder used on Xilinx DSP48E2

// ✅ Pipeline stages — critical for fMAX
reg [17:0] a_r, b_r;
reg [35:0] mult_r;
always @(posedge clk) begin
    a_r   <= a;
    b_r   <= b;
    mult_r <= a_r * b_r;        // M-reg stage
    acc   <= acc + mult_r;     // P-reg stage
end
```

### Patterns That Break DSP Inference

```verilog
// ❌ Complex expression — synthesis may not recognize DSP
assign result = (a * b) + (c * d) + (e * f);  // 3 DSPs but may infer LUTs

// ❌ Reset on accumulator — resets are fabric, not DSP
always @(posedge clk or posedge rst)
    if (rst) acc <= 0; else acc <= acc + a * b;  // Async reset blocks DSP inference

// ❌ Wide multiply without register stages
assign wide = {16'd0, a} * {16'd0, b};  // 32×32 may infer 4 DSPs + fabric logic
```

### Multi-Vendor DSP Inference Pragmas

| Vendor | Attribute |
|---|---|
| Xilinx | `(* use_dsp = "yes" *)` / `(* mult_style = "dsp" *)` |
| Intel | `(* multstyle = "dsp" *)` |
| Lattice | `(* mult_style = "dsp" *)` / `(* syn_multstyle = "dsp" *)` |
| Gowin | `(* use_dsp = "yes" *)` |

---

## When to Use / When NOT to Use

### When to Use DSP

| Scenario | Reason |
|---|---|
| Multiplier > 4×4 bits | LUT multipliers explode exponentially; >4×4 always use DSP |
| fMAX > 200 MHz | DSP pipelining achieves fMAX impossible with LUT-based DSP |
| FIR/FFT/DDS pipelines | DSP48E2 pre-adder cuts FIR resource count in half. Cascade chains avoid routing bottlenecks |
| INT8/INT16 convolution | SIMD mode packs 2–4 ops per slice (Xilinx/Intel) |
| Floating-point emulation | Wide multipliers (27×27) with 48/64-bit accumulators handle mantissa + exponent comfortably |

### When NOT to Use DSP

| Scenario | Recommendation |
|---|---|
| 4×4 or smaller multiply | LUT-based. A 4×4 multiply uses 16 LUTs — cheaper than consuming a DSP slice |
| Basic counter/comparator | Use LUTs + carry chain. DSP is overkill for simple add/compare |
| All DSPs consumed | Fall back to LUT multipliers if vendor tool allows; accept the fMAX/power penalty |
| FPGA without DSP (iCE40) | LUT multipliers. Use pipelining to recover fMAX; expect ~10× area and ~3× lower fMAX vs DSP |

---

## Best Practices & Antipatterns

### Best Practices
1. **Pipeline, pipeline, pipeline** — Always register DSP inputs and outputs. A single unregistered multiply limits the entire block to ~100 MHz. Two pipeline stages (input + M-reg + output) pushes it to 450 MHz
2. **Use cascade paths for adder chains** — Chaining DSP accumulate outputs through the dedicated cascade port is 3× faster than routing through fabric
3. **Enable SIMD for INT8 inference** — 4 MACs/slice beats using 4 separate DSPs. Check vendor documentation for SIMD RTL patterns
4. **Match data widths to DSP native sizes** — 18×18, 27×18, 25×18 are the native widths. Using 19×17 wastes DSP capability. Pad to next compatible size or accept that synthesis will use two DSPs

### Antipatterns

| Antipattern | The Problem | The Fix |
|---|---|---|
| **"The Unpipelined Wish"** | Writing `always @(posedge clk) result <= a * b + c` with no intermediate registers | fMAX drops to ~150 MHz. Add at least one pipeline stage between multiply and accumulate |
| **"The Reset Addiction"** | Adding async reset to DSP accumulator | Async reset forces fabric logic around the DSP, breaking inference. Use sync reset in same always block or no reset (power-on value is 0) |
| **"The Cascade Avoidance"** | Connecting DSP outputs through fabric instead of cascade | Routing delay increases 3–5×. Use dedicated PCIN/PCOUT (Xilinx) or chainin/chainout (Intel) |
| **"The Mixed-Vendor Assumption"** | Writing RTL that depends on DSP48E2 pre-adder or SIMD and expecting it to work on ECP5 | Abstract vendor-specific DSP patterns behind `ifdef or generate. Accept resource doubling on Lattice/Gowin |

---

## Pitfalls & Common Mistakes

### 1. Under-Pipelining the DSP48 Chain

**The mistake:** Implementing a 16-tap FIR filter with DSP48 cascades at 1 pipeline stage per tap.

**Why it fails:** Each DSP adds combinatorial delay. At 16 taps × 1.5 ns per DSP = 24 ns → 42 MHz fMAX. The design fails timing.

**The fix:** Enable the internal M-reg and P-reg on each DSP48. Each tap runs at 1/(1.5 ns + negligible routing) ≈ 450 MHz. The pipeline adds latency (16 × 3 = 48 cycles) but preserves throughput.

### 2. Expecting SIMD Mode Without Explicit Coding

**The mistake:** Writing `packed_a = {a3, a2, a1, a0}` and multiplying, expecting the tool to use FOUR12 mode.

**Why it fails:** Synthesis does not auto-split packed vectors into SIMD ops. It treats the operation as a wide multiply and uses multiple DSPs.

**The fix:** Use vendor-specific DSP instantiation templates or Vitis HLS SIMD pragmas. Most vendors require explicit RTL patterns or IP catalog instantiation for SIMD mode.

### 3. Floating-Point on Fixed-Point DSP

**The mistake:** Translating `float a, b; result = a * b + c;` directly to FPGA, expecting DSP inference.

**Why it fails:** FPGA DSPs are fixed-point. Floating-point requires mantissa multiply, exponent add, normalization, and rounding — 5–10 DSPs per float operation. A naive conversion wastes resources.

**The fix:** Use fixed-point wherever possible. Pre-scale values to avoid overflow. If floating-point is mandatory, use vendor FPU IP (Xilinx FloPoCo, Intel FP functions) or consider Agilex BF16 tensor DSPs.

---

## Real-World Use Cases

- **FIR filters:** DSP48E2 pre-adder + cascade chain → symmetric FIR at 1 DSP/tap instead of 2
- **FFT butterflies:** 3 DSPs per radix-2 complex multiply (18×18 real/imag components)
- **NCO / DDS:** Phase accumulator (DSP or LUT) + sine/cosine LUT (BRAM)
- **AI inference:** INT8 convolution with SIMD FOUR12 (Xilinx) or tensor DSP (Agilex) → 4 MACs/slice
- **PID control loops:** Single DSP per axis: P×err + I×integrator + D×derivative, all in one accumulated pipeline
- **CORDIC rotation:** DSP-based CORDIC runs 3× faster than LUT CORDIC at the cost of DSP blocks

---

## References

| Source | Document |
|---|---|
| Xilinx UG479 — 7-Series DSP48E1 | https://docs.xilinx.com/ |
| Xilinx UG579 — UltraScale DSP58 | https://docs.xilinx.com/ |
| Intel CV-5V2 — Cyclone V Variable-Precision DSP | Intel FPGA Documentation |
| Lattice TN1265 — ECP5 sysDSP Usage Guide | Lattice Tech Docs |
| Gowin UG287 — DSP User Guide | Gowin Docs |
| Microchip PolarFire Math Block | Microchip Docs |
| [LUTs and CLBs](luts_and_clbs.md) | Fabric logic primitives |
| [BRAM and URAM](bram_and_uram.md) | Memory for coefficient/LUT storage |
| [Routing](routing.md) | How DSPs connect to fabric and each other |
