# 海燕党 · Solidity 合约安全审计报告

> **审计日期**: 2026-07-26
> **审计目标**: PetrelVoteContract.sol + HY-Token-SmartContract.sol
> **链环境**: Sepolia 测试网
> **创世铭文**: 海燕党 / PETREL AI PARTY / 刘海燕

---

## 一、审计概要

| 合约 | 文件路径 | 代码行数 | 严重问题 | 高危问题 | 中危问题 | 低危问题 |
|------|---------|---------|---------|---------|---------|---------|
| PetrelVoteContract | 02-algorithm/voting/PetrelVoteContract.sol | 191 | 0 | 1 | 2 | 3 |
| HYToken | 05-tool/tokenomics/HY-Token-SmartContract.sol | 74 | 0 | 0 | 1 | 1 |

**最终安全评级**: ⚠️ **中等风险 (Medium)** — 未发现严重漏洞，但存在可被利用的中危/高危问题，建议修复后上线。

---

## 二、PetrelVoteContract.sol 详细审计

### 2.1 重入攻击 [安全]

**结果**: ✅ 未发现重入漏洞
**说明**: 合约遵循 Checks-Effects-Interactions 模式。`vote()` 函数中先更新状态（`hasVoted` 映射 + `voteCounts` 累加）再进行外部调用（事件），无外部合约调用导致重入的可能。`executeProposal()` 只读取状态不发送 ETH/调用外部合约。

### 2.2 整数溢出/下溢 [安全]

**结果**: ✅ 未发现溢出问题
**说明**: Solidity ^0.8.20 版本内置溢出检查。`proposalCount++`、`voteCounts[][]+` 均有安全保护。

### 2.3 未授权的访问控制 [⚠️ 高危]

**结果**: ❌ **发现问题**

**问题详情**: 任何人可以创建提案和调用 `executeProposal()`。虽然投票本身应该是开放的，但以下问题存在：

1. **`createProposal()` 无权限控制** — 任何地址都可以创建提案，可能导致垃圾提案耗尽 gas（第71-97行）
2. **`executeProposal()` 无权限控制** — 任何地址都可以在其他人的提案结束后执行结果公布（第122-138行），虽无直接资金风险，但违反治理预期

**严重等级**: ⚠️ **高危**

**修复建议**:
```solidity
// 添加 modifier 限制提案创建
modifier onlyMember() {
    require(isMember[msg.sender], "only members");
    _;
}

// 限制执行者为提案创建者或委员会
modifier onlyCreatorOrCommittee(uint256 proposalId) {
    require(
        msg.sender == proposals[proposalId].creator || 
        msg.sender == committee,
        "not authorized"
    );
    _;
}

function createProposal(...) public onlyMember returns (uint256) { ... }
function executeProposal(uint256 proposalId) public onlyCreatorOrCommittee(proposalId) { ... }
```

### 2.4 前端运行/抢跑 [⚠️ 中危]

**结果**: ❌ **发现问题**

**问题详情**: Sepolia 测试网作为公开网络，`vote()` 函数依赖交易排序。抢跑者可以：
1. 监视 mempool 中的提案交易，抢先投票
2. 在提案即将结束时，通过提高 gas 抢跑来影响结果

虽然测试网影响有限，但若迁移至主网需要修复。

**严重等级**: ⚠️ **中危**

**修复建议**:
```solidity
// 方案1：提交-揭晓模式（Commit-Reveal）
mapping(address => bytes32) public commitments;
function commitVote(uint256 proposalId, bytes32 commitment) public { ... }
function revealVote(uint256 proposalId, uint256 optionIndex, bytes32 salt) public { ... }

// 方案2：引入随机排序或批量投票
```

### 2.5 未检查的外部调用 [安全]

**结果**: ✅ 未发现问题
**说明**: 合约不进行 ETH 转账或外部合约调用，所有操作均为内部状态变更。

### 2.6 拒绝服务漏洞 [⚠️ 中危]

**结果**: ❌ **发现问题**

**问题详情**:

