[← 06 IP & Cores Home](../README.md) · [← Interconnect Home](README.md) · [← Project Home](../../../README.md)

# AXI Interconnect — Crossbars, Addressing, and Arbitration

When an AXI design has multiple masters and multiple slaves, someone must route transactions, decode addresses, and arbitrate contention. The AXI Interconnect (called "SmartConnect" in modern Xilinx, "AXI Interconnect" in classic Xilinx, and "Memory-Mapped Interconnect" in Intel Platform Designer) is that someone.

---

## Why an Interconnect Exists

A flat AXI bus works for one master and one slave. Add a second master, and you immediately face three problems:

1. **Routing**: Which slave does address 0x4000_0000 belong to?
2. **Arbitration**: Two masters want the same slave simultaneously — who goes first?
3. **Deadlock**: Master A is writing to Slave X while Slave X's read response needs to reach Master B — can this stall forever?

The interconnect solves all three by implementing a **multi-layer switching fabric** with configurable address maps, QoS-aware arbitration, and protocol-level deadlock avoidance.

---

## Topology: Crossbar vs Shared Bus

```
┌──── Crossbar ────────────────────────────────┐
│                                               │
│  Master 0 ──┬─── switch ───┬── Slave 0        │
│             │    matrix    │                  │
│  Master 1 ──┤              ├── Slave 1        │
│             │   (N×M)      │                  │
│  Master 2 ──┼──────────────┼── Slave 2        │
│             │              │                  │
│  Master 3 ──┘              └── Slave 3        │
│                                               │
│  Any master → any slave concurrently          │
└───────────────────────────────────────────────┘

┌──── Shared Bus ──────────────────────────────┐
│                                               │
│  M0 ──┐                                      │
│  M1 ──┼── [Arbiter] ──── Shared Bus ──── S0   │
│  M2 ──┤                       ├── S1         │
│  M3 ──┘                       └── S2         │
│                                               │
│  One transaction at a time (reads + writes)   │
└───────────────────────────────────────────────┘
```

| Topology | Throughput | Area (LUTs) | Latency | When to Use |
|---|---|---|---|---|
| **Full Crossbar** | N×M concurrent | O(N×M×DW) | 1–2 cycles per hop | Multi-master, high bandwidth |
| **Shared Bus** | 1 at a time | O(N×DW) | 1 cycle + arbitration | Simple designs, ≤3 masters |
| **Partial Crossbar** | Subset of N×M | O(sub×DW) | 1–2 cycles | Known access patterns |

> **Real-world**: Xilinx AXI SmartConnect builds a full crossbar by default; Intel Platform Designer builds a shared bus unless you instantiate multiple master-to-slave connections.

---

## Address Decoding

The interconnect routes transactions by comparing AWADDR/ARADDR against a configurable address map:

```tcl
# Xilinx: Assign address segments in the Address Editor
# Slave 0: 0x0000_0000 - 0x3FFF_FFFF  (1 GB) — DDR controller
# Slave 1: 0x4000_0000 - 0x4000_FFFF  (64 KB) — GPIO peripheral
# Slave 2: 0x4001_0000 - 0x4001_FFFF  (64 KB) — UART
# Default: error response (DECERR on AXI)
```

### Address Decoding Logic

```
AWADDR[31:0] ────→│  Decoder   │
                   │            │──→ Slave 0 (bits [31:30] == 00)
                   │  Range      │──→ Slave 1 (bits [31:16] == 0x4000)
                   │  Match      │──→ Slave 2 (bits [31:16] == 0x4001)
                   │            │──→ Default Slave (DECERR / SLVERR)
                   └────────────┘
```

**Key rules:**
- Address ranges are **power-of-2 aligned** and sized (e.g., 1 GB = 0x4000_0000 range)
- Ranges must **not overlap** (overlap → undefined routing behavior)
- A **default slave** catches unmapped addresses — usually responds with DECERR (decode error)
- The interconnect generates AWPROT/ARPROT from the address range attributes

---

## QoS Arbitration

When multiple masters contend for a slave, the interconnect's arbiter picks a winner:

### Arbitration Schemes

| Scheme | Behavior | Use Case |
|---|---|---|
| **Round-Robin** | Rotates priority each cycle; fair and starvation-free | General purpose (default) |
| **Weighted Round-Robin** | Master 0 gets 3 slots, Master 1 gets 1 slot | Guarantee minimum bandwidth per master |
| **Fixed Priority** | Master 0 always wins; Master N starves if Master 0 is busy | Real-time master (deterministic worst-case latency) |
| **Read/Write Group** | Separate arbitration for read and write channels | Maximize concurrency between R/W |

