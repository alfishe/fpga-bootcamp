[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Advanced HLS Patterns & Optimization

Moving beyond basic High-Level Synthesis (HLS) overviews, this article dives into writing performant algorithms in C++ for FPGA synthesis.

## Key Concepts
*   **Loop Optimization**: Deep dive into `PIPELINE` vs `UNROLL`, and how to calculate the Initiation Interval (II).
*   **Memory Architecture**: Using `ARRAY_PARTITION` to avoid BRAM bottlenecks and achieve parallel data access.
*   **Debugging Stalls**: How to read the Vitis HLS Schedule Viewer and fix dependencies that break the pipeline.
*   **DSP Inference**: Structuring C++ math so the compiler correctly infers dedicated DSP48 slices instead of burning LUTs.

*(This is a stub. Expand with a practical matrix multiplication or FFT example.)*
