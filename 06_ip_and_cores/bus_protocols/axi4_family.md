[← 06 IP & Cores Home](../README.md) · [← Bus Protocols Home](README.md) · [← Project Home](../../../README.md)

# AXI4 Family — AMBA 4 in Practice

AXI4 (Advanced eXtensible Interface 4) is the dominant on-chip bus protocol in the FPGA world. Every Xilinx IP core, every memory controller, and every DMA engine speaks AXI. Understanding its five-channel architecture is the prerequisite for building, debugging, and optimizing FPGA SoC designs.

The AXI4 family has three members, each optimized for a different traffic type:

| Protocol | Width | Burst | Flow Control | Best For |
|---|---|---|---|---|
| **AXI4-Full** | Up to 1024-bit | Yes (1–256 beats) | VALID/READY per channel | Memory-mapped high-throughput: DDR, PCIe DMA |
| **AXI4-Lite** | 32-bit typical | No (single beat) | VALID/READY | Control/status registers, MMIO |
| **AXI4-Stream** | Arbitrary | Continuous flow | TVALID/TREADY | Unidirectional streaming: video, ADC/DAC, packet processing |

---

## The Five Channels

AXI4 separates transactions into independent channels that operate concurrently:

```
Master (Initiator)                              Slave (Target)
┌─────────────────┐                            ┌─────────────────┐
│  Write Address   │── AWADDR, AWVALID/AWREADY ──→│                  │
│  Channel (AW)    │                            │                  │
│  Write Data      │── WDATA, WVALID/WREADY ────→│  Decode +        │
│  Channel (W)     │                            │  Buffer          │
│  Write Response  │←─ BRESP, BVALID/BREADY ────│                  │
│  Channel (B)     │                            │                  │
│                  │                            │                  │
│  Read Address    │── ARADDR, ARVALID/ARREADY ──→│                  │
│  Channel (AR)    │                            │                  │
│  Read Data       │←─ RDATA, RVALID/RREADY ────│                  │
│  Channel (R)     │                            │                  │
└─────────────────┘                            └─────────────────┘
```

**Key design points:**

### VALID/READY Handshake — The Universal Mechanism

Every channel uses the same two-wire handshake:
- **VALID** (initiator → target): "My data/address is valid, act on it"
- **READY** (target → initiator): "I am ready to accept your data/address"

A transfer occurs on the clock edge where **both VALID and READY are HIGH**. This allows either side to backpressure the other:

```
clk    ┌─┐  ┌─┐  ┌─┐  ┌─┐  ┌─┐  ┌─┐
       ┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──
VALID  ────┐     ┌───────────┐
           └─────┘           └──────────
READY  ────────────────────────────────  (always ready, no backpressure)
Transfer      ↑           ↑
              X1          X2
```

### Burst Types

| Type | Behavior | Use Case |
|---|---|---|
| **FIXED** | All beats go to the same address (e.g., FIFO register) | Streaming to a single register |
| **INCR** | Address increments by transfer size each beat | Sequential memory access |
| **WRAP** | Address wraps within a boundary (cache-line aligned) | Cache line fills |

### Transaction ID and Ordering

Each transaction carries an **AXI ID** (AWID/ARID). The spec guarantees:
- Transactions with **different IDs** have no ordering constraints (can complete out of order)
- Transactions with **the same ID** must complete in order
- The **write response (B)** must not be sent until the last write data beat is received

---

## AXI4-Lite — The Register Interface

AXI4-Lite strips AXI4 down to single-beat, 32-bit (or 64-bit) accesses:

```verilog
// AXI4-Lite write: single cycle
// AWVALID + WVALID + BREADY all high simultaneously
always @(posedge clk) begin
    if (awvalid && awready)
        wr_addr <= awaddr;
    if (wvalid && wready)
        wr_data <= wdata;
    if (bvalid && bready)
        wr_done <= 1'b1;
end
```

AXI4-Lite is the interface for **control and status registers** (CSR). Nearly every IP core exposes an AXI4-Lite port for configuration.

---

## AXI4-Stream — The Data Pipeline

AXI4-Stream removes addresses entirely — it's a pure point-to-point streaming interface:

```verilog
// AXI4-Stream: simple pipeline stage
always @(posedge clk) begin
    if (m_axis_tready) begin
        m_axis_tvalid <= s_axis_tvalid;
        m_axis_tdata  <= s_axis_tdata;
        m_axis_tlast  <= s_axis_tlast;  // End-of-packet marker
        m_axis_tkeep  <= s_axis_tkeep;  // Byte enables within beat
    end
end
```

Additional optional signals:
- **TLAST** — marks the last beat of a packet/frame
- **TKEEP** — byte-level valid within a data beat (for narrow transfers)
- **TID/TDEST/TUSER** — routing, destination, and user-defined sideband

---

## AXI4 Cross-Vendor Usage

| Vendor | AXI4-Full | AXI4-Lite | AXI4-Stream |
|---|---|---|---|
| **Xilinx** | Native (all IP) | Native | Native |
| **Intel** | Via Platform Designer bridge (Avalon ↔ AXI) | Via bridge | Via bridge; native on Agilex HPS |
| **Microchip** | Native (CoreAXI) | Native (CoreAXI4Lite) | Native |
| **Lattice** | Via IP and interconnect | Via IP | Via IP |

> Intel uses Avalon-MM as its native bus. Cross-vendor designs that target both Xilinx and Intel typically converge on AXI4 as the common denominator, using Intel's Avalon-to-AXI bridge IPs.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **READY deassertion during a burst** | Write data channel stalls mid-burst, FIFO overflow | Ensure READY stays high for minimum burst length, or buffer internally |
| **Forgetting BVALID after write** | Master hangs waiting for write response | Always drive BVALID after last write data beat |
| **AXI ID width mismatch** | Out-of-order completion not working | Match ID width across all connected components |
| **Unconnected TKEEP on stream** | All bytes treated as valid; may cause unexpected sideband data | Tie TKEEP to all-ones if all bytes are always valid |
| **Crossing clock domains without AXI CDC IP** | Protocol violation due to VALID/READY crossing domains | Use Xilinx AXI Clock Converter or Intel AXI CDC bridge |

---

## Further Reading

| Article | Topic |
|---|---|
| [other_buses.md](other_buses.md) | Wishbone, Avalon, APB/AHB — comparison with AXI |
| [interconnect/](../interconnect/README.md) | AXI Interconnect: crossbar, QoS, width/clock conversion |
| ARM IHI 0022 | AMBA AXI and ACE Protocol Specification |
| Xilinx UG1037 | AXI Reference Guide (excellent practical supplement) |
