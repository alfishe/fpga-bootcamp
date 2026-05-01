# TODO.md — FPGA Knowledge Base Build Plan

> Auto-generated plan. Update statuses as work progresses. See [AGENTS.md](AGENTS.md) for quality standards.
> **Last synced:** 2026-04-25 — matched against actual filesystem content.

---

## Phase 6: IP & Cores (`06_ip_and_cores/`)

| # | Task | File | Status |
|---|---|---|---|
| 6.1 | Chip-to-chip interfaces (PCIe, CXL, CCIX, UCIe) | `06_ip_and_cores/external_interfaces/chip_to_chip_interfaces.md` | COMPLETE |
| 6.2 | Parallel buses (68000, Zorro, ISA, PCI) | `06_ip_and_cores/external_interfaces/parallel_buses.md` | COMPLETE |
| 6.3 | High-speed serial interfaces — USB soft IP and hardened | `06_ip_and_cores/external_interfaces/high_speed_serial_interfaces.md` | COMPLETE |

## Phase 8 Additions (`08_debug_and_tools/`)

| # | Task | File | Status |
|---|---|---|---|
| 8.7 | Commercial JTAG / Boundary scan tools | `08_debug_and_tools/commercial_jtag_tools.md` | COMPLETE |

## Phase 16: Advanced Applications (`16_advanced_topics/`)

| # | Task | File | Status |
|---|---|---|---|
| 16.1 | Dynamic Function eXchange (DFX) | `16_advanced_topics/dfx_partial_reconfiguration.md` | STUB |
| 16.2 | Hardware Acceleration (ML, Blockchain, Custom Algorithms) | `16_advanced_topics/hardware_acceleration.md` | COMPLETE |
| 16.3 | Advanced Networking & SmartNICs (DPDK/TOE) | `16_advanced_topics/networking_smartnics.md` | STUB |
| 16.4 | Hardware Security & Trust (Secure Boot/PUF) | `16_advanced_topics/hardware_security.md` | STUB |
| 16.5 | Advanced HLS Patterns & Optimization | `16_advanced_topics/advanced_hls_patterns.md` | COMPLETE |
| 16.6 | FPGA as a Service (FaaS) & Cloud | `16_advanced_topics/fpga_as_a_service.md` | COMPLETE |
| 16.7 | Compute Comparison: FPGA vs GPU vs TPU | `16_advanced_topics/fpga_vs_gpu_vs_tpu.md` | COMPLETE |


---

## Legend

| Symbol | Meaning |
|---|---|
| PENDING | File does not exist; not started |
| STUB | File exists — outline only, needs expansion |
| IN PROGRESS | Currently writing / expanding |
| COMPLETE | Written with substantial content (50+ lines), reviewed |
| BLOCKED | Waiting on dependency |
