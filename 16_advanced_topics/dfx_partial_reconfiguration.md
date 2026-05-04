[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Dynamic Function eXchange (DFX) / Partial Reconfiguration

This article covers how to hot-swap bitstream regions at runtime without halting the rest of the FPGA fabric — the most architecturally complex feature in modern FPGA design flows.

> **Prerequisites:** This article builds on [configuration.md](../02_architecture/infrastructure/configuration.md) (configuration modes), [bitstream.md](../03_design_flow/bitstream.md) (bitstream format and partial reconfiguration overview), and [floorplanning.md](../03_design_flow/floorplanning.md) (pblock constraints). For the Linux side, see [device_tree_and_overlays.md](../10_embedded_linux/04_drivers_and_dma/device_tree_and_overlays.md).

---

## 1. What Is DFX and Why It Matters

Dynamic Function eXchange (DFX) — also called **Partial Reconfiguration (PR)** — allows you to modify a defined region of the FPGA fabric while the rest of the design continues operating uninterrupted. Only the configuration frames belonging to the reconfigurable partition are overwritten.

### Use Cases

| Use Case | Example |
|---|---|
| **Algorithm switching** | Swap between AES-256 and ChaCha20 encryption engines without resetting the datapath |
| **In-field updates** | Patch a bug in one module without a full FPGA reconfiguration cycle |
| **Resource time-sharing** | Load accelerator A, process, then swap to accelerator B — effectively doubling available LUTs |
| **Multi-tenant cloud** | Each VM gets a different FPGA accelerator loaded into its own partition |
| **Military/SDR** | Switch modulation schemes (QPSK ↔ 16-QAM) on the same radio hardware |

### Vendor Support

| Vendor | PR Support | Minimum Family | Interface | Notes |
|---|---|---|---|---|
| **Xilinx** | Yes | 7-series and later | ICAP / PCAP / ICAPE2 | Most mature PR ecosystem. DFX flow in Vivado. |
| **Intel** | Yes | Arria 10, Stratix 10, Agilex | PR IP (internal or JTAG) | **Not on Cyclone V / MAX 10**. Requires paid PR license. |
| **Lattice** | No | — | — | No fabric PR. "Dynamic reconfiguration" only reconfigures PLL/transceiver settings via LMMI/APB, not logic. Dual-boot for full-image swap. |
| **Gowin** | No | — | — | Not supported. |
| **Microchip** | No | — | — | Flash-based fabric; no runtime partial reconfiguration. |
| **Efinix** | No | — | — | Not supported. |

> **Bottom line:** DFX is a premium feature available only on Xilinx (7-series+) and Intel (Arria 10+). For all other vendors, use multi-boot (full bitstream swap) instead.

---

## 2. Core Concepts

### 2.1 Static Region vs Reconfigurable Partition

```
┌──────────────────────────────────────────────────┐
│                 Static Region                    │
│  (always running, never reconfigured)            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │   Clock Gen  │  │  AXI Inter-  │              │
│  │   (PLL/MMCM) │  │  connect     │              │
│  └──────────────┘  └──────┬───────┘              │
│                           │                      │
│  ┌────────────────────────▼───────────────────┐  │
│  │    Reconfigurable Partition (RP)           │  │
│  │                                            │  │
│  │  Module A: FFT accelerator                 │  │  ← Swap at runtime
│  │  Module B: FIR filter bank                 │  │
│  │  Module C: Crypto engine                   │  │
│  │                                            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐              │
│  │  DDR Ctrl    │  │  PCIe DMA    │              │
│  └──────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────┘
```

**Static Region:** Contains clocks, resets, infrastructure IPs (AXI interconnect, DDR controller, PCIe), and any logic that must remain running during reconfiguration. Never reconfigured.

**Reconfigurable Partition (RP):** A bounded rectangular region of the FPGA floorplan. Multiple **Reconfigurable Modules (RMs)** can be loaded into the same RP at different times. Only one RM is active at a time.

**Key rule:** All RMs for a given RP must have **identical interface signals** (same port names, widths, directions). The static region connects to the RP through these fixed interfaces.

### 2.2 Partial Bitstream Format

A partial bitstream contains **only the configuration frames for the reconfigurable partition** — typically 1–5 MB (vs 20–50 MB for a full bitstream). It includes:

```
┌── Partial Bitstream ──┐
│ Sync word             │
│ Partial device ID     │
│ Frame data (RP only)  │  ← Only columns within the pblock
│ CRC checksum          │
│ NO startup sequence   │  ← Partial bitstreams skip GSR/DCI release
└───────────────────────┘
```

Loading a partial bitstream does **not** trigger a global reset. Only the RP's LUTs, routing, and BRAM contents change. The rest of the fabric continues executing.

---

## 3. Configuration Ports

### 3.1 ICAP (Internal Configuration Access Port)

ICAP is a **fabric-visible** primitive that allows user logic to write partial bitstreams into the configuration engine from inside the FPGA.

| Primitive | Family | Data Width | Max Bandwidth |
|---|---|---|---|
| `ICAPE2` | 7-series | 16/32-bit | ~400 MB/s (32-bit @ 100 MHz) |
| `ICAPE3` | UltraScale/UltraScale+ | 32-bit | ~950 MB/s (32-bit @ 300 MHz) |

```verilog
// ICAPE2 instantiation (7-series)
ICAPE2 #(
    .ICAP_WIDTH("X32")
) icap_inst (
    .CLK    (clk_100mhz),
    .CSIB   (~icap_cs),
    .RDWRB  (~icap_write),  // 0 = write
    .DI     (icap_data_in),
    .DO     ()               // Readback (rarely used for PR)
);
```

**Typical ICAP load time:** A 2 MB partial bitstream at 32-bit × 100 MHz ≈ 0.5 ms.

### 3.2 PCAP (Processor Configuration Access Port) — Zynq

On Zynq SoCs, the ARM Cortex-A processors configure the FPGA through PCAP. This is the **highest-bandwidth** option:

| Mode | Bandwidth | Typical Use |
|---|---|---|
| PCAP DMA mode | ~400 MB/s | Full and partial bitstream loading from DDR |
| PCAP register mode | ~50 MB/s | Small configuration register writes |

```c
// Zynq PCAP loading from Linux userspace
#include <fcntl.h>
#include <unistd.h>

void load_partial_bitstream(const char *path) {
    int fd = open("/sys/class/fpga_manager/fpga0/firmware", O_WRONLY);
    write(fd, path, strlen(path));  // Kernel reads from /lib/firmware/
    close(fd);
}
```

### 3.3 Intel PR IP

Intel Arria 10/Stratix 10/Agilex use a dedicated **PR IP core** that accepts partial bitstreams via:
- **Avalon-MM slave interface** — CPU writes partial bitstream data into the PR IP
- **AXI slave interface** — Same concept, AXI variant
- **JTAG** — External host loads partial bitstream via JTAG

The PR IP handles the handshaking with the FPGA configuration controller internally.

---

## 4. Xilinx DFX Flow (Vivado Tcl)

### 4.1 Design Flow Overview

```
┌─ Define RP ─┐    ┌─ OOC Synth ─┐   ┌─ Implement ─┐    ┌─ Gen Bits ─┐
│ Add PR XML  │──▶│ synth_top   |──▶│ parent run  │──▶│ full.bit   │
│ pblock      │    │ synth_rm_a  │   │ child_a run │    │ rm_a_p.bit │
│ constraints │    │ synth_rm_b  │   │ child_b run │    │ rm_b_p.bit │
└─────────────┘    └─────────────┘   └─────────────┘    └────────────┘
```

**Out-of-Context (OOC) Synthesis:** Each RM is synthesized independently, knowing only the interface signals to the static region. This allows adding new RMs later without re-synthesizing the static region.

### 4.2 Step-by-Step Tcl Workflow

```tcl
# ── Step 1: Create project and add sources ──
create_project my_dfx ./build -part xc7z020clg400-1
add_files {top.sv static_infra.sv}
add_files -fileset sources_1 {rm_fft.sv rm_fir.sv rm_crypto.sv}

# ── Step 2: Define the reconfigurable partition ──
# Mark the RP module for out-of-context synthesis
set_property PR_FLOW_GROUP rm_group [get_files rm_fft.sv]
set_property PR_FLOW_GROUP rm_group [get_files rm_fir.sv]
set_property PR_FLOW_GROUP rm_group [get_files rm_crypto.sv]

# Tell Vivado which module instance is the RP
set_property HD.RECONFIGURABLE TRUE [get_cells inst_rp]

# ── Step 3: Floorplan the RP with pblock ──
create_pblock pblock_inst_rp
add_cells_to_pblock [get_pblocks pblock_inst_rp] [get_cells inst_rp]
resize_pblock [get_pblocks pblock_inst_rp] \
    -add {SLICE_X50Y100:SLICE_X80Y200} \
    -add {DSP48_X2Y40:DSP48_X4Y80} \
    -add {RAMB18_X2Y40:RAMB18_X4Y80} \
    -add {RAMB36_X2Y20:RAMB36_X4Y40}

# ── Step 4: Run OOC synthesis for each RM ──
# Vivado automatically creates OOC runs for PR_FLOW_GROUP modules
launch_runs synth_1 -jobs 4
wait_on_run synth_1

# ── Step 5: Implement parent run (static + RM_A) ──
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

# ── Step 6: Implement child runs (RM_B, RM_C) ──
# These reuse the static routing from impl_1
create_run child_rm_b -parent_run impl_1 -pr_config rm_b_config
set_property PR_CONFIG rm_b_config [get_runs child_rm_b]
launch_runs child_rm_b -to_step write_bitstream
wait_on_run child_rm_b

# ── Step 7: Generate bitstreams ──
# Full bitstream (static + RM_A)
write_bitstream -force ./build/top_full.bit

# Partial bitstreams (RP only)
write_bitstream -force -cell inst_rp ./build/rm_fft_partial.bit
write_bitstream -force -cell inst_rp ./build/rm_fir_partial.bit
write_bitstream -force -cell inst_rp ./build/rm_crypto_partial.bit

# ── Step 8: Generate clear bitstream (blanking) ──
# Required to safely remove an RM without loading a new one
write_bitstream -force -cell inst_rp ./build/rm_blank_partial.bit
```

### 4.3 PR Configuration File

Vivado requires an XML file defining the partition and its modules:

```xml
<!-- pr_config.xml -->
<partial_reconfiguration>
  <reconfig_module name="rm_fft"   file="rm_fft_synth.dcp"/>
  <reconfig_module name="rm_fir"   file="rm_fir_synth.dcp"/>
  <reconfig_module name="rm_crypto" file="rm_crypto_synth.dcp"/>
</partial_reconfiguration>
```

### 4.4 Vivado GUI Flow (Alternative)

For those who prefer the GUI:
1. **Tools → Set Up Debug** → Ensure no ILA probes cross partition boundaries
2. **Tools → Enable Partial Reconfiguration** → Launches the PR wizard
3. The wizard creates the OOC runs, pblock constraints, and implementation runs automatically

---

## 5. Intel Partial Reconfiguration Flow

### 5.1 Overview

Intel's PR flow is **revision-based** rather than run-based. Each RM is a separate Quartus revision:

```
┌─ Base Revision ─────────────┐
│  Static region + RM_A       │  ← "base" revision
│  (compiles everything)      │
└─────────────────────────────┘
         │
         ▼  Exported static region
┌─ PR Revision ──────────────┐
│  RM_B only (OOC)           │  ← "rm_b" revision
│  (only RP re-synthesized)  │
└────────────────────────────┘
```

### 5.2 Step-by-Step Quartus PR Flow

```tcl
# ── Step 1: Assign PR partition in QSF ──
set_global_assignment -name PARTIAL_RECONFIGURATION ON
set_global_assignment -name RECONFIGURABLE_PARTITION_PARTITION_NAME rp_region
set_instance_assignment -name PARTITION rp_region -to inst_rp

# ── Step 2: Compile base revision (static + RM_A) ──
execute_flow -compile

# ── Step 3: Export static region ──
# Quartus generates the static region .qdb file
# File → Create/Update → Export Design Partition → static_region.qdb

# ── Step 4: Create PR revision for RM_B ──
project_new -revision rm_b my_design
set_global_assignment -name RECONFIGURABLE_PARTITION_PARTITION_NAME rp_region
set_global_assignment -name BASE_REVISION base_revision
# Import static_region.qdb for the static partition
set_instance_assignment -name QDB_FILE static_region.qdb -to | -section_id Top

# ── Step 5: Compile PR revision ──
execute_flow -compile
# Output: rm_b.rbf (partial bitstream)
```

### 5.3 Intel PR IP Integration

The PR IP core must be instantiated in the static region to accept partial bitstreams at runtime:

```
┌─────────── Static Region ─────────────│─┐
│                                         │
│  ┌──────┐    ┌────────┐     ┌────────┐  │
│  │ ARM  │───▶│ PR IP  │───▶│ Config │  │
│  │ CPU  │    │ (Avalon)│    │ Engine │  │
│  └──────┘    └────────┘     └────────┘  │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Reconfigurable Partition        │   │
│  │  (PR IP controls this region)    │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

The PR IP supports two interface variants:

| Interface | Usage | Notes |
|---|---|---|
| **Avalon-MM slave** | HPS Nios II / ARM writes PR data | Default on Arria 10 SoC |
| **AXI4-Lite slave** | ARM Cortex-A writes PR data via HPS bridge | Preferred on Agilex 7 SoC |
| **JTAG** | External host via USB-Blaster | Development only |

### 5.4 SUPR — Static Update Partial Reconfiguration

Intel (unlike Xilinx) supports **SUPR**: updating the static region while keeping reconfigurable partitions running. This is critical for:

- Patching a bug in the AXI interconnect without re-loading all RMs
- Updating clock infrastructure without a full reconfiguration cycle
- Fixing timing violations in the static region in the field

**SUPR flow:**
1. Export each RM's current configuration as a `.qdb` file
2. Modify the static region design
3. Re-import the unchanged RM `.qdb` files
4. Re-compile only the static region
5. Generate a SUPR bitstream that updates static + preserves RP state

> **Caveat:** SUPR requires all RMs to be re-verified against the new static region. The interface signals between static and RP must not change.

### 5.5 Hierarchical PR (Intel)

Intel Arria 10, Stratix 10, and Agilex support **hierarchical partial reconfiguration** — nested partitions within partitions:

```
┌──────────────────────────────────────────┐
│  Static Region                           │
│  ┌── RP_Level0 ─────────────────────┐    │
│  │  ┌── RP_Level1_A ──┐  Static_RP0 │    │
│  │  │  RM_1A          │             │    │
│  │  └─────────────────┘             │    │
│  │  ┌── RP_Level1_B ──┐             │    │
│  │  │  RM_1B          │             │    │
│  │  └─────────────────┘             │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

This allows independent reconfiguration of sub-partitions without affecting sibling partitions or the parent RP.

**Xilinx equivalent:** UltraScale+ supports nested PR through `HD.RECONFIGURABLE` on hierarchical instances, but the flow is less automated than Intel's.

### 5.6 Intel PR on Agilex 7 SoC

On Agilex 7 SoC FPGAs, the HPS (ARM Cortex-A53/A55) can initiate PR directly:

```c
// Agilex 7 SoC — HPS-driven PR via PR IP
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

void agilex_pr_load(const char *rbf_path) {
    // Write partial bitstream path to FPGA manager
    int fd = open("/sys/class/fpga_manager/fpga0/firmware", O_WRONLY);
    write(fd, rbf_path, strlen(rbf_path));
    close(fd);
}
```

The Agilex 7 PR IP also supports **cold start PR** — loading an RM before the FPGA enters user mode, allowing the system to boot with a specific RM pre-loaded.

### 5.7 SignalTap with PR

SignalTap II can be used inside reconfigurable partitions on Intel FPGAs:
1. Add SignalTap instance to the RM (not the static region)
2. Each RM can have its own SignalTap configuration
3. After swapping RMs, use **JTAG Chain → Add Device** in SignalTap to re-detect the new tap
4. Altera provides a dedicated [Signal Tap Tutorial for Agilex 7 PR](https://docs.altera.com/r/docs/710463/current)

---

## 6. Decoupling Logic — Preventing Bus Hangs

### 6.1 The Problem

When a partial bitstream is being loaded, the RP's outputs are **undefined** — they may glitch, float, or drive random values. If the static region's AXI interconnect is connected to the RP, a glitch on `AXI_AWREADY` or `AXI_BVALID` can cause:

- **AXI bus deadlock** — master waits forever for a response that never comes
- **Data corruption** — garbage values written to DDR or peripheral registers
- **System crash** — AXI protocol violation triggers an interconnect error

### 6.2 The Solution: Decoupler IP

A **decoupler** sits between the static region and the RP. During reconfiguration, it:
1. **Disconnects** the RP from the bus (drives safe idle values to the static side)
2. **Holds** the RP-side signals in a known state
3. **Reconnects** after reconfiguration is complete

```
Static Region                          RP
┌──────────┐     ┌──────────┐     ┌──────────┐
│  AXI     │◀──▶│  AXI     │◀──▶│  RM      │
│  Inter-  │     │ Decoupler│     │  Module  │
│  connect │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘
                      ▲
                      │
                 decouple_signal
                 (from ICAP/PR IP)
```

**Xilinx:** `AXI Decoupler` IP (ug1085). Supports AXI4, AXI4-Lite, and AXI4-Stream.

**Intel:** Built into the PR IP. The PR IP automatically decouples the PR region during reconfiguration.

### 6.3 Handshake Protocol

```
           ┌───── Decouple ─────┐
           │                    │
───────────┤                    ├────────────
  Normal   │  Reconfiguration   │  Normal
  Operation│  (RP outputs = X)  │  Operation
           │                    │
           ▼                    ▼
      decouple = 1         decouple = 0
      (safe idle on        (RM drives
       static side)         bus again)
```

**Critical timing:** The decoupler must assert **before** partial bitstream loading begins, and deassert **after** the RP is fully configured. The ICAP/PR IP typically provides a status signal for this sequencing.

### 6.4 What Happens Without Decoupling

| Symptom | Root Cause | Fix |
|---|---|---|
| AXI read returns `0xDEADBEEF` | RP BRAM uninitialized during reconfig | Add decoupler + initialization logic in RM |
| System hangs after PR load | AXI bus deadlock from glitched handshake | Add decoupler (non-optional!) |
| Intermittent crashes | Race between RP startup and first AXI transaction | Add decoupler + startup delay |
| ILA shows corrupt data | RP outputs glitched during frame writes | Add decoupler + hold static-side signals |

---

## 7. Floorplanning for DFX

### 7.1 pblock Rules

The `pblock` constraint defines the physical boundaries of the reconfigurable partition:

```tcl
create_pblock pblock_rp
add_cells_to_pblock pblock_rp [get_cells inst_rp]
resize_pblock pblock_rp -add {SLICE_X50Y100:SLICE_X80Y200}
resize_pblock pblock_rp -add {DSP48_X2Y40:DSP48_X4Y80}
resize_pblock pblock_rp -add {RAMB18_X2Y40:RAMB18_X4Y80}
```

**Rules:**
1. The pblock must be a **contiguous rectangle** of resources
2. All RMs for the same RP must fit within the same pblock
3. The pblock cannot overlap with static region resources
4. Clock routing and global signals must remain in the static region

### 7.2 Resource Reservation

Use `SNAP_TO_SITE` to prevent the router from placing static logic in the RP area:

```tcl
set_property SNAPPING_MODE ON [get_pblocks pblock_rp]
set_property EXCLUDE_PLACEMENT 1 [get_pblocks pblock_rp]
```

### 7.3 Routing Channel Considerations

Reconfigurable partitions need extra routing margin because the router must create identical routing channels for all RMs:

| Family | Recommended Routing Margin | Setting |
|---|---|---|
| 7-series | 5–10% extra routing | `set_property ROUTING_MARGIN 10 [get_pblocks pblock_rp]` |
| UltraScale+ | Automatic (directed routing) | `set_property DIRECTED_ROUTE_BUFFER 2 [get_pblocks pblock_rp]` |

### 7.4 Common Floorplanning Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| RP too small for largest RM | Implementation fails for that RM | Size pblock for the **largest** RM |
| RP splits a clock region | DRC error — PR boundaries must align to clock region edges | Align pblock to clock region boundaries |
| DSP/BRAM not included in pblock | RM's DSP/BRAM placed in static region → DRC error | Add `DSP48` and `RAMB18/36` to pblock |
| Overlapping pblocks | DRC error — pblocks must not overlap | Ensure pblocks are disjoint |

---

## 8. Linux FPGA Manager for Partial Reconfiguration

> For a broader introduction to FPGA Manager, see [device_tree_and_overlays.md](../10_embedded_linux/04_drivers_and_dma/device_tree_and_overlays.md).

### 8.1 FPGA Region for Partial Reconfiguration

The Linux kernel supports partial reconfiguration through the `fpga-region` device tree binding. Each reconfigurable partition is described as a separate FPGA region:

```dts
// Base device tree — describes the static region
/ {
    fpga_region0: fpga-region-0 {
        compatible = "fpga-region";
        fpga-mgr = <&pcap>;
        #address-cells = <1>;
        #size-cells = <1>;
        ranges;

        // Reconfigurable partition as a sub-region
        fpga_region1: fpga-region-1 {
            compatible = "fpga-region";
            fpga-mgr = <&pcap>;
            partial-reconfig = <1>;    // This is a PR region
        };
    };
};
```

### 8.2 Loading a Partial Bitstream from Userspace

```bash
# Method 1: Direct firmware loading
echo rm_fft_partial.bin > /sys/class/fpga_manager/fpga1/firmware

# Method 2: Configfs with overlay (recommended for PR)
mkdir -p /sys/kernel/config/device-tree/overlays/rp_fft
cat rp_fft-overlay.dtbo > /sys/kernel/config/device-tree/overlays/rp_fft/dtbo
# The overlay's fpga-region triggers partial bitstream load automatically
```

### 8.3 DT Overlay for PR Region

```dts
// rp_fft-overlay.dts — Loads RM_FFT into the PR region
/dts-v1/;
/plugin/;

/ {
    fragment@0 {
        target-path = "/fpga-region-0/fpga-region-1";

        __overlay__ {
            firmware-name = "rm_fft_partial.bin";
            #address-cells = <1>;
            #size-cells = <1>;

            accel: fft@43C00000 {
                compatible = "mycorp,fft-accel";
                reg = <0x43C00000 0x10000>;
                interrupts = <0 29 4>;
            };
        };
    };
};
```

```bash
# Compile and load
dtc -I dts -O dtb -o rp_fft-overlay.dtbo rp_fft-overlay.dts
mkdir -p /sys/kernel/config/device-tree/overlays/rp_fft
cat rp_fft-overlay.dtbo > /sys/kernel/config/device-tree/overlays/rp_fft/dtbo
# Kernel: loads rm_fft_partial.bin → programs FPGA → probes fft-accel driver
```

### 8.4 Swapping RMs at Runtime

```bash
# Unload current RM (remove overlay)
rmdir /sys/kernel/config/device-tree/overlays/rp_fft

# Load new RM (different overlay + bitstream)
mkdir -p /sys/kernel/config/device-tree/overlays/rp_fir
cat rp_fir-overlay.dtbo > /sys/kernel/config/device-tree/overlays/rp_fir/dtbo
# Kernel: loads rm_fir_partial.bin → programs FPGA → probes fir-accel driver
```

> **Important:** Between unloading and loading, the RP is in an undefined state. The decoupler must be active during this window.

---

## 9. Anti-Patterns and Gotchas

### 9.1 Cross-Boundary Signals

**Illegal:** A signal that originates in the RP and fans out to multiple static-region modules **without going through a partition pin**. Vivado automatically inserts partition pins at RP boundaries, but some patterns confuse the tool:

```verilog
// BAD: RP output fans out to two static modules
assign static_ctrl_a = rp_output;  // OK (single partition pin)
assign static_ctrl_b = rp_output;  // OK (same partition pin, different route)

// BAD: RP output used as clock in static region
assign static_clk = rp_clk_out;    // ILLEGAL — clocks must be in static region
```

### 9.2 Global Signals in Reconfigurable Partitions

| Signal | Allowed in RP? | Workaround |
|---|---|---|
| **Global clock (BUFG)** | No | Generate clocks in static region; route via partition pin |
| **Global set/reset (GSR)** | No | Use local synchronous resets in RM |
| **Global tri-state (GTS)** | No | Not applicable |
| **STARTUP primitives** | No | Keep in static region |
| **MMCM/PLL** | Limited | 7-series: not in RP. UltraScale+: allowed with restrictions |

### 9.3 BRAM Initialization

BRAM contents are **not preserved** across partial reconfiguration. The new RM's BRAM initialization is loaded with the partial bitstream. If the RM needs pre-initialized data (e.g., a coefficient table), it must be in the RM's HDL:

```verilog
// RM must include its own BRAM initialization
(* ram_style = "block" *)
reg [15:0] coeff_rom [0:255];
initial begin
    $readmemh("coeff_hex.txt", coeff_rom);  // Loaded into partial bitstream
end
```

### 9.4 Timing Impact

Partition pins add routing delay. The DFX flow adds:

| Impact | Typical Penalty |
|---|---|
| Partition pin routing | 0.5–2 ns per boundary signal |
| Routing margin (congestion) | 5–10% of clock period budget |
| Decoupler latency | 1–2 clock cycles on AXI paths |

**Mitigation:** Register all signals at partition boundaries (input and output registers).

---

## 10. Verification and Debug

### 10.1 Simulation

Vivado supports simulation of partial reconfiguration through the `pr_sim` flow:

```tcl
# Generate simulation models for each RM
export_simulation -of_objects [get_cells inst_rp] -directory ./sim

# In testbench: trigger PR by writing to ICAP
icap_write_data(.data(partial_bitstream), .size(2048));
# Wait for RP to reconfigure
# Verify RP outputs match expected RM behavior
```

### 10.2 ILA Debugging

ILA probes **can** be placed in reconfigurable partitions, but:
- The ILA itself is part of the RM — different RMs can have different ILA configurations
- ILA triggers and probes must not cross partition boundaries
- After swapping RMs, the Vivado Hardware Manager must refresh the ILA definition

### 10.3 Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `[DRC NSTD-1]` — Unconstrained RP ports | Missing partition pin constraints | Add `set_property HD.PARTPIN_RANGE ...` |
| `[DRC HDNS-1]` — Non-DFX net crosses boundary | Signal illegally connects static to RP | Route through a partition pin or add a register |
| Partial bitstream loads but RP doesn't function | Decoupler never reconnects | Check decouple signal timing; add startup delay |
| Different RMs give different timing | RP placement varies between RMs | Use `SNAPPING_MODE ON` to force consistent placement |
| `ERROR: [Shape-builder 18-1000]` | Pblock overlaps clock region boundary | Align pblock to clock region edges |

---

## 11. Blanking Bitstreams

A **blanking bitstream** clears the RP to a safe, inert state. This is required when:

1. You want to **power down** the RP (save power)
2. You need to **unload** an RM before loading a different one (some flows require an intermediate blank state)
3. The system enters a **fail-safe** mode where the RP must not drive any signals

```tcl
# Generate a blanking bitstream (all zeros in the RP region)
write_bitstream -force -cell inst_rp ./build/rm_blank_partial.bit
```

The blanking bitstream sets all RP LUTs to `0`, tri-states all outputs, and clears BRAM. The decoupler must remain active until the blanking bitstream is fully loaded.

---

## 12. Resource and Timing Budget

### 12.1 DFX Infrastructure Overhead

| Resource | 7-Series | UltraScale+ | Intel Arria 10 |
|---|---|---|---|
| **ICAP/PR IP** | ~200 LUTs | ~300 LUTs | ~500 ALMs |
| **AXI Decoupler** (64-bit) | ~400 LUTs | ~500 LUTs | ~600 ALMs |
| **Partition pin routing** | ~50 LUTs per pin | ~30 LUTs per pin | ~40 ALMs per pin |
| **Routing margin** | 5–10% extra | 3–5% extra | 5% extra |
| **Total (typical 1 RP, 64-bit AXI)** | ~1,500 LUTs | ~1,500 LUTs | ~2,000 ALMs |

### 12.2 Reconfiguration Time

| Method | Bitstream Size | Time |
|---|---|---|
| ICAP 32-bit @ 100 MHz | 2 MB | ~0.5 ms |
| ICAP 32-bit @ 200 MHz | 2 MB | ~0.25 ms |
| PCAP DMA (Zynq) | 2 MB | ~5 ms |
| JTAG (10 MHz TCK) | 2 MB | ~1.6 s |
| Intel PR IP (Avalon) | 2 MB | ~0.5 ms |

> **ICAP vs PCAP:** ICAP is the fastest path for 7-series standalone FPGAs. PCAP is preferred on Zynq because it uses DMA (CPU is free during load). JTAG is only for development — far too slow for production PR.

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [UG909 — Vivado Partial Reconfiguration](https://docs.amd.com/r/en-US/ug909-vivado-partial-reconfiguration) | AMD/Xilinx | Complete DFX flow, pblock constraints, Tcl commands |
| [UG1208 — UltraScale+ Architecture Partial Reconfiguration](https://docs.amd.com/r/en-US/ug1208-partial-reconfiguration) | AMD/Xilinx | UltraScale+ specific PR features (directed routing, nested PR) |
| [Quartus Prime Pro — Partial Reconfiguration User Guide](https://docs.altera.com/r/docs/683834/25.1/quartus-prime-pro-edition-user-guide-partial-reconfiguration) | Altera | Quartus PR flow, PR IP, SUPR, hierarchical PR |
| [Agilex 7 Configuration — Partial Reconfiguration](https://docs.altera.com/r/docs/683673/25.1/agilextm-7-configuration-user-guide/partial-reconfiguration) | Altera | Agilex 7 PR via SDM and HPS |
| [Agilex 5 Configuration — Partial Reconfiguration](https://docs.altera.com/r/docs/813773/25.3.1/device-configuration-user-guide-agilextm-5-fpgas-and-socs/partial-reconfiguration) | Altera | Agilex 5 PR support and configuration |
| [AN-817 — SUPR Tutorial for Arria 10](https://docs.altera.com/r/docs/683428/current) | Altera | Static Update PR step-by-step on Arria 10 |
| [AN-987 — SUPR Tutorial for Agilex 7](https://docs.altera.com/r/docs/749443/current) | Altera | Static Update PR step-by-step on Agilex 7 F-Series |
| [AN-806 — Hierarchical PR Tutorial for Arria 10](https://docs.altera.com/r/docs/683278/current) | Altera | Nested PR partitions on Arria 10 |
| [Signal Tap Debugging for PR Designs](https://docs.altera.com/r/docs/683819/26.1/quartus-prime-pro-edition-user-guide-debug-tools/debugging-partial-reconfiguration-designs-with-signal-tap) | Altera | SignalTap usage inside reconfigurable partitions |
| [Altera Configuration Support Center](https://www.altera.com/design/guidance/configuration) | Altera | Central hub for all configuration and PR documentation |
| [AXI Decoupler Product Guide (PG174)](https://docs.amd.com/r/en-US/pg174-axi-decoupler) | AMD/Xilinx | Decoupler IP configuration and timing |
| [Linux FPGA Manager Documentation](https://www.kernel.org/doc/html/latest/driver-api/fpga/) | kernel.org | FPGA Manager, fpga-region, overlay loading |
| [Configuration & Bitstream](../02_architecture/infrastructure/configuration.md) | This KB | Configuration modes, bitstream format |
| [Bitstream Generation](../03_design_flow/bitstream.md) | This KB | Partial reconfiguration overview, vendor support matrix |
| [Device Tree & FPGA Manager](../10_embedded_linux/04_drivers_and_dma/device_tree_and_overlays.md) | This KB | FPGA Manager, DT overlays, userspace loading |
| [Floorplanning](../03_design_flow/floorplanning.md) | This KB | pblock constraints, region constraints |
