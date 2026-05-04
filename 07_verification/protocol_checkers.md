[← 07 Verification Home](README.md) · [← Project Home](../../README.md)

# Protocol Checkers — AXI, Avalon, Wishbone VIPs and BFM

Protocol Verification IP (VIP) and Bus Functional Models (BFMs) verify that your design follows bus protocol rules — catching the hardest FPGA bugs at the interface level. A single AXI handshake violation can cause silent data corruption that only manifests under heavy traffic or specific timing.

This article covers why protocol checkers matter, complete SVA assertion examples for AXI4 and Wishbone, BFM usage patterns, open-source VIP sources, and integration with simulation and formal verification.

---

## Why Protocol Checkers Matter

Bus protocol violations are the #1 cause of "works in simulation, fails on hardware" bugs:
- **AXI**: Handshake rules (valid→ready dependency), ID ordering, burst boundary crossing, exclusive access
- **Avalon**: Waitrequest handling, readdatavalid timing, pipeline depth, burst count rules
- **Wishbone**: Stall/ACK/ERR cycle rules, classic vs pipelined mode differences

A protocol checker sits between master and slave, monitoring every transaction:

```
┌─────────┐     ┌──────────────┐     ┌─────────┐
│  Master │────►│ Protocol VIP │────►│  Slave  │
│  (your  │     │ (SVA + BFM)  │     │  (DUT)  │
│   IP)   │◄────│              │◄────│         │
└─────────┘     └──────┬───────┘     └─────────┘
                       │
                  Assertion violations
                  (reported when protocol rules break)
```

**Without a checker:** A master deasserts AWVALID before AWREADY — the slave sees a partial address. No simulation error. On silicon, the slave latches garbage and writes to the wrong register. You spend weeks debugging data corruption.

**With a checker:** The assertion fires immediately: `"AWVALID deasserted before AWREADY at time 2450 ns"`. Bug found in minutes.

---

## AXI4 Protocol Checker — Complete SVA Assertions

The AXI4 protocol has 5 independent channels. Each has specific rules that must be followed.

### Write Address (AW) Channel

```systemverilog
module axi4_aw_checker #(
    parameter ID_WIDTH = 4,
    parameter ADDR_WIDTH = 32,
    parameter MAX_BURST_LEN = 16
)(
    input  logic                    aclk,
    input  logic                    aresetn,
    input  logic                    awvalid,
    input  logic                    awready,
    input  logic [ID_WIDTH-1:0]     awid,
    input  logic [ADDR_WIDTH-1:0]   awaddr,
    input  logic [7:0]              awlen,
    input  logic [2:0]              awsize,
    input  logic [1:0]              awburst,
    input  logic                    awlock,
    input  logic [3:0]              awcache,
    input  logic [2:0]              awprot
);

    // Rule 1: AWVALID must not deassert until AWREADY is asserted
    property p_aw_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && !awready |=> awvalid;
    endproperty
    assert_aw_valid_stable: assert property (p_aw_valid_stable)
        else $error("AXI AW: AWVALID deasserted before AWREADY");

    // Rule 2: AW signal stability — when AWVALID and !AWREADY, signals must not change
    property p_aw_stable_id;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && !awready |=> $stable(awid);
    endproperty
    assert_aw_stable_id: assert property (p_aw_stable_id)
        else $error("AXI AW: AWID changed while AWVALID && !AWREADY");

    property p_aw_stable_addr;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && !awready |=> $stable(awaddr);
    endproperty
    assert_aw_stable_addr: assert property (p_aw_stable_addr)
        else $error("AXI AW: AWADDR changed while AWVALID && !AWREADY");

    property p_aw_stable_len;
        @(posedge aclk) disable iff (!aresetn)
            awvalid && !awready |=> $stable(awlen);
    endproperty
    assert_aw_stable_len: assert property (p_aw_stable_len)
        else $error("AXI AW: AWLEN changed while AWVALID && !AWREADY");

    // Rule 3: AWLEN must be 0–255 (always true for 8-bit, but check reserved)
    property p_awlen_range;
        @(posedge aclk) disable iff (!aresetn)
            awvalid |-> awlen <= 255;
    endproperty
    assert_awlen_range: assert property (p_awlen_range)
        else $error("AXI AW: AWLEN out of range");

    // Rule 4: AWSIZE must be 0–7 (1–128 bytes per beat)
    property p_awsize_range;
        @(posedge aclk) disable iff (!aresetn)
            awvalid |-> awsize <= 3'b111;
    endproperty
    assert_awsize_range: assert property (p_awsize_range)
        else $error("AXI AW: AWSIZE out of range");

    // Rule 5: AWBURST must be 00 (FIXED), 01 (INCR), or 10 (WRAP) — 11 is reserved
    property p_awburst_valid;
        @(posedge aclk) disable iff (!aresetn)
            awvalid |-> awburst != 2'b11;
    endproperty
    assert_awburst_valid: assert property (p_awburst_valid)
        else $error("AXI AW: AWBURST = 11 (reserved)");

    // Rule 6: AWLOCK must be 00 or 01 (10 and 11 are AXI3 exclusive, reserved in AXI4)
    property p_awlock_valid;
        @(posedge aclk) disable iff (!aresetn)
            awvalid |-> awlock <= 1'b1;
    endproperty
    assert_awlock_valid: assert property (p_awlock_valid)
        else $error("AXI AW: AWLOCK reserved value used in AXI4");

endmodule
```

