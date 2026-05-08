[← Advanced Topics Home](README.md) · [← Project Home](../README.md)

# FPGA in Data Centers — SmartNICs, OPAF, Acceleration Cards & OFS

Data centers are the largest and fastest-growing market for high-end FPGAs. Microsoft, Amazon, Google, and Meta deploy millions of FPGA instances for network acceleration, compute offload, and storage processing. This article covers the FPGA's role in the data center: SmartNIC architectures, the Open Programmable Acceleration Framework (OPAF), the Open FPGA Stack (OFS), and the major acceleration card platforms.

For FPGA-as-a-Service cloud offerings, see [FPGA as a Service](fpga_as_a_service.md). For SmartNIC networking details, see [Networking & SmartNICs](networking_smartnics.md). For hardware security relevant to multi-tenant data centers, see [Hardware Security](hardware_security.md).

---

## Why FPGAs in the Data Center?

| Use Case | What the FPGA Does | Why Not GPU/CPU |
|----------|-------------------|-----------------|
| **Network acceleration** | Parse, transform, route packets at 100G+ line rate | CPU can't sustain 100Gpps; GPU has too much latency |
| **Search ranking** | Run ranking models at microsecond latency | GPU batch-oriented; FPGA deterministic low-latency |
| **Compression / encryption** | Real-time data at line rate | CPU too slow per-watt; ASIC inflexible |
| **Storage offload** | Erasure coding, dedup, compression | CPU cycles are expensive for data movement |
| **AI inference** | Low-batch, low-latency model serving | GPU underutilized at batch=1 |
| **Financial (HFT)** | Tick-to-trade < 1 μs | Only FPGA delivers sub-microsecond pipeline |

---

## Acceleration Card Platforms

### AMD/Xilinx Alveo

| Card | FPGA | HBM | PCIe | Network | Use Case | Price Range |
|------|------|-----|------|---------|----------|-------------|
| **Alveo AU50** | VU9P (25M LUT) | 8 GB | Gen3 ×16 | — | General compute | $5K–$8K |
| **Alveo AU55N** | VU35P (8M LUT) | 32 GB | Gen3 ×16 | 2×100G | Networking + compute | $15K–$20K |
| **Alveo AU250** | VU33P (4M LUT) | — | Gen3 ×16 | — | Cost-effective compute | $4K–$6K |
| **Alveo AU280** | VU9P + HBM2 | 8 GB | Gen3 ×16 | — | Memory-intensive | $8K–$12K |
| **Alveo AU45T** | VU45P (8M LUT) | 16 GB | Gen4 ×16 | — | High-bandwidth | $12K–$15K |
| **Alveo SN1022** | 2×VU45P | 32 GB | Gen4 ×16 | 2×100G | SmartNIC | $20K–$30K |

### Intel/Altera Agilex-based Cards

| Card | FPGA | HBM | PCIe | Network | Use Case |
|------|------|-----|------|---------|----------|
| **Intel FPGA IPU F2000X** | Agilex 7 | 16 GB | Gen4 ×16 | 2×100G | SmartNIC |
| **Intel D5005** | Stratix 10 SX | — | Gen3 ×16 | — | General acceleration |
| **Silicom Melbourne** | Stratix 10 | — | Gen3 ×16 | 2×100G | SmartNIC |

### Silicom / Napatech / Mellanox (NVIDIA)

| Card | FPGA | Network | Target |
|------|------|---------|--------|
| **Napatech NT200A02** | Agilex 7 | 2×100G | SmartNIC |
| **NVIDIA ConnectX-6** | — (ASIC) | 2×100G | Baseline NIC (non-FPGA) |
| **NVIDIA BlueField-2** | — (ASIC + ARM) | 100G | DPU (non-FPGA, for comparison) |

---

## SmartNIC Architecture

### What Is a SmartNIC?

A SmartNIC adds programmable logic (FPGA or ASIC + processor) between the server's PCIe bus and the network, enabling:

1. **Line-rate packet processing** — no CPU involvement for common paths
2. **Offloaded security** — TLS/IPsec at 100G without CPU overhead
3. **NVMe-oF target** — remote storage without host CPU
4. **Custom telemetry** — per-flow counters at line rate
5. **Virtual switching** — OVS offload, VXLAN encap/decap

### FPGA SmartNIC Block Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                      FPGA (VU45P / Agilex)                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  100G    │  │  Packet  │  │   Match  │  │   Action │    │
│  │  MAC+PCS │─►│ Parser   │─►│  Action  │─►│ Executor │    │
│  │  (hard)  │  │(pipeline)│  │  Table   │  │(pipeline)│    │
│  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘    │
│       ▲                                          │          │
│       │                    ┌──────────┐          │          │
│       │                    │  DMA     │◄─────────┤          │
│       │                    │ Engine   │          │          │
│       │                    └────┬─────┘          │          │
│       │                         │                │          │
│  ┌────┴─────┐           ┌─────┴──────┐   ┌─────┴──────┐   │
│  │  100G    │           │  PCIe      │   │  Management│   │
│  │  MAC+PCS │           │  Gen4 x16  │   │  ARM / RISC│   │
│  │  (hard)  │           │  (hard)    │   │  -V core   │   │
│  └──────────┘           └────────────┘   └────────────┘   │
│       ▲                       ▲                             │
└───────┼───────────────────────┼─────────────────────────────┘
        │                       │
   Network QSFP28         Server PCIe slot
