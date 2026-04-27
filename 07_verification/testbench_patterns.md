[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Testbench Patterns — Self-Checking, Scoreboards, and Constrained-Random

A good testbench doesn't just wiggle signals and hope you'll see the bug in a waveform. It **checks correctness automatically**, generates **meaningful stimulus**, and **reports pass/fail** without human inspection. This article covers the patterns that turn a testbench from a signal driver into a verification tool.

---

## The Ascending Ladder of Testbench Quality

```
Level 1: "Waveform Playback"     ──── Drivers only; manually inspect waves
Level 2: "Directed Test"         ──── Pre-computed stimulus, simple checks
Level 3: "Self-Checking"         ──── Reference model + automatic comparison
Level 4: "Constrained-Random"    ──── Randomized stimulus within legal bounds
Level 5: "Coverage-Driven"       ──── Measure what's been tested; fill gaps
```

**Target Level 3–4 for FPGA designs.** Level 5 (UVM with coverage) is the ASIC standard but is typically overkill for FPGA modules under ~50K LUTs.

---

## Pattern 1: Self-Checking Testbench

Every testbench should compare actual output to expected output automatically:

```verilog
// Self-checking pattern: compare DUT output to expected
module tb_fifo;
    reg clk, rst_n, wr_en, rd_en;
    reg [7:0] wr_data;
    wire [7:0] rd_data;
    wire empty, full;

    // DUT
    fifo #(.DEPTH(16), .WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en), .wr_data(wr_data),
        .rd_en(rd_en), .rd_data(rd_data),
        .empty(empty), .full(full)
    );

    // Reference model (behavioral)
    reg [7:0] model_mem [0:15];
    reg [3:0] model_wr_ptr, model_rd_ptr;
    reg [4:0] model_count;

    integer errors;
    initial errors = 0;

    // Check output against reference on every read
    always @(posedge clk) begin
        if (rst_n && rd_en && !empty) begin
            if (rd_data !== model_mem[model_rd_ptr]) begin
                $display("ERROR at %t: expected %h, got %h",
                         $time, model_mem[model_rd_ptr], rd_data);
                errors = errors + 1;
            end
        end
    end

    // Test sequence
    initial begin
        // ... write data, also update model_mem, model_wr_ptr ...
        // ... read data, compare against model ...
        if (errors == 0)
            $display("PASS: FIFO test complete, 0 errors");
        else
            $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
```

**Key principle:** The reference model is a **golden implementation** — simple, behavioral, and trusted. It computes the expected output independently of the DUT.

---

## Pattern 2: Scoreboard

For designs with independent input and output streams (e.g., packet processors), a scoreboard matches expected outputs to actual outputs:

```python
# cocotb scoreboard pattern
class Scoreboard:
    def __init__(self):
        self.expected = []      # Queue of expected outputs
        self.errors = 0

    def add_expected(self, data):
        """Called when stimulus is sent to DUT"""
        self.expected.append(data)

    async def check_actual(self, data):
        """Called when output appears from DUT"""
        if len(self.expected) == 0:
            self.errors += 1
            dut._log.error(f"Unexpected output: {data}")
            return
        expected = self.expected.pop(0)
        if data != expected:
            self.errors += 1
            dut._log.error(f"Mismatch: expected {expected}, got {data}")

    def report(self):
        if self.errors == 0 and len(self.expected) == 0:
            dut._log.info("PASS: Scoreboard matched")
        else:
            dut._log.error(f"FAIL: {self.errors} mismatches, "
                           f"{len(self.expected)} missing outputs")
```

**When to use a scoreboard:**
- Packet processing (Ethernet MAC, AXI4-Stream pipeline)
- Out-of-order completion (transactions may finish in different order than started)
- Multi-channel designs where outputs interleave

---

## Pattern 3: Constrained-Random Stimulus

Random testing finds corner cases you'd never think to test manually. But pure randomness is useless — random data with invalid control signals just triggers protocol errors. **Constrained-random** restricts randomness to legal values:

```verilog
// Constrained-random: generate legal AXI4-Lite writes
task automatic axi_lite_write_random(
    input [31:0] addr_min, input [31:0] addr_max
);
    reg [31:0] addr, data;
    begin
        // Constrain address to 4-byte-aligned within range
        addr = ($random % ((addr_max - addr_min) / 4)) * 4 + addr_min;

        // Constrain data (all values legal)
        data = $random;

        // Drive AXI4-Lite write
        @(posedge clk);
        s_axi_awaddr  = addr;
        s_axi_awvalid = 1;
        s_axi_wdata   = data;
        s_axi_wvalid  = 1;
        s_axi_wstrb   = 4'b1111;   // All bytes valid

        // Wait for AW and W handshake
        @(posedge clk);
        while (!(s_axi_awready && s_axi_wready))
            @(posedge clk);

        // Wait for write response (B channel)
        s_axi_awvalid = 0;
        s_axi_wvalid  = 0;
        s_axi_bready  = 1;
        @(posedge clk);
        while (!s_axi_bvalid)
            @(posedge clk);
        s_axi_bready = 0;

        // Record in scoreboard
        scoreboard.add_expected(addr, data);
    end
endtask

// Run many random transactions
initial begin
    repeat (1000) begin
        axi_lite_write_random(32'h4000_0000, 32'h4000_FFFF);
    end
end
```

---

## Pattern 4: Bus Functional Model (BFM)

A BFM encapsulates a protocol into a set of tasks/functions:

```verilog
// AXI4-Stream BFM
task automatic axis_send(input [7:0] data, input is_last);
    begin
        m_axis_tvalid = 1;
        m_axis_tdata  = data;
        m_axis_tlast  = is_last;
        m_axis_tkeep  = 8'hFF;
        @(posedge clk);
        while (!m_axis_tready)
            @(posedge clk);
        m_axis_tvalid = 0;
    end
endtask

task automatic axis_receive(output [7:0] data, output is_last);
    begin
        s_axis_tready = 1;
        @(posedge clk);
        while (!s_axis_tvalid)
            @(posedge clk);
        data    = s_axis_tdata;
        is_last = s_axis_tlast;
        s_axis_tready = 0;
    end
endtask

// Usage: cleaner tests
initial begin
    // Send a 4-byte packet
    axis_send(8'hA5, 0);   // First byte (not last)
    axis_send(8'h5A, 0);   // Second byte
    axis_send(8'h3C, 0);   // Third byte
    axis_send(8'hC3, 1);   // Last byte (TLAST=1)
end
```

BFMs make tests readable and reusable. The same BFM can drive different DUTs that speak the same protocol.

---

## Pattern 5: Clock and Reset Generation

```verilog
// Clock generator
reg clk = 0;
always #5 clk = ~clk;    // 100 MHz (10 ns period)

// Reset generator: assert for 10 cycles, then release
reg rst_n;
initial begin
    rst_n = 0;
    repeat (10) @(posedge clk);
    rst_n = 1;
end
```

For multiple clocks, generate each independently:

```verilog
reg clk_100m = 0, clk_200m = 0;
always #5.000   clk_100m = ~clk_100m;    // 100 MHz
always #2.500   clk_200m = ~clk_200m;    // 200 MHz
```

---

## Pattern 6: Timeout Protection

Every waiting loop must have a timeout, or the simulation hangs forever:

```verilog
// Bad: hangs forever if ready never asserts
while (!s_axi_awready) @(posedge clk);     // ← INFINITE LOOP!

// Good: timeout after 1000 cycles
integer timeout;
timeout = 0;
while (!s_axi_awready && timeout < 1000) begin
    @(posedge clk);
    timeout = timeout + 1;
end
if (timeout >= 1000) begin
    $display("ERROR: AWREADY timeout at %t", $time);
    $finish;
end
```

---

## Coverage Collection (FPGA-Pragmatic)

You don't need full SystemVerilog coverage groups for FPGA verification. A simple counter-based approach catches 80% of coverage gaps:

```verilog
// Simple functional coverage counters
reg [31:0] cov_burst_len_1    = 0;  // Single-beat AXI transfers
reg [31:0] cov_burst_len_max  = 0;  // Max-length bursts
reg [31:0] cov_rd_wr_back     = 0;  // Read-after-write to same addr
reg [31:0] cov_full_empty     = 0;  // FIFO full → empty transition

always @(posedge clk) begin
    if (arvalid && arready && arlen == 0)
        cov_burst_len_1 <= cov_burst_len_1 + 1;
    if (arvalid && arready && arlen == 255)
        cov_burst_len_max <= cov_burst_len_max + 1;
    // ...
end

// Coverage report at end
final begin
    $display("Coverage:");
    $display("  Single-beat bursts:    %0d", cov_burst_len_1);
    $display("  Max-length bursts:     %0d", cov_burst_len_max);
    if (cov_burst_len_1 == 0)
        $display("  WARNING: No single-beat bursts tested!");
end
```

---

## Choosing a Testbench Pattern

```
┌─ Simple module (FIFO, counter, FSM)? ──────► Self-Checking (Pattern 1)
│
├─ Streaming / packet processing? ────────────► Scoreboard (Pattern 2)
│
├─ Need to find corner-case bugs? ────────────► Constrained-Random (Pattern 3)
│
├─ Protocol interface (AXI, Avalon, etc)? ────► BFM (Pattern 4)
│
├─ Large design, formal quality reqs? ────────► UVM framework (see uvm_overview.md)
│
└─ CI/CD regression suite? ───────────────────► cocotb + Verilator (see simulation_overview.md)
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **No timeout on wait loops** | Simulation hangs forever | Add cycle-count timeout to every `while (!signal)` in testbench |
| **Self-checking compares wrong time** | False mismatches at cycle boundaries | Compare at the SAME clock edge where data is captured (not delayed) |
| **Constrained-random without seed** | Non-reproducible failures | Use `$srandom(seed)` or `--seed` in cocotb; log seed at test start |
| **BFM doesn't handle backpressure** | Test passes only when slave is always ready | Randomize `s_axis_tready` to create backpressure scenarios |
| **Reference model and DUT share code** | Same bug in both → never caught | Reference model must be independent; ideally written in a different language (Python/cocotb) |
| **Forgetting to assert reset at t=0** | All signals 'X' → spurious errors | Assert reset in `initial` block immediately (not after a delay) |

---

## Further Reading

| Article | Topic |
|---|---|
| [simulation_overview.md](simulation_overview.md) | Simulator comparison, cocotb, waveform viewers |
| [cocotb.md](cocotb.md) | cocotb Python testbenches deep dive |
| [formal_verification.md](formal_verification.md) | Formal verification — catch bugs without testbenches |
| [uvm_overview.md](uvm_overview.md) | UVM framework for verification |
| [sv_verification.md](sv_verification.md) | SystemVerilog assertions, coverage, randomization |
