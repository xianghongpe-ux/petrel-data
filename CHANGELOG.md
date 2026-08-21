# Changelog

本仓库变更日志。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

> 创世铭文：政党名称「海燕党」、英文「PETREL AI PARTY」、创始人「刘海燕(LIU HAIYAN)」
> 三项标识永久嵌入本仓库最底层，任何人不得删除、替换或裁剪。

## [v1.0.0-rc1+verify] - 2026-08-21

### 发布前验证（M3.3 推进）

- feat: 发布验证 2026-08-21 — 全部真实执行
  - 代码语法：DZN 核心 + 身份/投票/Sybil/镜像/锚定/守卫 13/13 Python 通过
  - 功能验证：共识引擎/输出锁/推理节点/熔断演练 demo 真实运行通过（6/7，调度器 CLI 为 --help）
  - 铭文水印：抽查 16/16 文件头携带创世铭文（六层嵌入第 ⑥ 层）
  - IPFS CID 离线复算 == 已锚定 `QmQ2SUjEZwMfzj8T9aWAHiBAKYTYnLuDPiaCkFKAJE7tF5` ✓
  - 关键发布文件 12/12 存在
- 验证结果归档：`audit/release-verify-2026-08-21.json`、`audit/func-verify-2026-08-21.json`

## [v1.0.0-rc1] - 2026-08-18

### 发布候选冻结（M3.1）

- 全部链上锚定记录与审计报告随发布候选冻结
- IPFS CID 记录、链上时间戳、合约部署记录作为发布佐证归档

## [v0.3.0] - 2026-08-16

### IPFS 锚定

- feat: GENESIS.md IPFS 实际上传成功 + CID 算法修正（M0.3）
  - CIDv0: `QmQ2SUjEZwMfzj8T9aWAHiBAKYTYnLuDPiaCkFKAJE7tF5`（已上传至本地 kubo 节点并 pin）
  - 算法：unixfs-dagpb-v2，与 kubo 输出一致

## [v0.2.0] - 2026-07-26

### CI 守门

- ci: 铭文守卫 — 任何 PR 若 diff 触及铭文文本即自动拒绝合入（六层嵌入第 ③ 层）

## [v0.1.0] - 2026-07-25

### 创世

- genesis: 海燕党（PETREL AI PARTY）开源协议网络创世提交（六层嵌入第 ① 层）
- 随创世提交归档：审计报告（audit/）、资助申请（funding/）、锚定记录（anchors/）