### Write Data (W) Channel

```systemverilog
module axi4_w_checker #(
    parameter DATA_WIDTH = 32,
    parameter MAX_BURST_LEN = 16
)(
    input  logic                        aclk,
    input  logic                        aresetn,
    input  logic                        wvalid,
    input  logic                        wready,
    input  logic [DATA_WIDTH-1:0]       wdata,
    input  logic [DATA_WIDTH/8-1:0]     wstrb,
    input  logic                        wlast
);

    // Rule 1: WVALID must not deassert until WREADY
    property p_w_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            wvalid && !wready |=> wvalid;
    endproperty
    assert_w_valid_stable: assert property (p_w_valid_stable)
        else $error("AXI W: WVALID deasserted before WREADY");

    // Rule 2: WSTRB must not have bits set where no data byte exists
    property p_wstrb_valid;
        @(posedge aclk) disable iff (!aresetn)
            wvalid |-> (wstrb & ~((DATA_WIDTH/8)'(1) << (DATA_WIDTH/8)) - 1) == 0;
            // Simplified: upper bits of wstrb must be zero
    endproperty

    // Rule 3: WLAST must be asserted on the last beat of a burst
    // (Requires burst counter — see full VIP implementations)

endmodule
```

### Write Response (B) Channel

```systemverilog
module axi4_b_checker #(
    parameter ID_WIDTH = 4
)(
    input  logic                    aclk,
    input  logic                    aresetn,
    input  logic                    bvalid,
    input  logic                    bready,
    input  logic [ID_WIDTH-1:0]     bid,
    input  logic [1:0]              bresp
);

    // Rule 1: BVALID must not deassert until BREADY
    property p_b_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            bvalid && !bready |=> bvalid;
    endproperty
    assert_b_valid_stable: assert property (p_b_valid_stable)
        else $error("AXI B: BVALID deasserted before BREADY");

    // Rule 2: BRESP must be 00 (OKAY), 01 (EXOKAY), 10 (SLVERR), or 11 (DECERR)
    // All values are legal — no range check needed

    // Rule 3: BID stability while BVALID && !BREADY
    property p_b_stable_id;
        @(posedge aclk) disable iff (!aresetn)
            bvalid && !bready |=> $stable(bid);
    endproperty
    assert_b_stable_id: assert property (p_b_stable_id)
        else $error("AXI B: BID changed while BVALID && !BREADY");

endmodule
```

### Read Address (AR) + Read Data (R) Channels

```systemverilog
module axi4_ar_r_checker #(
    parameter ID_WIDTH = 4,
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  logic                        aclk,
    input  logic                        aresetn,
    // AR channel
    input  logic                        arvalid,
    input  logic                        arready,
    input  logic [ID_WIDTH-1:0]         arid,
    input  logic [ADDR_WIDTH-1:0]       araddr,
    input  logic [7:0]                  arlen,
    input  logic [2:0]                  arburst,
    // R channel
    input  logic                        rvalid,
    input  logic                        rready,
    input  logic [ID_WIDTH-1:0]         rid,
    input  logic [DATA_WIDTH-1:0]       rdata,
    input  logic [1:0]                  rresp,
    input  logic                        rlast
);

    // AR: ARVALID must not deassert until ARREADY
    property p_ar_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            arvalid && !arready |=> arvalid;
    endproperty
    assert_ar_valid_stable: assert property (p_ar_valid_stable)
        else $error("AXI AR: ARVALID deasserted before ARREADY");

    // AR: ARBURST != 2'b11
    property p_arburst_valid;
        @(posedge aclk) disable iff (!aresetn)
            arvalid |-> arburst != 2'b11;
    endproperty
    assert_arburst_valid: assert property (p_arburst_valid)
        else $error("AXI AR: ARBURST = 11 (reserved)");

    // R: RVALID must not deassert until RREADY
    property p_r_valid_stable;
        @(posedge aclk) disable iff (!aresetn)
            rvalid && !rready |=> rvalid;
    endproperty
    assert_r_valid_stable: assert property (p_r_valid_stable)
        else $error("AXI R: RVALID deasserted before RREADY");

    // R: RLAST must be asserted on final beat
    // (Requires burst counter for full check)

    // R: RID stability while RVALID && !RREADY
    property p_r_stable_id;
        @(posedge aclk) disable iff (!aresetn)
            rvalid && !rready |=> $stable(rid);
    endproperty
    assert_r_stable_id: assert property (p_r_stable_id)
        else $error("AXI R: RID changed while RVALID && !RREADY");

endmodule
```

