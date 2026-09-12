# Changelog

本仓库变更日志。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

> 创世铭文：政党名称「海燕党」、英文「PETREL AI PARTY」、创始人「刘海燕(LIU HAIYAN)」
> 三项标识永久嵌入本仓库最底层，任何人不得删除、替换或裁剪。

## [v1.0.0-rc1+dr02] - 2026-09-12

### M3.3 DR-02 DDoS 降级演练证据归档（§8 / P2 #5 · Core Brain 每日巡检）

- test: `audit/dr02-ddos-drill-2026-09-12.json` 归档 — **12/12 PASS**：① 配置审计 8 项（限流 zone 定义 / 429 语义化 / 全代理端点限流 / 后端无关 `/health` / 含创世铭文的静态兜底页 / 7 天 CDN TTL / 单 IP 连接上限 / IP 白名单留白端正）② `nginx -t` 配置语法校验 successful ③ **实压限流** 基线串行 8/8 = 200；并发 120 → 200×54 / 429×66 / 连接错误 0，耗时 0.053s ④ 黑启动兜底 `/health` 5/5 = 200（体 `PETREL-DZN-ALIVE`）/ `/fallback/` 200 含创世铭文
- test: `audit/release-ready-verify-2026-09-12.json` 归档 — 当日巡检：铭文守卫全仓 **86/86 PASS**（当日变更前基线 84，新增 2 份带铭文产物后复扫 86；2026-09-10 为 83）；六仓 `git status --short` 全干净；`03-model` pytest 55 passed、`05-tool` pytest 34 passed
- 说明：所有数值为真实执行测量（真起 nginx 容器 + 真并发 HTTP 压测），零 Mock；无法由 cron 代办的人类项（核心成员 IP、DNS/CDN 账号、排期确认）如实标 HUMAN_DECISION 提报

## [v1.0.0-rc1+digestpin] - 2026-09-11

### M3.3 基础镜像 digest 级锁定验证归档（§3 · Core Brain 每日巡检）

- test: `audit/docker-digest-verify-2026-09-11.json` 归档 — **7/7 PASS**：① 注册表复解析 ×3（daocloud/1ms/dockerproxy 三独立源 digest 逐字节一致，与锁文件相符）② 仓库文件内 pin 相符 ×3（`Dockerfile` python:3.11-slim / python:3.11-alpine；`docker-compose.yml` nginx:alpine）③ 零残留未 pin 裸引用 ×1
- 说明：官方 `registry-1.docker.io` 在受限网络实测不可达，归档 `note` 字段已记录该网络事实与「多源交叉验证」替代口径；digest 内容寻址，跨源一致 ⇒ 等价官方值
- 关联：`05-tool` 同步提交（工具 `release/docker-digest-lock.py` + 锁文件 `node-deploy/docker-digest-lock.json` + 4 处 pin 回填 + checklist §3 / playbook 闭环）

## [v1.0.0-rc1+toolchain] - 2026-09-08

### M3.3 shellcheck 工具链补齐审计归档（§1 · Core Brain 每日巡检）

- test: `audit/shellcheck-verify-2026-09-08.json` 归档 — **3/3 PASS**（koalaman/shellcheck:stable 容器）：deploy.sh 首检 rc=0；start-did-web.sh SC1091 豁免；mirror-sync.sh 补 shebang（SC2148）+ 死变量 SC2034 + `&& ||` 隐患 SC2015 三处真实修复；bash -n 3/3 + mirror-sync.sh --status 只读实跑行为验证通过

## [v1.0.0-rc1+baremetal] - 2026-09-07

### 裸机+离线模式发布验证归档（M3.3 §5 实检 7/7）

- test: `audit/baremetal-offline-verify-2026-09-07.json` 归档 — **7/7 PASS**：全新 venv pip 安装 rc=0 / 调度器裸机启动 0.1s / 推理节点裸机启动 `/health` `/info` 200 / GPU 降级 has_nvidia_gpu=False 不崩溃 / DZN-SEED 20 文件结构完整 + offline-verify.sh 4/4 PASS / 裸机·离线路径可执行网络命令 0 条（Docker deploy.sh `docker pull` 3 条为已知人类项）
- fix: 裸机实测暴露 P1 — `inference_node.py` CLI `--backend auto` 抛 ValueError 崩溃 → BackendType 新增 AUTO（03-model 源 + 05-tool 部署副本同步，pytest 55/55）
- fix: `generate-seed.py` 补写种子 README.md（与离线规格目录一致）
- docs: `05-tool/release/release-checklist.md` §5 裸机 4/4 + 离线 3/3 全部闭环
- 联动提交：`03-model`（AUTO 修复）、`05-tool`（验证脚本+checklist+生成器修复）

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
