[← Design Flow Home](README.md) · [← Project Home](../README.md)

# Incremental & Hierarchical Design — OOC Synthesis, Partitioning, and Team Flows

As FPGA designs grow beyond 100K LUTs, full-design synthesis and implementation times stretch from minutes to hours. A 500K-LUT UltraScale+ design can take 4–8 hours for a complete build. Incremental and hierarchical design techniques decompose the design into manageable partitions that can be synthesized, implemented, and verified independently — reducing build times, enabling team-based development, and improving design reuse. This article covers out-of-context (OOC) synthesis, hierarchical design flows, incremental implementation, and vendor-specific partitioning tools.

> [!NOTE]
> For the standard design flow (synthesis → implementation → bitstream), see [Overview](overview.md). This article covers the **partitioned** and **incremental** flows used for large designs.

---

## Overview: Why Partitioning Matters

| Design Size | Full Build Time | Problem | Partitioning Benefit |
|---|---|---|---|
| < 50K LUTs | 5–15 min | Manageable | Marginal benefit |
| 50–200K LUTs | 15–60 min | Annoying | OOC synthesis saves 30–50% |
| 200K–1M LUTs | 1–8 hours | Productivity killer | OOC + incremental saves 50–80% |
| > 1M LUTs | 8–24 hours | Requires overnight builds | Essential — team-based development |

---

## Out-of-Context (OOC) Synthesis

OOC synthesis processes each module independently, producing a synthesized netlist (EDIF/DCP) that is later combined at the top level. This allows:

- **Parallel synthesis** — each module synthesized simultaneously on different machines
- **Incremental re-synthesis** — only changed modules are re-synthesized
- **IP reuse** — pre-synthesized IP cores are not re-synthesized
- **Team isolation** — each team owns their module's synthesis

### Xilinx: OOC Flow in Vivado

```tcl
# Create OOC run for a module
create_run synth_module_a -flow {Vivado Synthesis 2024} -srcset [get_filesets sources_1]
set_property -dict [list \
  STRATEGY {Vivado Synthesis Defaults} \
  STEPS.SYNTH_DESIGN.ARGS.MODE {Out_Of_Context} \
] [get_runs synth_module_a]

# Synthesize module A independently
launch_runs synth_module_a -jobs 4
wait_on_run synth_module_a

# The output is a DCP (Design Checkpoint) that can be linked at top level
# module_a.dcp contains: synthesized netlist + constraints + utilization estimates
```

### Xilinx: Block-Level Container (Vivado 2023.2+)

Vivado 2023.2 introduced **Block-Level Containers** — a formalized OOC flow where each block is a self-contained unit with:

- Synthesized netlist (DCP)
- Local constraints (XDC)
- Interface definition (port list, clock domains)
- Utilization and timing estimates

```tcl
# Create block-level container
create_block_container -name module_a -type ooc
add_files_to_block -name module_a [list module_a.v module_a_pkg.sv]
synth_block -name module_a

# Link blocks at top level
link_blocks -names [list module_a module_b module_c]
```

### Intel: QDB (Quartus Database) Partitions

Intel Quartus provides partition-based incremental compilation through QDB files:

```tcl
# Create partition for a module
set_global_assignment -name PARTITION_HIERARCHY root_partition
set_instance_assignment -name PARTITION_HIERARCHY module_a -to u_module_a -section_id module_a

# Compile partition
execute_flow -compile

# Export partition as QDB
export_partition -partition module_a -file module_a.qdb

# In future builds, import unchanged partition instead of re-compiling
set_global_assignment -name QDB_FILE module_a.qdb -section_id module_a
```

---

## Incremental Implementation

Incremental implementation reuses the placement and routing from a previous build for unchanged modules, dramatically reducing implementation time.

### Xilinx: Incremental Implementation

```tcl
# Reference design: previous successful build
set_property incremental_checkpoint reference.dcp [get_runs impl_1]

# Only changed modules are re-implemented
# Unchanged modules reuse their previous placement and routing
launch_runs impl_1 -jobs 8
```

**Impact:**
- Build time reduction: 40–70% (depending on percentage of design that changed)
- Timing predictability: unchanged paths retain their timing from the reference build
- Best for: bug-fix iterations where < 20% of the design changed

### Intel: Fast Forward Incremental Compile

Quartus Pro provides incremental compilation through the `--incremental` flag:

```tcl
# Enable incremental compilation
set_global_assignment -name INCREMENTAL_COMPILATION ON

# After first build, subsequent builds reuse unchanged partitions
# Only modified partitions are re-compiled
quartus_fit --incremental my_project
```

