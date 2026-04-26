[← Home](../README.md)

# 03 — Design Flow: RTL to Bitstream

The end-to-end pipeline that turns HDL source code into a configured FPGA. Covers synthesis, placement, routing, bitstream generation, floorplanning, and partial reconfiguration across all vendor toolchains.

## Index

| File | Topic |
|---|---|
| [overview.md](overview.md) | End-to-end design flow: RTL → synthesis → place & route → bitstream → configuration |
| [project_structure.md](project_structure.md) | Recommended directory layout, revision control for HDL, IP versioning, constraint files |
| [synthesis.md](synthesis.md) | Synthesis engine behavior, optimization strategies, resource sharing, retiming, FSM extraction |
| [place_and_route.md](place_and_route.md) | Placement algorithms, routing congestion, physical optimization |
| [bitstream.md](bitstream.md) | Bitstream generation, compression, encryption, authentication, partial reconfiguration (DFX) |
| [floorplanning.md](floorplanning.md) | Manual floorplanning, pblock/LogicLock constraints, region constraints, IO planning |
