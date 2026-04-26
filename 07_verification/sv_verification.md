[← Section Home](README.md) · [← Project Home](../README.md)

# SV Verification — SystemVerilog Testbench Primitives

SystemVerilog is the verification backbone for FPGA and ASIC design. This article covers the language features that turn it from a hardware description language into a verification powerhouse — the primitives that every testbench framework (UVM, cocotb wrappers, custom) ultimately relies on.

---

## Assertions (SVA)

SystemVerilog Assertions let you specify temporal behavior that simulators and formal tools check automatically.

### Immediate vs Concurrent

| Type | Syntax | When Evaluated | Use |
|---|---|---|---|
| **Immediate** | `assert (a == b);` | Procedural (like an `if`) | Simple combinational checks |
| **Concurrent** | `assert property (@(posedge clk) a |-> b);` | Clock-edge driven | Temporal sequences, pipelined protocols |

### Key Operators

| Operator | Meaning | Example |
|---|---|---|
| `|->` | Overlapping implication | If `a` then `b` *in same cycle* |
| `|=>` | Non-overlapping implication | If `a` then `b` *next cycle* |
| `##N` | Delay by N cycles | `a ##2 b` — b two cycles after a |
| `##[M:N]` | Range delay | `a ##[1:3] b` — b 1 to 3 cycles after a |
| `$rose()`, `$fell()` | Edge detection | `$rose(req)` — rising edge |
| `$past()` | Historical value | `$past(data, 2)` — data from 2 cycles ago |

### Coverage

SVA also drives **cover properties** — did this sequence ever occur?

```systemverilog
cover property (@(posedge clk) $rose(req) ##1 $rose(ack));
```

---

## Functional Coverage

```systemverilog
covergroup cg @(posedge clk);
    coverpoint addr {
        bins low    = {[0:63]};
        bins mid    = {[64:127]};
        bins high   = {[128:255]};
    }
    coverpoint cmd {
        bins reads  = {READ, READX};
        bins writes = {WRITE, WRITEX};
    }
    cross cmd, addr;  // cross-coverage
endgroup
```

| Construct | Purpose |
|---|---|
| `covergroup` | Define what to sample |
| `coverpoint` | Variable or expression to track |
| `bins` | Value ranges to bin into |
| `cross` | Combined coverage of multiple points |
| `option.goal` | Target (default 100%) |
| `sample()` | Trigger manually |

---

## Constrained-Random Stimulus

```systemverilog
class Packet;
    rand bit [7:0]  addr;
    rand bit [3:0]  size;
    
    constraint addr_range { addr inside {[0:127]}; }
    constraint size_limit { size > 0; size < 13; }
    
    function void print();
        $display("Packet: addr=%0d size=%0d", addr, size);
    endfunction
endclass

Packet p = new();
assert(p.randomize());  // generate random valid packet
```

| Keyword | Purpose |
|---|---|
| `rand` | Randomize every call |
| `randc` | Cycle through all values before repeating |
| `constraint` | Limit the solution space |
| `inside` | Set membership |
| `solve X before Y` | Control distribution order |
| `randomize() with {}` | Inline constraints |

---

## Classes & Object-Oriented Testbenches

```systemverilog
class Driver;
    virtual intf vif;  // handle to interface
    mailbox #(Packet) gen2drv;  // communication channel
    
    task run();
        forever begin
            Packet pkt;
            gen2drv.get(pkt);
            @(vif.cb);        // sync to clocking block
            vif.cb.addr <= pkt.addr;
            vif.cb.data <= pkt.data;
        end
    endtask
endclass
```

## Virtual Interfaces & Clocking Blocks

```systemverilog
interface bus_if (input clk);
    logic [7:0] addr, data;
    logic req, ack;
    
    clocking cb @(posedge clk);
        input  ack, data;   // sampled before edge
        output addr, req;   // driven after edge
    endclocking
    
    modport tb (clocking cb);
endinterface
```

Clocking blocks eliminate race conditions: inputs sampled in the **Observed** region, outputs driven in the **Reactive** region, avoiding timing races between DUT and testbench.

---

## Best Practices

1. **Start with SVA for protocol checks** — even without a full UVM environment, assertions catch protocol violations silently and permanently.
2. **Use constrained-random sparingly on FPGA** — it's more useful for ASIC verification. For FPGA, directed tests with coverage gaps filled by random often suffice.
3. **Clocking blocks prevent the #1 testbench bug** — sampling/output timing mismatches. Always use them for synchronous interfaces.

## Pitfall: OOP Overhead

SV classes, queues, and dynamic arrays consume simulator heap memory. Large constrained-random runs with thousands of packets can overwhelm lightweight simulators. Know when to fall back to simpler directed tests.

---

## References

| Source | Path |
|---|---|
| IEEE 1800-2017 (SystemVerilog LRM) | IEEE standards |
| SystemVerilog for Verification (Spear) | ISBN 978-1-4614-0714-0 |
| SVA Handbook (Cerny, Dudani, Havlicek) | Formal reference |
