# 海燕党 Data Repository · 数据仓库

> **Party name: PETREL AI PARTY** ｜ **Chinese name: 海燕党** ｜ **Founder: LIU HAIYAN（刘海燕）**

This repository is the **data and audit repository** of the PETREL AI PARTY open-source
protocol network. Transparency is not optional — it is the protocol's spine.

## Repository layout

```
06-data/
├── GENESIS.md              # Genesis inscription (shared)
├── anchors/                # On-chain anchoring records
│   ├── ipfs_cid.json       # GENESIS.md IPFS CID
│   ├── onchain.json        # Sepolia inscription anchor
│   ├── hy-token.json       # HY Token deployment
│   └── vote-contract*.json # Voting contract deployment
├── audit/                  # Audit reports & verification logs
│   ├── audit-report.md
│   ├── solidity-audit-report.md
│   ├── release-ready-verify-*.json
│   └── security-verify-*.json
├── funding/                # Public-goods funding applications
│   ├── gitcoin-grant-application.md
│   └── optimism-retropgf-application.md
├── VERSION
└── README.md / README.en.md
```

## On-chain proof of existence

| Artifact | Anchor |
|----------|--------|
| Genesis inscription | Sepolia `0x0427bc36...5bbb0` |
| GENESIS.md | IPFS CID `QmQ2SUjEZwMfzj8T9aWAHiBAKYTYnLuDPiaCkFKAJE7tF5` |
| HY Token | deployed on Sepolia, 4 vaults allocated |
| PetrelVoteContract | deployed on Sepolia |

## Status

- ✅ Phase 0–2 complete
- ✅ `v1.0.0-rc1` frozen; all audit records archived
- Latest daily inspection: inscription guard 81/81 PASS, six repositories git-clean

> **"Verify, don't trust."**