```

### P4 + FPGA Flow

P4 is the standard language for programming data-plane behavior on SmartNICs:

```
P4 source → P4 compiler → FPGA bitstream
  (data plane)  (vendor-specific)  (match-action tables)
```

| P4 Compiler | Target FPGA | Vendor |
|-------------|------------|--------|
| **P4->NetFPGA** | Xilinx 7-series | Princeton (open-source) |
| **Intel P4 Studio** | Agilex / Stratix 10 | Intel |
| **AMD P4** | Alveo / UltraScale+ | AMD |
| **x4c** | Any (via Xilinx switch) | Xilinx (open-source) |

---

## OPAF — Open Programmable Acceleration Framework

OPAF (originally OPAE — Open Programmable Acceleration Engine) is Intel's software framework for accessing FPGA accelerators from user-space applications.

### OPAF Architecture

```
┌──────────────────────────────────┐
│         User Application         │
│     (C/C++/Python/Go/Rust)      │
├──────────────────────────────────┤
│         OPAF SDK                 │
│  ┌─────────┐  ┌──────────────┐  │
│  │ libopae-c│  │ libopae-cxx  │  │
│  │ (C API)  │  │ (C++ API)    │  │
│  └────┬─────┘  └──────┬───────┘  │
│       └───────┬───────┘          │
├───────────────┼──────────────────┤
│          OPAF Linux Driver       │
│          (intel_fpga_pci)        │
├───────────────┼──────────────────┤
│          FPGA Hardware           │
│  ┌──────────┐  ┌──────────────┐ │
│  │ AFU      │  │ FME          │ │
│  │(Accel)   │  │(Management) │ │
│  └──────────┘  └──────────────┘ │
└──────────────────────────────────┘
```

| Component | Full Name | Role |
|-----------|----------|------|
| **FME** | FPGA Management Engine | Manages FPGA: reconfiguration, power, errors |
| **AFU** | Accelerator Functional Unit | User's acceleration logic (the bitstream) |
| **OPAF SDK** | Software Development Kit | User-space library for AFU access |
| **intel_fpga_pci** | Kernel driver | Maps AFU MMIO space to user process |

### OPAF Hello World (C)

```c
#include <opae/fpga.h>
#include <stdio.h>

int main() {
    fpga_token token;
    fpga_handle handle;
    fpga_properties filter;

    // Find FPGA accelerator
    fpgaGetProperties(NULL, &filter);
    fpgaPropertiesSetObjectType(filter, FPGA_ACCELERATOR);
    fpgaEnumerate(&filter, 1, &token, 1, NULL);

    // Open and map
    fpgaOpen(token, &handle, 0);

    // Write to AFU CSR (control-status register)
    uint64_t value = 0x1;
    fpgaWriteMMIO64(handle, 0, 0x40, value);

    // Read result
    uint64_t result;
    fpgaReadMMIO64(handle, 0, 0x48, &result);
    printf("Result: 0x%lx\n", result);

    fpgaClose(handle);
    fpgaDestroyProperties(&filter);
    return 0;
}
```

---

## OFS — Open FPGA Stack (AMD/Xilinx)

OFS is AMD/Xilinx's equivalent framework, providing a standardized hardware/software interface for Alveo and Agilex cards.

### OFS Architecture

```
┌──────────────────────────────────────────────┐
│              User Application                │
├──────────────────────────────────────────────┤
│         OFS Software Stack                   │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ OPAE SDK │  │  DPDK     │  │  OVS     │ │
│  │ (FPGA)   │  │ (network) │  │ (virtual │ │
│  │          │  │           │  │  switch) │ │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘ │
├───────┼──────────────┼──────────────┼────────┤
│       │    Linux Kernel Drivers     │        │
│       │    (fpga_pci, dfl)          │        │
├───────┼──────────────┼──────────────┼────────┤
│       │    FPGA Hardware            │        │
│  ┌────┴────┐  ┌─────┴────┐  ┌─────┴────┐   │
│  │ FIM     │  │  AFU     │  │  HSSI    │   │
│  │(FPGA    │  │(User     │  │(High-Speed│   │
│  │ Infra)  │  │ Accel)   │  │ Serial)  │   │
│  └─────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────┘
```

| Component | Full Name | Role |
|-----------|----------|------|
| **FIM** | FPGA Interface Manager | Board management: PCIe, HSSI, DDR, reset, PR |
| **AFU** | Accelerator Functional Unit | User's acceleration logic (partial reconfiguration region) |
| **DFL** | Device Feature List | Hardware discovery: enumerates FIM + AFU blocks |
| **HSSI** | High-Speed Serial Interface | 100G/200G Ethernet MAC + PHY |

### OFS Build Flow

```bash
# Clone OFS repository
git clone https://github.com/OFS/ofs-n3000.git
cd ofs-n3000