### AXI4-Lite Subset Checker

AXI4-Lite has no bursts, no IDs, and fixed data width:

```systemverilog
module axi4_lite_checker (
    input  logic        aclk,
    input  logic        aresetn,
    // AW
    input  logic        awvalid, awready,
    input  logic [31:0] awaddr,
    // W
    input  logic        wvalid, wready,
    input  logic [31:0] wdata,
    input  logic [3:0]  wstrb,
    // B
    input  logic        bvalid, bready,
    input  logic [1:0]  bresp,
    // AR
    input  logic        arvalid, arready,
    input  logic [31:0] araddr,
    // R
    input  logic        rvalid, rready,
    input  logic [31:0] rdata,
    input  logic [1:0]  rresp
);

    // AW stability
    assert_aw_stable: assert property (@(posedge aclk) disable iff (!aresetn)
        awvalid && !awready |=> $stable(awaddr))
        else $error("AXI-Lite AW: awaddr changed during wait");

    // W stability
    assert_w_stable: assert property (@(posedge aclk) disable iff (!aresetn)
        wvalid && !wready |=> $stable(wdata) && $stable(wstrb))
        else $error("AXI-Lite W: wdata/wstrb changed during wait");

    // B stability
    assert_b_stable: assert property (@(posedge aclk) disable iff (!aresetn)
        bvalid && !bready |=> $stable(bresp))
        else $error("AXI-Lite B: bresp changed during wait");

    // AR stability
    assert_ar_stable: assert property (@(posedge aclk) disable iff (!aresetn)
        arvalid && !arready |=> $stable(araddr))
        else $error("AXI-Lite AR: araddr changed during wait");

    // R stability
    assert_r_stable: assert property (@(posedge aclk) disable iff (!aresetn)
        rvalid && !rready |=> $stable(rdata) && $stable(rresp))
        else $error("AXI-Lite R: rdata/rresp changed during wait");

endmodule
```

---

## Wishbone B4 Protocol Checker

```systemverilog
module wishbone_b4_checker #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  logic                        clk,
    input  logic                        rst,
    // Master signals
    input  logic                        cyc,
    input  logic                        stb,
    input  logic                        we,
    input  logic [DATA_WIDTH/8-1:0]     sel,
    input  logic [ADDR_WIDTH-1:0]       adr,
    input  logic [DATA_WIDTH-1:0]       dat_mosi,
    // Slave signals
    input  logic                        ack,
    input  logic                        err,
    input  logic                        rty,
    input  logic [DATA_WIDTH-1:0]       dat_miso
);

    // Rule 1: STB must not be asserted without CYC
    assert_stb_requires_cyc: assert property (@(posedge clk) disable iff (rst)
        stb |-> cyc)
        else $error("Wishbone: STB asserted without CYC");

    // Rule 2: ACK/ERR/RTY must not be asserted without STB
    assert_ack_requires_stb: assert property (@(posedge clk) disable iff (rst)
        ack |-> stb)
        else $error("Wishbone: ACK asserted without STB");

    assert_err_requires_stb: assert property (@(posedge clk) disable iff (rst)
        err |-> stb)
        else $error("Wishbone: ERR asserted without STB");

    assert_rty_requires_stb: assert property (@(posedge clk) disable iff (rst)
        rty |-> stb)
        else $error("Wishbone: RTY asserted without STB");

    // Rule 3: Only one of ACK/ERR/RTY should be asserted at a time
    assert_one_response: assert property (@(posedge clk) disable iff (rst)
        $onehot({ack, err, rty}) || (!ack && !err && !rty))
        else $error("Wishbone: Multiple responses (ACK/ERR/RTY) simultaneously");

    // Rule 4: ADR, WE, SEL must be stable during a transaction (STB && !ACK)
    assert_adr_stable: assert property (@(posedge clk) disable iff (rst)
        stb && !ack && !err && !rty |=> $stable(adr))
        else $error("Wishbone: ADR changed during pending transaction");

    assert_we_stable: assert property (@(posedge clk) disable iff (rst)
        stb && !ack && !err && !rty |=> $stable(we))
        else $error("Wishbone: WE changed during pending transaction");

endmodule
```

