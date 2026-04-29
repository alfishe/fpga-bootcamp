[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Advanced Networking & SmartNICs

In High-Frequency Trading (HFT) and data centers, the latency of the Linux kernel network stack is unacceptable. FPGAs are used as SmartNICs to process packets in hardware.

## Key Technologies
*   **10G / 100G MACs**: Instantiating high-speed transceivers.
*   **TCP Offload Engines (TOE)**: Handling TCP/IP handshakes, sliding windows, and retransmissions directly in FPGA logic.
*   **DPDK Integration**: Bypassing the kernel entirely and pushing packets straight from the FPGA PCIe card into userspace memory.

*(This is a stub. Expand with DPDK setup guides and TOE architecture.)*
