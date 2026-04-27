[← Home](../README.md) · [03 — Design Flow](README.md)

# Floorplanning — Manual Placement for Timing and Routability

Floorplanning is the art of telling the placer where to put logic — before it makes the wrong choice and the router fails. This article covers pblock constraints (Xilinx), LogicLock regions (Intel), and floorplanning strategies for timing closure, congestion relief, and partial reconfiguration.

---

## Overview

Floorplanning constrains logic to specific physical regions of the FPGA die. You need floorplanning when the auto-placer spreads critical logic across the die (causing routing delay failures), packs too much logic into one area (causing congestion), or places logic in resource-incompatible sites. Floorplanning is not about optimizing every LUT — it's about identifying the 2–3 contentious regions in your design and giving the placer the constraints it needs to succeed. Over-constraining (pblocks everywhere) is worse than no floorplanning at all — it handcuffs the placer and creates artificial congestion.

---

## When Floorplanning Is Necessary

| Symptom | Root Cause | Floorplanning Fix |
|---|---|---|
| Long routes on critical paths (>50% of die) | Placer scattered critical primitives | Constrain critical path modules to adjacent pblocks |
| Congestion "hotspots" in one quadrant | Placer packed too many LUTs into one area | Distribute logic evenly with pblock utilization targets |
| IO timing failures | Logic placed far from IO banks | Constrain IO-adjacent logic to pblocks near the bank |
| DSP column saturation | All DSP modules placed in one column | Split DSP instantiation across pblocks in different columns |
| SLR crossing penalty (>1 ns) | Critical path crosses SLR boundary | Constrain each side of the SLR to separate pblocks; add pipeline register at boundary |
| Partial reconfiguration | Need to isolate a module for runtime swap | Define a reconfigurable partition pblock |

---

## Xilinx: pblock Constraints

### Basic pblock

```tcl
# Create a pblock for the DSP core
create_pblock pblock_dsp
add_cells_to_pblock pblock_dsp [get_cells dsp_top/*]
resize_pblock pblock_dsp -add {SLICE_X20Y50:SLICE_X40Y100 DSP48_X2Y5:DSP48_X4Y15 RAMB18_X2Y5:RAMB18_X4Y15}

# Set utilization target (percentage of sites)
set_property CONTAIN_ROUTING true [get_pblocks pblock_dsp]
set_property UTILIZATION 70 [get_pblocks pblock_dsp]
```

### pblock for IO-Bound Logic

```tcl
# Constrain logic driving IO bank 34 to pblock near bank 34
create_pblock pblock_io34
add_cells_to_pblock pblock_io34 [get_cells io_interface_34/*]
resize_pblock pblock_io34 -add {SLICE_X0Y0:SLICE_X20Y50}  # Bank 34 is in bottom-left quadrant
```

### pblock for SLR Crossing (UltraScale+ SSI)

```tcl
# Two pblocks, one per SLR, with pipeline register at boundary
create_pblock pblock_slr0
add_cells_to_pblock pblock_slr0 [get_cells pipeline_stage_0/*]
resize_pblock pblock_slr0 -add {SLR0}

create_pblock pblock_slr1
add_cells_to_pblock pblock_slr1 [get_cells pipeline_stage_1/*]
resize_pblock pblock_slr1 -add {SLR1}

# Pipeline register between stages sits at SLR boundary
# Router uses dedicated SLR-crossing wires (Laguna)
```

---

## Intel: LogicLock Regions

```tcl
# Create LogicLock region
set_global_assignment -name LL_ENABLED ON -section_id ll_dsp
set_global_assignment -name LL_WIDTH 21 -section_id ll_dsp    # in LAB columns
set_global_assignment -name LL_HEIGHT 25 -section_id ll_dsp   # in LAB rows
set_global_assignment -name LL_ORIGIN MCELL_X20_Y50 -section_id ll_dsp
set_global_assignment -name LL_MEMBER_OF "dsp_core" -section_id ll_dsp

# Reserve the region (prevent other logic from using it)
set_global_assignment -name LL_AUTO_SIZE OFF -section_id ll_dsp
set_global_assignment -name LL_STATE LOCKED -section_id ll_dsp
```

---

## Floorplanning Strategies

### 1. Dataflow-Oriented Floorplanning

Match the dataflow of your pipeline to the physical layout:

