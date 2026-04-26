[← Others Home](../README.md) · [← Section Home](../../README.md)

# Achronix Speedster7t — 7nm Networking & AI FPGA

Speedster7t is a high-end FPGA designed for 400G/800G network line cards and AI inference acceleration. Uses a **2D network-on-chip** instead of traditional routing fabric, clocking at ~2 GHz.

---

| Feature | Specification |
|---|---|
| **Process** | 7nm |
| **MLP (ML Processors)** | 256–1,536 blocks: INT8/FP16/FP32/Block FP |
| **2D NoC** | 256-bit bi-directional, ~20 Tbps per port |
| **SerDes** | Up to 72× 112 Gbps PAM4 |
| **PCIe** | Gen5 x16 |
| **Ethernet** | Hard 400G MAC × 8 |
| **GDDR6** | 4× 8 GB HBM-equivalent bandwidth (lower cost than HBM) |
| **Target** | Smart NICs, 5G, AI training offload |

Achronix is only relevant for >100 Gbps per-port networking or edge datacenter ML inference. Development kits start at ~$10K.

---

## Development Boards

### Achronix (First-Party)

| Board | FPGA | Notable Features | Approx. Price | Best For |
|---|---|---|---|---|
| **Speedster7t AC7t1500 Dev Kit** | AC7t1500 | 112G PAM4 SerDes ×72, GDDR6 8 GB ×4, PCIe Gen5 ×16, QSFP-DD ×4, 400G Eth hard MAC ×8 | ~$10,000+ | 400G/800G networking + AI inference eval |

### Choosing a Board

| You want... | Get... |
|---|---|
| 400G/800G networking evaluation | Speedster7t AC7t1500 Dev Kit |
| Note: development kits start at ~$10K | For production, contact Achronix directly |

---

## References

| Source | Path |
|---|---|
| Speedster7t | https://www.achronix.com/products/speedster7t |
