[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Protocol Checkers — AXI, Avalon, Wishbone VIPs

Protocol Verification IP (VIP) and Bus Functional Models (BFMs) that verify your design follows bus protocol rules — catching the hardest FPGA bugs at the interface level.

---

## Why Protocol Checkers Matter

Bus protocol violations are the #1 cause of "works in simulation, fails on hardware" bugs:
- **AXI**: Handshake rules (valid→ready dependency), ID ordering, burst boundary crossing
- **Avalon**: Waitrequest handling, readdatavalid timing, pipeline depth
- **Wishbone**: Stall/ACK/ERR cycle rules, classic vs pipelined mode differences

A protocol checker sits between master and slave, monitoring every transaction:

```
┌─────────┐     ┌──────────────┐     ┌─────────┐
│  Master  │────►│ Protocol VIP │────►│  Slave  │
│  (your   │     │ (SVA + BFM)  │     │  (DUT)  │
│   IP)    │◄────│              │◄────│         │
└─────────┘     └──────┬───────┘     └─────────┘
                       │
                  Assertion violations
                  (reported when protocol rules break)
```

## Available Open Protocol Checkers

| Protocol | Source | Verilog/VHDL | Features |
|---|---|---|---|
| **AXI4/AXI3** | Alex Forencich (verilog-axis) | Verilog | Assertion modules for all AXI channels, BFM included |
| **AXI4-Stream** | Alex Forencich | Verilog | TREADY/TVALID handshake, TLAST alignment |
| **Wishbone B4** | OpenCores / various | Verilog/VHDL | Classic, pipelined mode checkers |
| **Avalon-MM** | Intel Community | SystemVerilog | Waitrequest, pipeline, burst modes |
| **APB** | Various | Verilog | Simple PSEL/PENABLE sequence checker |

## AXI Protocol Checker Example

```systemverilog
// AXI Write Address Channel Protocol Rules
module axi_aw_checker (
    input aclk, aresetn,
    input awvalid, awready,
    input [3:0] awid, awlen, awsize, awburst
);
    // Rule: awvalid must not deassert until awready asserted
    property aw_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && !awready |=> awvalid;
    endproperty
    assert property (aw_valid_stable);

    // Rule: burst length must stay within 4-bit value
    property awlen_valid;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && awready |-> awlen <= 15;
    endproperty
    assert property (awlen_valid);
endmodule
```

## Quick-Start: Adding a Protocol Checker

1. **Instantiate** the checker module in your testbench between master and slave
2. **Connect** all protocol signals (ACLK, ARESETn, AW*, W*, B*, AR*, R*)
3. **Run simulation** — assertions fire automatically when protocol violations occur
4. **Trace** the assertion failure back to the exact cycle and signal state

## Protocol Checkers vs UVM

| Aspect | Protocol Checker (SVA) | UVM VIP |
|---|---|---|
| **Setup time** | Minutes (instantiate module) | Hours (configure agent/environment) |
| **Coverage** | Protocol rule violations only | Protocol + functional scenario coverage |
| **Reusability** | Drop-in module, any testbench | UVM environment required |
| **Best for** | Quick protocol compliance checks | Full verification environments |

---

## Original Stub Description

AXI, Avalon, Wishbone protocol assertion VIPs and bus functional models (BFMs)

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../README.md)
- [README.md](README.md)
