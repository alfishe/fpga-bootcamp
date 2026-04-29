[<- Phase 16 Home](README.md) · [<- Project Home](../../README.md)

# Hardware Security & Trust (SecOps)

As FPGAs enter critical infrastructure, securing the bitstream and the execution environment is paramount to prevent IP theft, cloning, and malicious tampering.

## Core Security Features
*   **Secure Boot**: AES-GCM encrypted bitstreams and RSA/ECDSA authentication.
*   **Physical Unclonable Functions (PUFs)**: Deriving encryption keys from microscopic variations in the silicon.
*   **ARM TrustZone**: Isolating secure operating systems (e.g., OP-TEE) from the rich OS (Linux) in SoC FPGAs.

*(This is a stub. Expand with eFuse programming guides and threat models.)*