```tcl
# Xilinx SmartConnect: Set QoS per master port
set_property CONFIG.NUM_MI {1} [get_bd_cells smartconnect_0]
set_property CONFIG.S00_ARB {0} [get_bd_cells smartconnect_0]
# 0=RoundRobin, 1=FixedPriority, 2=WeightedRoundRobin
```

> [!WARNING]
> Fixed priority can cause **master starvation** — a low-priority master never gets the bus if the high-priority master issues back-to-back transactions. Use weighted round-robin for mixed-criticality designs.

---

## Deadlock Avoidance

AXI separates read and write channels, which creates a deadlock risk: if the write response channel (B) stalls, it can block the read address channel (AR) in a shared interconnect.

### The Circular-Dependency Problem

```
Master A write → Slave X (B channel stalled waiting for X's internal buffer)
Master B read  → Slave X (AR channel accepted, but R data can't return because
                          Slave X is busy processing Master A's write...)
```

### Solution: Independent Read/Write Arbitration

Modern interconnects (Xilinx SmartConnect, Intel MM Interconnect 2.0+) use **completely separate read and write arbitration** within the crossbar:

```
┌─ Write Side ─┐     ┌─ Read Side ──────┐
│ AW Arbiter    │     │ AR Arbiter       │
│ W Data Path   │     │ R Data Path      │
│ B Response    │     │                  │
└───────────────┘     └──────────────────┘
        │                      │
        └──────┬───────────────┘
               │
         Slave Interface
```

Reads and writes proceed independently — a stalled B channel never blocks the AR channel.

### Pipeline Register Insertion

Adding pipeline stages (register slices) between interconnect layers breaks long combinatorial paths and prevents timing-related protocol violations:

```verilog
// AXI Register Slice: breaks timing by inserting one cycle of pipeline
// on ALL five channels simultaneously
// Xilinx: axis_register_slice IP
// Intel: Avalon-MM Pipeline Bridge
```

---

## Xilinx SmartConnect vs Classic AXI Interconnect

| Feature | AXI Interconnect (classic) | AXI SmartConnect |
|---|---|---|
| **XCIs supported** | Up to 16 MI, 16 SI | Up to 16 MI, 16 SI |
| **Auto-pipelining** | Manual | Automatic (timing-driven) |
| **Data width conversion** | Manual (separate IP) | Built-in (auto-upsizing/downsizing) |
| **Clock conversion** | Manual (separate IP) | Built-in (async clock crossing) |
| **QoS** | Round-robin only | Weighted, fixed-priority |
| **AXI4-Stream passthrough** | No | Yes |
| **Vivado version** | All versions | 2017.1+ (default from 2019.1) |

> **Recommendation**: Use SmartConnect for all new Xilinx designs unless you have a specific reason to use the classic interconnect (e.g., compatibility with older IP that requires AXI3).

---

## Intel Platform Designer Interconnect

Intel uses **Avalon-MM** natively, but the interconnect architecture parallels AXI:

```
Master 0 (Avalon-MM) ┐
Master 1 (AXI4)      ├──→ [Platform Designer Interconnect] ──→ Slave 0 (Avalon-MM)
                      │        │                               ├── Slave 1 (AXI4)
                      │   Address Map                          └── Slave 2 (Avalon-MM)
                      │   Arbitration (Round-Robin)
                      │   Pipeline Bridges
                      │   Clock Crossing
                      └── Avalon ↔ AXI bridges
```

Platform Designer auto-generates the interconnect fabric based on the connections you draw in the GUI. Each master-to-slave connection adds a port to the switch.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Overlapping address ranges** | Transactions routed to wrong slave | Verify all address segments are non-overlapping in Address Editor |
| **Unconnected default slave** | DECERR on unmapped address → master hangs | Always connect a default slave or use `set_property ADDR_WIDTH` |
| **Fixed priority starvation** | Low-priority master never gets bus | Switch to weighted round-robin or insert idle cycles in high-priority master |
| **ID width mismatch** | Out-of-order responses lost | Match AWID/ARID width across all connected masters/slaves |
| **Forgetting register slices on long paths** | Timing failures on interconnect → max frequency drops | Insert register slices every ~1000 LUTs of distance |
| **AXI3 slave on AXI4 interconnect** | Protocol violation (burst length encoding differs) | Use AXI Protocol Converter or ensure all slaves are AXI4 |

---

## Further Reading

| Article | Topic |
|---|---|
| [data_width_clock_conversion.md](data_width_clock_conversion.md) | Data width, clock domain, and protocol conversion |
| [bus_protocols/axi4_family.md](../bus_protocols/axi4_family.md) | AXI4 protocol deep dive |
| Xilinx PG059 | AXI Interconnect Product Guide |
| Xilinx PG247 | AXI SmartConnect Product Guide |
