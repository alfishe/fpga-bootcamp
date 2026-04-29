[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Dynamic Function eXchange (DFX) / Partial Reconfiguration

This article covers how to hot-swap bitstream regions at runtime without halting the rest of the FPGA fabric.

## Overview
*   **Concepts**: ICAP vs PCAP, `pblock` constraints.
*   **Implementation**: Decoupling logic to prevent AXI bus hangs during reconfiguration.
*   **Linux Integration**: The `/sys/class/fpga_manager` subsystem.

*(This is a stub. Expand with practical examples and TCL workflows.)*
