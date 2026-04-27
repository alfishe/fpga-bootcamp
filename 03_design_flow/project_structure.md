[← Home](../README.md) · [03 — Design Flow](README.md)

# Project Structure — Directory Layout, Version Control, and IP Management

A disorganized FPGA project wastes more time than slow synthesis. The right directory structure separates source, constraints, IP, build artifacts, and testbenches — enabling clean version control, reproducible builds, and painless handoff between team members. This article prescribes a layout that works across Vivado, Quartus, Diamond, and open-source flows.

---

## Overview

FPGA projects generate orders of magnitude more files than software projects: thousands of netlist, log, and report files across multiple tool runs. Without a disciplined directory structure, these artifacts bleed into source directories, poison version control, and make it impossible to reproduce a build from six months ago. The recommended layout separates **source** (HDL, constraints, IP definitions), **build** (tool-generated artifacts: netlists, logs, bitstreams), **sim** (testbenches and simulation models), and **ip** (vendor and third-party IP cores). All tool-generated files belong in the build directory and are excluded from version control.

---

## Recommended Directory Layout

```
project/
├── rtl/                    # All synthesizable HDL source
│   ├── top.sv              # Top-level module
│   ├── core/               # Core design modules
│   │   ├── datapath.sv
│   │   └── control.sv
│   ├── interfaces/          # Bus interfaces, bridge modules
│   │   ├── axi_lite_regs.sv
│   │   └── spi_master.sv
│   └── wrappers/            # Vendor-specific wrappers (keep thin)
│       └── xilinx_clk_wiz.v
├── constraints/             # Timing, placement, IO constraints
│   ├── timing.xdc           # Clock definitions, clock groups
│   ├── io.xdc               # Pin assignments, IO standards
│   └── floorplan.xdc         # pblock/LogicLock constraints
├── sim/                     # Testbenches and simulation artifacts
│   ├── tb_top.sv
│   ├── models/              # Simulation-only models (BFM, memory)
│   │   └── ddr3_sim_model.sv
│   └── waves/               # Waveform config files (.wcfg, .do)
├── ip/                      # Vendor IP and third-party cores
│   ├── xilinx/              # Xilinx IP (XCI files, not generated output)
│   │   └── clk_wiz/
│   │       ├── clk_wiz.xci
│   │       └── clk_wiz.xml
│   └── community/           # Open-source IP (git submodules recommended)
│       └── verilog-ethernet -> github.com/alexforencich/verilog-ethernet
├── build/                   # ALL tool-generated files (gitignored)
│   ├── vivado/
│   │   ├── runs/            # Synthesis, P&R run directories
│   │   └── reports/         # Timing, utilization, power reports
│   ├── quartus/
│   │   ├── output_files/    # SOF, POF, reports
│   │   └── db/              # Synthesis database
│   └── yosys_nextpnr/       # Open-source build
│       ├── synth.json       # Yosys output
│       └── top.bit          # Final bitstream
├── scripts/                 # Build scripts (Tcl, Makefiles, Python)
│   ├── vivado.tcl           # Vivado non-project flow
│   ├── quartus.tcl          # Quartus non-project flow
│   ├── yosys.tcl            # Yosys synthesis script
│   └── Makefile             # Top-level build orchestration
├── docs/                    # Project documentation
│   ├── architecture.md
│   └── register_map.md
├── .gitignore
└── README.md
```

---

## Critical Rules

### 1. Keep RTL Vendor-Agnostic

The `rtl/` directory should synthesize on any vendor's tool with no changes. Vendor-specific primitives (PLLs, transceivers, DDR controllers) belong in `rtl/wrappers/` and should be wrapped with `ifdef or generate to enable multi-vendor builds:

```verilog
// rtl/wrappers/clk_gen.v
generate
    if (VENDOR_XILINX) begin : xilinx_clk
        clk_wiz_0 xilinx_pll (.clk_in(clk_in), .clk_out(clk_out), .locked(locked));
    end else if (VENDOR_INTEL) begin : intel_clk
        cyclonev_pll intel_pll (.inclk0(clk_in), .c0(clk_out), .locked(locked));
    end else if (VENDOR_LATTICE) begin : lattice_clk
        e CP5_pll lattice_pll (.clki(clk_in), .clko(clk_out), .lock(locked));
    end
endgenerate
```

