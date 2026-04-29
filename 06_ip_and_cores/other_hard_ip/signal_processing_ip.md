[← 06 Ip And Cores Home](../README.md) · [← Other Hard Ip Home](README.md) · [← Project Home](../../../README.md)

# Signal Processing IP — FFT, FIR, DDS, CORDIC

DSP-heavy FPGA designs rely heavily on vendor IP blocks for FFT (Fast Fourier Transform), FIR (Finite Impulse Response) filters, DDS (Direct Digital Synthesis), and CORDIC (Coordinate Rotation Digital Computer). This article compares vendor IP against hand-coded RTL and analyzes resource/throughput trade-offs.

---

## FFT

### Vendor IP vs Hand-Coded

| Aspect | Vendor FFT IP | Hand-Coded FFT |
|---|---|---|
| Implementation | Optimized for vendor DSP slices | Your choice of architecture |
| Configurations | Pipelined, streaming, burst, radix-2/4/8 | Whatever you write |
| Resource efficiency | Best — maps to DSP48/MULTADD exactly | Usually worse than vendor |
| Latency | Predictable (vendor data sheet) | Variable |
| Throughput | 1 sample/clock (pipelined) | Depends on design |

### By Vendor

| Vendor | IP Name | Max Points | Architecture | Notes |
|---|---|---|---|---|
| **Xilinx** | Fast Fourier Transform (PG109) | Up to 65536 | Pipelined Streaming, Burst, Radix-2/4, Radix-2 Lite | AXI4-Stream interface. Internal rounding/convergent rounding options. |
| **Intel** | FFT IP Core | Up to 65536 | Streaming, Variable Streaming, Buffered Burst, Burst | Avalon-ST interface. Variable streaming can change FFT size on-the-fly. |
| **Lattice** | FFT Compiler | Up to 4096 | Pipelined, Burst | Smaller catalog, fewer options. |

**Resource example (Xilinx 1024-pt pipelined):** ~16 DSP48, ~12 BRAM, ~3K LUTs

---

## FIR Filter

### Architecture Choices

| Architecture | DSP Usage | Latency | Best For |
|---|---|---|---|
| **Systolic (fully pipelined)** | 1 DSP per tap | Linear with taps | High throughput, fixed coefficients |
| **Semi-parallel (folded)** | N DSPs for M taps | Higher | Balance DSP vs throughput |
| **Transposed** | 1 DSP per tap | 1 sample (pipelined) | Lowest latency |
| **Polyphase** | Sub-filter DSP count | Sub-filter depth | Decimation/interpolation |

### By Vendor

| Vendor | IP Name | Max Taps | Rate Change | Notes |
|---|---|---|---|---|
| **Xilinx** | FIR Compiler (PG149) | Unlimited (resource-limited) | Interpolation 1–64×, Decimation 1–64× | Coefficient reload, symmetric/antisymmetric, Hilbert/Interpolating. |
| **Intel** | FIR II IP Core | Unlimited | Interpolation, Decimation, Fractional | Fixed, reloadable coefficients. Multi-cycle variable support. |
| **Lattice** | FIR Filter | 1024 taps typical | Single rate or multirate | Radiant Clarity Designer integration. |

---

## DDS (Direct Digital Synthesis)

Generates sine/cosine waveforms digitally from a phase accumulator:

\[f_{out} = \frac{\Delta\theta \times f_{clk}}{2^N}\]

| Vendor | IP Name | Output Width | SFDR (typical) | Notes |
|---|---|---|---|---|
| **Xilinx** | DDS Compiler (PG141) | 8–32 bit | 48–96 dB | Phase dithering, Taylor series correction. AXI4-Stream. |
| **Intel** | NCO IP Core | 8–32 bit | 48–115 dB | Multi-channel (up to 32). Phase dithering, Taylor correction. |
| **Lattice** | DDS | 8–24 bit | 48–72 dB | Simpler implementation. |

**Hand-coded alternative:** Phase accumulator + BRAM sine LUT (simple, 200 LUTs + 1 BRAM for 16-bit DDS). Use vendor IP only for multi-channel, high-SFDR requirements.

---

## CORDIC

A rotation-mode CORDIC computes:

\[x' = x \cos\theta - y \sin\theta\]
\[y' = y \cos\theta + x \sin\theta\]

Uses iterative shift-and-add for hardware-efficient trig/rotations.

| Vendor | IP Name | Modes | Latency | Notes |
|---|---|---|---|---|
| **Xilinx** | CORDIC (PG105) | Rotate, Translate, Sin/Cos, Sinh/Cosh, Arctan, Square Root | N+2 cycles (N=iterations) | AXI4-Stream. Configurable precision. |
| **Intel** | CORDIC (part of DSP Builder) | Rotate, Sin/Cos, Arctan, Magnitude | N cycles | Tighter integration with DSP Builder. |

**When to hand-code CORDIC:** Simple rotation with fixed angle → use DSP48 multiply instead (1 cycle). CORDIC is for variable-angle rotation or when DSP slices are exhausted.

---

## Best Practices

1. **Try vendor IP first** — vendor DSP IP maps to hardware DSP slices optimally, often better than hand-written inference
2. **Use pipelined streaming FFT** whenever throughput matters — the latency hit (1024 cycles for 1024-pt) is worth the 1 sample/clock throughput
3. **DDS for simple sine: BRAM LUT** — a 4096-entry × 16-bit sine table uses 1 BRAM and ~200 LUTs vs vendor IP overhead (~500 LUTs for wrapper)
4. **Coefficient reload** — for adaptive FIR filters, verify the IP supports real-time coefficient update without re-synthesis
5. **Check SFDR, not just resolution** — a 16-bit DDS with 72 dB SFDR is cleaner than 24-bit with 48 dB SFDR

---

## References

- Xilinx PG109: Fast Fourier Transform LogiCORE IP
- Xilinx PG149: FIR Compiler LogiCORE IP
- Xilinx PG141: DDS Compiler LogiCORE IP
- Intel FIR II IP Core User Guide
- Lattice Radiant IP User Guides