---

## APB Protocol Checker

```systemilog
module apb_checker #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  logic                        pclk,
    input  logic                        presetn,
    input  logic                        psel,
    input  logic                        penable,
    input  logic                        pwrite,
    input  logic [ADDR_WIDTH-1:0]       paddr,
    input  logic [DATA_WIDTH-1:0]       pwdata,
    input  logic [DATA_WIDTH/8-1:0]     pstrb,
    input  logic [DATA_WIDTH-1:0]       prdata,
    input  logic                        pready,
    input  logic                        pslverr
);

    // Rule 1: PENABLE must not be asserted without PSEL
    assert_penable_requires_psel: assert property (@(posedge pclk) disable iff (!presetn)
        penable |-> psel)
        else $error("APB: PENABLE asserted without PSEL");

    // Rule 2: PSEL → PENABLE must follow setup/access phase
    // SETUP phase: PSEL=1, PENABLE=0 (1 cycle minimum)
    // ACCESS phase: PSEL=1, PENABLE=1 (1+ cycles, until PREADY)
    assert_setup_before_access: assert property (@(posedge pclk) disable iff (!presetn)
        $fell(penable) && psel |-> !penable throughout [1:$] ##1 penable)
        else $error("APB: Missing SETUP phase before ACCESS phase");

    // Rule 3: PADDR, PWRITE, PWDATA must be stable during ACCESS phase
    assert_paddr_stable: assert property (@(posedge pclk) disable iff (!presetn)
        psel && penable && !pready |=> $stable(paddr))
        else $error("APB: PADDR changed during ACCESS phase with PREADY low");

    assert_pwrite_stable: assert property (@(posedge pclk) disable iff (!presetn)
        psel && penable && !pready |=> $stable(pwrite))
        else $error("APB: PWRITE changed during ACCESS phase");

endmodule
```

---

## Open-Source Protocol VIPs

