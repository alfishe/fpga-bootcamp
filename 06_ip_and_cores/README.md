[← Home](../README.md)

# 06 — IP & Cores

Intellectual Property blocks — the reusable building blocks of FPGA design. From bus protocols and memory controllers to PCIe endpoints and transceivers. Covers vendor IP ecosystems, interconnect design, hard IP blocks, and the tools for packaging and reusing your own IP.

## Index

| Folder | Coverage |
|---|---|
| [bus_protocols/](bus_protocols/README.md) | AXI4 family (AXI4, AXI4-Lite, AXI4-Stream), Wishbone, Avalon, APB/AHB — protocol deep dives and comparison |
| [vendor_ip/](vendor_ip/README.md) | Xilinx IP Integrator, Intel Platform Designer, Lattice Clarity, Microchip SmartDesign, Gowin IP generator |
| [interconnect/](interconnect/README.md) | AXI Interconnect: crossbar vs shared bus, address decoding, QoS arbitration, data width/clock conversion |
| [ddr/](ddr/README.md) | DDR memory controllers: MIG (Xilinx), UniPHY/EMIF (Intel), Lattice/Microchip/Gowin, pin planning |
| [pcie/](pcie/README.md) | Integrated PCIe hard blocks (Gen1–Gen5), BAR configuration, MSI/MSI-X, DMA (XDMA), endpoint vs root port |
| [transceivers/](transceivers/README.md) | Multi-gigabit transceivers (GTP/GTH/GTY/GTM), PMA+PCS, CDR, equalization, line rates |
| [other_hard_ip/](other_hard_ip/README.md) | Hard Ethernet MACs, video/audio IP blocks, FFT/FIR/DDS/CORDIC signal processing IP |
| [ip_reuse/](ip_reuse/README.md) | IP packaging (IP-XACT, component.xml), FuseSoC package manager & build system, IP licensing (MIT/LGPL/GPL/Apache/CERN OHL) |