### 2. Gitignore All Build Artifacts

```gitignore
# .gitignore
build/
*.jou
*.log
*.str
*.xpr
*.qpf
*.qsf  # exception: keep if hand-written
*.qar
*.lpf  # exception: keep if hand-written
*.backup.*
*.runs/
*_sim/
.vivado_hls/
*.dcp
*.bit
*.sof
*.pof
```

> [!WARNING]
> **Never commit generated constraint files.** Xilinx writes `*.xdc` files with default pin assignments. These override your hand-written constraints. Only commit hand-written `constraints/*.xdc`.

### 3. Manage IP as Source, Not Generated Output

Vendor IP cores (PLLs, MIG, PCIe) generate hundreds of files — synthesis scripts, simulation models, example designs. Commit only the IP definition files (`.xci` for Xilinx, `.qsys`/`.ip` for Intel) and regenerate the output during the build. The generated output belongs in `build/`.

### 4. Use Git Submodules for Third-Party IP

```bash
git submodule add https://github.com/alexforencich/verilog-ethernet ip/community/verilog-ethernet
git submodule add https://github.com/enjoy-digital/litedram ip/community/litedram
```

Submodules pin third-party IP to a specific commit, ensuring reproducible builds. Without submodules, a `git pull` of the IP can silently break your design.

---

## Multi-Vendor Project Example

A `common.mk` that abstracts vendor-specific builds:

```makefile
# scripts/Makefile
VENDOR ?= xilinx
DEVICE ?= xc7a35tcsg324-1
TOP    ?= top

ifeq ($(VENDOR),xilinx)
	BUILD_CMD = vivado -mode batch -source scripts/vivado.tcl -tclargs $(DEVICE) $(TOP)
	OUTPUT    = build/vivado/$(TOP).bit
else ifeq ($(VENDOR),intel)
	BUILD_CMD = quartus_sh -t scripts/quartus.tcl $(DEVICE) $(TOP)
	OUTPUT    = build/quartus/$(TOP).sof
else ifeq ($(VENDOR),lattice)
	BUILD_CMD = yosys -s scripts/yosys.tcl && nextpnr-ecp5 ... && ecppack ...
	OUTPUT    = build/yosys_nextpnr/$(TOP).bit
endif

build:
	$(BUILD_CMD)

program:
	openocd -f board/$(BOARD).cfg -c "program $(OUTPUT) verify reset exit"

clean:
	rm -rf build/
```

---

## Version Control Best Practices

| Practice | Rationale |
|---|---|
| **Commit hand-written files only** | Reproducibility without repo bloat |
| **Tag releases with bitstream SHA** | `git tag v1.0.0-abc1234` — tag includes the bitstream hash for deployed firmware tracking |
| **Use `.gitattributes` for HDL** | `*.v linguist-language=Verilog`, `*.sv linguist-language=SystemVerilog` — ensures GitHub renders correctly |
| **Branch per feature, merge to main** | Same as software. Main should always build |
| **CI: build on push to main** | GitHub Actions or Jenkins runs `make build` and archives bitstream artifacts |

---

## Antipatterns

| Antipattern | The Problem | The Fix |
|---|---|---|
| **"The Flat Repo"** | All files in root — 200 `.v`, `.xdc`, `.tcl` files, no organization | Use the recommended directory layout. New team members should know where everything lives without documentation |
| **"The Committed Bitstream"** | Committing `.bit`/`.sof` files to version control | Generated artifacts go in `build/`, gitignored. Tag releases instead |
| **"The IP Copy-Paste"** | Copying vendor IP generated output into source tree | Commit `.xci`/`.ip` definition files; generate output during build |
| **"The Vendor Lock-Through-Structure"** | Vivado `.xpr` / Quartus `.qpf` file committed as the build definition | Use Tcl scripts in `scripts/` for build definition; project files are not portable |

---

## References

| Source | Document |
|---|---|
| Vivado UG894 — Using Tcl Scripting | https://docs.xilinx.com/ |
| Quartus Prime Scripting Reference Manual | Intel FPGA Documentation |
| Yosys Command Reference | https://yosyshq.readthedocs.io/ |
| [Design Flow Overview](overview.md) | Six-stage pipeline |
| [Synthesis deep dive](synthesis.md) | Next article |
