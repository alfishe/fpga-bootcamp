# TODO.md — FPGA Knowledge Base Build Plan

> Auto-generated plan. Update statuses as work progresses. See [AGENTS.md](AGENTS.md) for quality standards.

---

## Phase 1: Architecture (`02_architecture/`)

| # | Task | File | Status |
|---|---|---|---|
| 1.1 | LUTs & CLBs across vendors | `02_architecture/fabric/luts_and_clbs.md` | ✅ COMPLETE |
| 1.2 | BRAM & URAM deep dive | `02_architecture/fabric/bram_and_uram.md` | ✅ COMPLETE |
| 1.3 | DSP slices (DSP48/DSP58) | `02_architecture/fabric/dsp_slices.md` | ✅ COMPLETE |
| 1.4 | Routing & interconnect | `02_architecture/fabric/routing.md` | ✅ COMPLETE |
| 1.5 | Clocking (PLL/MMCM/DCM) | `02_architecture/infrastructure/clocking.md` | ✅ COMPLETE |
| 1.6 | IO standards & SERDES | `02_architecture/infrastructure/io_standards.md` | ✅ COMPLETE |
| 1.7 | Configuration & bitstream | `02_architecture/infrastructure/configuration.md` | ✅ COMPLETE |

## Phase 2: Remaining Overview (`00_overview/`)

| # | Task | File | Status |
|---|---|---|---|
| 2.1 | FPGA market landscape | `00_overview/landscape.md` | ✅ COMPLETE |
| 2.2 | History of FPGA technology | `00_overview/history.md` | ✅ COMPLETE |
| 2.3 | Process technology nodes | `00_overview/technology_nodes.md` | ✅ COMPLETE |

## Phase 3: Design Flow (`03_design_flow/`)

| # | Task | File | Status |
|---|---|---|---|
| 3.1 | End-to-end flow overview | `03_design_flow/overview.md` | ✅ COMPLETE |
| 3.2 | Project structure & revision control | `03_design_flow/project_structure.md` | ✅ COMPLETE |
| 3.3 | Synthesis deep dive | `03_design_flow/synthesis.md` | ✅ COMPLETE |
| 3.4 | Place & route | `03_design_flow/place_and_route.md` | ✅ COMPLETE |
| 3.5 | Bitstream generation | `03_design_flow/bitstream.md` | ✅ COMPLETE |
| 3.6 | Floorplanning | `03_design_flow/floorplanning.md` | ✅ COMPLETE |
| 3.7 | Netlist formats & fundamentals | `03_design_flow/netlist.md` | ✅ COMPLETE |

## Phase 4: Cyclone V Anchor Deep Dive (`01_vendors_and_families/altera_intel/cyclone_v/`)

| # | Task | File | Status |
|---|---|---|---|
| 4.1 | HPS-FPGA address map | `cyclone_v/soc/address_map.md` | ⬜ PENDING |
| 4.2 | Boot sequence (ROM → Linux) | `cyclone_v/soc/boot_sequence.md` | ⬜ PENDING |
| 4.3 | Transceivers deep dive (GX/GT) | `cyclone_v/fpga_only/transceivers.md` | ⬜ PENDING |
| 4.4 | Cyclone V vs Zynq-7000 | `cyclone_v/vs_zynq7000.md` | ⬜ PENDING |
| 4.5 | MiSTer platform specifics | `cyclone_v/soc/mister_platform.md` | ⬜ PENDING |

## Legend

| Symbol | Meaning |
|---|---|
| ⬜ PENDING | Not started |
| 🔄 IN PROGRESS | Currently writing |
| ✅ COMPLETE | Written, reviewed |
| ⏸️ BLOCKED | Waiting on dependency |
