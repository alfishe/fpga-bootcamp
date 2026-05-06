[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# FPGA Design Patterns — Proven RTL Building Blocks for Common Problems

Software engineering has design patterns (singleton, observer, factory). FPGA design has its own set of recurring patterns that solve specific hardware problems: crossing clock domains safely, arbitrating between multiple requesters, detecting edges, debouncing mechanical inputs, and building pipelines that handle backpressure. These patterns are not vendor-specific — they apply to every FPGA on every vendor's silicon. This article catalogs the most commonly needed design patterns with complete, synthesizable Verilog/SystemVerilog code, tradeoff analysis, and guidance on when to use each pattern.

> [!NOTE]
> For CDC-specific patterns (synchronizers, async FIFOs, handshakes), see [CDC Coding](cdc_coding.md). For state machine patterns, see [State Machines](state_machines.md). This article covers the broader set of general-purpose building blocks.

---

## Pattern Catalog

| # | Pattern | Problem Solved | Key Resources |
|---|---|---|---|
| 1 | **[Edge Detector](#pattern-1-edge-detector)** | Detect rising/falling edges of a signal | 2–3 FFs |
| 2 | **[Pulse Synchronizer](#pattern-2-pulse-synchronizer)** | Pass a single-clock-cycle pulse across domains | 4–6 FFs |
| 3 | **[Debouncer](#pattern-3-debouncer)** | Remove bounce from mechanical switches | Counter + FFs |
| 4 | **[Round-Robin Arbiter](#pattern-4-round-robin-arbiter)** | Fairly grant access among N requesters | N × log2(N) LUTs |
| 5 | **[Fixed-Priority Arbiter](#pattern-5-fixed-priority-arbiter)** | Grant access by fixed priority | N LUTs |
| 6 | **[Pipeline with Backpressure](#pattern-6-pipeline-with-backpressure-validready)** | Data pipeline with valid/ready handshake | N stages × pipeline width |
| 7 | **[Rate Limiter](#pattern-7-rate-limiter)** | Limit event rate to maximum N per M clocks | Counter + comparator |
| 8 | **[One-Shot (Monostable)](#pattern-8-one-shot-monostable-multivibrator)** | Generate a pulse of fixed width from an edge | Counter + FF |
| 9 | **[Shift Register (SRL)](#pattern-9-shift-register-srl)** | Delay a signal by N clock cycles | 1 LUT per 2 bits (Xilinx SRL16) |
| 10 | **[Gray-Code Counter](#pattern-10-gray-code-counter)** | Counter whose output changes by 1 bit per increment | Binary counter + XOR |

---

## Pattern 1: Edge Detector

Detects the rising edge, falling edge, or both edges of a signal.

```verilog
// Rising-edge detector
// Output is high for exactly 1 clock cycle when input transitions 0→1
module edge_detect_rising (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output wire rising
);
    reg din_d;
    always @(posedge clk or posedge rst) begin
        if (rst) din_d <= 1'b0;
        else     din_d <= din;
    end
    assign rising = din & ~din_d;  // Current=1, previous=0
endmodule

// Falling-edge detector
// Output is high for exactly 1 clock cycle when input transitions 1→0
module edge_detect_falling (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output wire falling
);
    reg din_d;
    always @(posedge clk or posedge rst) begin
        if (rst) din_d <= 1'b0;
        else     din_d <= din;
    end
    assign falling = ~din & din_d;  // Current=0, previous=1
endmodule

// Both-edge detector
module edge_detect_both (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output wire any_edge
);
    reg din_d;
    always @(posedge clk or posedge rst) begin
        if (rst) din_d <= 1'b0;
        else     din_d <= din;
    end
    assign any_edge = din ^ din_d;  // XOR: different from previous
endmodule
```

**When to use:** Interrupt detection, protocol event detection, button press detection.

---

## Pattern 2: Pulse Synchronizer

Passes a single-clock-cycle pulse from one clock domain to another. Unlike a level signal, a pulse is too short for a simple 2-FF synchronizer — it may be missed entirely.

```verilog
// Pulse synchronizer: src_clk → dst_clk
// The pulse in the source domain toggles a flip-flop, which is
// synchronized and edge-detected in the destination domain.
module pulse_synchronizer (
    input  wire src_clk,
    input  wire dst_clk,
    input  wire rst,
    input  wire src_pulse,   // Pulse in source domain
    output wire dst_pulse    // Pulse in destination domain
);
    // Source domain: toggle FF on each pulse
    reg toggle_src;
    always @(posedge src_clk or posedge rst) begin
        if (rst)       toggle_src <= 1'b0;
        else if (src_pulse) toggle_src <= ~toggle_src;
    end

    // Destination domain: 2-FF synchronizer + edge detection
    reg toggle_dst_sync1, toggle_dst_sync2, toggle_dst_sync3;
    always @(posedge dst_clk or posedge rst) begin
        if (rst) begin
            toggle_dst_sync1 <= 1'b0;
            toggle_dst_sync2 <= 1'b0;
            toggle_dst_sync3 <= 1'b0;
        end else begin
            toggle_dst_sync1 <= toggle_src;      // Stage 1 (metastable)
            toggle_dst_sync2 <= toggle_dst_sync1; // Stage 2 (stable)
            toggle_dst_sync3 <= toggle_dst_sync2; // Edge detection register
        end
    end

    // Rising-edge detect on the synchronized toggle
    assign dst_pulse = toggle_dst_sync2 ^ toggle_dst_sync3;
endmodule
```

**When to use:** Interrupt pulses crossing clock domains, event signals between asynchronous modules.

> [!WARNING]
> **Do not send rapid pulses faster than the destination clock can synchronize.** Minimum pulse spacing: 2× the destination clock period plus synchronization latency.

---

## Pattern 3: Debouncer

Removes contact bounce from mechanical switches (typical bounce: 5–20 ms).

```verilog
// Debouncer: filters input to change only after stable for N clocks
// At 100 MHz with COUNTER_WIDTH=20 (1M cycles): 10 ms debounce time
module debouncer #(
    parameter COUNTER_WIDTH = 20  // log2(clk_freq × debounce_time)
) (
    input  wire clk,
    input  wire rst,
    input  wire noisy_in,     // Raw input from switch
    output wire clean_out     // Debounced output
);
    reg [COUNTER_WIDTH-1:0] counter;
    reg clean_r;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
            clean_r <= 1'b0;
        end else begin
            if (noisy_in !== clean_r) begin
                counter <= counter + 1;
                if (counter[COUNTER_WIDTH-1]) begin  // MSB set = count expired
                    clean_r <= noisy_in;
                    counter <= 0;
                end
            end else begin
                counter <= 0;
            end
        end
    end

    assign clean_out = clean_r;
endmodule
```

**When to use:** Button/switch inputs, rotary encoders, any mechanical contact.

---

## Pattern 4: Round-Robin Arbiter

Grants access to one of N requesters in a fair, rotating order. Each requester gets equal priority over time.

```verilog
// Round-robin arbiter for N requesters
// Parameterized: supports 2–16 requesters
module round_robin_arbiter #(
    parameter NUM_REQ = 4
) (
    input  wire                  clk,
    input  wire                  rst,
    input  wire [NUM_REQ-1:0]   req,     // Request inputs
    output reg  [NUM_REQ-1:0]   gnt,     // Grant outputs (one-hot)
    input  wire                  ack      // Acknowledge: current grant consumed
);
    reg [$clog2(NUM_REQ)-1:0] last_gnt;

    integer i;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            gnt <= 0;
            last_gnt <= 0;
        end else begin
            if (ack || gnt == 0) begin
                // Starting from last_gnt + 1, find next requester
                gnt <= 0;
                for (i = 0; i < NUM_REQ; i = i + 1) begin
                    if (gnt == 0) begin
                        // Check each position starting from (last_gnt + 1) % NUM_REQ
                        if (req[(last_gnt + i + 1) % NUM_REQ]) begin
                            gnt <= (1 << ((last_gnt + i + 1) % NUM_REQ));
                            last_gnt <= (last_gnt + i + 1) % NUM_REQ;
                        end
                    end
                end
            end
        end
    end
endmodule
```

**When to use:** Shared bus access (multiple masters, one bus), memory port arbitration, DMA channel selection.

---

## Pattern 5: Fixed-Priority Arbiter

Grants access to the highest-priority requester. Simple and fast but can starve lower-priority requesters.

```verilog
// Fixed-priority arbiter: req[0] = highest priority
module priority_arbiter #(
    parameter NUM_REQ = 4
) (
    input  wire [NUM_REQ-1:0]  req,
    output wire [NUM_REQ-1:0]  gnt
);
    // One-hot grant: only the highest-priority requester wins
    assign gnt[0] = req[0];
    genvar i;
    generate
        for (i = 1; i < NUM_REQ; i = i + 1) begin : gnt_gen
            assign gnt[i] = req[i] & ~(|req[i-1:0]);  // No higher-priority request
        end
    endgenerate
endmodule
```

**When to use:** Interrupt priority encoding, emergency stop has highest priority, DMA with known priority order.

**Warning:** Lower-indexed requesters can starve higher-indexed ones under heavy load.

---

## Pattern 6: Pipeline with Backpressure (Valid/Ready)

A pipeline stage that propagates data forward only when both the producer and consumer are ready. This is the AXI-Stream handshake pattern.

```verilog
// Pipeline stage with valid/ready backpressure
// Implements: data moves forward only when both valid_in and ready_out are high
module pipeline_stage #(
    parameter DATA_WIDTH = 32
) (
    input  wire                  clk,
    input  wire                  rst,
    input  wire [DATA_WIDTH-1:0] data_in,
    input  wire                  valid_in,
    output wire                  ready_out,    // Can accept new data
    output reg  [DATA_WIDTH-1:0] data_out,
    output reg                  valid_out,
    input  wire                  ready_in      // Consumer can accept
);
    // Can accept new data when:
    //   (1) output is not valid, OR
    //   (2) consumer is ready (output will be consumed)
    assign ready_out = ~valid_out | ready_in;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            data_out  <= {DATA_WIDTH{1'b0}};
            valid_out <= 1'b0;
        end else begin
            if (ready_out) begin
                data_out  <= data_in;
                valid_out <= valid_in;
            end
        end
    end
endmodule
```

**When to use:** AXI-Stream pipelines, data processing chains, any producer-consumer interface where rates differ.

---

## Pattern 7: Rate Limiter

Limits an output to fire at most N times per M clock cycles.

```verilog
// Rate limiter: output at most 1 event per MIN_PERIOD clock cycles
module rate_limiter #(
    parameter MIN_PERIOD = 100  // Minimum clocks between output events
) (
    input  wire clk,
    input  wire rst,
    input  wire event_in,   // Input event (may be faster than allowed)
    output wire event_out   // Rate-limited output
);
    reg [$clog2(MIN_PERIOD)-1:0] counter;
    reg cooldown;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter  <= 0;
            cooldown <= 1'b0;
        end else begin
            if (cooldown) begin
                if (counter == MIN_PERIOD - 1) begin
                    counter  <= 0;
                    cooldown <= 1'b0;
                end else begin
                    counter <= counter + 1;
                end
            end else if (event_in) begin
                cooldown <= 1'b1;
                counter  <= 0;
            end
        end
    end

    assign event_out = event_in & ~cooldown;
endmodule
```

**When to use:** Throttling interrupts to a processor, limiting API call rates, preventing bus congestion.

---

## Pattern 8: One-Shot (Monostable Multivibrator)

Generates a pulse of fixed width when triggered by an edge.

```verilog
// One-shot: generates a pulse of PULSE_WIDTH clocks on rising edge of trigger
module one_shot #(
    parameter PULSE_WIDTH = 10
) (
    input  wire clk,
    input  wire rst,
    input  wire trigger,  // Rising edge triggers the pulse
    output wire pulse     // Output pulse
);
    reg [$clog2(PULSE_WIDTH)-1:0] counter;
    reg active;

    // Edge detection on trigger
    wire rising_edge;
    reg trigger_d;
    always @(posedge clk or posedge rst) begin
        if (rst) trigger_d <= 1'b0;
        else     trigger_d <= trigger;
    end
    assign rising_edge = trigger & ~trigger_d;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 0;
            active  <= 1'b0;
        end else if (rising_edge && !active) begin
            active  <= 1'b1;
            counter <= PULSE_WIDTH - 1;
        end else if (active) begin
            if (counter == 0) begin
                active <= 1'b0;
            end else begin
                counter <= counter - 1;
            end
        end
    end

    assign pulse = active;
endmodule
```

**When to use:** Reset pulse generation, timed enable signals, watchdog kick pulses.

---

## Pattern 9: Shift Register (SRL)

Delays a signal by N clock cycles. On Xilinx, SRL16/SRL32 primitives implement this in a single LUT per bit.

```verilog
// Shift register delay: output = input delayed by DELAY cycles
module shift_delay #(
    parameter DELAY = 16,
    parameter WIDTH = 1
) (
    input  wire             clk,
    input  wire             rst,
    input  wire [WIDTH-1:0] din,
    output wire [WIDTH-1:0] dout
);
    // Xilinx SRL16 inference: the synthesizer maps this to SRL16 primitives
    // For DELAY ≤ 16: 1 LUT per bit
    // For DELAY ≤ 32: 2 LUTs per bit (SRL32 on UltraScale+)
    reg [WIDTH-1:0] sr [0:DELAY-1];
    integer i;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < DELAY; i = i + 1)
                sr[i] <= {WIDTH{1'b0}};
        end else begin
            sr[0] <= din;
            for (i = 1; i < DELAY; i = i + 1)
                sr[i] <= sr[i-1];
        end
    end

    assign dout = sr[DELAY-1];
endmodule
```

**When to use:** Pipeline delay matching, audio effects (echo/reverb), synchronization delay elements.

**Xilinx optimization:** Use `(* SHREG_EXTRACT = "yes" *)` to force SRL inference, or `(* SHREG_EXTRACT = "no" *)` to force flip-flop implementation.

---

## Pattern 10: Gray-Code Counter

A counter whose output changes by exactly 1 bit per increment — essential for safe pointer crossing between clock domains (e.g., in async FIFOs).

```verilog
// Gray-code counter: binary counter + binary-to-gray conversion
module gray_counter #(
    parameter WIDTH = 8
) (
    input  wire              clk,
    input  wire              rst,
    output wire [WIDTH-1:0]  gray_out
);
    reg [WIDTH-1:0] binary_count;

    always @(posedge clk or posedge rst) begin
        if (rst) binary_count <= 0;
        else     binary_count <= binary_count + 1;
    end

    // Binary → Gray conversion: XOR adjacent bits
    assign gray_out = binary_count ^ (binary_count >> 1);
endmodule
```

**When to use:** Async FIFO read/write pointers, any counter that crosses clock domains.

---

## Pattern Selection Guide

| Need | Pattern | Why |
|---|---|---|
| "I need to detect when a signal changes" | Edge Detector | Simplest, 2 FFs |
| "I need to pass a pulse across clock domains" | Pulse Synchronizer | Preserves single-cycle pulse nature |
| "My switch input bounces" | Debouncer | Filters mechanical noise |
| "Multiple modules need shared bus access" | Round-Robin Arbiter | Fair access for all |
| "One requester must always win" | Fixed-Priority Arbiter | Simple, low-latency |
| "My pipeline stalls when the consumer is slow" | Pipeline with Backpressure | Valid/ready handshake |
| "Events arrive too fast" | Rate Limiter | Throttles to maximum rate |
| "I need a timed pulse on an edge" | One-Shot | Monostable behavior |
| "I need to delay a signal by N cycles" | Shift Register (SRL) | Efficient on Xilinx (1 LUT/bit) |
| "My counter crosses clock domains" | Gray-Code Counter | 1-bit change per increment |

---

## References

| Source | Description |
|---|---|
| Xilinx UG901 — Vivado Synthesis User Guide | SRL inference, coding style for pattern recognition |
| Clifford Cummings, "Clock Domain Crossing" | Pulse synchronizer and gray-code patterns |
| [CDC Coding](cdc_coding.md) | CDC-specific patterns (synchronizers, async FIFOs, handshakes) |
| [State Machines](state_machines.md) | FSM design patterns |
| [Inference Rules](inference_rules.md) | What HDL pattern infers what hardware |
