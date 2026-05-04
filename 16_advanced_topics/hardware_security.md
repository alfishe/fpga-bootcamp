[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Hardware Security & Trust (SecOps)

As FPGAs enter critical infrastructure — financial trading, 5G base stations, automotive ADAS, defense systems — securing the bitstream and the execution environment is paramount to prevent IP theft, cloning, and malicious tampering. This article covers the threat landscape, cryptographic primitives, key management, side-channel countermeasures, and ARM TrustZone integration unique to FPGA SoCs.

> **Prerequisites:** This article builds on [configuration.md](../02_architecture/infrastructure/configuration.md) (encryption/authentication hardware), [bitstream.md](../03_design_flow/bitstream.md) (encryption in the bitstream pipeline), and the per-vendor secure boot articles: [boot_flow_xilinx_zynq.md](../10_embedded_linux/02_boot_flow/boot_flow_xilinx_zynq.md), [boot_flow_intel_soc.md](../10_embedded_linux/02_boot_flow/boot_flow_intel_soc.md), [boot_flow_microchip_soc.md](../10_embedded_linux/02_boot_flow/boot_flow_microchip_soc.md).

---

## 1. Threat Model for FPGA Systems

### 1.1 Attack Surfaces

| Attack Surface | Example | Risk Level |
|---|---|---|
| **Bitstream extraction** | Read SPI flash with clip-on programmer; dump via JTAG | High — IP theft, cloning |
| **Bitstream modification** | Flip bits in flash to insert backdoors | High — supply chain attack |
| **Side-channel analysis** | DPA to extract AES key during bitstream decryption | Medium — requires lab equipment |
| **Fault injection** | Voltage glitch during boot to bypass authentication | Medium — requires physical access |
| **Remote exploit** | Linux kernel vulnerability → FPGA register tampering | Medium — network-accessible |
| **Supply chain** | Counterfeit or tampered FPGA installed during manufacturing | Low — but catastrophic if it occurs |
| **Insider threat** | Engineer leaks AES key or bitstream to competitor | High — hard to detect |

### 1.2 What Each Attack Achieves

```
┌─────────────────────── Attack Goal ──────────────────────┐
│                                                          │
│  IP Theft          Cloning          Tampering            │
│  ┌────────│─┐      ┌─────────┐     ┌───────────┐         │
│  │Extract   │      │Copy     │     │Modify     │         │
│  │bitstream │      │bitstream│     │bitstream  │         │
│  │→ reverse │      │→ program│     │→ insert   │         │
│  │  engineer│      │  clone  │     │  backdoor │         │
│  └────────│─┘      └─────────┘     └───────────┘         │
│       ▲                ▲                ▲                │
│       │                │                │                │
│  ┌────┴────┐    ┌──────┴─────┐   ┌──────┴──────┐         │
│  │Flash    │    │No authen-  │   │No authenti- │         │
│  │read +   │    │tication on │   │cation on    │         │
│  │no encry-│    │bitstream   │   │bitstream    │         │
│  │ption    │    │            │   │             │         │
│  └─────────┘    └────────────┘   └─────────────┘         │
└──────────────────────────────────────────────────────────┘
```

**Key insight:** Encryption prevents IP theft and cloning. Authentication prevents tampering. You need **both**.

---

## 2. Bitstream Encryption Deep Dive

### 2.1 AES-CBC vs AES-GCM

| Property | AES-256-CBC | AES-256-GCM |
|---|---|---|
| **Confidentiality** | Yes | Yes |
| **Integrity/authentication** | No (needs separate HMAC) | Yes (built-in GMAC tag) |
| **Bit-flip attack** | Vulnerable — attacker can flip bits and decrypt modified bitstream | Protected — any modification invalidates GMAC tag |
| **Performance** | Same encryption speed | ~5% overhead for tag computation |
| **Standard** | FIPS 46-3 (legacy) | NIST SP 800-38D (modern) |

**Why GCM matters:** With AES-CBC, an attacker who can modify the encrypted bitstream in flash can flip specific bits that propagate predictably through the CBC decryption. This allows targeted modifications (e.g., changing a single LUT value to insert a backdoor) without knowing the key. AES-GCM prevents this — any modification is detected by the authentication tag.

### 2.2 Vendor Encryption Support

| Vendor | AES Mode | Key Length | Key Storage | Authentication | Notes |
|---|---|---|---|---|---|
| **Xilinx 7-series** | CBC | 256-bit | eFUSE or BBRAM | RSA-2048 + HMAC (separate) | CBC vulnerable to bit-flip; HMAC is optional |
| **Xilinx UltraScale+** | GCM | 256-bit | eFUSE or BBRAM | RSA-4096 + HMAC | GCM is standard; authentication mandatory |
| **Intel Cyclone V** | CBC | 256-bit | eFUSE or volatile | HMAC-SHA-256 | CBC mode; HMAC optional |
| **Intel Agilex** | GCM | 256-bit | PUF + eFUSE | ECDSA P-384 | GCM + ECDSA; strongest stack |
| **Lattice ECP5** | ECB | 128-bit | eFUSE | None | ECB is weakest mode; no authentication |
| **Microchip PolarFire** | CBC | 256-bit | eFUSE + DSN | ECDSA P-384 | DSN binding adds device-unique protection |

> **Lattice ECP5 warning:** AES-128-ECB provides the weakest encryption. Identical plaintext blocks produce identical ciphertext blocks, enabling pattern analysis. No authentication means bit-flip attacks are trivial. Not recommended for high-security applications.

### 2.3 BBRAM vs eFUSE Key Storage

| Property | BBRAM (Battery-Backed RAM) | eFUSE (One-Time Programmable) |
|---|---|---|
| **Volatility** | Volatile — key lost if battery dies | Permanent — key survives power cycles |
| **Re-programmable** | Yes — can update key | No — once blown, cannot change |
| **Key extraction risk** | Lower — key not in permanent storage | Higher — fuse values can be read with SEM/FIB |
| **Lifecycle** | Battery lifetime (5–10 years typical) | Device lifetime |
| **Supported by** | Xilinx 7-series / UltraScale+ | All vendors |

**Recommendation:** Use BBRAM for development (keys can be rotated). Use eFUSE for production (keys survive battery failure). Some designs use both: BBRAM for AES key, eFUSE for RSA public key hash.

---

## 3. Bitstream Authentication

### 3.1 Why Authentication Matters Even With Encryption

Encryption alone does **not** prevent tampering. An attacker can:
1. Flip bits in the encrypted bitstream stored in flash
2. The FPGA decrypts the modified bitstream using the correct AES key
3. The resulting plaintext has predictable corruption from CBC bit-flip propagation
4. This may disable a security check or insert a useful glitch

Authentication (digital signature) ensures the bitstream was signed by the designer and has not been modified.

### 3.2 Algorithm Comparison

| Algorithm | Key Size | Signature Size | Verification Time (FPGA) | Quantum Resistance |
|---|---|---|---|---|
| **RSA-2048** | 2048-bit | 256 bytes | ~50 ms | None |
| **RSA-4096** | 4096-bit | 512 bytes | ~200 ms | None |
| **ECDSA P-256** | 256-bit | 64 bytes | ~30 ms | None |
| **ECDSA P-384** | 384-bit | 96 bytes | ~50 ms | None |
| **HMAC-SHA-256** | 256-bit | 32 bytes | ~1 ms | None |
| **HMAC-SHA3-384** | 384-bit | 48 bytes | ~2 ms | Partial (larger hash) |

**Key differences:**
- **RSA vs ECDSA:** ECDSA provides equivalent security with much smaller keys and signatures. RSA-2048 ≈ ECDSA P-256; RSA-4096 ≈ ECDSA P-384.
- **HMAC vs digital signatures:** HMAC uses a shared secret (symmetric) — the FPGA must know the HMAC key. RSA/ECDSA use public-key cryptography — the FPGA stores only the public key hash. HMAC is faster but provides weaker assurance (insider with the HMAC key can forge signatures).
- **Quantum threat:** All listed algorithms are vulnerable to quantum computing attacks. Post-quantum algorithms (CRYSTALS-Dilithium, SPHINCS+) are not yet implemented in FPGA silicon.

---

## 4. Physical Unclonable Functions (PUFs)

### 4.1 How PUFs Work

A PUF derives a unique cryptographic key from microscopic manufacturing variations in the silicon — no two chips produce the same output, even with identical masks.

```
┌── PUF Challenge-Response ──┐
│                            │
│  Challenge (input)         │
│      │                     │
│      ▼                     │
│  ┌─────────────┐           │
│  │ SRAM cells  │           │  ← Power-on state is random
│  │ Ring osc.   │           │  ← Frequency varies per die
│  │ Arbiter     │           │  ← Race condition varies
│  └─────────────┘           │
│      │                     │
│      ▼                     │
│  Response (unique key)     │
│  = f(challenge, silicon)   │
│                            │
└────────────────────────────┘
```

### 4.2 PUF Types

| PUF Type | Source | Entropy | Reproducibility | Vendor Use |
|---|---|---|---|---|
| **SRAM PUF** | Power-on state of SRAM cells | High | ~95% stable; needs error correction | Xilinx UltraScale+, Intel Agilex |
| **Ring Oscillator PUF** | Frequency difference between ring oscillators | Medium | ~90% stable; temperature-sensitive | Research; not in production FPGAs |
| **Butterfly PUF** | LUT feedback loop settling state | Medium | ~92% stable | Research only |

### 4.3 PUF Key Enrollment

PUF responses are noisy — they vary slightly between power cycles. A **Key Reconstruction** process uses error correction (BCH or Reed-Muller codes) and a stored **Helper Data** to reproduce the exact same key every time:

```
Enrollment (one-time, in factory):
    PUF response → Error correction → Helper Data stored in eFUSE
    PUF response → Key Derivation → AES key (wrapped and stored)

Reconstruction (every boot):
    PUF response + Helper Data → Error correction → Original PUF response
    → Key Derivation → AES key → Decrypt bitstream
```

**Security property:** The helper data alone does not reveal the key. An attacker who reads the eFUSE helper data cannot reconstruct the PUF key without the physical chip.

### 4.4 Vendor PUF Implementations

| Vendor | PUF Type | Device Families | Key Reconstruction | Use Case |
|---|---|---|---|---|
| **Xilinx** | SRAM PUF | UltraScale+ Zynq MPSoC, Versal | Built-in PUF registration + reconstruction | AES key derivation; no eFUSE needed for AES key |
| **Intel** | SRAM PUF | Agilex 5, Agilex 7 | SDM (Secure Device Manager) PUF module | AES-GCM key; anti-rollback |
| **Microchip** | N/A | PolarFire | No PUF — uses DSN binding instead | Device-unique encryption via DSN |

---

## 5. eFuse Programming — Irreversible Operations

### 5.1 What eFuses Store

| Data | Size | Purpose |
|---|---|---|
| **AES encryption key** | 256 bits | Bitstream decryption |
| **RSA/ECDSA public key hash** | 256–384 bits | Boot image authentication |
| **HMAC key** | 256 bits | Bitstream authentication (Cyclone V) |
| **Security policy bits** | ~32 bits | Force secure boot, disable JTAG, etc. |
| **Anti-rollback counter** | 32–64 bits | Prevent firmware downgrade |
| **PUF helper data** | Variable | Error correction for PUF key reconstruction |
| **Device DNA / Chip ID** | 57–128 bits | Factory-programmed unique identifier |

### 5.2 Irreversible Operations Checklist

> [!WARNING]
> **Once eFUSEs are blown, they CANNOT be reversed.** The following operations are permanent:

| Operation | Effect | Recovery |
|---|---|---|
| Program AES key into eFUSE | Device now requires encrypted bitstream | None — all future bitstreams must be encrypted with this key |
| Program RSA public key hash | Device only boots authenticated images | None — must have the corresponding private key to sign all future images |
| Set `FORCE_SECURE_BOOT` | Boot ROM rejects unsigned images | None |
| Set `DISABLE_JTAG` | JTAG boundary scan permanently disabled | None — no JTAG recovery possible |
| Set `SEC_LOCK` (Xilinx) | Full debug lock + force secure boot | None — device is permanently locked |
| Increment anti-rollback counter | Firmware version cannot be downgraded below this value | None — counter only increments |

### 5.3 Production eFuse Programming Workflow

```
1. Test complete secure boot flow on development device (BBRAM/volatile key)
2. Verify: encrypted + authenticated bitstream boots correctly
3. Verify: JTAG access still works for debug
4. Verify: fallback/recovery mechanism is documented
5. ── PRODUCTION GATE ──
6. Program AES key into eFUSE
7. Program RSA/ECDSA public key hash into eFUSE
8. Test: encrypted + authenticated bitstream boots on production device
9. Set FORCE_SECURE_BOOT (if required)
10. Set DISABLE_JTAG (if required — only after field deployment)
11. Document: key storage location, key rotation procedure, recovery plan
```

---

## 6. Unique Device Identity

| Vendor | Identifier | Size | Access Method | Use |
|---|---|---|---|---|
| **Xilinx** | Device DNA | 57-bit (7-series), 96-bit (UltraScale+) | `DNA_PORT` primitive (7-series), `EFUSE_USR` (UltraScale+) | Anti-cloning: encrypt bitstream bound to device DNA |
| **Intel** | Chip ID | 57-bit (Cyclone V), 256-bit (Agilex) | JTAG `IDCODE` register, or soft register | Anti-cloning: DSN-bound encryption |
| **Microchip** | Design Serial Number (DSN) | 128-bit | MSS register; accessible from Linux | Anti-cloning: bitstream encrypted and bound to DSN |

**Anti-cloning pattern:**
```verilog
// Xilinx 7-series — read Device DNA at runtime
DNA_PORT #(
    .SIM_DNA_VALUE(57'h0)  // For simulation only
) dna_inst (
    .CLK   (clk),
    .READ  (dna_read),
    .DIN   (1'b0),
    .DOUT  (dna_bit),
    .SHIFT (dna_shift)
);

// Compare DNA against expected value
// If mismatch → zeroize sensitive registers → halt
```

---

## 7. Side-Channel Attacks and Countermeasures

### 7.1 Attack Types

| Attack | What It Targets | Equipment Cost | Success Rate |
|---|---|---|---|
| **DPA (Differential Power Analysis)** | AES key during bitstream decryption | $1K–$10K (oscilloscope + shunt resistor) | High — well-documented on 7-series |
| **CPA (Correlation Power Analysis)** | Same as DPA, different statistical method | $1K–$10K | High |
| **EM (Electromagnetic)** | AES key via near-field EM probe | $5K–$50K (EM probe + spectrum analyzer) | Medium — requires precise probe placement |
| **Timing** | Cache timing, branch timing | $0 (software-only) | Low on FPGA (no caches in fabric) |
| **Voltage glitch** | Skip authentication check | $500–$5K (glitch generator) | Medium — precise timing required |
| **Clock glitch** | Same as voltage glitch | $500–$5K | Medium |
| **Optical / FIB** | Direct read of eFUSE values | $100K+ (FIB workstation) | High — but very expensive |

### 7.2 Vendor Countermeasures

| Countermeasure | Xilinx UltraScale+ | Intel Agilex | Microchip PolarFire |
|---|---|---|---|
| **DPA countermeasures** | Yes — internal key processing randomized | Yes — SDM hardened crypto engine | Yes — FIPS 140-2 certified |
| **Decryption key never exposed** | Key stays in dedicated crypto block | Key stays in SDM | Key stays in secure enclave |
| **Tamper monitors** | Temperature (select devices) | Voltage/temperature monitors | Voltage + temperature + clock glitch monitors |
| **Zeroization on tamper** | No (not standard) | Select devices | Yes — wipes sNVM and keys |
| **JTAG secure access** | Secure JTAG (authenticated) | JTAG secure mode | JTAG disable via eFuse |

### 7.3 DPA Mitigation for Designers

Even with vendor countermeasures, your own design can leak information:

1. **Avoid key-dependent branches** in FPGA fabric — use constant-time comparisons
2. **Use hardware crypto engines** (hard IP) instead of soft RTL AES when available
3. **Randomize processing order** for batch operations (e.g., encrypt multiple blocks in shuffled order)
4. **Add dummy operations** to equalize power consumption across different key values
5. **Shield critical signals** — internal routing is harder to probe than IO

---

## 8. JTAG Security

### 8.1 The JTAG Attack Surface

JTAG provides full access to:
- **Boundary scan** — read/write every IO pin (can extract secret data from pin states)
- **Internal configuration access** — read back bitstream via `JTAG2AXI` or `ICAP`
- **Debug access** — halt CPU, inspect registers, single-step (on SoC FPGAs)
- **Flash programming** — replace bitstream in SPI flash

### 8.2 JTAG Security Options

| Option | What It Does | Irreversible? | When to Use |
|---|---|---|---|
| **No protection** | JTAG fully accessible | No | Development only |
| **Secure JTAG** | JTAG requires authentication (shared secret) | No — can be reconfigured | Production with field debug access |
| **JTAG disable** | Permanently disables JTAG TAP controller | Yes (eFUSE) | Production — no field debug needed |
| **JTAG in secure region** | JTAG only accessible from secure world (TrustZone) | No | SoC FPGAs with ARM TrustZone |

**Xilinx Secure JTAG:** Uses a shared HMAC key. The JTAG host must provide the correct HMAC response before TAP access is granted. Key is programmed into eFUSE or BBRAM.

**Intel JTAG Secure Mode:** Similar concept — JTAG access requires a key exchange before the TAP is unlocked.

---

## 9. ARM TrustZone on FPGA SoCs

### 9.1 Architecture

On ARM-based FPGA SoCs (Zynq MPSoC, Agilex SoC), TrustZone partitions the system into **Secure World** and **Normal World**:

```
┌─────────────────────────────────────────────────────────┐
│                    SoC FPGA                             │
│                                                         │
│  ┌─── Secure World ────────┐  ┌─── Normal World ──────┐ │
│  │  OP-TEE (secure OS)     │  │  Linux (rich OS)      │ │
│  │  Secure key storage     │  │  User applications    │ │
│  │  Secure boot verifier   │  │  Network stack        │ │
│  └──────────┬──────────────┘  └───────────┬───────────┘ │
│             │                             │             │
│  ┌──────────▼─────────────────────────────▼───────────┐ │
│  │            TrustZone Controller (TZC-400)          │ │
│  │  Enforces secure/non-secure memory regions         │ │
│  └────────────────────────────────────────────────────┘ │
│             │                             │             │
│  ┌──────────▼─────────────────────────────▼───────────┐ │
│  │            FPGA Fabric                             │ │
│  │  Secure peripherals    │  Normal peripherals       │ │
│  │  (key manager, crypto) │  (DMA, video, network)    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 9.2 TrustZone Components

| Component | Function | Present In |
|---|---|---|
| **TZC-400** | Memory access controller — filters AXI transactions by secure/non-secure attribute | Zynq MPSoC, Agilex SoC |
| **ARM Cortex-A53/A55** | CPU with secure/non-secure exception levels (EL3 → S-EL1 → NS-EL1) | Zynq MPSoC, Agilex SoC |
| **OP-TEE** | Open-source Trusted Execution Environment (secure OS) | Zynq MPSoC, Agilex SoC |
| **APU GIC** | Interrupt controller with secure/non-secure interrupt groups | Zynq MPSoC |

### 9.3 FPGA Fabric Access from Secure World

The FPGA fabric can be partitioned so that secure-world software accesses crypto accelerators and key storage, while normal-world Linux accesses data-path peripherals:

```dts
// Device tree — secure FPGA peripheral
secure_crypto: crypto@80000000 {
    compatible = "mycorp,secure-crypto";
    reg = <0x0 0x80000000 0x0 0x10000>;
    status = "okay";
    // This region is marked secure in TZC-400 configuration
    // Linux (Normal World) CANNOT access this address range
};
```

**Practical note:** TZC-400 configuration is typically done in the FSBL/ARM Trusted Firmware (ATF) at boot time. Linux never sees the secure peripherals — they are physically inaccessible from the Normal World.

---

## 10. Anti-Tamper and Zeroization

### 10.1 Tamper Detection

| Sensor | What It Detects | Vendors |
|---|---|---|
| **Voltage monitor** | Under-voltage (glitch injection), over-voltage (fault probe) | Microchip SmartFusion2, PolarFire |
| **Temperature monitor** | Heating for fault injection, freezing for data retention attacks | Microchip, select Xilinx |
| **Clock glitch monitor** | Abnormal clock frequency or missing clock edges | Microchip PolarFire |
| **Tamper mesh** | Physical intrusion into package (laser decapping) | Microchip SmartFusion2 |

### 10.2 Zeroization

When a tamper event is detected, the device **zeroizes** — permanently destroys sensitive data:

| What Gets Zeroized | Vendors |
|---|---|
| AES decryption key (volatile key register) | All vendors with volatile key storage |
| BBRAM key | Xilinx (if tamper-detect pin is asserted) |
| sNVM (secure non-volatile memory) contents | Microchip |
| PUF-reconstructed key | Intel Agilex (SDM clears reconstructed key) |
| FPGA configuration (full device reset) | All vendors |

**Recovery after zeroization:** The device must reboot and re-establish the chain of trust from the Boot ROM. Keys stored in eFUSE survive zeroization (they're permanent). Only volatile/cached copies are destroyed.

---

## 11. PR Security (Partial Reconfiguration)

Partial reconfiguration introduces a new attack surface: the partial bitstream. See [dfx_partial_reconfiguration.md](dfx_partial_reconfiguration.md) for the full PR article.

| Threat | Mitigation | Vendor Support |
|---|---|---|
| **Unauthorized RM loading** | Encrypt + authenticate partial bitstreams | Xilinx UltraScale+: AES-GCM on partial bitstreams. Intel Agilex: PR security with ECDSA |
| **RM tampering** | Authenticate partial bitstream before ICAP/PR IP accepts it | Xilinx: HMAC verification in ICAP. Intel: PR IP signature check |
| **RM reads secret data from static region** | Decoupler IP + memory isolation between static and RP | Designer responsibility — no vendor enforcement |
| **Rollback to vulnerable RM** | Anti-rollback counter in eFUSE, verified before PR load | Xilinx UltraScale+: supported. Intel Agilex: supported |

**Xilinx PR encryption:**
```tcl
# Generate encrypted partial bitstream
set_property BITSTREAM.ENCRYPTION.ENCRYPT TRUE [current_design]
set_property BITSTREAM.ENCRYPTION.KEY0 256'h... [current_design]
write_bitstream -cell inst_rp -force rm_encrypted_partial.bit
```

---

## 12. Key Management Best Practices

### 12.1 Key Hierarchy

```
┌─── Master Key (HSM) ────────────────────────────────┐
│  Stored in Hardware Security Module                 │
│  Never leaves the HSM                               │
│                                                     │
│  ├─► Firmware Signing Key (RSA-4096 / ECDSA P-384)  │
│  │    Signs: FSBL, U-Boot, kernel, bitstream        │
│  │                                                  │
│  ├─► Bitstream Encryption Key (AES-256-GCM)         │
│  │    Encrypts: full and partial bitstreams         │
│  │                                                  │
│  └─► Device Provisioning Key                        │
│       Injects: eFUSE keys during manufacturing      │
└─────────────────────────────────────────────────────┘
```

### 12.2 Development vs Production Keys

| Aspect | Development | Production |
|---|---|---|
| **AES key storage** | BBRAM / volatile | eFUSE / PUF |
| **Signing key** | Self-generated test key | HSM-protected production key |
| **JTAG** | Enabled | Disabled or Secure JTAG |
| **Secure boot** | Optional | Mandatory |
| **Key rotation** | Yes (change BBRAM key) | No (eFUSE is permanent) |
| **Anti-rollback** | Disabled | Enabled |

### 12.3 Key Rotation Strategy

Since eFUSE keys cannot be changed, plan for key revocation:

1. **Program multiple key slots** (Xilinx UltraScale+ supports up to 4 AES key slots in eFUSE)
2. **Use key revocation registers** — if Key Slot 0 is compromised, set the revocation bit and switch to Key Slot 1
3. **Maintain a key escrow** — store backup keys in an HSM with multi-party authorization
4. **Version your signing keys** — include a key ID in the signed image header; Boot ROM checks the key ID against valid eFUSE entries

---

## 13. Regulatory and Compliance Frameworks

| Framework | Domain | FPGA Security Requirements |
|---|---|---|
| **FIPS 140-2/3** | Cryptographic modules (US government) | AES key must never leave the cryptographic boundary. Requires physical tamper evidence. Microchip PolarFire is FIPS 140-2 certified. |
| **DO-254** | Avionics (airborne systems) | Design assurance for complex hardware. Requires configuration management, traceability, and verification. |
| **IEC 62443** | Industrial control systems | Security levels (SL 1–4) for networked devices. FPGAs in SCADA/ICS must support secure boot and encrypted updates. |
| **Common Criteria (ISO 15408)** | General IT security evaluation | EAL levels (1–7). FPGA secure boot chains can contribute to EAL 4+ evaluations. |
| **ARM PSA (Platform Security Architecture)** | IoT / embedded | Root of Trust implementation requirements. TrustZone-based secure boot qualifies. |
| **NIST SP 800-193** | Firmware resiliency | Requires secure update, fail-safe recovery, and immutable root of trust. FPGA multi-boot + secure boot satisfies this. |

---

## References

| Document | Source | What It Covers |
|---|---|---|
| [UG821 — Zynq UltraScale+ Device Security](https://docs.amd.com/r/en-US/ug821-zynq-ultrascale-devices) | AMD/Xilinx | Zynq MPSoC security: PUF, secure boot, key management |
| [UG1220 — Vivado Design Suite Security](https://docs.amd.com/r/en-US/ug1220-vivado-security) | AMD/Xilinx | Bitstream encryption, authentication, secure JTAG |
| [Agilex 7 Security User Guide](https://docs.altera.com/r/docs/683750/25.1/agilextm-7-f-series-security-user-guide) | Altera | Agilex security: PUF, SDM, AES-GCM, ECDSA |
| [Agilex 5 Security User Guide](https://docs.altera.com/r/docs/813775/25.3.1/device-configuration-user-guide-agilextm-5-fpgas-and-socs) | Altera | Agilex 5 security features and configuration |
| [Microchip PolarFire SoC Security](https://www.microchip.com/en-us/products/fpgas-and-plds/fpga-design-resources) | Microchip | DSN binding, tamper detection, FIPS 140-2 |
| [NIST SP 800-38D — GCM Specification](https://csrc.nist.gov/pubs/sp/800/38/d/final) | NIST | AES-GCM specification (the mode all modern FPGAs should use) |
| [FIPS 140-3 — Security Requirements](https://csrc.nist.gov/pubs/fips/140-3/final) | NIST | Cryptographic module security requirements |
| [Configuration & Bitstream](../02_architecture/infrastructure/configuration.md) | This KB | Encryption hardware, authentication, anti-tamper |
| [Bitstream Generation](../03_design_flow/bitstream.md) | This KB | Encryption in the bitstream pipeline |
| [Zynq Secure Boot Chain](../10_embedded_linux/02_boot_flow/boot_flow_xilinx_zynq.md) | This KB | bootgen, eFuse programming, RSA authentication |
| [Cyclone V & Agilex Secure Boot](../10_embedded_linux/02_boot_flow/boot_flow_intel_soc.md) | This KB | Security policy bits, ECDSA on Agilex |
| [PolarFire DSN & Tamper Detection](../10_embedded_linux/02_boot_flow/boot_flow_microchip_soc.md) | This KB | Device Serial Number binding, zeroization |
| [DFX / Partial Reconfiguration](dfx_partial_reconfiguration.md) | This KB | PR security for partial bitstreams |
| [OpenTitan](../12_open_source_open_hardware/initiatives/opentitan.md) | This KB | Open-source root of trust |