# Build FIM (board infrastructure)
ofs.py build fim --target n3000

# Build AFU (user accelerator)
ofs.py build afu --target n3000 --afu my_accelerator

# Combine FIM + AFU into full bitstream
ofs.py build image --target n3000
```

---

## Deployment Models

### 1. Full-FPGA Reconfiguration

Replace the entire bitstream per workload. Simple but slow (seconds).

| Advantage | Disadvantage |
|-----------|-------------|
| Full FPGA available | Reconfiguration time (1–10 seconds) |
| No resource fragmentation | Requires full rebuild for changes |
| Simple management | Can't multiplex workloads |

### 2. Partial Reconfiguration (DFX)

Swap only the AFU region while FIM remains active. Fast (milliseconds).

```
┌────────────────────────────────────┐
│              FPGA                  │
│  ┌──────────────────────────────┐ │
│  │  FIM (static region)         │ │
│  │  - PCIe DMA                 │ │
│  │  - DDR controller            │ │
│  │  - HSSI MAC                  │ │
│  │  - Management                │ │
│  └──────────────┬───────────────┘ │
│                 │                 │
│  ┌──────────────▼───────────────┐ │
│  │  PR Region (swapable AFU)    │ │
│  │  ┌─────┐  ┌─────┐  ┌─────┐ │ │
│  │  │ AFU │  │ AFU │  │ AFU │ │ │
│  │  │ #0  │  │ #1  │  │ #2  │ │ │
│  │  └─────┘  └─────┘  └─────┘ │ │
│  └──────────────────────────────┘ │
└────────────────────────────────────┘
```

### 3. Multi-Tenant (Virtual FPGA)

Allocate AFU slots to different VMs or containers:

```
┌───────────────────────────────────────┐
│                FPGA                    │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │ VM1 AFU │ │ VM2 AFU │ │Host AFU│ │
│  │ (VFs)   │ │ (VFs)   │ │ (PF)   │ │
│  └─────────┘ └─────────┘ └────────┘ │
│  ┌──────────────────────────────────┐│
│  │  FIM + IOMMU + PR manager       ││
│  └──────────────────────────────────┘│
└───────────────────────────────────────┘
```

**SR-IOV:** Each AFU appears as a Virtual Function (VF). The FIM manages isolation.

---

## Performance Considerations

### PCIe Bandwidth

| Generation | ×1 | ×4 | ×8 | ×16 |
|-----------|-----|-----|-----|------|
| Gen3 | ~1 GB/s | ~4 GB/s | ~8 GB/s | ~16 GB/s |
| Gen4 | ~2 GB/s | ~8 GB/s | ~16 GB/s | ~32 GB/s |
| Gen5 | ~4 GB/s | ~16 GB/s | ~32 GB/s | ~64 GB/s |

**For 100G line-rate processing:** Minimum PCIe Gen3 ×16 or Gen4 ×8 to sustain full duplex.

### HBM Bandwidth

| Card | HBM Size | HBM Bandwidth | Use Case |
|------|----------|--------------|----------|
| AU55N | 32 GB | ~460 GB/s | Search ranking, large models |
| AU45T | 16 GB | ~460 GB/s | Memory-intensive compute |
| AU280 | 8 GB | ~460 GB/s | Genome sequencing, databases |

### Latency Budget (Typical 100G SmartNIC)

| Stage | Latency |
|-------|---------|
| Packet arrival (QSFP28) | 0 ns |
| PHY + PCS | 50–100 ns |
| MAC (parse) | 20–50 ns |
| Match-action pipeline | 100–200 ns |
| DMA to host memory | 500–1000 ns |
| Host kernel processing | 5–50 μs |
| **Total (fast path, no host)** | **200–400 ns** |
| **Total (with host DMA)** | **700–1300 ns** |

---

## Open-Source Data Center FPGA Projects

| Project | Organization | Target | Focus |
|---------|-------------|--------|-------|
| **OFS** | AMD/Xilinx | Alveo | Full FPGA stack (hardware + software) |
| **OPAE** | Intel | Agilex, Stratix 10 | Software framework |
| **FireSim** | UC Berkeley | AWS F1 | RISC-V SoC prototyping on cloud FPGA |
| **Corundum** | Alex Forencich | Various | 100G open-source NIC |
| **NetFPGA SUME** | Stanford | VC709 | Teaching/research 10G NIC |
| **P4-NetFPGA** | Princeton | NetFPGA | P4 → FPGA compilation |

---

## Cross-References

| Topic | Article |
|-------|---------|
| FPGA as a Service (cloud) | [FPGA as a Service](fpga_as_a_service.md) |
| Networking & SmartNICs | [Networking & SmartNICs](networking_smartnics.md) |
| Hardware security | [Hardware Security](hardware_security.md) |
| DFX / partial reconfiguration | [DFX](dfx_partial_reconfiguration.md) |
| PCIe bringup | [PCIe Bringup](../15_case_studies/pcie_bringup.md) |
| Transceivers | [Transceivers](../06_ip_and_cores/transceivers/transceiver_basics.md) |