[← Home](../README.md)

# 05 — Timing & Constraints

**Every FPGA design lives or dies by its constraints.** This section covers the SDC/XDC/QSF constraint syntax used across all vendors, clock domain crossing theory, false and multicycle path declarations, timing closure methodology, and IO timing for source-synchronous interfaces.

## Index

| File | Topic |
|---|---|
| [sdc_basics.md](sdc_basics.md) | SDC/XDC/QSF constraint syntax: create_clock, create_generated_clock, set_input_delay, set_output_delay |
| [clock_domain_crossing.md](clock_domain_crossing.md) | Metastability theory, MTBF calculation, synchronizer chains, gray-code FIFOs, handshake protocols |
| [false_paths.md](false_paths.md) | set_false_path, set_clock_groups (-asynchronous), async reset paths, static signals |
| [multicycle_paths.md](multicycle_paths.md) | set_multicycle_path: setup multiplier, hold adjustment, fractional cycles, common mistakes |
| [timing_closure.md](timing_closure.md) | Methodology: analyze slack, identify critical paths, fix strategies (pipelining, retiming, physical) |
| [io_timing.md](io_timing.md) | Source-synchronous interfaces, center vs edge-aligned capture, forwarded clocks, RGMII/SDR/DDR |
