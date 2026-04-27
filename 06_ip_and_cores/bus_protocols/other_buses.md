[← 06 IP & Cores Home](../README.md) · [← Bus Protocols Home](README.md) · [← Project Home](../../../README.md)

# Wishbone, Avalon, APB/AHB — Beyond AXI4

Not every bus is AXI. Three alternatives dominate specific niches: **Wishbone** (open-source, simple), **Avalon** (Intel's native bus), and **APB/AHB** (ARM's lighter-weight protocols). Understanding when to use each — and how they map to AXI4 — is essential for IP selection and cross-vendor design.

---

## Quick Comparison

| Criterion | AXI4-Full | Avalon-MM | Wishbone (Classic) | APB | AHB |
|---|---|---|---|---|---|
| **Origin** | ARM (AMBA 4) | Altera/Intel | OpenCores / OpenRISC | ARM (AMBA 2+) | ARM (AMBA 2+) |
| **Complexity** | High (5 channels) | Moderate (read + write ports) | Low (single bus) | Very low | Moderate |
| **Throughput** | Highest (concurrent R/W) | High (pipelined) | Low–Moderate | Lowest | Moderate |
| **Burst support** | Yes (1–256 beats) | Yes | Optional (pipelined mode) | No | Yes (INCR/WRAP) |
| **Flow control** | VALID/READY per channel | waitrequest per transfer | ACK/ERR/RTY per cycle | PREADY/PSLVERR | HREADY/HRESP |
| **Open standard** | Royalty-free license | Proprietary (Intel) | Fully open (public domain) | Royalty-free license | Royalty-free license |
| **Primary ecosystem** | Xilinx, ARM, Microchip | Intel/Altera | Open-source IP (OpenCores, LiteX, RISC-V) | ARM MCU/SoC peripherals | ARM MCU/SoC |

---

## Wishbone — The Open-Source Workhorse

Wishbone was designed for simplicity. The classic version is a single shared bus with master/slave addressing:

```
Master                    Slave 0      Slave 1
│                         │            │
├── ADR_O ────────────────┼────────────┤  (address)
├── DAT_O ────────────────┼────────────┤  (write data)
├── DAT_I ────────────────┼────────────┤  (read data, shared)
├── WE_O ─────────────────┼────────────┤  (write enable)
├── SEL_O ────────────────┼────────────┤  (byte select)
├── STB_O ────────────────┼────────────┤  (strobe — "this cycle is valid")
├── CYC_O ────────────────┼────────────┤  (cycle — "transaction in progress")
├── ACK_I ◄───────────────┼────────────┤  (acknowledge from addressed slave)
```

### Wishbone Variants

| Variant | Key Feature | Use Case |
|---|---|---|
| **Classic** | Single-cycle, single-master | Simple peripherals, GPIO, UART |
| **Pipelined** | Overlapped address/data phases | Higher throughput memory access |
| **Registered Feedback** | Registered ACK path | Timing closure on large designs |
| **Crossbar** | Multiple masters, concurrent access | Multi-master SoC |

### Where Wishbone Dominates

- **LiteX SoC builder** — all internal buses are Wishbone
- **OpenCores** — the de facto bus for community IP
- **RISC-V soft cores** — VexRiscv, SERV, NEORV32 use Wishbone
- **Anything that needs zero licensing overhead**

---

## Avalon — Intel's Native Bus

Avalon Memory-Mapped (Avalon-MM) is Intel's answer to AXI. Unlike AXI's five independent channels, Avalon-MM uses a **single address/data pair** with shared flow control:

```verilog
// Avalon-MM master write
always @(posedge clk) begin
    if (avm_write && !avm_waitrequest) begin
        // Write committed this cycle
        // Slave accepted address + data
    end
end

// Key: waitrequest is the ONLY backpressure mechanism
// There is no READY — master asserts write, slave holds waitrequest
// until it can accept, then deasserts waitrequest to ACK
```

### Avalon-MM vs AXI4 Key Differences

