[← 06 IP & Cores Home](../README.md) · [← Interconnect Home](README.md) · [← Project Home](../../../README.md)

# AXI Data Width, Clock, and Protocol Converters

The AXI interconnect routes transactions between masters and slaves, but it doesn't solve **format mismatches**. When a 64-bit master talks to a 32-bit slave, or a 200 MHz AXI domain crosses into a 100 MHz AXI domain, you need converter IP blocks.

---

## Three Converter Types

| Converter | Problem It Solves | Xilinx IP | Intel Equivalent |
|---|---|---|---|
| **Data Width Converter** | Master and slave have different DATA_WIDTH | AXI Data Width Converter | Avalon-MM Width Adapter |
| **Clock Converter** | Master and slave are in different clock domains | AXI Clock Converter | Avalon-MM Clock Crossing Bridge |
| **Protocol Converter** | Master is AXI4, slave is AXI3 (or AXI4-Lite ↔ AXI4) | AXI Protocol Converter | Avalon ↔ AXI Bridge |

---

## Data Width Converter — Upsizing and Downsizing

### Upsizing (Narrow Master → Wide Slave)

A 32-bit master writes to a 64-bit slave. The converter must **pack** multiple narrow beats into one wide beat:

```
Master (32-bit) → Converter → Slave (64-bit)
Beat 0: 0xAAAA_BBBB        ┐
Beat 1: 0xCCCC_DDDD        ├──→ Beat 0: 0xCCCC_DDDD_AAAA_BBBB
                            ┘    (merged when 2nd beat arrives)
```

**Behavior:**
- Write channel: Converter buffers beats until a full wide word is assembled, then issues the slave write
- Read channel: One wide read returns data for two narrow read responses (cached internally)
- **Latency penalty**: Up to 2× for upsizing writes (must wait for second beat)

### Downsizing (Wide Master → Narrow Slave)

A 64-bit master writes to a 32-bit slave. The converter must **split** each wide beat into multiple narrow beats:

```
Master (64-bit) → Converter → Slave (32-bit)
Beat 0: 0xCCCC_DDDD_AAAA_BBBB
                                 → Beat 0: 0xAAAA_BBBB
                                 → Beat 1: 0xCCCC_DDDD
```

**Behavior:**
- Write channel: WSTRB determines which byte lanes are valid; converter splits accordingly
- Read channel: Multiple narrow reads are assembled into one wide response
- **Throughput penalty**: Throughput halves (slave is the bottleneck)

### Key Parameter: Data FIFO Depth

The converter uses internal FIFOs to buffer partial beats. Insufficient depth causes backpressure:

```tcl
# Vivado: Set FIFO depth for data width converter
set_property CONFIG.FIFO_DEPTH {32} [get_bd_cells axi_dwidth_converter_0]
```

| FIFO Depth | Effect |
|---|---|
| 16 | OK for burst ≤ 16 beats |
| 32 | Recommended for long bursts |
| 512 | Overkill for most; use only with deep pipelines |

---

## Clock Converter — Crossing Clock Domains

### Asynchronous Mode (Different Frequencies, Unrelated Phase)

Uses an **async FIFO** on each of the 5 AXI channels:

```
Clock Domain A (150 MHz)         Clock Domain B (100 MHz)
┌──────────────────┐            ┌──────────────────┐
│ AXI Master       │            │ AXI Slave        │
│                  │──→ FIFO ──→│                  │
│ AW/W/B/AR/R      │   (async)  │ AW/W/B/AR/R      │
└──────────────────┘            └──────────────────┘
```

**Constraints:**
- Each async FIFO depth is configurable (default 16)
- Full AXI ordering guarantees are preserved across the FIFO boundary
- **Latency penalty**: 4–8 cycles per direction (FIFO write + read latency)

### Synchronous Mode (Integer Ratio, Same Phase)

When clocks are related (e.g., 200 MHz ↔ 100 MHz, locked to same MMCM), use a simpler **synchronous converter**:

```tcl
# Xilinx: Synchronous clock converter (lower latency, lower area)
set_property CONFIG.SYNCHRONIZATION_STAGES {2} [get_bd_cells axi_clock_converter_0]
# Set to 0 for synchronous mode (clocks are phase-aligned)
```

