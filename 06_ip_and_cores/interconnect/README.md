[← Section Home](../README.md) · [← Project Home](../../README.md)

# 06-C — Interconnect & Infrastructure IP

The glue that connects masters to slaves. Deep dive into AXI interconnect design, including crossbar topologies, address decoding, QoS, and the converter IPs needed when clocks or data widths don't match.

## Index

| File | Topic |
|---|---|
| [axi_interconnect.md](axi_interconnect.md) | AXI Interconnect deep dive: crossbar vs shared bus, address decoding and routing, QoS arbitration (round-robin, weighted, fixed priority), deadlock avoidance, pipelining, AXI SmartConnect vs AXI Interconnect |
| [data_width_clock_conversion.md](data_width_clock_conversion.md) | AXI Data Width Converters, Clock Converters, Protocol Converters — when and why you need them, latency and throughput impact |