| Feature | Avalon-MM | AXI4 |
|---|---|---|
| Channels | Single address + data pair | 5 independent channels |
| Backpressure | `waitrequest` (shared) | `VALID/READY` (per channel) |
| Read/Write concurrency | Separate read and write ports | Independent read/write channels |
| Burst | `burstcount` signal | `AWLEN`/`ARLEN` in address channel |
| Byte enables | `byteenable` per beat | `WSTRB` in write data channel |
| Pipeline stages | `readdatavalid` for read latency | RVALID indicates read data valid |

Intel Platform Designer (Qsys) auto-generates Avalon interconnects and can bridge to AXI4 via adapter IP.

---

## APB — ARM's Peripheral Bus

APB (Advanced Peripheral Bus) is the minimalist ARM bus for low-bandwidth peripherals (timers, GPIO, UART, I2C):

```
APB Write (2 cycles minimum):
PCLK    ┌─┐  ┌─┐  ┌─┐  ┌─┐
        ┘ └──┘ └──┘ └──┘ └──
PSEL    ────┐     ┌───────  (select slave)
PENABLE ────────┐     ┌───  (enable — second cycle)
PADDR   ────┐XXXXXXXXXXXXX  (address)
PWDATA  ────┐XXXXXXXXXXXXX  (write data)
PREADY  ────────────────┐  ┌── (slave ready)
PWRITE  ────┐           │  │  (high = write)
            └───────────┘  └──
            ↑  Setup phase  ↑ Access phase
```

APB is so simple it has no pipelining, no burst, and no flow control beyond PREADY. It's ideal for register-file access where throughput is irrelevant.

---

## AHB — The Middle Ground

AHB (Advanced High-performance Bus) sits between APB and AXI in complexity. It adds burst support and pipelining but keeps a single shared bus:

| AHB Feature | Description |
|---|---|
| **HREADY/HRESP** | Flow control and error response (OKAY, ERROR, RETRY, SPLIT) |
| **Burst types** | SINGLE, INCR, WRAP4/8/16 |
| **Protection** | HPORT for privilege/cacheable/bufferable attributes |
| **Bus matrix** | Multiple masters via arbitration (round-robin or fixed-priority) |

AHB is common on ARM Cortex-M SoCs and as the interconnect between APB peripherals and the AXI backbone. On FPGA SoCs, AHB appears as the internal bus for the HPS/PS peripheral subsystem.

---

## Choosing a Bus Protocol

```
┌─ Need >1 GB/s throughput? ─Yes──► AXI4-Full
│  No
├─ Only register access? ─┬─ Intel platform? ──► Avalon-MM
│                         └─ Xilinx/ARM? ──────► AXI4-Lite
│  No
├─ Open-source / LiteX? ──Yes──► Wishbone
│  No
├─ Streaming only (no addr)? ──► AXI4-Stream
│  No
└─ Slow MCU peripheral? ────────► APB
```

---

## Bridging Between Protocols

| From → To | How | Availability |
|---|---|---|
| AXI4 ↔ Avalon-MM | Intel Platform Designer adapter IP | Free (Quartus) |
| AXI4 ↔ Wishbone | LiteX bridge; open-source modules | Free (open source) |
| AXI4 ↔ APB | Xilinx AXI APB Bridge IP | Free (Vivado) |
| APB ↔ AHB | Standard AMBA bridge | Simple RTL, widely available |
| AXI4 ↔ AXI4-Lite | AXI Protocol Converter (Xilinx) | Free (Vivado) |

---

## Further Reading

| Article | Topic |
|---|---|
| [axi4_family.md](axi4_family.md) | AXI4-Full, AXI4-Lite, AXI4-Stream deep dive |
| [interconnect/](../interconnect/README.md) | AXI Interconnect — crossbar, QoS, conversion |
| Wishbone B4 Spec | https://opencores.org/howto/wishbone |
| Intel Avalon Interface Spec | https://www.intel.com/content/www/us/en/docs/programmable/683091 |
| AMBA APB/AHB Spec (ARM IHI 0011) | APB/AHB protocol specification |
