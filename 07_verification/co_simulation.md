[← Section Home](README.md) · [← Project Home](../README.md)

# Co-Simulation — Mixing Languages & External Models

Co-simulation connects your HDL design to code running in a different language or runtime. This lets you verify against C/C++ reference models, integrate MATLAB algorithms, boot real ARM Linux on an SoC design, or mix VHDL legacy IP with modern SV testbenches.

---

## DPI-C: Verilog ↔ C/C++

The Direct Programming Interface is the standard bridge between SystemVerilog and C/C++. It's zero-overhead — function calls cross the language boundary directly.

### Export (C called from SV)

```c
// reference_model.c
#include "svdpi.h"
int fir_filter(int input, int* coeffs) {
    int result = 0;
    for (int i = 0; i < 16; i++) result += input * coeffs[i];
    return result;
}
```

```systemverilog
// testbench.sv
import "DPI-C" function int fir_filter(input int data, input int coeffs[]);

always @(posedge clk) begin
    filtered <= fir_filter(raw_sample, tap_coeffs);
end
```

### Import (SV called from C)

```systemverilog
export "DPI-C" function sv_log;  // make visible to C

function void sv_log(int level, string msg);
    $display("[SV:%0d] %s", level, msg);
endfunction
```

| Direction | Keyword | Use |
|---|---|---|
| C → SV | `import "DPI-C"` | Call C functions from SV |
| SV → C | `export "DPI-C"` | Call SV functions from C |
| Types | `svdpi.h` | `svLogic`, `svBitVecVal`, arrays |
| Arrays | Open or sized | `[]` = open, `[15:0]` = sized |

---

## MATLAB / Simulink Co-Simulation

Two approaches for integrating MATLAB models:

| Method | How | Best For |
|---|---|---|
| **HDL Verifier** | Simulink ↔ HDL simulator via TCP/IP | Algorithm validation, DSP pipelines |
| **Export C via MATLAB Coder** | MATLAB → C → DPI-C → SV | Cheaper (no toolbox), good for fixed-point filters |
| **File I/O bridge** | $readmemh / $fwrite intermediate data | Quick-and-dirty; ~0 MB/s throughput |

---

## QEMU + SystemC for SoC Verification

For FPGA SoC designs (Zynq, Cyclone V SoC, MPSoC), verify HW/SW interaction before silicon:

```
┌──────────────────────────────────────┐
│  QEMU (ARM Linux + application code) │
│  ← socket / shared memory →         │
│  ┌──────────────────────────────┐    │
│  │  SystemC TLM-2.0 wrapper      │    │
│  │  ↔ AXI/AVMM transactions      │    │
│  │  ┌──────────────────────┐    │    │
│  │  │  HDL Simulator (RTL)   │    │    │
│  │  └──────────────────────┘    │    │
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

The CPU side runs real Linux + driver code; the FPGA side runs RTL. They communicate through a SystemC Transaction-Level Model (TLM) that translates AXI bursts into memory reads/writes visible to both sides.

---

## VHDL + SystemVerilog Mixing

| Scenario | Approach |
|---|---|
| VHDL DUT, SV testbench | Vivado/Questa natively support mixed-language elaboration |
| SV DUT, VHDL testbench | Supported but rarer; limit to simple wrappers |
| VHDL `foreign` attribute | Like DPI-C but VHDL-side; implementation-specific |
| Shared packages | Not possible — use C structs in DPI-C as intermediary |

---

## Practical Co-Simulation Decision Table

| Your Situation | Approach |
|---|---|
| Reference model in C/C++ | DPI-C (fastest, standard) |
| DSP algorithm in MATLAB | MATLAB Coder → C → DPI-C |
| SoC: ARM Linux + FPGA | QEMU + SystemC + HDL simulator |
| Legacy VHDL IP + new SV | Mixed-language in Questa/Vivado |
| Third-party IP binary model | Vendor-specific encrypted model + SWIFT/VHPI |

---

## Best Practices

1. **DPI-C over file I/O** — direct function calls are ~1000× faster than writing/reading $fwrite/$fread files. Don't use file I/O bridging for anything beyond one-off debug.
2. **QEMU co-simulation saves months** — catching a Linux driver bug before tape-out is worth the setup effort. The alternative is finding it on real silicon.
3. **Keep the C reference model simple** — if it's too complex to re-derive from the RTL spec, it's easy to introduce errors in the model that mask RTL bugs.

## Pitfall: DPI-C Array Overhead

Passing large arrays across DPI-C can become a bottleneck. Each call copies array data between SV and C memory spaces. For high-bandwidth data paths (>100 MB/s), consider streaming through a shared memory buffer or DMA model instead.

---

## References

| Source | Path |
|---|---|
| IEEE 1800-2017 DPI Annex | IEEE standards (Section 35) |
| SystemC TLM-2.0 User Manual | Accellera |
| QEMU SystemC bridge | https://wiki.qemu.org |
