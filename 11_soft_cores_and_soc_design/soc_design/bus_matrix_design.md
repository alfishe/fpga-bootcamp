[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Bus Matrix Design — Topology Patterns for FPGA SoCs

Designing the interconnect fabric is the single most consequential architectural decision in an FPGA SoC — it determines bandwidth, latency, and how many masters can talk to how many slaves simultaneously. Get it wrong and your 200 MHz CPU stalls waiting for DMA to release the bus.

This article covers topology patterns, arbitration, address decoding, pipelining, deadlock avoidance, and practical FPGA SoC examples.

---

## Topology Comparison

| Topology | Max Concurrent Transactions | Latency | LUT Cost | Best For |
|---|---|---|---|---|
| **Shared Bus** (ARM AMBA AHB) | 1 (one master at a time) | Low | ~500 LUTs | Simple microcontrollers, <4 masters |
| **Full Crossbar** (ARM NIC-301) | N (all masters concurrently to different slaves) | Medium | ~2,000–8,000 LUTs | SoCs with 4–10 masters |
| **Multi-Layer** (Xilinx AXI Interconnect) | Varies (configurable per slave) | Medium | ~1,500–5,000 LUTs | Mixed bandwidth requirements |
| **Network-on-Chip** (Versal NoC, TileLink) | Very high | Higher per-hop | 10,000+ LUTs | Manycore, large SoCs |

### Shared Bus

```
                ┌──────────┐
  CPU ─────────►│          │
  DMA ─────────►│ Arbiter  │──── Shared bus ────┬──► DDR
  USB ─────────►│ (round-  │                    ├──► UART
                │  robin)  │                    └──► GPIO
                └──────────┘
  Only one master accesses bus at a time.
```

- **Bandwidth:** All masters share one path → total throughput = bus bandwidth
- **Arbitration:** Round-robin, fixed priority, or TDM (time-division multiplex)
- **Best for:** Low-cost microcontrollers, simple soft-core SoCs

### Full Crossbar

```
  CPU ─────┐                   ┌──── DDR
           │  ┌──────────────┐ │
  DMA ─────┤──│              │─┤──── BRAM
           │  │  Full NxM    │ │
  ETH ─────┘  │  Crossbar    │─┘──── UART
              │              │
              └──────────────┘
  Every master can access every slave simultaneously
  (as long as they target different slaves)
```

- **Bandwidth:** N concurrent transactions (N = min(masters, slaves))
- **Cost:** N×M crosspoints; grows quadratically
- **Contention:** Only when two masters access the same slave simultaneously

### Partial Crossbar (Multi-Layer)

```
  CPU ─────┐                     ┌──── DDR (2 ports)
           │  ┌────────────────┐ │
  DMA ─────┤──│  Partial       │─┤──── BRAM
           │  │  Crossbar      │
  ETH ─────┘  │  (DDR has 2    │────── APB → UART, GPIO
              │   slave ports) │
              └────────────────┘
  High-bandwidth slaves get multiple ports
  Low-bandwidth slaves share a port
```

- **Bandwidth:** Configurable per slave — DDR gets 2 ports, UART gets 1 shared
- **Cost:** Between shared bus and full crossbar
- **Xilinx AXI Interconnect** uses this topology

---

## Arbitration

When multiple masters request the same slave, the arbiter decides who goes first.

### Arbitration Schemes

| Scheme | Fairness | Determinism | Implementation | Use When |
|---|---|---|---|---|
| **Fixed priority** | Poor (low-priority starves) | Best | 1 comparator per priority level | Latency-critical path must always win |
| **Round-robin** | Good | Moderate | ~50 LUTs per arbiter | General purpose (default choice) |
| **Weighted round-robin** | Configurable | Good | ~100 LUTs | Bandwidth allocation per master |
| **TDM (time-division)** | Best | Best | Counter + mux | Hard real-time guarantees |
| **Lock (AXI ARLOCK)** | N/A | N/A | Atomic operation | Atomic read-modify-write |

### Fixed Priority Example

```verilog
// Fixed priority arbiter: master 0 > master 1 > master 2
always @(*) begin
    if (req[0])      grant = 3'b001;
    else if (req[1]) grant = 3'b010;
    else if (req[2]) grant = 3'b100;
    else             grant = 3'b000;
end
```

### Round-Robin Arbiter

```verilog
// Round-robin arbiter — last winner gets lowest priority next cycle
reg [1:0] last_grant;

always @(posedge clk or posedge rst) begin
    if (rst) last_grant <= 0;
    else if (|req) begin
        case (last_grant)
            0: if (req[1])      last_grant <= 1;
               else if (req[2]) last_grant <= 2;
               else             last_grant <= 0;
            1: if (req[2])      last_grant <= 2;
               else if (req[0]) last_grant <= 0;
               else             last_grant <= 1;
            2: if (req[0])      last_grant <= 0;
               else if (req[1]) last_grant <= 1;
               else             last_grant <= 2;
        endcase
    end
end
```

### TDM Arbiter (Deterministic Bandwidth)

```verilog
// TDM: each master gets a fixed time slot
// 4 slots: CPU, CPU, DMA, ETH (CPU gets 50% bandwidth)
reg [1:0] tdm_slot;

always @(posedge clk) begin
    tdm_slot <= tdm_slot + 1;
end

// Slot assignment
assign grant[0] = (tdm_slot == 0 || tdm_slot == 1) && req[0];
assign grant[1] = (tdm_slot == 2) && req[1];  // DMA
assign grant[2] = (tdm_slot == 3) && req[2];  // ETH
```

---

## Address Decoding

### Central Address Decoder

```verilog
// Single decoder for all slaves
// Slave select based on address bits [31:28]
always @(*) begin
    ddr_sel  = 0; bram_sel = 0; uart_sel = 0; gpio_sel = 0;
    case (addr[31:28])
        4'h0: ddr_sel  = 1;   // 0x0000_0000 – DDR
        4'h4: bram_sel = 1;   // 0x4000_0000 – BRAM
        4'h8: uart_sel = 1;   // 0x8000_0000 – UART
        4'hC: gpio_sel = 1;   // 0xC000_0000 – GPIO
        default: ;             // Decode error
    endcase
end
```

### Default Slave (Error Response)

When a master accesses an unmapped address, the bus must return a DECERR response instead of hanging:

```verilog
// Default slave: returns SLVERR or DECERR for unmapped addresses
always @(posedge clk) begin
    if (awvalid && awready && !any_slave_selected) begin
        bresp  <= 2'b11;  // DECERR
        bvalid <= 1;
    end
    if (arvalid && arready && !any_slave_selected) begin
        rresp  <= 2'b11;  // DECERR
        rvalid <= 1;
        rdata  <= 32'hDEAD_BEEF;
    end
end
```

---

## Pipeline Stages

Adding pipeline stages to the interconnect increases Fmax at the cost of latency:

| Configuration | Latency (cycles) | Fmax Target | LUT Cost | Use When |
|---|---|---|---|---|
| **Combinational** (no registers) | 0 | 50–100 MHz | Lowest | Small designs, slow clocks |
| **1-stage pipeline** | 1 | 100–200 MHz | +10% | Most FPGA SoCs |
| **2-stage pipeline** | 2 | 200–350 MHz | +25% | High-performance Zynq MPSoC |
| **3-stage pipeline** | 3 | 350+ MHz | +40% | Versal NoC, ASIC-grade |

### Xilinx AXI Interconnect Pipeline Configuration

In Vivado, the AXI Interconnect IP has per-slave pipeline options:
- **Register Slice:** Adds a pipeline stage on master or slave side
- **FIFO:** Adds depth-16 FIFO for clock domain crossing or burst buffering

```
Master 0 ──► [REG SLICE] ──► AXI Interconnect ──► [REG SLICE] ──► Slave 0
                              (crossbar + arbiter)
Master 1 ──► [FIFO CDC]  ──►                  ──► [FIFO]      ──► DDR (async)
```

---

## Deadlock Avoidance

Deadlock occurs when two transactions depend on each other in a cycle. This is a critical concern in multi-master SoCs.

### Common Deadlock Scenario

```
CPU writes to DMA descriptor register
  → DMA starts reading DDR → writing to peripheral
  → Peripheral sends interrupt → CPU ISR reads DMA status
  → But CPU's read is stuck behind the DMA write!
  → DMA can't complete because CPU can't service interrupt!
```

### Deadlock Prevention Rules

| Rule | Implementation |
|---|---|
| **1. Separate ID spaces** | CPU transactions use low IDs, DMA uses high IDs — interconnect can route independently |
| **2. No dependency chains** | A master that waits for a response must not block other masters from completing |
| **3. Slave can't depend on another slave** | A slave's response must not require access to another slave in the same fabric |
| **4. Use multiple slave ports for shared slaves** | DDR should have ≥2 ports so CPU and DMA can both access simultaneously |
| **5. Timeout on all transactions** | Add a watchdog that aborts transactions stuck > N cycles |

### Xilinx AXI Interconnect Deadlock Prevention

The AXI Interconnect has built-in deadlock prevention:
- **REGISTER_SLICE_MODE** on shared paths to prevent combinational loops
- **M_SECURE** bit to isolate masters that could cause deadlock
- **Separate write and read paths** — write responses can't block read data

---

## Clock Domain Crossing in the Interconnect

When masters and slaves run on different clocks, the interconnect must cross clock domains:

```
CPU (100 MHz) ──► [Async FIFO] ──► AXI Interconnect ──► DDR (200 MHz)
DMA (150 MHz)  ──► [Async FIFO] ──►                  ──► BRAM (100 MHz)
```

**Xilinx AXI Interconnect** handles CDC automatically when you set different `ACLK` frequencies on masters and slaves. It inserts async FIFOs at the clock boundaries.

**Custom interconnect:** You must implement your own async FIFOs or dual-clock BRAM for CDC. See [CDC Coding](../../04_hdl_and_synthesis/cdc_coding.md) for patterns.

---

## Practical FPGA SoC Example

### 3-Master, 5-Socket SoC (VexRiscv + DMA + Ethernet)

```
CPU (VexRiscv) ──► AXI Crossbar ──┬──► DDR Ctrl (high BW)
DMA Engine     ──►       │        ├──► Ethernet MAC
Ethernet RX    ──►       │        ├──► Frame Buffer (BRAM)
                         │        └──► APB Bridge → GPIO, UART, I2C
                         │
                   (3 concurrent:
                    CPU reads DDR,
                    DMA streams Eth→DDR,
                    Ethernet RX writes BRAM)
```

### Resource Budget

| Component | LUTs | BRAM | Fmax |
|---|---|---|---|
| 3×5 AXI Crossbar | ~3,000 | 0 | 200 MHz |
| APB Bridge | ~200 | 0 | 200 MHz |
| 3× Async FIFO (CDC) | ~600 | 3 | 200 MHz |
| Address Decoder | ~100 | 0 | 200 MHz |
| Default Slave | ~50 | 0 | 200 MHz |
| **Total interconnect** | **~3,950** | **3** | — |

### Bandwidth Analysis

| Path | Width | Clock | Theoretical BW | Expected Utilization |
|---|---|---|---|---|
| CPU → DDR | 128-bit | 200 MHz | 3.2 GB/s | ~30% (cache misses only) |
| DMA → DDR | 128-bit | 200 MHz | 3.2 GB/s | ~60% (burst transfers) |
| ETH RX → BRAM | 32-bit | 125 MHz | 500 MB/s | ~15% (1G Ethernet) |
| CPU → APB | 32-bit | 100 MHz | 400 MB/s | <1% (register access) |

---

## Key Design Decisions

| Decision | Options | Trade-Off |
|---|---|---|
| **Shared vs dedicated slave ports** | Each slave gets own port vs slaves share one | Bandwidth vs area |
| **Address decoding** | Central decoder vs distributed decode | Latency vs flexibility |
| **Burst support** | Full AXI bursts vs single-beat only | Bandwidth efficiency vs complexity |
| **QoS** | Round-robin vs priority vs weighted | Fairness vs determinism |
| **APB bridge for low-speed** | AXI→APB bridge for GPIO, I2C, UART | Simplifies slave design, saves area |
| **Pipeline depth** | 0–3 stages | Fmax vs latency |
| **CDC** | Async FIFO vs same clock | Multi-clock flexibility vs complexity |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Single slave port for DDR** | CPU stalls when DMA uses DDR | Add 2nd slave port on DDR controller |
| **No default slave** | Bus hangs on unmapped address access | Add default slave that returns DECERR |
| **Fixed priority starvation** | Low-priority master never gets bus access | Use round-robin or TDM arbitration |
| **AXI ID collision** | Out-of-order responses mismatched | Ensure each master has unique ID bits |
| **Missing CDC FIFO** | Corrupted data across clock domains | Add async FIFO or use AXI Interconnect CDC |
| **Combinational loop** | Synthesis error or X-propagation | Add pipeline stage or break dependency |
| **Too many masters on one slave** | Contention → high latency | Add slave port replication |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [AXI Bridges and Interconnect](../../02_architecture/soc/axi_bridges_and_interconnect.md) | This KB | AXI interconnect architecture, crossbar internals |
| [AXI4 Family](../../06_ip_and_cores/bus_protocols/axi4_family.md) | This KB | AXI4/Lite/Stream protocol reference |
| [Memory Map Design](memory_map_design.md) | This KB | Address decoder design, aperture sizing |
| [DMA Architecture](dma_architecture.md) | This KB | DMA engine design, descriptor chains |
| [CDC Coding](../../04_hdl_and_synthesis/cdc_coding.md) | This KB | Clock domain crossing patterns |
