[← HDL & Synthesis Home](README.md) · [← Project Home](../README.md)

# Vendor Pragmas & Synthesis Attributes

Synthesis pragmas (also called attributes or directives) are vendor-specific annotations embedded in HDL source or constraint files that control how the synthesis tool maps RTL to hardware. They override default inference behavior, preserve signals, control optimization, and declare physical constraints that can't be expressed in portable HDL.

---

## Why Pragmas Exist

Pure IEEE-standard HDL has no concept of "keep this net" or "map this multiplier to a DSP." The standard only defines behavior and structure. Vendor synthesis tools need additional instructions to make good engineering decisions:

- **Preserve hierarchy** — stop the tool from flattening a module boundary
- **Force or suppress resource mapping** — RAM vs LUT, DSP vs fabric
- **Control optimization** — prevent removal of "unused" debug/test signals
- **CDC safety** — declare asynchronous clock domain crossings
- **Physical constraints** — IO standard, drive strength, slew rate, termination

Each vendor has its own syntax, but the **concepts** are remarkably similar — they all solve the same engineering problems.

---

## Syntax Convention Summary

| Vendor | Verilog Syntax | VHDL Syntax | Constraint File |
|---|---|---|---|
| **AMD/Xilinx** | `(* attribute = "value" *)` | `attribute attribute of signal : signal is "value";` | XDC |
| **Intel/Altera** | `(* altera_attribute = "value" *)` | `attribute altera_attribute : string;` | QSF |
| **Gowin** | `(* syn_attr = "value" *)` | Same attribute pattern | CST / SDC |
| **Lattice** | `(* lpf_attribute = "value" *)` | `attribute attribute : string;` | LPF |
| **Microchip** | Verilog attribute or Synplify `syn_*` | VHDL attribute or Synplify `syn_*` | PDC / SDC |

---

## Signal Preservation (keep / dont_touch / preserve)

Prevents the synthesis tool from optimizing away a signal it deems "unused" — essential for debug probes, ILA/SignalTap connections, and signals that matter at a higher integration level.

| Vendor | Attribute | What It Does |
|---|---|---|
| **Xilinx** | `(* keep = "true" *)` | Prevents optimization removal of the annotated net |
| **Xilinx** | `(* dont_touch = "true" *)` | Prevents any optimization — stronger than `keep`; freezes the entire netlist cell |
| **Xilinx** | `DONT_TOUCH` (on instance) | Instance-level freeze; applied in XDC: `set_property DONT_TOUCH true [get_cells ...]` |
| **Intel** | `(* preserve = "true" *)` | Prevents register removal/duplication |
| **Intel** | `(* keep = "true" *)` | Prevents removal of combinational nodes |
| **Intel** | `(* noprune = "true" *)` | Prevents removal of unused ports |
| **Gowin** | `(* syn_preserve = 1 *)` | Prevents synthesis removal |
| **Lattice** | `(* syn_keep = "true" *)` | Keeps signal in netlist (Synplify) |
| **Microchip** | `(* syn_preserve = 1 *)` | Synplify attribute |

### Example: Keeping a Debug Probe

**Verilog (Xilinx):**
```verilog
(* keep = "true" *) wire debug_strobe;
assign debug_strobe = (state == IDLE) & valid;
```

**VHDL (Xilinx):**
```vhdl
attribute keep : string;
attribute keep of debug_strobe : signal is "true";
signal debug_strobe : std_logic;
debug_strobe <= '1' when state = IDLE and valid = '1' else '0';
```

---

## RAM/ROM Style Control

Overrides the tool's automatic decision between Block RAM, distributed (LUT) RAM, or MLAB.

