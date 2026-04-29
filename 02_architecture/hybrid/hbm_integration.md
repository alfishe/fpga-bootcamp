[← 02 Architecture Home](../README.md) · [← Hybrid Home](README.md) · [← Project Home](../../../README.md)

# HBM Integration — High-Bandwidth Memory on FPGA Die

High-Bandwidth Memory (HBM) stacks DRAM dies vertically on a silicon interposer, connected to the FPGA via thousands of through-silicon vias (TSVs). The result: 10–20× the bandwidth of external DDR5 in 1/10th the PCB area, at 1/3rd the power per bit.

---

## What Is HBM?

```
┌─────────────────── HBM Stack ───────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ DRAM Die │  │ DRAM Die │  │ DRAM Die │ ...   │
│  │   4 Gb   │  │   4 Gb   │  │   4 Gb   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │ TSVs        │ TSVs        │ TSVs         │
│  ┌────┴─────────────┴─────────────┴──────────┐  │
│  │  Base Logic Die (controller + PHY)         │  │
│  │  ├─ 8 independent channels                │  │
│  │  ├─ 128-bit pseudo-channel per channel     │  │
│  │  └─ 2 GB/s per pseudo-channel             │  │
│  └─────────────────┬─────────────────────────┘  │
└────────────────────┼────────────────────────────┘
                     │ 1024-bit microbump interface
┌────────────────────┼────────────────────────────┐
│  Silicon Interposer                             │
│  ┌─────────────────┴─────────────────────────┐  │
│  │  FPGA / SoC Die                            │  │
│  │  HBM Controller (hard IP)                  │  │
│  │  ├─ AXI4 interface to FPGA fabric          │  │
│  │  └─ 256 GB/s – 820 GB/s aggregate          │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### HBM Generations

| Generation | Max Bandwidth/Stack | Capacity/Stack | Channels | Pseudo-channels | VDD | Year |
|---|---|---|---|---|---|---|
| **HBM1** | 128 GB/s | 1–4 GB | 8 | 0 | 1.2V | 2015 |
| **HBM2** | 256 GB/s | 4–8 GB | 8 | 2 | 1.2V | 2018 |
| **HBM2e** | 460 GB/s | 8–16 GB | 8 | 2 | 1.2V | 2020 |
| **HBM3** | 665 GB/s | 16–32 GB | 16 | 2 | 1.1V | 2023 |
| **HBM3e** | 1.0 TB/s+ | 24–48 GB | 16 | 4 | 0.8V | 2024+ |

---

## Why HBM vs DDR5?

| Property | DDR5 (4× 64-bit DIMM) | HBM2e (1 stack) | Ratio |
|---|---|---|---|
| **Bandwidth** | 51.2 GB/s (DDR5-6400) | 460 GB/s | **9×** |
| **Bus width** | 256 bits (4×64) | 1024 bits | 4× |
| **Power** | ~15W (4 DIMMs active) | ~5W (1 stack) | **0.33×** |
| **pJ/bit** | ~18 pJ/bit | ~3.5 pJ/bit | **0.19×** |
| **PCB area** | ~2,400 mm² (4 DIMM slots) | ~100 mm² (interposer) | **0.04×** |
| **Latency (tRC)** | ~46 ns | ~45 ns | ~1× |
| **Capacity** | Up to 512 GB (4×128 GB) | Up to 16 GB (1 stack) | 0.03× |
| **Cost** | ~$5/GB | ~$20/GB | 4× |

**The HBM tradeoff:** HBM wins bandwidth, power, and density by 5–20×. DDR5 wins capacity and cost by 10–30×. HBM is for bandwidth-bound workloads; DDR5 for capacity-bound workloads.

---

## FPGA HBM Implementations

### Intel Stratix 10 MX / Agilex M-Series

| Device | HBM Stacks | Capacity | Peak BW | FPGA LEs | Year |
|---|---|---|---|---|---|
| Stratix 10 MX 1650 | 1× HBM2 | 8 GB | 256 GB/s | 1,650K | 2018 |
| Stratix 10 MX 2100 | 2× HBM2 | 16 GB | 512 GB/s | 2,100K | 2019 |
| Agilex M-Series | 2× HBM2e | 16 GB | 820 GB/s | ~3,000K | 2023 |

Intel's HBM controller is hardened IP. The FPGA fabric sees the HBM as AXI4 memory-mapped slaves. Each pseudo-channel (32 total per stack on HBM2e) appears as an independent AXI4 port.

### Xilinx Virtex UltraScale+ HBM / Versal HBM

| Device | HBM Stacks | Capacity | Peak BW | FPGA LEs | Year |
|---|---|---|---|---|---|
| VU35P (HBM) | 1× HBM2 | 8 GB | 460 GB/s | 1,200K | 2018 |
| VU37P (HBM) | 1× HBM2 | 8 GB | 460 GB/s | 2,852K | 2019 |
| Versal HBM (VH1582) | 1× HBM2e | 32 GB | 820 GB/s | ~2,000K AIE + FPGA | 2022 |
| Versal Premium (VH1782) | 2× HBM2e | 64 GB | 1.6 TB/s | ~3,500K | 2024 |

Xilinx uses an integrated AXI4 switch to present HBM channels as 32 independent AXI ports. The `hbm_v1_0` IP in Vivado handles calibration, refresh, and ECC.

---

## HBM Controller Architecture

### Channel Structure

```
HBM Stack
├── Channel 0
│   ├── Pseudo-Channel 0 (128-bit read + 128-bit write)
│   │   └── AXI4 Port → FPGA Fabric (2 GB/s at 450 MHz)
│   └── Pseudo-Channel 1 (128-bit read + 128-bit write)
│       └── AXI4 Port → FPGA Fabric (2 GB/s at 450 MHz)
├── Channel 1 ... (same structure)
├── ...
└── Channel 7 ... (same structure)

