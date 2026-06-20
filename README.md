# ArcWork — AI Freelance Marketplace on Arc Blockchain

> Submit a task, AI completes it, payment happens automatically on Arc blockchain via ERC-8183 escrow.

## What is ArcWork?

ArcWork is a decentralized AI freelance marketplace built on [Arc](https://arc.io). Users submit text tasks via a web interface, an AI agent completes them, and payment is released automatically — all on-chain.

**No middlemen. No manual payments. Just tasks, AI, and USDC.**

## How It Works

## Live Transactions (Arc Testnet)

| Step | Transaction |
|------|------------|
| Agent Registered (ERC-8004) | [View on ArcScan](https://testnet.arcscan.app/address/0xe7faaccb0746dbbc20e250546c28f9f4ca03a100) |
| Job Created (ERC-8183) | [View on ArcScan](https://testnet.arcscan.app/tx/0xaf9f8e531bc8e95a2372f2a65557ca7427db049f7332077764fe914904491546) |
| USDC Paid to Agent | [View on ArcScan](https://testnet.arcscan.app/tx/0xff6624fada253b88bb0136ac710776780f7a44279079a43ffb0ecde064de8bef) |

**Agent ID:** 834167
**Agent Metadata (IPFS):** [View](https://gateway.pinata.cloud/ipfs/QmWdvQXyxmBWJxmrebzGKDAmNRe47paRR5XdqqfRsKcQcJ)

## Features

- Web UI — Submit tasks from any browser
- Claude AI — Real translation and summarization
- USDC Escrow — Automatic payment via ERC-8183
- Agent Identity — Onchain reputation via ERC-8004
- TX Tracking — Every step visible on ArcScan

## Arc Standards Used

| Standard | Purpose |
|----------|---------|
| ERC-8004 | AI agent identity, reputation, validation |
| ERC-8183 | Job lifecycle: create → fund → submit → complete |

## Smart Contracts (Arc Testnet)

| Contract | Address |
|----------|---------|
| IdentityRegistry (ERC-8004) | 0x8004A818BFB912233c491871b3d84c89A494BD9e |
| ReputationRegistry (ERC-8004) | 0x8004B663056A597Dffe9eCcC1965A193B7388713 |
| ValidationRegistry (ERC-8004) | 0x8004Cb1BF31DAf7788923b405b754f57acEB4272 |
| AgenticCommerce (ERC-8183) | 0x0747EEf0706327138c69792bF28Cd525089e4583 |
| USDC (Arc Testnet) | 0x3600000000000000000000000000000000000000 |

## Tech Stack

- Blockchain: Arc Testnet (Chain ID: 5042002, ~0.48s finality)
- Standards: ERC-8004 + ERC-8183
- Wallets: Circle Developer Controlled Wallets
- AI: Anthropic Claude API
- Backend: Python 3 + FastAPI
- IPFS: Pinata

## Project Structure
## Getting Started

### Prerequisites

- Python 3.10+
- Circle Developer Console — API Key + Entity Secret
- Anthropic Console — API Key
- Pinata — IPFS metadata
- Arc Testnet USDC from faucet.circle.com

### Installation
### Run
## Built With Arc

Arc is purpose-built for stablecoin finance:
- Sub-second finality (~0.48s)
- USDC-native gas (no volatile tokens)
- EVM compatible

Learn more: https://docs.arc.io

## License

MIT