| Mode | Latency | LUTs | When |
|---|---|---|---|
| **Async** | 6–12 cycles | ~800 LUTs per channel | Unrelated clocks |
| **Sync** | 2–3 cycles | ~300 LUTs per channel | Integer-ratio, same MMCM/PLL |

---

## Protocol Converter — AXI4 ↔ AXI3 ↔ AXI4-Lite

### AXI4 to AXI3 (Down-conversion)

AXI3 differs from AXI4 in burst length encoding:
- **AXI4**: Burst length 1–256, encoded in AWLEN[7:0]
- **AXI3**: Burst length 1–16, encoded in AWLEN[3:0]

The converter must split AXI4 bursts longer than 16 beats into multiple AXI3 bursts:

```
AXI4 Master: AWLEN = 63 (64-beat burst)
                 │
                 ▼
    Protocol Converter: Split into 4 × AXI3 bursts (16 beats each)
                 │
                 ▼
            AXI3 Slave
```

> This splitting is transparent to the AXI4 master — it sees one long burst; the AXI3 slave sees four shorter bursts.

### AXI4-Lite to AXI4 (Up-conversion)

AXI4-Lite adds burst support. The converter translates single-beat Lite transactions to AXI4 bursts of length 1:

```verilog
// Converter internally:
// AXI4-Lite AWVALID → AXI4 AWVALID with AWLEN = 0, AWSIZE = 2 (4 bytes)
// AXI4-Lite WVALID   → AXI4 WVALID with WSTRB = 4'b1111, WLAST = 1
```

---

## Conversion Latency Budget

When chaining converters, the total latency adds up. Here's a budget for a typical path:

```
Master (AXI4, 200 MHz)
  │
  ├── Data Width Converter (32→128-bit upsizing) ........... +3–6 cycles
  │
  ├── Clock Converter (200→150 MHz, async) ................. +6–12 cycles
  │
  ├── AXI Interconnect (crossbar, no conversion) ............. +1 cycle
  │
  └── Slave (AXI4, 128-bit, 150 MHz)

Total worst-case latency: 10–19 cycles (~95–127 ns at 150 MHz)
```

### Minimizing Conversion Overhead

| Strategy | When |
|---|---|
| **Match data widths at IP boundaries** | Design all IP with the same AXI_DATA_WIDTH (e.g., 128-bit) |
| **Use a single unified clock domain** | Run all AXI logic at the same frequency; avoid clock converters entirely |
| **Push conversion to SmartConnect** | SmartConnect has built-in width/clock conversion with optimized implementations |
| **Avoid unnecessary protocol conversion** | Keep all IP AXI4; only use AXI3 for legacy IP; use AXI4-Lite only for register interfaces |

---

## Open-Source Equivalents

| Converter Type | Open-Source Equivalent |
|---|---|
| AXI Data Width Converter | `wb_data_resize` (Wishbone data width adapter in LiteX) |
| AXI Clock Converter (async) | `clock_domain_crossing` wrapper with dual-clock FIFO |
| AXI Protocol Converter | Manually implemented in RTL (no standard open-source IP) |
| AXI4-Stream width converter | `axis_dwidth_converter` in Alex Forencich's `verilog-axis` |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Async clock converter without proper CDC constraints** | Data corruption, intermittent failures | Apply `set_clock_groups -asynchronous` between the two clock domains |
| **FIFO depth too small for burst length** | WREADY deasserts mid-burst → throughput drops | Set FIFO depth ≥ burst length |
| **Downsizing without checking WSTRB** | Byte-level data corruption on sub-word writes | Ensure WSTRB is correctly propagated through the converter |
| **Protocol converter AWID width mismatch** | Out-of-order transaction completion breaks | Match ID width at both sides |
| **Chaining too many converters** | Total latency exceeds system budget | Measure end-to-end latency in simulation; flatten where possible |

---

## Further Reading

| Article | Topic |
|---|---|
| [axi_interconnect.md](axi_interconnect.md) | Crossbar design, address decoding, QoS arbitration |
| [bus_protocols/axi4_family.md](../bus_protocols/axi4_family.md) | AXI4 protocol deep dive (AXI3 vs AXI4 differences) |
| Xilinx PG085 | AXI Data Width Converter |
| Xilinx PG200 | AXI Clock Converter |