1. **`getTotalVoters()` 线性遍历**（第174-185行）— 如果有大量选项，该函数的 gas 消耗会线性增长，可能超出区块 gas limit
2. **`allVotes[] 数组无上限增长** — 每次投票都 push 新的 `VoteRecord`，随着投票数增长会无限消耗存储空间

**严重等级**: ⚠️ **中危**

**修复建议**:
```solidity
// 优化 getTotalVoters：使用累计计数器
uint256 public totalVotesCount;

function vote(...) public {
    ...
    totalVotesCount++;
    ...
}

// 或限制最大选项数
require(options.length <= 20, "too many options");

// 添加 allVotes 数组增长保护
require(allVotes.length <= 100000, "vote limit reached");
```

### 2.7 时间戳依赖 [低危]

**结果**: ⚠️ **低风险**

**问题详情**: 合约使用 `block.timestamp` 决定投票开始/结束（第91行）和提案执行（第128行）。矿工可在 ±15 秒范围内操纵时间戳。

**严重等级**: ⚠️ **低危**

**修复建议**: 对于非金融场景（投票），±15 秒误差可接受。如需更精确的时间控制，可：
```solidity
// 使用区块编号替代时间戳
uint256 public constant BLOCKS_PER_DAY = 7200; // ~15s/block
uint256 public endBlock;
require(block.number < endBlock, "voting closed");
```

### 2.8 Gas限制问题 [低危]

**结果**: ⚠️ **低风险**

**问题详情**:
1. `string[] options` 存储在 `Proposal` 结构体中，使用动态数组未限制大小
2. `allVotes` 数组无上限，长期运行存储成本持续增加
3. `getTotalVoters()` 和 `getResults()` 使用循环遍历，gas 成本随选项数线性增长

**严重等级**: ⚠️ **低危**

**修复建议**:
```solidity
// 限制选项数量
require(options.length >= 2 && options.length <= 20, "invalid options count");

// 添加 VoterCount 累计变量（见2.6优化方案）
```

### 2.9 逻辑缺陷 [⚠️ 高危]

**结果**: ❌ **发现问题**

**问题详情**:

1. **`voteCounts[proposalId][optionIndex]++` 无验证** — 虽然 `hasVoted` 防止重复投票，但未检查提案是否已执行。如果某人在 `votingOpen` 阶段之后但 `executeProposal` 之前调用，理论上 `votingOpen` modifier 中的 `!proposals[proposalId].executed` 已做保护。**但在边界情况 `executeProposal` 重入或时间竞争下，`requir(!prop.executed)` 在 `executeProposal` 和 `vote` 中的执行顺序可能存在同步问题。** 修复：在 `vote()` 内部再加一道检查：

```solidity
function vote(uint256 proposalId, uint256 optionIndex) public {
    ...
    require(!proposals[proposalId].executed, "already executed"); // 额外保护
    ...
}
```

2. **无提案取消机制** — 一旦创建无法撤销
3. **`getTotalVoters()` 实际统计的是总票数而非总投票人数** — 函数名有误导

**严重等级**: ⚠️ **高危**

**修复建议**:
```solidity
// 在 vote() 中添加执行状态双重检查
require(!proposals[proposalId].executed, "proposal_executed");

// 添加提案取消功能
function cancelProposal(uint256 proposalId) public {
    require(msg.sender == proposals[proposalId].creator, "only creator");
    require(!proposals[proposalId].executed, "already executed");
    require(block.timestamp < proposals[proposalId].endAt, "voting ended");
    proposals[proposalId].executed = true;
    emit ProposalCancelled(proposalId);
}

// 重命名 getTotalVoters → getTotalVotes
```

---

## 三、HY-Token-SmartContract.sol 详细审计

### 3.1 重入攻击 [安全]

**结果**: ✅ 未发现重入漏洞
**说明**: 继承 OpenZeppelin 标准 ERC20，无自定义转账逻辑，安全。

### 3.2 整数溢出 [安全]

**结果**: ✅ 未发现溢出问题
**说明**: Solidity ^0.8.20 + OpenZeppelin 标准实现，溢出有保障。

### 3.3 未授权的访问控制 [⚠️ 中危]

**结果**: ❌ **发现问题**

**问题详情**:

1. **`initializeVaults()` 一次性的初始铸造权** — 只有 `onlyOwner` 可以调用，但一旦 `initialized` 被设为 `true` 后无法重新配置金库地址（第43-68行）。如果某个金库地址填错，Token 将永远锁定。
2. **无撤销机制** — 如果 `owner` 私钥泄露，攻击者无法增发（因为 mint 只在 initialize 时执行），但攻击者可调用 Ownable 的 `transferOwnership`。

**严重等级**: ⚠️ **中危**

**修复建议**:
```solidity
// 添加含时间锁的金库更新机制
uint256 public constant VAULT_CHANGE_DELAY = 7 days;
mapping(address => uint256) public vaultChangeRequested;