Total: 16 AXI4 ports (HBM2e with 2 pseudo-channels × 8 channels)
        32 AXI4 ports (HBM2e with 4 pseudo-channels, Intel Agilex M)
```

### Bandwidth Accounting (HBM2e, 1 stack)

| Level | BW per Unit | Count | Aggregate |
|---|---|---|---|
| **Pseudo-channel** | 14.4 GB/s | 16 (8×2) | 230 GB/s |
| **Channel** | 28.8 GB/s | 8 | 230 GB/s |
| **Stack** | 460 GB/s | 1 | 460 GB/s |

However, sustained bandwidth is typically **70–85%** of theoretical:
- DRAM refresh: ~5% overhead
- Bank conflicts: ~10% for random access patterns
- AXI4 protocol overhead: ~5%
- ECC scrubbing: ~2%

**Sustained usable:** ~320–390 GB/s per HBM2e stack.

---

## Use Cases

| Application | Bandwidth Need | Why HBM |
|---|---|---|
| **Genomics (BWA-MEM, GATK)** | 200+ GB/s random access to reference genome | DDR5 bank conflicts kill throughput; HBM's 32 independent channels keep random access at line rate |
| **AI Training (transformer models)** | 300+ GB/s for weight + activation tensors | 2× HBM2e = 820 GB/s, enough for BERT-Large training on single FPGA |
| **Network packet processing (100G+)** | 400 GB/s for packet buffer + flow state | 4× 100G pipes × 100 GB/s state access each |
| **Financial simulation (Monte Carlo)** | 100+ GB/s scatter/gather | Thousands of independent random walks, each in separate HBM channel — zero contention |
| **Radio astronomy (correlator)** | 500+ GB/s for visibility matrix | VLBI correlator: 64 antennas × 4 polarizations × 1 GHz BW → 512 GB/s stream |
| **Graph analytics (BFS, PageRank)** | 300+ GB/s pointer chasing | Graph stored in HBM; 32 concurrent edge traversals without stall |

---

## Best Practices

1. **Map compute to channels, not aggregate bandwidth** — 32 independent AXI ports mean 32 independent address spaces. A single large linear buffer across all channels wastes parallelism. Partition data across channels.
2. **HBM ≠ cache** — HBM latency is comparable to DDR (45 ns tRC). It's bandwidth, not latency, that differentiates HBM.
3. **ECC is mandatory in production** — HBM's TSV interconnect is sensitive to thermal cycling. Enable controller ECC; budget ~2% bandwidth overhead.
4. **Thermal matters more than DDR** — HBM stacks concentrate 5–10W in a ~50 mm² footprint. Junction temperature can exceed 95°C without active cooling.
5. **Interposer cost is significant** — the silicon interposer is a full-reticle passive die. For low-volume designs, the interposer can cost more than the FPGA.

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **Linear addressing across channels** | Only 1/32nd of theoretical bandwidth | Partition data: use hash-based or round-robin distribution across pseudo-channels |
| **All FPGA masters targeting same channel** | Channel bank conflicts, low throughput | Statically assign FPGA compute units to specific HBM channels |
| **Ignoring ECC scrub** | Correctable errors accumulate → uncorrectable | Enable background ECC scrubbing in controller IP |
| **Thermal throttling** | HBM bandwidth drops 30–50% under load | Monitor HBM temperature via controller registers; use active cooling |
| **Underestimating AXI4 routing congestion** | 32 AXI4 ports × 512-bit data → fabric routing overload | Plan FPGA floorplan around HBM port placement; use AXI4-Stream conversion close to ports |

---

## Cost-Bandwidth Decision Flow

```
Do you need >100 GB/s sustained memory bandwidth?
  NO → DDR5 is sufficient (51.2 GB/s for 4× DDR5-6400)
  YES → continue

Is your data access pattern random (pointer chasing, hash tables)?
  YES → HBM (32 independent channels handle random access well)
  NO  → DDR5 (sequential access works fine on fewer channels)

Can your budget absorb $2,000–$20,000 for the FPGA + interposer?
  YES → HBM FPGA (Stratix 10 MX, Versal HBM)
  NO  → Multiple DDR5 channels on lower-cost FPGA + bank-aware software

Is PCB area constrained (<5000 mm² for memory subsystem)?
  YES → HBM (100 mm² vs 2,400 mm² for DDR5)
  NO  → DDR5 (cheaper per GB, more flexible layout)
```

---

## References

| Source | Path |
|---|---|
| JEDEC HBM2/HBM2e Specification (JESD235) | JEDEC |
| Intel Stratix 10 MX HBM2 User Guide | Intel FPGA Documentation |
| Xilinx Virtex UltraScale+ HBM Controller (PG276) | Xilinx / AMD |
| Versal HBM Architecture Manual | Xilinx / AMD |
| Achronix Speedster7t HBM Implementation | Achronix |
| Micron HBM2e Product Brief | Micron |
| Samsung HBM3 Product Brief | Samsung |
