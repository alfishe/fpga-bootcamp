[← Section Home](../README.md) · [← Project Home](../../README.md)

# 06-A — Bus & Interconnect Protocols

Everything in an FPGA connects through a bus. This folder covers the three protocol families you'll actually encounter: AXI4 (the industry standard), Wishbone (the open-source standard), and Avalon/APB/AHB (vendor-specific and legacy buses).

## Index

| File | Topic |
|---|---|
| [axi4_family.md](axi4_family.md) | **AXI4 / AXI4-Lite / AXI4-Stream** — AMBA 4 in practice: 5 channels, VALID/READY handshake, burst (FIXED/INCR/WRAP), ordering, ID threading, register slices |
| [other_buses.md](other_buses.md) | **Wishbone** (classic vs pipelined), **Avalon** (MM + ST), **APB/AHB** (AMBA 3) — comparison matrix: throughput, complexity, openness, where each dominates |
