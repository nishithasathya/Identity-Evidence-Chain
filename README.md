# Identity-Evidence-Chain

### From Face Discovery to Verifiable Evidence

Identity-Evidence-Chain is an end-to-end system that transforms a face image into **discoverable, structured, and independently verifiable web evidence**.

The core idea is simple: finding a matching result online is only the beginning. Our system creates an evidence trail that connects **discovery, evidence extraction, cryptographic integrity, and verification** in one pipeline.

## The Pipeline

```text
Face Image
    ↓
Face Detection & Encoding
    ↓
Live Reverse-Image / Web Search
    ↓
Public Web Evidence
    ↓
Evidence Structuring
    ↓
Cryptographic Fingerprint
    ↓
Blockchain Anchoring
    ↓
Independent Verification
```

## How It Works

### 1. Face Processing

The input image is processed using face detection and encoding to obtain a machine-readable representation of the detected face.

The system handles cases such as missing or unusable faces instead of assuming every input is valid.

### 2. Live Evidence Discovery

The system performs a **genuine live reverse-image/web search** to discover publicly available evidence associated with the input image.

Search results are processed into a structured evidence package containing relevant information such as:

```json
{
  "matched_url": "...",
  "platform": "...",
  "image_url": "...",
  "caption": "...",
  "author": "...",
  "timestamp": "...",
  "confidence": 0.95
}
```

The system does not rely on a pre-selected or hardcoded result.

### 3. Evidence Fingerprinting

Once evidence is discovered, it is converted into a deterministic representation and processed using **SHA-256**.

```text
Evidence
    ↓
Canonical Representation
    ↓
SHA-256
    ↓
Unique Evidence Fingerprint
```

This fingerprint represents the exact state of the evidence at the time it was recorded.

### 4. Blockchain Anchoring

The cryptographic fingerprint is recorded through a Solidity smart contract on an Ethereum-compatible blockchain.

The blockchain is used as an **integrity layer**, rather than as a database for storing the complete evidence.

```text
Evidence → SHA-256 Fingerprint → Blockchain
```

### 5. Independent Verification

At any later point, the evidence can be processed again to generate a new fingerprint.

```text
Current Evidence
      ↓
   SHA-256
      ↓
Compare with On-Chain Fingerprint
      ↓
 ┌───────────────┐
 │ Match         │ → ✓ Verified
 │ Mismatch      │ → ✗ Tampered
 └───────────────┘
```

Even a small modification to the recorded evidence produces a different fingerprint, allowing the system to detect tampering.

## What Makes the Approach Strong

- **Live discovery:** results are obtained through an actual search rather than predetermined URLs.
- **Evidence-centric:** the system captures the discovered result as structured evidence instead of treating a search result as the final answer.
- **Tamper-evident:** cryptographic fingerprinting makes changes detectable.
- **Verifiable:** the system provides an explicit verification step against the recorded fingerprint.
- **Modular:** face processing, evidence discovery, and integrity verification are independently testable components.
- **Minimal on-chain data:** only the cryptographic fingerprint needs to be anchored on-chain.

## Technology Stack

| Layer | Technology |
|---|---|
| Programming | Python |
| Face Processing | DeepFace |
| Web Evidence Discovery | Google Cloud Vision Web Detection |
| Search Fallback | SerpApi |
| Cryptography | SHA-256 |
| Smart Contract | Solidity |
| Blockchain Interface | Web3.py |
| Blockchain | Ganache |
| Version Control | Git / GitHub |

## Architecture

```text
                    ┌─────────────────┐
                    │   Face Image    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Face Detection  │
                    │  & Encoding     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   Live Web      │
                    │     Search      │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │    Evidence     │
                    │     Package     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │    SHA-256      │
                    │   Fingerprint   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   Blockchain    │
                    │     Anchor      │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Verification   │
                    └─────────────────┘
```

## Project Structure

```text
Identity-Evidence-Chain/
├── README.md
├── main.py
├── face/
├── search/
└── blockchain/
    ├── contract.sol
    ├── compile.py
    ├── deploy.py
    ├── upload.py
    ├── verify.py
    ├── evidence.py
    └── blockchain_service.py
```

## Responsible Use

The demonstration uses a **consenting participant's own image** and publicly accessible web evidence.

The system is designed to demonstrate evidence discovery and integrity verification, not unauthorized identification or surveillance.

## Core Principle

> **Discover it. Structure it. Fingerprint it. Anchor it. Verify it.**