function requestVaultChange(address _newVault, VaultType _type) external onlyOwner {
    vaultChangeRequested[_newVault] = block.timestamp;
}

function executeVaultChange(address _newVault, VaultType _type) external onlyOwner {
    require(block.timestamp >= vaultChangeRequested[_newVault] + VAULT_CHANGE_DELAY, "delay not met");
    // 转移未分配的余额到新金库
}
```

### 3.4 前端运行 [安全]

**结果**: ✅ 未发现问题
**说明**: 无交易排序敏感的竞争条件操作。初始化铸造是确定性分配。

### 3.5 未检查的外部调用 [安全]

**结果**: ✅ 未发现问题
**说明**: 无外部合约调用。

### 3.6 拒绝服务 [安全]

**结果**: ✅ 未发现问题
**说明**: 无循环或无界存储增长，继承标准 ERC20 安全。

### 3.7 时间戳依赖 [安全]

**结果**: ✅ 未发现问题
**说明**: 无时间戳依赖逻辑。

### 3.8 Gas限制 [低危]

**结果**: ⚠️ **低风险**
**说明**: 单次 `initializeVaults()` 执行4次 `_mint`，如果 Token 传输量大可能 gas 偏高，但预估仍在合理范围内。

### 3.9 逻辑缺陷 [低危]

**结果**: ⚠️ **低风险**

**问题详情**:

1. **`maxSupply()` 为 pure 函数但未在 mint 时检查** — 当前 `initializeVaults` 铸造总量正好等于 MAX_SUPPLY（100M），但如果后续通过 `_mint` 子类扩展（虽然在当前实现中无接口），铸造可能超限
2. **`Votes.sol` import 但未使用** — 合约继承 `Votes` 但从未使用其治理能力

**修复建议**:
```solidity
// 在 mint 中加入 max supply 检查
function _update(address from, address to, uint256 value) internal override {
    if (from == address(0)) {
        require(totalSupply() + value <= MAX_SUPPLY, "max supply exceeded");
    }
    super._update(from, to, value);
}
```

---

## 四、问题汇总

| ID | 合约 | 问题描述 | 类别 | 严重等级 |
|----|------|---------|------|---------|
| V-01 | PetrelVote | createProposal() 无权限控制 | 访问控制 | ⚠️ 高危 |
| V-02 | PetrelVote | getTotalVoters 线性遍历 + allVotes 无限增长 | DoS | ⚠️ 中危 |
| V-03 | PetrelVote | vote() 边界状态竞争 | 逻辑缺陷 | ⚠️ 高危 |
| V-04 | PetrelVote | 抢跑/MEV 风险 | 前端运行 | ⚠️ 中危 |
| V-05 | PetrelVote | block.timestamp 依赖 | 时间戳 | ⚠️ 低危 |
| V-06 | PetrelVote | options/数组无界 | Gas | ⚠️ 低危 |
| T-01 | HYToken | 金库地址不可更新 | 访问控制 | ⚠️ 中危 |
| T-02 | HYToken | Votes import 未使用 | 代码质量 | ⚠️ 低危 |

---

## 五、最终建议

1. **立即修复**: V-01（访问控制）、V-03（逻辑缺陷）— 影响合约治理安全性
2. **尽快修复**: V-02（DoS 风险）、V-04（抢跑）、T-01（金库不可逆）
3. **建议优化**: V-05、V-06、T-02

> 总评：合约整体结构清晰，遵循了安全检查基本原则（无重入、无溢出），但存在治理权限过多开放、存储无界增长等新手常见问题。HYToken 继承 OpenZeppelin 标准库，安全性较好。PetrelVote 作为自定义治理合约需要补充权限控制和边界保护。