```
┌─ pblock_input ──┬── pblock_proc ──┬── pblock_output ──┐
│  Input FIFOs    │  Processing     │  Output formatting │
│  (near IO bank) │  (center die)   │  (near other IO)   │
└─────────────────┴─────────────────┴────────────────────┘
         ↑ Data flows left to right (aligned with die routing) ↑
```

**Why it works:** Horizontal routing resources on FPGAs are more abundant than vertical. Aligning dataflow left-to-right minimizes long diagonal routes.

### 2. Resource-Aware Floorplanning

Consider which resources each module needs:

| Module Needs | Constrain Near |
|---|---|
| DSP-heavy | DSP columns. Spread across 2+ columns |
| BRAM-heavy | BRAM columns. Pair with adjacent DSP columns if DSP+BRAM interact |
| IO-bound | IO bank of the target pins |
| PCIe / transceiver | Transceiver quad location |
| Clock-domain-specific | Clock region of the driving BUFG/BUFR |

### 3. Utilization-Bounded Floorplanning

Each pblock should have a utilization target:

| pblock Type | Max Utilization | Why |
|---|---|---|
| **General logic** | 70% | Leaves 30% for routing slack |
| **DSP column** | 85% | DSP sites are fixed; routing is the bottleneck |
| **BRAM column** | 80% | BRAMs have dedicated routing; fabric access routes can congest |
| **SLR boundary** | 60% | SLR crossing adds ~1 ns; lower utilization reduces detour need |

---

## Best Practices & Antipatterns

### Best Practices
1. **Floorplan only the problem children** — If 90% of your design routes fine, only floorplan the 10% causing congestion/timing failures. Over-floorplanning is counterproductive
2. **Use `CONTAIN_ROUTING true` sparingly** — It prevents the router from using resources outside the pblock for nets inside. This can help timing but increases congestion inside the pblock
3. **Iterate: floorplan → P&R → check congestion → adjust** — Floorplanning is experimental. Start loose, tighten only where needed
4. **Verify pblock resource counts** — Vivado/Quartus tell you how many SLICEs/DSPs/BRAMs are in a pblock. If your design uses more, the placer cannot meet the constraint

### Antipatterns

| Antipattern | The Problem | The Fix |
|---|---|---|
| **"The Grid Lock"** | Floorplanning every module into its own pblock | The placer has zero flexibility. P&R runs forever or fails. Only constrain the critical 2–3 modules |
| **"The Too-Small pblock"** | Creating a pblock with exactly the number of sites needed | Zero slack for placement optimization. Use at least 1.2× the required resources |
| **"The SLR Ignorer"** | Ignoring SLR boundaries in a multi-die UltraScale+ design | Cross-SLR routes cost ~1 ns. Floorplan to minimize SLR crossings; add pipeline stages at boundaries |
| **"The Floating pblock"** | Creating a pblock with no fixed location | The tool can't resolve conflicting pblocks. Always specify an ORIGIN or GRID_RANGE |

---

## Pitfalls & Common Mistakes

### 1. pblock Overprovisioning Causing False Congestion

**The mistake:** Creating a pblock that contains 500 Slice LUT sites for a module using 400 LUTs, but the pblock straddles a clock region boundary.

**Why it fails:** The placer uses sites in both clock regions. Routing between them requires clock-region-crossing buffers, creating congestion that wouldn't exist if the pblock was confined to one clock region.

**The fix:** Align pblock boundaries to clock regions, DSP columns, and BRAM columns. Use the device view to see resource boundaries.

### 2. Forgetting BRAM/DSP in pblock Specs

**The mistake:** `resize_pblock pblock_dsp -add {SLICE_X20Y50:SLICE_X40Y100}` — no DSP or BRAM site ranges included.

**Why it fails:** The DSP module needs DSP sites. Without DSP ranges in the pblock, the placer may put DSPs outside the pblock, creating long routes between LUTs and DSPs.

**The fix:** Always include all resource type ranges: `-add {SLICE_X20Y50:SLICE_X40Y100 DSP48_X2Y5:DSP48_X4Y15 RAMB18_X2Y5:RAMB18_X4Y15}`.

---

## References

| Source | Document |
|---|---|
| Vivado UG904 — Implementation (Floorplanning) | https://docs.xilinx.com/ |
| Intel Quartus Prime Incremental Compilation | Intel FPGA Documentation |
| [Place & Route](place_and_route.md) | How the placer uses your constraints |
| [Bitstream](bitstream.md) | Partial reconfiguration floorplanning |
| [Routing Architecture](../02_architecture/fabric/routing.md) | Why alignment to routing resources matters |
