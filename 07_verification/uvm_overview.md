[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# UVM for FPGA — Overview

UVM (Universal Verification Methodology) is the industry-standard verification framework. While UVM's full weight is often overkill for FPGA projects, understanding its architecture helps you scale verification when needed.

---

## UVM Architecture

```
┌──────────────────────────────────────────┐
│              UVM Environment              │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Agent   │  │ Score-   │  │ Coverage│  │
│  │┌───────┐│  │ board    │  │Collector│  │
│  ││Driver ││  │          │  │         │  │
│  │├───────┤│  └────┬─────┘  └────┬────┘  │
│  ││Monitor││       │              │       │
│  │├───────┤│       │              │       │
│  ││Sequen-││       │              │       │
│  ││cer    ││       │              │       │
│  │└───────┘│       │              │       │
│  └────┬────┘       │              │       │
│       │ TLM        │              │       │
└───────┼────────────┼──────────────┼───────┘
        │            │              │
   ┌────▼────────────▼──────────────▼───┐
   │           DUT (your design)        │
   └────────────────────────────────────┘
```

## Core UVM Components

| Component | Role | FPGA Relevance |
|---|---|---|
| **Agent** | Groups driver, monitor, sequencer for one interface | One agent per AXI/Avalon interface |
| **Driver** | Converts transactions to pin-level signals | Drives stimulus onto DUT inputs |
| **Monitor** | Observes pin-level signals, creates transactions | Watches outputs, sends to scoreboard |
| **Sequencer** | Routes sequence items to driver | Controls test flow ("send 100 AXI writes, then 50 reads") |
| **Scoreboard** | Compares expected vs actual results | Reference model: does DUT output match golden model? |
| **Coverage Collector** | Tracks functional coverage metrics | "Did we test all AXI burst types?" |
| **TLM Ports** | Transaction-Level Modeling connections | FIFO-like communication between components |
| **Factory Override** | Replace components without modifying code | Swap "AXI driver" for "AXI error-injection driver" |

## When to Use UVM (vs Cocotb + SVA)

| Scenario | UVM | Cocotb + SVA |
|---|---|---|
| Single AXI/streaming IP test | Overkill | ✅ Quick Python test |
| SoC with 5+ bus interfaces | ✅ Agent per interface | ❌ Hard to coordinate |
| Reusable verification IP | ✅ Factory pattern | ❌ Limited reusability |
| Team of 3+ verification engineers | ✅ Standard methodology | ❌ Each person writes own framework |
| Solo FPGA developer, 1–2 interfaces | ❌ Too heavy | ✅ Fast iteration |

## UVM Lite — Practical for FPGA

Most FPGA projects don't need full UVM. Instead:

1. **Use SVA assertions** for protocol checks (AXI, Avalon handshake rules)
2. **Use Cocotb** for functional test writing (Python → faster iteration)
3. **Add UVM concepts** selectively: scoreboard for reference model comparison, coverage collection for sign-off
4. **Only go full UVM** when you have: multiple bus interfaces, a team, or reuse requirements across projects

---

## Original Stub Description

UVM basics for FPGA: agents, drivers, monitors, sequencers, scoreboards, factory override, TLM ports

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../README.md)
- [README.md](README.md)
