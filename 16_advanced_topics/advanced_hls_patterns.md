[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Advanced HLS Patterns & Optimization

Moving beyond basic High-Level Synthesis (HLS) overviews, this article dives into writing performant algorithms in C++ for FPGA synthesis. The difference between "it synthesizes" and "it runs at 300 MHz with II=1" is entirely in how you structure your C++ for the compiler's micro-architecture inference.

This article uses a running example throughout: **tiled 32×32 matrix multiply**. This is the canonical HLS problem — it exercises loop pipelining, memory partitioning, data reuse, and DSP inference all at once.

> [!NOTE]
> For an introduction to HLS tools, pragmas, and the basic synthesis flow, see [HLS Overview](../../13_toolchains/hls_overview.md). This article assumes familiarity with `#pragma HLS PIPELINE`, `UNROLL`, and `ARRAY_PARTITION`.

---

## 1. The Running Example: Tiled Matrix Multiply

### 1.1 Naive Implementation (Baseline)

```cpp
void matmul_naive(
    const float A[32][32],
    const float B[32][32],
    float C[32][32]
) {
    for (int i = 0; i < 32; i++) {
        for (int j = 0; j < 32; j++) {
            float sum = 0.0f;
            for (int k = 0; k < 32; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}
```

**Vitis HLS synthesis result (no pragmas):**
- Latency: ~34,000 cycles (32³ = 32,768 compute cycles + loop overhead)
- II (innermost loop): ~1 cycle (simple accumulator)
- Resource: ~5 DSP slices, ~300 LUTs
- Throughput: one 32×32 multiply every 34k cycles — **terrible**

The compiler produced a sequential, single-accumulator machine. No parallelism.

### 1.2 What We Need

| Goal | Target | How |
|---|---|---|
| Parallel multiplies per cycle | 8 MACs | `UNROLL` the `k` loop by 8 |
| Continuous throughput | One result per cycle | `PIPELINE` the `j` loop with II=1 |
| Feed 8 operands per cycle | 8 reads from each array | `ARRAY_PARTITION` A, B, C |
| Use DSP48 slices | Not LUTs | Fixed-point `ap_int` types; DSP inference |
| If memory-bound, tile to reuse data | 1 tile = 8×8 | Add outer tiling loops |

### 1.3 From C++ to Hardware — What the Compiler Actually Builds

Understanding what HDL the HLS compiler generates for a given C++ pattern is essential for reasoning about resource usage and latency. Below, the same `add_arrays` function is shown under four different pragma regimes, each producing radically different hardware.

**Baseline C++ function (Variant A—no pragmas):**

```cpp
void add_arrays(const int A[8], const int B[8], int C[8]) {
    for (int i = 0; i < 8; i++) {
        C[i] = A[i] + B[i];
    }
}
```

> We use plain `int` here to isolate control-structure translation. For DSP-friendly types, see Section 6.

#### Variant A — No Pragmas (Sequential State Machine)

Without any `#pragma`, the compiler produces a **finite state machine** that iterates sequentially. Each loop iteration becomes a state transition.

**Conceptual HDL equivalent:**

```verilog
// HLS compiler infers a state machine with one adder, one counter
always @(posedge clk) begin
    case (state)
        S_IDLE: begin
            i <= 0;
            if (start) state <= S_LOOP;
        end
        S_LOOP: begin
            if (i < 8) begin
                C[i] <= A[i] + B[i];  // single 32-bit addition
                i    <= i + 1;
            end else begin
                state <= S_DONE;
            end
        end
        S_DONE: begin
            done <= 1;
            if (start == 0) state <= S_IDLE;
        end
    endcase
end
```

**Result:**

| Metric | Approximate |
|---|---|
| Latency | 8 + overhead ≈ 10 cycles |
| Throughput | 1 result every 10 cycles |
| LUTs | ~50 (counter + FSM) |
| DSP48 | 0 (no multiply; 32-bit add in fabric) |
| BRAM | 0 (arrays small enough to be registers) |

> The compiler builds one execution unit (a single adder) and reuses it 8 times. This is the most area-efficient variant but has the worst throughput.

---

#### Variant B — PIPELINE II=1 (Pipelined Datapath)

```cpp
void add_arrays(const int A[8], const int B[8], int C[8]) {
    for (int i = 0; i < 8; i++) {
        #pragma HLS PIPELINE II=1
        C[i] = A[i] + B[i];
    }
}
```

`PIPELINE II=1` instructs the compiler to start a new iteration every clock cycle. The FSM is replaced by a **pipelined datapath** where read, compute, and write stages overlap.

**Conceptual HDL equivalent:**

```verilog
// Pipeline stages inferred by HLS:
//   Stage 1: read A, B   →   Stage 2: add   →   Stage 3: write C
always @(posedge clk) begin
    // Stage 1: address generation + read
    A_stage1 <= A[i];
    B_stage1 <= B[i];
    i_stage1 <= i;
    // Stage 2: compute
    sum_stage2 <= A_stage1 + B_stage1;
    i_stage2   <= i_stage1;
    // Stage 3: write-back
    C[i_stage2] <= sum_stage2;

    if (i == 7 && i_stage1 == 7 && i_stage2 == 7)
        done <= 1;
    else
        i <= i + 1;
end
```

**Result:**

| Metric | Approximate |
|---|---|
| Latency | 8 + 2 (pipeline fill/drain) ≈ 10 cycles |
| Throughput | **1 result every cycle** (after pipeline fills) |
| II | 1 (new iteration starts every clock) |
| LUTs | ~80 (FSM, pipeline registers, control) |
| Flip-flops | ~150 (three pipeline stages holding data in flight) |
| DSP48 | 0 |
| BRAM | 0 |

> The area is about 1.5× Variant A, but throughput improves by nearly **10×**. The hardware now resembles a 3-stage CPU pipeline: fetch operands, execute add, write result—each stage operating on a different iteration simultaneously.

---

#### Variant C — PIPELINE II=1 + UNROLL factor=4 (Parallel Datapaths)

```cpp
void add_arrays(const int A[8], const int B[8], int C[8]) {
    for (int i = 0; i < 8; i += 4) {
        #pragma HLS PIPELINE II=1
        #pragma HLS UNROLL factor=4
        C[i]   = A[i]   + B[i];
        C[i+1] = A[i+1] + B[i+1];
        C[i+2] = A[i+2] + B[i+2];
        C[i+3] = A[i+3] + B[i+3];
    }
}
```

`UNROLL factor=4` **replicates** the loop body 4 times in hardware. Each copy contains its own adder. All 4 results are computed in parallel every cycle.

**Conceptual HDL equivalent:**

```verilog
// 4 independent adders in parallel, each fed by separate array ports
always @(posedge clk) begin
    // Stage 1: read 4 elements from each array simultaneously
    A0 <= A[i];   A1 <= A[i+1];   A2 <= A[i+2];   A3 <= A[i+3];
    B0 <= B[i];   B1 <= B[i+1];   B2 <= B[i+2];   B3 <= B[i+3];
    addr_stage1 <= i;
    // Stage 2: 4 parallel 32-bit additions
    sum0 <= A0 + B0;  sum1 <= A1 + B1;
    sum2 <= A2 + B2;  sum3 <= A3 + B3;
    addr_stage2 <= addr_stage1;
    // Stage 3: write 4 results
    C[addr_stage2]   <= sum0;  C[addr_stage2+1] <= sum1;
    C[addr_stage2+2] <= sum2;  C[addr_stage2+3] <= sum3;

    if (addr_stage2 >= 4) done <= 1;
    else i <= i + 4;
end
```

**Result (requires ARRAY_PARTITION to feed 4 parallel reads):**

| Metric | Approximate |
|---|---|
| Latency | 2 + 2 (pipeline fill/drain) ≈ 4–5 cycles |
| Throughput | **4 results every cycle** |
| II | 1 |
| LUTs | ~200 (4 adders + control + muxing) |
| Flip-flops | ~300 |
| DSP48 | 0 |
| BRAM (if arrays are large) | 4 blocks (must partition to give 4 read ports) |

> The area scales roughly **linearly** with unroll factor. Each unroll factor adds one more parallel execution unit. If the arrays are large enough to require BRAM, you **must** also `ARRAY_PARTITION` to provide enough simultaneous read ports; otherwise II degrades to ≥4 regardless of the unroll directive.

---

#### Variant D — UNROLL Complete + ARRAY_PARTITION Complete (Fully Unrolled Registered Datapath)

```cpp
void add_arrays(const int A[8], const int B[8], int C[8]) {
    #pragma HLS ARRAY_PARTITION variable=A complete dim=0
    #pragma HLS ARRAY_PARTITION variable=B complete dim=0
    #pragma HLS ARRAY_PARTITION variable=C complete dim=0
    for (int i = 0; i < 8; i++) {
        #pragma HLS UNROLL
        C[i] = A[i] + B[i];
    }
}
```

`UNROLL` with no factor unrolls the **entire** loop. Combined with `ARRAY_PARTITION complete`, every array element is a discrete register. The compute logic is combinational, bounded by registered inputs and outputs.

**Conceptual HDL equivalent:**

```verilog
// All 8 additions computed in parallel as a single combinational cloud.
// ARRAY_PARTITION complete makes each element an independent wire/reg.
wire [31:0] A [0:7];  // 8 independent 32-bit input wires
wire [31:0] B [0:7];
reg  [31:0] C [0:7];

// Purely combinational: no FSM, no pipeline stages, no loop counter
always @(posedge clk) begin
    C[0] <= A[0] + B[0];
    C[1] <= A[1] + B[1];
    C[2] <= A[2] + B[2];
    C[3] <= A[3] + B[3];
    C[4] <= A[4] + B[4];
    C[5] <= A[5] + B[5];
    C[6] <= A[6] + B[6];
    C[7] <= A[7] + B[7];
end
```

**Result:**

| Metric | Approximate |
|---|---|
| Latency | **1 cycle** (input register → add → output register) |
| Throughput | **8 results every cycle** |
| LUTs | ~64 (8 × 32-bit adders, ≈8 LUTs each for fabric add) |
| Flip-flops | ~50 (just the output registers; no pipeline overhead) |
| DSP48 | 0 |
| BRAM | 0 (complete partition → all registers, no BRAM) |

> This variant has the lowest latency and highest throughput, but it scales poorly. An `N=1024` array with complete unroll would create 1,024 parallel adders — consuming tens of thousands of LUTs and likely failing routing. Complete unroll is for small, fixed-size arrays (N ≤ ~64 for 32-bit operations; N ≤ ~256 for 8-bit).

---

#### Summary: Pragma → HDL Translation Chain

| C++ Directive | HDL Equivalent | Area | Latency | Throughput |
|---|---|---|---|---|
| _(none)_ | FSM + single datapath unit | ★ (minimum) | N × cycle_time | 1/N per cycle |
| `PIPELINE II=1` | Pipelined datapath with overlapping stages | ★★ | N + pipeline_depth | 1 per cycle |
| `PIPELINE II=1` + `UNROLL factor=F` | F parallel datapaths, each pipelined | ★★★ (≈F×) | N/F + pipe_depth | F per cycle |
| `UNROLL complete` + `PARTITION complete` | Fully combinational cloud (no FSM) | ★★★★★ (≈N×) | 1 cycle | N per cycle |

**The fundamental trade-off:** HLS lets you dial anywhere from minimal-area sequential to maximal-throughput combinational by adding a single pragma. The compiler handles the mechanical work of replicating hardware, inserting pipeline registers, and resolving memory port contention. But you must understand what each pragma instructs the compiler to build, or you risk unwittingly requesting a design that cannot fit on the device.

---

## 2. PIPELINE — The Heart of HLS

### 2.1 How Pipeline Works

`#pragma HLS PIPELINE` overlaps loop iterations. Without pipelining, iteration N+1 starts only after iteration N finishes:

```
No pipeline:
  Iter 0: [read|compute|write]                   Latency = 3 cycles/iter
  Iter 1:                           [read|comp|w]
  Iter 2:                                        [r|c|w]
  Total = 9 cycles for 3 iterations
```

With pipelining, iteration N+1 starts before N finishes — as soon as the first stage is free:

```
II=1 pipeline:
  Cycle:   1    2    3    4    5
           [R ][C ][W ]
  Iter 0:  A  | A  | A  |    |
  Iter 1:      B  | B  | B  |
  Iter 2:          C  | C  | C
  Total = 5 cycles for 3 iterations (II=1)
```

**II (Initiation Interval)** = cycles between starting iteration N and N+1. II=1 means one new result every clock.

### 2.2 Why II > 1 Happens

The HLS compiler prints `II=2` (or worse) when something blocks the pipeline. The most common causes:

| Cause | Symptom | Fix |
|---|---|---|
| **BRAM port contention** | "Unable to schedule load operation" | `ARRAY_PARTITION` — give the array more ports |
| **Loop-carried dependency** | Variable written in iteration N and read in N+1 | Restructure algorithm to remove dependency, or accept higher II |
| **Unbalanced pipeline stages** | One operation takes 3 cycles, rest take 1 | Add explicit pipeline registers via `ap_shift_reg` |
| **Function call inside pipeline** | Called function not inlined | `#pragma HLS INLINE` |

### 2.3 Fixing II with the Console Output

When synthesis reports `II=2`, the Vitis HLS console tells you exactly why:

```
WARNING: [HLS 200-845] Unable to schedule 'load' operation ('B_load_1',
matrix_mult.cpp:12) on array 'B' due to limited memory ports.

Resolution: Consider using array reshape/partition to increase memory bandwidth.
```

**Translation:** The array `B` is stored in a single BRAM block. A BRAM has 2 ports (1 read + 1 write, or 2 reads on dual-port). The pipeline needs to read from `B` twice in the same cycle (iteration N reads B[k][j], iteration N+1 reads B[k+1][j]). BRAM can't do it. Partition `B`.

### 2.4 Overriding False Dependencies

The compiler's dependency analysis is conservative. If you know two memory accesses don't alias, override it:

```cpp
for (int i = 0; i < N; i++) {
    #pragma HLS PIPELINE II=1
    #pragma HLS DEPENDENCE variable=buf inter false
    buf[i] = buf[i + K];  // Compiler sees WAR without pragma
}
```

`STABLE` tells the compiler an input doesn't change during execution — it is registered once, not re-read every cycle:

```cpp
void kernel(int A[1024], int coeff) {
    #pragma HLS STABLE variable=coeff
    // coeff captured at start; saves a read port on every iteration
}
```

---

## 3. UNROLL — Trading Area for Throughput

### 3.1 UNROLL Mechanics

`UNROLL` replicates the loop body in hardware. An unroll factor of 8 creates 8 parallel copies:

```cpp
// Without UNROLL: 1 MAC per cycle
for (int k = 0; k < 32; k++) {
    #pragma HLS PIPELINE II=1
    sum += A[i][k] * B[k][j];
}
// Hardware: 1 multiplier, 1 adder. Latency: 32 cycles.

// With UNROLL factor=8: 8 MACs per cycle
for (int k = 0; k < 32; k += 8) {
    #pragma HLS PIPELINE II=1
    #pragma HLS UNROLL factor=8
    sum += A[i][k] * B[k][j]
         + A[i][k+1] * B[k+1][j]
         + A[i][k+2] * B[k+2][j]
         + A[i][k+3] * B[k+3][j]
         + A[i][k+4] * B[k+4][j]
         + A[i][k+5] * B[k+5][j]
         + A[i][k+6] * B[k+6][j]
         + A[i][k+7] * B[k+7][j];
}
// Hardware: 8 multipliers, 1 adder tree. Latency: 4 cycles.
```

| Unroll Factor | DSP Slices | BRAM Ports Needed | Latency (k loop) |
|---|---|---|---|
| 1 (no unroll) | 1 | 2 (1 from A, 1 from B) | 32 |
| 2 | 2 | 4 (2 from A, 2 from B) | 16 |
| 4 | 4 | 8 (4 from A, 4 from B) | 8 |
| 8 | 8 | 16 (8 from A, 8 from B) | 4 |
| 32 (full) | 32 | 64 (32 from A, 32 from B) | 1 |

**The memory wall hits hard:** full `UNROLL factor=32` needs 64 simultaneous reads from BRAM. No BRAM block supports that. You must `ARRAY_PARTITION`.

### 3.2 UNROLL vs PIPELINE — When to Use Which

| Goal | Use | Notes |
|---|---|---|
| **High throughput on small loops** | UNROLL | N≤~64; replicates hardware |
| **High throughput on large loops** | PIPELINE | N>~64; area proportional to pipeline depth, not N |
| **Both** | UNROLL inner loop + PIPELINE outer loop | Unroll gives parallelism; pipeline gives throughput |

> [!WARNING]
> `#pragma HLS UNROLL` (no factor) unrolls the **entire** loop. A `for (k=0; k<1024; k++)` with full unroll creates 1,024 copies of the loop body. This either fails routing or consumes the entire FPGA. Always specify a factor.

---

## 4. ARRAY_PARTITION — Feeding the Pipeline

### 4.1 Why ARRAY_PARTITION is Mandatory

BRAM blocks have 2 ports max. A `PIPELINE`'d loop with `UNROLL factor=8` needs 16 reads per cycle from `B` (8 for iteration N, potentially 8 more for iteration N+1 if the pipeline overlaps reads).

`ARRAY_PARTITION` physically splits one array across multiple BRAM blocks. Each BRAM provides its own 2 ports, multiplying total bandwidth.

### 4.2 Partition Modes

```cpp
float A[32][32];

// Block: contiguous chunks → different BRAMs
// A[0..15][*] in BRAM0, A[16..31][*] in BRAM1
#pragma HLS ARRAY_PARTITION variable=A block factor=2 dim=1

// Cyclic: interleaved → different BRAMs
// A[0],A[2],A[4]... in BRAM0; A[1],A[3],A[5]... in BRAM1
#pragma HLS ARRAY_PARTITION variable=A cyclic factor=4 dim=2

// Complete: every element in its own register (not BRAM)
// Uses FFs, not BRAM. Only for very small arrays.
#pragma HLS ARRAY_PARTITION variable=A complete dim=0
```

### 4.3 The Matrix Multiply Memory Problem

In `C[i][j] += A[i][k] * B[k][j]`:

- **A is accessed by row:** `A[i][k]` — adjacent `k` values are adjacent in memory. `block` partition on dim=2 works well.
- **B is accessed by column:** `B[k][j]` — adjacent `k` values in **different** rows. `block` partition on dim=1 works. But `cyclic` on dim=2 also works if you partition both dimensions.

**The correct partition for an 8× unroll:**

```cpp
#pragma HLS ARRAY_PARTITION variable=A cyclic factor=8 dim=2
#pragma HLS ARRAY_PARTITION variable=B block factor=8 dim=1
#pragma HLS ARRAY_PARTITION variable=C cyclic factor=8 dim=2
```

A: 32×32 → 8 BRAMs, each holds 4 columns (32×4), achieves 8 parallel reads on dim=2.
B: 32×32 → 8 BRAMs, each holds 4 rows (4×32), achieves 8 parallel reads on dim=1.
C: 32×32 → 8 BRAMs, achieves 8 parallel writes on dim=2.

> [!WARNING]
> **The #1 HLS performance trap:** `#pragma HLS PIPELINE II=1` + `#pragma HLS UNROLL factor=8` on a loop that reads from a **single, unpartitioned** array. The compiler can't schedule 8 reads per cycle from a 2-port BRAM. Result: II=4 (or worse), and you can't figure out why. **Always partition arrays BEFORE pipelining loops that access them.**

---

## 4.5 DATAFLOW — Function-Level Parallelism

`#pragma HLS DATAFLOW` enables concurrent execution of multiple functions or loops within a single top-level function. Unlike `PIPELINE` (which overlaps iterations of one loop), `DATAFLOW` runs entire functions in parallel, communicating through FIFOs.

### 4.5.1 When to Use DATAFLOW

Use DATAFLOW when your algorithm has distinct sequential stages that can be pipelined at the function level:

```cpp
#include <hls_stream.h>

void stage_a(hls::stream<int>& in, hls::stream<int>& out) { /* ... */ }
void stage_b(hls::stream<int>& in, hls::stream<int>& out) { /* ... */ }

void top(hls::stream<int>& in, hls::stream<int>& out) {
    #pragma HLS DATAFLOW
    hls::stream<int> fifo1("fifo1");
    #pragma HLS STREAM variable=fifo1 depth=512
    
    stage_a(in, fifo1);
    stage_b(fifo1, out);
}
// Hardware: stage_a || stage_b running concurrently
```

**DATAFLOW vs PIPELINE:**

| Aspect | PIPELINE | DATAFLOW |
|---|---|---|
| Granularity | Loop iteration | Entire function/loop body |
| Communication | Registers / BRAM | `hls::stream` FIFOs |
| Best for | Single hot loop | Multi-stage pipelines (e.g., demosaic: interpolate R→G→B) |
| Area cost | Pipeline registers | FIFO storage + separate hardware per stage |

### 4.5.2 FIFO Depth and Deadlock

The default FIFO depth is typically 2 or 16. If the producer writes faster than the consumer reads, the FIFO fills and stalls the producer.

```cpp
#pragma HLS STREAM variable=fifo1 depth=512
```

**Rule of thumb:** FIFO depth ≥ producer burst size. If `stage_a` outputs 256 values before `stage_b` can consume any, the FIFO must hold at least 256 elements or the design deadlocks.

### 4.5.3 DATAFLOW Restrictions

- No feedback loops — data must flow forward through the stream graph
- Arrays passed between functions must be converted to `hls::stream`
- Each function in the dataflow region can internally use `PIPELINE` — the two pragmas compose

---

## 4.6 Interface Synthesis

HLS defaults to `ap_none` — simple wire ports with no handshake. Real accelerators need memory-mapped or streaming interfaces.

### 4.6.1 AXI Memory-Mapped (`m_axi`)

For arrays stored in external DDR:

```cpp
#pragma HLS INTERFACE m_axi depth=1024 port=A offset=slave bundle=gmem
#pragma HLS INTERFACE m_axi depth=1024 port=B offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=return bundle=control
```

| Parameter | Meaning |
|---|---|
| `m_axi` | Memory-mapped AXI master — the kernel reads/writes DDR |
| `offset=slave` | Host writes the base address via a control register |
| `bundle=gmem` | Groups ports into one AXI interface (saves area) |
| `depth=1024` | Max burst length; compiler uses this to coalesce accesses |

**Burst coalescing:** Sequential accesses are automatically coalesced into AXI bursts. Tiling (Section 5.2) is critical here — contiguous tile data bursts efficiently; strided column access does not.

### 4.6.2 Streaming Interfaces (`axis`, `ap_fifo`)

For producer-consumer connections between kernels:

```cpp
// AXI Stream (includes TLAST/TKEEP for packet boundaries)
#pragma HLS INTERFACE axis port=video_stream
```

AXI Stream is essential for video, Ethernet, and radar frame processing where packet boundaries matter.

### 4.6.3 Scalar and Control Interfaces

```cpp
#pragma HLS INTERFACE s_axilite port=scale_factor bundle=control
```

Exposes `scale_factor` as an AXI-Lite register. The host can change it at runtime without recompiling the bitstream. Without `s_axilite`, scalars are hard-wired constants.

---

## 5. The Working Example: Optimized Tiled Matrix Multiply

### 5.1 Full Optimized Code

```cpp
#include <ap_int.h>

#define N 32
#define TILE 8

// Use 27×18 DSP-friendly types
// Each DSP48 can do one 27×18 multiply per cycle
typedef ap_int<18> mat_type;

void matmul_optimized(
    mat_type A[N][N],
    mat_type B[N][N],
    mat_type C[N][N]
) {
    // Partition arrays for parallel access
    // Cyclic on dimension 2: adjacent columns in different BRAMs
    #pragma HLS ARRAY_PARTITION variable=A cyclic factor=TILE dim=2
    #pragma HLS ARRAY_PARTITION variable=B block  factor=TILE dim=1
    #pragma HLS ARRAY_PARTITION variable=C cyclic factor=TILE dim=2

    // Tile the i and j loops for data reuse
    for (int ii = 0; ii < N; ii += TILE) {
        for (int jj = 0; jj < N; jj += TILE) {
            // Inner tiled loops
            for (int i = ii; i < ii + TILE; i++) {
                // Pipeline the j loop — one result per cycle
                for (int j = jj; j < jj + TILE; j++) {
                    #pragma HLS PIPELINE II=1
                    mat_type sum = 0;
                    // Unroll the inner reduction — 8 MACs per cycle
                    for (int k = 0; k < N; k++) {
                        #pragma HLS UNROLL factor=TILE
                        sum += A[i][k] * B[k][j];
                    }
                    C[i][j] = sum;
                }
            }
        }
    }
}
```

> [!NOTE]
> Vitis HLS attempts to flatten perfectly nested loops automatically when trip counts are compile-time constants. Explicit `#pragma HLS LOOP_FLATTEN` is rarely needed for simple nests like the one above.

### 5.2 Why Tiling Matters

Without tiling, the `j` loop is 32 iterations long. With tiling (8×8 tiles):

```
No tiling:
  for j = 0..31:      // 32 iterations
      for k = 0..31:   // each reads ALL of B column j from DRAM
  Each j iteration re-fetches B[k][j] from memory — 32 reads, no reuse.

With tiling:
  for jj = 0,8,16,24:
      for j = jj..jj+7:  // 8 iterations per tile
          for k = 0..31:  // within a tile, B[k][jj:jj+7] is reused
  A 32×8 tile of B fits in registers. B is read once per tile, not per j.
```

**Result:** 4× reduction in B memory reads. On bandwidth-constrained systems (e.g., FPGA accessing external DDR), tiling is the difference between memory-bound and compute-bound.

### 5.3 Expected Synthesis Results

| Metric | Value |
|---|---|
| Clock target | 200 MHz (5 ns period) |
| DSP slices | 8 (one per unrolled MAC) |
| LUTs | ~2,000 (control + adder tree) |
| BRAM blocks | 24 (8 partitions × 3 arrays) |
| Latency per 32×32 multiply | ~130 cycles |
| Throughput | 1 result per cycle per tile (8 MACs/cycle) |

---

## 6. DSP48 Inference — Not LUTs

### 6.1 The DSP48 Slice

Each Xilinx DSP48E2 slice contains:
- 27×18-bit signed multiplier
- 48-bit accumulator
- Optional pre-adder, pattern detector, SIMD mode

The multiplier is **hard silicon** — 1 clock cycle, 0 LUTs. One multiply in LUTs consumes ~200 LUTs and takes 2–3 cycles.

### 6.2 Writing Code That Maps to DSP48

HLS infers DSP usage from your data types. If the bit widths don't match DSP48 dimensions, you get LUTs:

| C++ Type | Maps To | DSP Usage |
|---|---|---|
| `float` / `double` | LUTs + fabric adders | 0 DSP slices (FP math is fabric) |
| `int` (32-bit) | 32×32 multiply → two DSP48 or LUTs | 0–2 DSP (compiler choice; 32-bit overflows 27×18) |
| `ap_int<27> × ap_int<18>` — explicit | 27×18 → exactly 1 DSP48 per multiply | 1 DSP |
| `ap_int<18> × ap_int<18>` | 18×18 → 1 DSP48 (fits in 1 DSP, 18 ≤ 18) | 1 DSP per multiply |
| `ap_int<16>` | 16×16 → 1 DSP48 | Best fit; leaves headroom for accumulation |
| `ap_int<8>` | 8×8 → 1 DSP48 | Under-utilized DSP; wastes 19×10 compute |

### 6.3 The Accumulator Width Trap

```cpp
ap_int<16> a, b;
ap_int<16> sum;  // WRONG — 16-bit accumulator overflows after ~2 iterations

sum += a * b;    // a*b = 32-bit result, truncated to 16 bits
```

**Fix:** The accumulator must be wide enough for N multiply-accumulates:

```cpp
ap_int<16> a, b;
ap_int<36> sum;  // Correct: log2(32) + 16 + 16 = 5 + 32 = 37 → use 40
// Conservative: DSP48 has 48-bit accumulator, so ap_int<48> is free
```

> [!TIP]
> **Always check the synthesis report** for "DSP48E Utilization." If it shows 0 DSPs but you expected 8, check your types. Vitis HLS silently falls back to LUTs for types that don't fit DSP48 dimensions.

---

## 7. Reading the Schedule Viewer

### 7.1 Accessing the Viewer

After C Synthesis in Vitis HLS: **Analysis perspective → Schedule Viewer**. It shows:
- Every operation (load, multiply, store, add)
- Which cycle each operation executes in
- Which resource each operation uses
- Dependencies between operations (arrows)

### 7.2 Diagnosing II Violations

When the pipeline target is II=1 but actual is II=2:

1. Open Schedule Viewer
2. Find the **longest chain of dependent operations** within one iteration
3. If that chain > 1 cycle, your pipeline can't start a new iteration every cycle
4. The viewer will show **red arrows** crossing iteration boundaries — that's the dependency

**Example diagnosis:**

```
Cycle 0: load A[i][k]        ──── red arrow ──→  Cycle 0: mul A[i][k]×B[k][j]
Cycle 1: load A[i][k+1]      ──── red arrow ──→  Cycle 1: mul A[i][k+1]×B[k+1][j]
Cycle 2: add all 8 products                  →  Cycle 2: store C[i][j]
```

If the adder tree takes 3 cycles (log2(8) = 3 levels for 8 inputs), the store at the end is 3 cycles after the last load. But the next iteration's load can start immediately — the adder tree is pipelined. II=1 is possible.

If the adder tree takes 8 cycles (serial add, no pipeline), the store blocks the next iteration's load. II≥8.

**Fix:** Write the sum as a balanced adder tree:

```cpp
// BAD: Serial accumulation (creates 8-cycle chain)
sum += a0*b0;
sum += a1*b1;
sum += a2*b2;
// ... HLS infers: sum = ((((a0*b0) + a1*b1) + a2*b2) + ...)
// Each + depends on previous +. Chain length = 8.

// GOOD: Balanced tree (3-cycle chain for 8 terms)
ap_int<32> s01 = a0*b0 + a1*b1;
ap_int<32> s23 = a2*b2 + a3*b3;
ap_int<32> s45 = a4*b4 + a5*b5;
ap_int<32> s67 = a6*b6 + a7*b7;
ap_int<32> s0123 = s01 + s23;
ap_int<32> s4567 = s45 + s67;
sum = s0123 + s4567;
// Chain depth = log2(8) = 3. Pipeline can achieve II=1.
```

---

## 8. Vendor Comparison: Vitis HLS vs Intel HLS vs Catapult

| Feature | Vitis HLS | Intel HLS Compiler | Catapult HLS | Bambu |
|---|---|---|---|---|
| **Input** | C/C++/OpenCL | C++ (SYCL optional) | C++/SystemC | C |
| **Pragmas** | `#pragma HLS` | `[[intel::ii(1)]]` C++17 attributes | `#pragma hls_design` | `__attribute__((bambu))` |
| **Pipeline** | `PIPELINE II=N` | `[[intel::ii(N)]]` | `#pragma hls_pipeline_init_interval` | `_Pragma("bambu pipeline II=N")` |
| **Array Partition** | `ARRAY_PARTITION` | `[[intel::fpga_memory]]` with `BANK` | `#pragma hls_array_partition` | `_Pragma("bambu array_partition")` |
| **Loop Unroll** | `UNROLL factor=N` | `[[intel::unroll(N)]]` | `#pragma hls_unroll yes` | `_Pragma("bambu unroll N")` |
| **DSP Mapping** | Auto from `ap_int` widths | Auto from `ac_int` widths | Auto; explicit `ac_int` + `hls::mul` | Auto from C types |
| **Schedule Viewer** | Yes (built-in) | Yes (High-Level Design Reports) | Yes (SCVerify) | No (rely on synthesis reports) |
| **Cost** | Free (in Vivado) | Free (in Quartus Pro) | Paid ($10k+/yr) | Free (GPL) |
| **Platform** | Xilinx only | Intel only | ASIC + FPGA (multi-vendor) | ASIC + FPGA (multi-vendor) |

### 8.1 Intel HLS Compiler — Key Differences

Intel uses C++17 attributes instead of pragmas:

```cpp
// Intel equivalent of the tiled matrix multiply
[[intel::fpga_memory(A), intel::bankwidth(8)]]  // ~ ARRAY_PARTITION
void matmul_intel(
    ac_int<18, false> A[32][32],  // ac_int<W, signed>
    ac_int<18, false> B[32][32],
    ac_int<36, false> C[32][32]
) {
    for (int i = 0; i < 32; i++) {
        [[intel::ii(1)]]  // ~ PIPELINE II=1
        for (int j = 0; j < 32; j++) {
            ac_int<36, false> sum = 0;
            #pragma unroll 8  // ~ UNROLL factor=8
            for (int k = 0; k < 32; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}
```

> [!NOTE]
> Intel `ac_int` and Xilinx `ap_int` are functionally identical. Both are arbitrary-width integer types that the HLS compiler maps to DSP blocks or LUTs based on bit width.

---

## 9. Common Pitfalls

### Pitfall 1: Floating Point in HLS

```cpp
float A[32][32];  // DON'T DO THIS for performance
```

FPGA fabric has **no native floating-point units**. Each `float` multiply becomes ~500 LUTs + 4 DSP slices (for the mantissa multiplier) and takes 4–8 cycles. A 32×32 float matrix multiply can consume 100k+ LUTs.

**Fix:** Use fixed-point `ap_fixed<W,I>` or quantize to `ap_int`. The DSP48 can do one 18×27 integer multiply per cycle.

```cpp
#include <ap_fixed.h>
typedef ap_fixed<16, 8> q8_8_t;  // 8 integer bits, 8 fractional bits
// Maps to DSP48 via integer multiply + shift. Far more efficient than float.
```

### Pitfall 2: Resetting Accumulators Inside a Pipelined Loop

```cpp
for (int i = 0; i < N; i++) {
    #pragma HLS PIPELINE II=1
    int sum = 0;  // Reset each iteration — this is CORRECT
    for (int j = 0; j < M; j++) {
        sum += data[i][j];
    }
    out[i] = sum;
}
// sum is a local variable inside the pipeline. Each iteration
// gets its own copy — no dependency. II=1 is achievable.
```

```cpp
// BAD: sum declared OUTSIDE the pipelined loop
int sum = 0;
for (int i = 0; i < N; i++) {
    #pragma HLS PIPELINE II=1
    sum += data[i];  // Loop-carried dependency! sum from iteration
                     // N is read in iteration N+1. Forces II>1.
}
// Fix: move sum declaration INSIDE the loop
```

### Pitfall 3: DATAFLOW Without Sufficient FIFO Depth

`#pragma HLS DATAFLOW` runs functions concurrently with FIFOs between them. If the producer is faster than the consumer, the FIFO fills up and blocks the producer.

```cpp
#pragma HLS DATAFLOW
void top(...) {
    #pragma HLS STREAM variable=fifo depth=1024  // Match rates
    hls::stream<int> fifo;
    producer(fifo);  // Writes 1000 values at 1/cycle
    consumer(fifo);  // Reads 1 value every 4 cycles
    // Without depth=1024, producer stalls after FIFO fills (~16 depth default)
}
```

### Pitfall 4: Ignoring Clock Uncertainty

HLS C Synthesis uses a target clock period (e.g., 5 ns for 200 MHz), but the scheduler subtracts a **clock uncertainty** margin (default ~12–15%) to account for Vivado implementation routing delay. Your design is effectively scheduled at ~4.4 ns, not 5 ns.

If your combinational path is too long for the reduced budget, the compiler either:
- Increases pipeline depth (adds latency), or
- Fails to achieve II=1 and reports a scheduling violation

**Fix:** Over-constrain the HLS target. If you need 200 MHz post-route, target 250 MHz (4.0 ns) in HLS. Do not rely on default uncertainty — know your device's routing characteristics.

### Pitfall 5: HLS Timing ≠ Vivado Timing

HLS C Synthesis reports estimated timing. **Vivado post-route timing** is reality. An HLS design that meets 200 MHz in C Synthesis may fail at 180 MHz post-route due to routing congestion.

**Workflow:**
1. Run C Synthesis at 250 MHz target (over-constrain by ~25%)
2. Export RTL → Run Vivado implementation
3. If timing fails, open Vivado timing report → identify critical paths
4. Back in HLS: pipeline the critical path, or reduce UNROLL factor to ease congestion

---

## 10. Putting It All Together: Performance Progression

Starting from the naive 32×32 matrix multiply and applying each optimization:

| Step | Change | Latency (cycles) | DSP48 | LUTs | BRAM |
|---|---|---|---|---|---|
| 0 | Naive, no pragmas | ~34,000 | 1 | ~300 | 0 |
| 1 | Add `PIPELINE II=1` on j loop | ~1,100 | 1 | ~400 | 0 |
| 2 | `UNROLL factor=4` on k loop | ~300 | 4 | ~800 | 0 |
| 3 | `ARRAY_PARTITION` for A, B, C | ~140 | 4 | ~1,000 | 12 |
| 4 | `UNROLL factor=8` | ~100 | 8 | ~1,800 | 24 |
| 5 | Tiling (8×8) + data reuse | ~130 | 8 | ~2,200 | 24 |
| 6 | Switch `float` → `ap_int<16>` | ~130 | 8 | ~400 | 24 |

> [!NOTE]
> Step 5 (tiling) shows slightly higher latency than Step 4 because tiling adds loop-control overhead. The benefit is **memory bandwidth reuse** — without tiling, external DDR bandwidth becomes the bottleneck and effective throughput collapses. Tiling is a bandwidth optimization, not a latency optimization.

**Step 6 is the biggest bang:** switching from float to fixed-point dropped LUT count from 2,200 to 400 — a 5.5× reduction — because DSP48 slices replaced LUT-based floating-point multipliers.

---

> [!NOTE]
> **Topics not covered in this article:** Systolic arrays, polyhedral loop transformations, HLS math libraries (`hls::fft`, `hls::math`), arbitrary-precision floating point (`half`, `bfloat16`), template metaprogramming for HLS, and custom RTL blackbox integration. These are advanced techniques for specialized domains.

## References

| Document | Source | What It Covers |
|---|---|---|
| UG1399 — Vitis High-Level Synthesis User Guide | AMD/Xilinx | Complete pragma reference, interface synthesis, scheduling |
| UG902 — Vivado Design Suite HLS User Guide | AMD/Xilinx | Legacy Vivado HLS (pre-Vitis) — still useful for fundamental concepts |
| UG1416 — Vitis HLS Migration Guide | AMD/Xilinx | Migrating from Vivado HLS to Vitis HLS; pragma and tool changes |
| WP470 — Leveraging FPGA Architectural Features with Vitis HLS | AMD/Xilinx | DSP48, BRAM/URAM inference, clock uncertainty guidance |
| Intel HLS Compiler User Guide | Intel/Altera | Intel's `[[intel::...]]` attribute reference, memory banking |
| UG579 — 7-Series DSP48E1 / UG479 — UltraScale DSP48E2 | AMD/Xilinx | DSP slice architecture — essential for writing correctly-sized `ap_int` types |
| Bambu HLS Documentation | Politecnico di Milano | Open-source HLS tool; useful for cross-vendor comparison |
| [HLS Overview](../../13_toolchains/hls_overview.md) | This KB | Introduction to HLS tools, pragmas, and the basic synthesis flow |
| [Hardware Acceleration](../hardware_acceleration.md) | This KB | When FPGA acceleration wins; domain analysis for HLS-driven designs |
