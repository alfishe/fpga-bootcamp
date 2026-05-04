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
| 16.1 | Dynamic Function eXchange (DFX) | `16_advanced_topics/dfx_partial_reconfiguration.md` | COMPLETE |
| 16.2 | Hardware Acceleration (ML, Blockchain, Custom Algorithms) | `16_advanced_topics/hardware_acceleration.md` | COMPLETE |
| 16.3 | Advanced Networking & SmartNICs (DPDK/TOE) | `16_advanced_topics/networking_smartnics.md` | COMPLETE |
| 16.4 | Hardware Security & Trust (Secure Boot/PUF) | `16_advanced_topics/hardware_security.md` | COMPLETE |
| 16.5 | Advanced HLS Patterns & Optimization | `16_advanced_topics/advanced_hls_patterns.md` | COMPLETE |
| 16.6 | FPGA as a Service (FaaS) & Cloud | `16_advanced_topics/fpga_as_a_service.md` | COMPLETE |
| 16.7 | Compute Comparison: FPGA vs GPU vs TPU | `16_advanced_topics/fpga_vs_gpu_vs_tpu.md` | COMPLETE |


---

## Phase 13: Toolchain Deep Dives (`13_toolchains/`)

| # | Task | File | Status |
|---|---|---|---|
| 13.1 | Vivado — full build flow, Tcl scripting, debug, IP packaging | `13_toolchains/vivado.md` | COMPLETE |
| 13.2 | Quartus Prime — build flow, Tcl scripting, Platform Designer | `13_toolchains/quartus_prime.md` | COMPLETE |

## Phase 04: HLS Expansion (`04_hdl_and_synthesis/hls/`)

| # | Task | File | Status |
|---|---|---|---|
| 4.1 | HLS Overview — pragmas, synthesis flow, code examples | `04_hdl_and_synthesis/hls/hls_overview.md` | COMPLETE |

## Phase 07: Verification Deep Dives (`07_verification/`)

| # | Task | File | Status |
|---|---|---|---|
| 7.1 | UVM for FPGA — class hierarchy, testbench example, build/run | `07_verification/uvm_overview.md` | COMPLETE |
| 7.2 | Formal Verification — AXI protocol proof, JasperGold, multi-tool | `07_verification/formal_verification.md` | COMPLETE |
| 7.3 | Cocotb — real testbench examples, Makefile, sim integration | `07_verification/cocotb.md` | COMPLETE |

## Phase 09: Board Design Expansion (`09_board_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 9.1 | Power Integrity — PDN tool walkthrough, multi-rail sequencing, simulation | `09_board_design/power_integrity.md` | COMPLETE |
| 9.2 | High-Speed Signals — SI simulation, eye diagrams, loss budgets | `09_board_design/high_speed_signals.md` | COMPLETE |

## Phase 11: SoC Design Expansion (`11_soft_cores_and_soc_design/soc_design/`)

| # | Task | File | Status |
|---|---|---|---|
| 11.1 | DMA Architecture — register maps, descriptor formats, Linux API | `11_soft_cores_and_soc_design/soc_design/dma_architecture.md` | COMPLETE |
| 11.2 | Multi-Core Coherency — ACP vs CCI vs ACE, cache stashing | `11_soft_cores_and_soc_design/soc_design/multi_core_coherency.md` | COMPLETE |
| 11.3 | Memory Map Design — address decoder patterns, AXI address filtering | `11_soft_cores_and_soc_design/soc_design/memory_map_design.md` | COMPLETE |
| 11.4 | Interrupt Routing — GIC, PLIC, NVIC, FPGA IRQ mapping | `11_soft_cores_and_soc_design/soc_design/interrupt_routing.md` | COMPLETE |

---

## Legend

| Symbol | Meaning |
|---|---|
| PENDING | File does not exist; not started |
| STUB | File exists — outline only, needs expansion |
| EXPAND | File exists with content (50–100 lines) — needs deeper coverage, code examples, verified references |
| IN PROGRESS | Currently writing / expanding |
| COMPLETE | Written with substantial content (50+ lines), reviewed |
| BLOCKED | Waiting on dependency |