---

## Hierarchical Design Rules

When partitioning a design, follow these rules to avoid integration failures:

### 1. Define Clean Interfaces

| Interface Type | Example | Rules |
|---|---|---|
| **AXI4** | CPU ↔ peripheral | Standard protocol — use AXI VIP for verification |
| **AXI4-Lite** | Register access | Simple — well-defined |
| **AXI4-Stream** | Data pipeline | No address — verify with protocol checker |
| **Custom parallel** | Module ↔ module | Must document: signal list, timing, protocol |

### 2. Clock Domain Boundaries

Each partition should belong to a single clock domain. If a partition spans two domains, the CDC logic must be at the boundary and well-documented.

### 3. Floorplanning Constraints

For large designs, assign each partition to a physical region (Pblock in Vivado) to prevent routing congestion:

```tcl
# Create Pblock for module A (UltraScale+)
create_pblock pblock_module_a
add_cells_to_pblock [get_pblocks pblock_module_a] [get_cells -hierarchical -filter {NAME =~ u_module_a/*}]
resize_pblock [get_pblocks pblock_module_a] -add {CLOCKREGION_X0Y0:CLOCKREGION_X1Y3}
```

### 4. Timing Budgets

Each partition must meet its local timing budget before integration. The top-level timing budget is allocated across partitions:

```
Top-level path: 10 ns (100 MHz)
  Module A internal: 8 ns
  Module B internal: 8 ns
  Inter-module routing: 2 ns (allocated for cross-partition paths)
```

---

## Team-Based Design Flow

### Directory Structure

```
project/
├── top/
│   └── top.v              # Top-level integration
├── modules/
│   ├── module_a/
│   │   ├── rtl/            # Module A RTL
│   │   ├── sim/            # Module A testbench
│   │   └── constr/         # Module A constraints
│   ├── module_b/
│   │   ├── rtl/
│   │   ├── sim/
│   │   └── constr/
│   └── module_c/
├── ip/                     # Shared IP cores
├── constr/                 # Top-level constraints
└── scripts/                # Build scripts
```

### CI/CD for Partitioned Designs

```yaml
# GitHub Actions: parallel synthesis of modules
jobs:
  synth_module_a:
    runs-on: self-hosted
    steps:
      - run: vivado -mode batch -source synth_module_a.tcl
  synth_module_b:
    runs-on: self-hosted
    steps:
      - run: vivado -mode batch -source synth_module_b.tcl
  link_and_impl:
    needs: [synth_module_a, synth_module_b]
    runs-on: self-hosted
    steps:
      - run: vivado -mode batch -source link_and_impl.tcl
```

---

## Common Pitfalls

### 1. Cross-Partition Timing Paths

**The problem:** A combinational path crosses from module A to module B. During OOC synthesis, neither module knows about the other's timing — the path is unconstrained.

**The fix:** Define interface timing constraints between partitions. Use `set_max_delay` for cross-partition paths:

```tcl
set_max_delay 5.0 -from [get_cells u_module_a/data_out_reg] \
                     -to   [get_cells u_module_b/data_in_reg]
```

### 2. Pblock Congestion

**The problem:** A Pblock is too small for the partition's logic. The placer cannot fit all LUTs, BRAMs, and DSPs within the assigned region.

**The fix:** Monitor utilization per Pblock. Target < 70% LUT utilization per region. Use the Vivado `report_utilization -hierarchical` command after synthesis.

### 3. Stale Reference Build

**The problem:** Incremental implementation uses a reference build from weeks ago. Logic changes have accumulated to the point where the reference placement is no longer a good starting point.

**The fix:** Regenerate the reference build periodically (e.g., weekly). Check that incremental build times are actually decreasing — if they plateau or increase, it's time for a fresh reference.

---

## References

| Source | Description |
|---|---|
| Xilinx UG905 — Vivado Design Methodology | Hierarchical design and OOC synthesis guidelines |
| Xilinx UG907 — Vivado Incremental Implementation | Reference-based implementation flow |
| Intel QUA-01040 — Quartus Pro Incremental Compilation | Partition-based compilation |
| [Project Structure](project_structure.md) | Directory layout for FPGA projects |
| [Floorplanning](floorplanning.md) | Physical region assignment for partitions |
| [Synthesis](synthesis.md) | Synthesis strategies and options |
| [CI/CD for Hardware](../13_toolchains/cicd_hardware.md) | Automation for partitioned builds |