| Vendor | Attribute | Values | Verilog Example |
|---|---|---|---|
| **Xilinx** | `ram_style` | `"block"`, `"distributed"`, `"registers"` | `(* ram_style = "block" *) reg [7:0] mem [0:255];` |
| **Xilinx** | `rom_style` | `"block"`, `"distributed"` | `(* rom_style = "block" *) reg [7:0] rom [0:255];` |
| **Intel** | `ramstyle` | `"M9K"`, `"M20K"`, `"MLAB"`, `"logic"` | `(* ramstyle = "M9K" *) reg [7:0] mem [0:255];` |
| **Intel** | `romstyle` | `"M9K"`, `"M20K"`, `"MLAB"`, `"logic"` | Same pattern |
| **Lattice** | `syn_ramstyle` | `"block_ram"`, `"registers"`, `"distributed"` | Synplify syntax |
| **Microchip** | `syn_ramstyle` | `"block_ram"`, `"registers"` | Synplify syntax |
| **Gowin** | `ram_style` | `"block"`, `"distributed"` | Same pattern as Xilinx |

---

## DSP / Multiplier Control

Controls whether `*` maps to DSP slices or fabric LUTs.

| Vendor | Attribute | Values |
|---|---|---|
| **Xilinx** | `use_dsp` | `"yes"`, `"no"`, `"logic"` |
| **Intel** | `multstyle` | `"dsp"`, `"logic"` |
| **Lattice** | `syn_multstyle` | `"dsp"`, `"logic"` |
| **Microchip** | `syn_multstyle` | `"dsp"`, `"logic"` |
| **Gowin** | `use_dsp` | `"yes"`, `"no"` |

### Example

```verilog
// Force DSP48 for this multiplier
(* use_dsp = "yes" *) wire [35:0] product = a * b;

// Force LUT-based multiplier (tight timing, small width)
(* use_dsp = "no" *) wire [17:0] product = a * b;
```

---

## Asynchronous Register Chain (async_reg)

The most critical CDC pragma. Declares a register as part of a synchronizer chain, telling the tool:

1. **Don't optimize these registers** — they must remain back-to-back
2. **Don't replicate** — metastability resolution requires exactly 2 (or 3) FFs in series
3. **Place them close together** — minimize routing delay between synchronizer stages
4. **Exclude from static timing analysis** — the first FF output is intentionally metastable

| Vendor | Attribute | Verilog Example |
|---|---|---|
| **Xilinx** | `ASYNC_REG` | `(* ASYNC_REG = "TRUE" *) reg [1:0] sync;` |
| **Xilinx** | Also in XDC | `set_property ASYNC_REG TRUE [get_cells sync_reg*]` |
| **Intel** | `(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)` | (Verbose — typically applied via QSF) |
| **Intel** | `FAST_INPUT_REGISTER` | Also used for async input register chains |
| **Lattice** | `syn_sync_ff` | Applied per register in Synplify flow |
| **Microchip** | `syn_sync_ff` | Synplify synchronizer declaration |

### Verilog Example (Xilinx):
```verilog
(* ASYNC_REG = "TRUE" *) reg [1:0] sync_ff;
always @(posedge clk) begin
    sync_ff <= {sync_ff[0], async_in};
end
assign sync_out = sync_ff[1];
```

---

## FSM Encoding

Controls how the synthesis tool encodes state machine states.

| Vendor | Attribute | Values | Notes |
|---|---|---|---|
| **Xilinx** | `fsm_encoding` | `"one-hot"`, `"sequential"`, `"gray"`, `"auto"` | Applied to state register |
| **Xilinx** | `fsm_safe_state` | `"auto"`, `"reset"`, `"power_on"` | Recovery from invalid states |
| **Intel** | `enum_encoding` | `"one-hot"`, `"sequential"`, `"gray"`, `"auto"` | Applied to enum type in SV |
| **Synplify** | `syn_encoding` | `"safe"`, `"onehot"`, `"sequential"`, `"gray"` | Common across Lattice/Microchip |

---

## Module-Level Pragmas

### Hierarchy Preservation

| Vendor | Attribute | Effect |
|---|---|---|
| **Xilinx** | `(* keep_hierarchy = "yes" *)` | Prevents flattening this module boundary |
| **Xilinx** | `(* keep_hierarchy = "no" *)` | Allows flattening (overrides global) |
| **Intel** | `(* preserve = "true" *)` on module | Preserves instance boundary |
| **Synplify** | `syn_hier = "hard"` or `"fixed"` | Hard = absolute; fixed = until optimization decides |

### Black Box Declaration

