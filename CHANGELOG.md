# Changelog

本仓库变更日志。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

> 创世铭文：政党名称「海燕党」、英文「PETREL AI PARTY」、创始人「刘海燕(LIU HAIYAN)」
> 三项标识永久嵌入本仓库最底层，任何人不得删除、替换或裁剪。

## [v1.0.0-rc1+perf] - 2026-09-05

### 发布前性能基准归档（M3.3 §6 实检 5/5）

- test: `audit/bench-perf-2026-09-05.json` 归档 — 调度器 100 并发任务 100/100 完成无崩溃 / 共识引擎 5 节点稳态 2.52s（<3s；冷启动含模型加载 24.6s 一次性成本）/ 熔断器 20000 次错误堆 +12.3KB 无泄漏 / 推理节点 CPU 基线 16.8MB / Docker 全栈启动 16.9s（<60s）
- fix: 基准暴露 P1 — `InferenceNode()` 默认构造崩溃，03-model 源 + 05-tool 部署副本同步修复（联动 03-model/05-tool commit）
- docs: `05-tool/release/release-checklist.md` §6 性能基准闭环

## [v1.0.0-rc1+verify5] - 2026-09-04

### 发布前阻塞项闭环（四 · M3.3 推进）· Docker 全栈 up 实测

- test: `docker compose up -d --no-build --wait` 真实执行成功 — 5 服务全部 Up+healthy，退出码 0
- test: 端点实测 10/10 PASS — 直连（gateway ping / voting health / market 9102 / dashboard 9103 ×2）与 nginx 80 反代（/p2p/ping、/voting/health、/market/、/dashboard/ 全 200；/→301 /dashboard/ 为设计行为）
- docs: `05-tool/release/release-checklist.md` §5 Docker 模式 4 项待办闭环
- 归档：`audit/deploy-verify-2026-09-04.json`（10/10 PASS）
- 联动提交：`05-tool`（checklist 闭环+CHANGELOG）

## [v1.0.0-rc1+verify4] - 2026-09-03

### 发布前阻塞项闭环（三 · M3.3 推进）

- build: `docker compose build` 4 目标全部 Built — node-deploy-gateway/voting/market/dashboard（2026-09-03 真实执行）
- fix: P1 容器启动缺陷 — `aiohttp has no attribute web`（aiohttp>=3.10 需显式 `import aiohttp.web`），03-model 源 + 05-tool 副本同步修复，重建后 gateway `/p2p/ping` 冒烟通过
- test: 容器冒烟 2/2 — gateway ping 200（真实 node_id+铭文）、voting /health 200
- feat: 协议种子生成器 `05-tool/node-deploy/seed-tools/generate-seed.py` + 离线验证 PASS（4/4）
- 归档：`audit/func-verify-2026-09-03.json`（8/8）、`audit/security-verify-2026-09-03.json`（15/17）
- 联动提交：`05-tool`（Docker 构建/种子工具/checklist）、`03-model`（aiohttp.web import 修复）

## [v1.0.0-rc1+verify3] - 2026-09-02

### 发布前阻塞项闭环（二 · M3.3 推进）

- fix(dashboard): `05-tool/node-deploy/dashboard/server.py` 启动崩溃修复 — CSS 花括号与 `.format()` 冲突（KeyError: ' margin'），改 `.replace()` 链式模板；实检 `/health`、`/api/status`、`/` 全部 200
- feat(voting): 新增 `voting_server.py` — 投票客户端真实服务，修复 `python -m http.server` 无 `/health` 端点导致健康检查永不过的发布缺陷；Dockerfile voting target 同步切换
- docs(API): 新增 `node-deploy/API.md` — 网关/投票/市场/看板/推理节点 5 服务全部端点与响应格式，闭环 release-checklist「API 端点说明」项
- test: DZN 四模块 demo 复跑全通过（调度器 / 共识 score=0.858 / 输出锁 / 熔断演练），dashboard+voting 服务真实启动 200
- 联动提交：`05-tool` d639668

## [v1.0.0-rc1+verify2] - 2026-08-29

### 发布前验证补测（M3.3 推进 · 功能验证 7/7 全通过）

- fix(dzn_scheduler): 新增 `--demo` 模式 — 任务拆分/节点综合评分/调度分配/声誉换算全部走真实代码路径，补齐发布验证 2a 项缺口
- fix(model_consensus): `SemanticComparator` 改用 `local_files_only=True` 加载 embedding 模型 — 无本地缓存时按设计降级 Jaccard，杜绝 HuggingFace 网络下载挂起（修复 90s 超时）
- 功能验证复跑：调度器/共识引擎/输出锁/推理节点/熔断演练/铭文守卫/IPFS CID 复算 **7/7 通过**（2026-08-29 实检）
- 验证结果归档：`audit/func-verify-2026-08-21.json`（total=7, passed=7, failed=[]）

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
