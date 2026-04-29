[← 11 Soft Cores And Soc Design Home](../README.md) · [← Soc Design Home](README.md) · [← Project Home](../../../README.md)

# Bus Matrix Design — Topology Patterns for FPGA SoCs

Designing the interconnect fabric is the single most consequential architectural decision in an FPGA SoC — it determines bandwidth, latency, and how many masters can talk to how many slaves simultaneously.

---

## Topology Comparison

| Topology | Max Concurrent Transactions | Latency | LUT Cost | Best For |
|---|---|---|---|---|
| **Shared Bus** (ARM AMBA AHB) | 1 (one master at a time) | Low | ~500 LUTs | Simple microcontrollers, \u003c4 masters |
| **Full Crossbar** (ARM NIC-301) | N (all masters concurrently to different slaves) | Medium | ~2,000–8,000 LUTs | SoCs with 4–10 masters |
| **Multi-Layer** (Xilinx AXI Interconnect) | Varies (configurable per slave) | Medium | ~1,500–5,000 LUTs | Mixed bandwidth requirements |
| **Network-on-Chip** (Versal NoC, TileLink) | Very high | Higher per-hop | 10,000+ LUTs | Manycore, large SoCs |

## Key Design Decisions

| Decision | Options | Trade-Off |
|---|---|---|
| **Shared vs dedicated slave ports** | Each slave gets own port vs slaves share one | Bandwidth vs area |
| **Address decoding** | Central decoder vs distributed decode | Latency vs flexibility |
| **Burst support** | Full AXI bursts vs single-beat only | Bandwidth efficiency vs complexity |
| **QoS** | Round-robin vs priority vs weighted | Fairness vs determinism |
| **APB bridge for low-speed** | AXI→APB bridge for GPIO, I²C, UART | Simplifies slave design, saves AXI licensing |

## Practical FPGA SoC Example

```
CPU (VexRiscv) ──► AXI Crossbar ──┬──► DDR Ctrl (high BW)
DMA Engine     ──►       │        ├──► Ethernet MAC
Ethernet RX    ──►       │        ├──► Frame Buffer (BRAM)
                          │        └──► APB Bridge → GPIO, UART, I²C
                          │
                   (3 concurrent:
                    CPU reads DDR,
                    DMA streams Eth→DDR,
                    Ethernet RX writes BRAM)
```

For deep dive on AXI bridge specifics, see [02_architecture/soc/axi_bridges_and_interconnect.md](../../../02_architecture/soc/axi_bridges_and_interconnect.md).

---

## Original Stub Description

Bus matrix design: topology patterns (shared bus, crossbar, multi-layer), master/slave classification, address decoding, concurrent access and bandwidth analysis, APB/AHB bridge for low-speed peripherals

## Planned Content

- Detailed technical coverage to be added.
- Cross-references and examples to be expanded.

## Referenced By

- [README.md](../../README.md)
- [README.md](README.md)