| Vendor | Attribute | Use Case |
|---|---|---|
| **Xilinx** | `(* black_box *)` | External netlist or encrypted IP |
| **Intel** | `(* altera_attribute = "-name SYNTHESIS_CRITICAL_SECTION YES" *)` | Critical logic preservation |
| **Synplify** | `syn_black_box = 1` | External module declaration |

### Resource Sharing

| Vendor | Attribute | Effect |
|---|---|---|
| **Xilinx** | `(* resource_sharing = "yes" *)` | Allow sharing arithmetic units across mutually exclusive paths |
| **Xilinx** | `(* resource_sharing = "no" *)` | Force dedicated hardware per operation |
| **Intel** | `(* altera_attribute = "-name AUTO_SHIFT_REGISTER_RECOGNITION OFF" *)` | Disable SRL inference |

---

## IO and Physical Attributes

These are typically applied in constraint files (XDC/QSF/LPF) rather than HDL source, but can sometimes be embedded:

| Vendor | Attribute | Meaning |
|---|---|---|
| **Xilinx** | `IOB = "TRUE"` | Force register into IO block (IOB FF) |
| **Xilinx** | `(* IOB = "true" *)` | HDL-embedded version |
| **Intel** | `(* altera_attribute = "-name FAST_OUTPUT_REGISTER ON" *)` | Force output register into IOE |
| **Lattice** | `syn_useioff = 1` | Force register into IOLOGIC |

---

## Cross-Vendor Equivalence Table

Most pragmas have equivalent intent across vendors, just different names:

| Intent | Xilinx | Intel | Synplify (Lattice/Microchip) |
|---|---|---|---|
| Keep a signal | `keep` / `dont_touch` | `keep` / `preserve` | `syn_keep` |
| Force BRAM | `ram_style = "block"` | `ramstyle = "M9K"` | `syn_ramstyle = "block_ram"` |
| Force LUT RAM | `ram_style = "distributed"` | `ramstyle = "logic"` | `syn_ramstyle = "registers"` |
| Force DSP | `use_dsp = "yes"` | `multstyle = "dsp"` | `syn_multstyle = "dsp"` |
| Async register chain | `ASYNC_REG` | `SYNCHRONIZER_IDENTIFICATION` | `syn_sync_ff` |
| FSM encoding | `fsm_encoding` | `enum_encoding` | `syn_encoding` |
| Preserve hierarchy | `keep_hierarchy` | `preserve` | `syn_hier` |
| Black box | `black_box` | (constraint file) | `syn_black_box` |
| IO register | `IOB` | `FAST_INPUT/OUTPUT_REGISTER` | `syn_useioff` |

---

## Pragmas in Constraint Files vs HDL Source

A pragmatic debate: **where should pragmas live?**

| Location | Pros | Cons |
|---|---|---|
| **HDL source** | Co-located with logic; survives porting | Vendor lock-in; harder to change without re-synthesis |
| **Constraint file** (XDC/QSF) | Clean HDL; change without re-synthesis | Separated from the intent; can drift from code |
| **Both** (belt + suspenders) | Maximum safety | Duplication risk; harder maintenance |

The modern consensus: **HDL source for intent-carrying pragmas** (`ASYNC_REG`, `ram_style`), **constraint files for physical/timing attributes** (`IOB`, `LOC`, `IOSTANDARD`).

---

## Further Reading

| Resource | Description |
|---|---|
| [Xilinx UG901: Synthesis Attributes](https://docs.amd.com/r/en-US/ug901-vivado-synthesis) | Complete list of Vivado synthesis attributes |
| [Intel Quartus Synthesis Attributes](https://www.intel.com/content/www/us/en/docs/programmable/) | Quartus attribute reference |
| [Gowin HDL Coding Guide](https://www.gowinsemi.com/en/support/documentation/) | Gowin-specific synthesis attributes |
| [Synplify Pro for Microchip Attribute Reference](https://ww1.microchip.com/downloads/aemDocuments/documents/FPGA/swdocs/synopsys/microchip_attribute_reference_2024_2.pdf) | Synplify attribute reference |
| [Inference Rules](inference_rules.md) | The patterns these pragmas control |
| [CDC Coding Patterns](cdc_coding.md) | How `ASYNC_REG` is used in practice |