| Protocol | Repository | Language | Features |
|---|---|---|---|
| **AXI4 / AXI4-Lite / AXI4-Stream** | [alexforencich/verilog-axi](https://github.com/alexforencich/verilog-axi) | Verilog | Full BFM + assertion checkers for all AXI channels, cocotb tests |
| **AXI4-Stream** | [alexforencich/verilog-axis](https://github.com/alexforencich/verilog-axis) | Verilog | TREADY/TVALID handshake, TLAST, TID, TDEST checkers |
| **AXI4 Formal VIP** | [YosysHQ/SVA-AXI4-FVIP](https://github.com/YosysHQ-GmbH/SVA-AXI4-FVIP) | SystemVerilog | SVA assertions designed for formal verification with SymbiYosys |
| **AMBA Formal** | [dh73/A_Formal_Tale_Chapter_I_AMBA](https://github.com/dh73/A_Formal_Tale_Chapter_I_AMBA) | SystemVerilog | AXI4 + AHB + APB formal properties |
| **Wishbone B4** | Various on OpenCores | Verilog/VHDL | Classic and pipelined mode checkers |
| **APB** | Various | Verilog | PSEL/PENABLE sequence checkers |

### Using Alex Forencich's AXI VIP with cocotb

```python
# test_with_axi_vip.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotbext.axi import AxiLiteMaster, AxiLiteRam

@cocotb.test()
async def test_axi_lite_rw(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units='ns').start())

    # Create AXI-Lite master BFM
    master = AxiLiteMaster(
        AxiLiteBus.from_prefix(dut, "s_axi"),
        dut.clk, dut.rst
    )

    # Create AXI-Lite RAM model
    ram = AxiLiteRam(
        AxiLiteBus.from_prefix(dut, "m_axi"),
        dut.clk, dut.rst,
        size=1024
    )

    # Reset
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    # Write and readback
    await master.write(0x00, 0xDEADBEEF.to_bytes(4, 'little'))
    await master.write(0x04, 0x12345678.to_bytes(4, 'little'))

    data = await master.read(0x00, 4)
    assert int.from_bytes(data, 'little') == 0xDEADBEEF
```

---

## Integration Patterns

### Pattern 1: Inline Checker in Testbench

```systemverilog
module tb_top;
    logic aclk, aresetn;
    // ... DUT signals ...

    dut u_dut (.*);

    // Instantiate checker — monitors DUT's AXI port
    axi4_lite_checker u_checker (.*);
endmodule
```

### Pattern 2: Passthrough Monitor (Non-Intrusive)

```systemverilog
// Connect checker by tapping into existing AXI signals
// No modification to DUT or interconnect required
axi4_aw_checker #(.ID_WIDTH(4)) u_aw_chk (
    .aclk     (axi_clk),
    .aresetn  (axi_rst_n),
    .awvalid  (master_awvalid),
    .awready  (slave_awready),
    .awid     (master_awid),
    .awaddr   (master_awaddr),
    .awlen    (master_awlen),
    .awsize   (master_awsize),
    .awburst  (master_awburst),
    .awlock   (master_awlock),
    .awcache  (master_awcache),
    .awprot   (master_awprot)
);
```

### Pattern 3: Formal Verification with Protocol VIP

```bash
# Use SymbiYosys with AXI formal VIP
sby --fpga axi_slave_proof.sby
```

```ini
# axi_slave_proof.sby
[options]
mode bmc
depth 20

[engines]
smtbmc

[script]
read -sv axi4_lite_checker.sv
read -sv my_axi_slave.sv
read -sv axi_slave_bind.sv

[files]
axi4_lite_checker.sv
my_axi_slave.sv
axi_slave_bind.sv
```

```systemverilog
// axi_slave_bind.sv — Bind checker into DUT
module axi_slave_bind;
    bind my_axi_slave axi4_lite_checker u_chk (
        .aclk    (clk),
        .aresetn (rst_n),
        .awvalid (awvalid),
        .awready (awready),
        .awaddr  (awaddr),
        .wvalid  (wvalid),
        .wready  (wready),
        .wdata   (wdata),
        .wstrb   (wstrb),
        .bvalid  (bvalid),
        .bready  (bready),
        .bresp   (bresp),
        .arvalid (arvalid),
        .arready (arready),
        .araddr  (araddr),
        .rvalid  (rvalid),
        .rready  (rready),
        .rdata   (rdata),
        .rresp   (rresp)
    );
endmodule
```

---

## Protocol Checkers vs UVM

| Aspect | Protocol Checker (SVA) | UVM VIP |
|---|---|---|
| **Setup time** | Minutes (instantiate module) | Hours (configure agent/environment) |
| **Coverage** | Protocol rule violations only | Protocol + functional scenario coverage |
| **Reusability** | Drop-in module, any testbench | UVM environment required |
| **Formal verification** | Works with SymbiYosys | Simulation only |
| **Speed** | Zero simulation overhead (parallel evaluate) | Significant (scoreboard, TLM) |
| **Debug detail** | "Which rule broke, which cycle" | "What was expected vs observed" |
| **Best for** | Quick compliance checks, formal proof | Full verification environments with coverage closure |

**Recommendation:** Always use SVA protocol checkers as a baseline. Add UVM VIP when you need coverage closure and constrained-random stimulus generation.

---

## AXI4 Common Violations Cheat Sheet

| Violation | Root Cause | Fix |
|---|---|---|
| AWVALID deasserted before AWREADY | Master FSM bug — early state transition | Keep AWVALID asserted until AWREADY received |
| WLAST not set on final beat | Burst counter off-by-one | Fix burst counter; validate with WLAST checker |
| BRESP = SLVERR unexpectedly | Slave address decode misses a range | Add address range to slave or fix decoder |
| RID mismatch (out-of-order) | Slave returns wrong ID | Check slave's ID pass-through logic |
| ARVALID without ARREADY hang | Slave never asserts ARREADY | Add timeout + default ARREADY in slave |
| WSTRB has holes (non-contiguous bytes) | Not illegal in AXI, but many slaves don't support | Check slave's byte-lane handling or fix WSTRB |
| AWLEN = 0 with AWBURST = WRAP | WRAP burst with length 1 is meaningless | Use INCR for single-beat transfers |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [AMBA AXI4 Protocol Spec](https://developer.arm.com/documentation/ihi0022/latest) | ARM | Complete AXI4 protocol rules (the source of truth for all assertions) |
| [verilog-axi](https://github.com/alexforencich/verilog-axi) | GitHub | Full AXI BFM + checkers + cocotb tests |
| [SVA-AXI4-FVIP](https://github.com/YosysHQ-GmbH/SVA-AXI4-FVIP) | GitHub | SVA assertions for formal verification |
| [AXI4 Family](../06_ip_and_cores/bus_protocols/axi4_family.md) | This KB | AXI4/Lite/Stream protocol reference |
| [Formal Verification](formal_verification.md) | This KB | SymbiYosys workflow for proving assertions |
| [UVM Overview](uvm_overview.md) | This KB | Full UVM testbench with AXI-Lite VIP |
