# 海燕党(PETREL AI PARTY) 全量安全审计报告

**审计时间**: 2026-07-26  
**审计范围**: 25 个 Python 文件（DID/零知识证明/投票/Sybil防御/金库/辩论/入党管理）  
**安全评级**: **D**（严重安全隐患）

---

## 安全评级说明

| 级别 | 标准 | 当前状态 |
|------|------|----------|
| A+   | 无任何发现，最佳实践全量覆盖 | ❌ |
| A    | 仅 LOW 级别问题 | ❌ |
| B    | 有 MEDIUM 问题，无 HIGH/CRITICAL | ❌ |
| C    | 有 HIGH 问题，无 CRITICAL | ❌ |
| **D** | **存在 CRITICAL 级别问题** | **✅ 当前评级** |
| F    | 存在可直接导致资产损失的漏洞 | ❌（但接近） |

---

## 紧急修复清单（CRITICAL + HIGH 优先）

### 🔴 CRITICAL-01: 硬编码以太坊私钥
- **文件**: `02-algorithm/voting/deploy_vote_sepolia.py:6-7`
- **严重程度**: 🔴 CRITICAL
- **描述**: 真实以太坊私钥和账户地址以明文硬编码在脚本中。
  ```python
  PRIVATE_KEY = "82ab21c7c0d1a445acd52453ae7e782b9b818e280be32552675f2cd20f1c1e57"
  ACCOUNT = "0xc87c7aA4C5104af91C653966388c33039D4D6Cc6"
  ```
  该私钥直接用于 `w3.eth.account.sign_transaction(tx, PRIVATE_KEY)` 签名交易并部署到 Sepolia 测试网。任何能读取该文件的人都能完全控制此账户。
- **修复建议**: 
  1. 立即轮换该私钥（假设该地址已泄露）
  2. 删除硬编码私钥
  3. 改用环境变量或 `.env` 文件读取：`PRIVATE_KEY = os.environ.get("ETH_PRIVATE_KEY")`
  4. 将该文件加入 `.gitignore`

### 🔴 CRITICAL-02: 入党管理API无任何认证/授权
- **文件**: `05-tool/membership/membership_api.py`（全部函数）
- **严重程度**: 🔴 CRITICAL
- **描述**: 所有 API 函数（`ai_initial_screening`, `human_review`, `committee_promote`, `handle_dismiss`, `list_members` 等）没有任何身份验证或授权检查。任何调用者都可以：
  - 查看所有成员的个人信息（姓名、邮箱、手机号、微信ID、GitHub ID）
  - 修改成员状态（初审、终审、转正、退党）
  - 创建新申请
- **修复建议**: 
  1. 添加 API Token 认证机制
  2. 实现基于角色的访问控制（RBAC）
  3. 管理操作需要额外签名/权限验证

### 🔴 CRITICAL-03: 个人身份信息(PII)泄露
- **文件**: `05-tool/membership/membership_api.py:288-297`
- **严重程度**: 🔴 CRITICAL
- **描述**: `list_members()` 函数返回成员的 email、github_id 等敏感字段，且该接口不加任何认证即可调用。
  ```python
  result.append({
      "email": app["email"],
      "github_id": app.get("github_id", ""),
      ...
  })
  ```
  数据库中还存储了 `wechat_id` 和 `phone` 字段（`member_db.py:49-51`），这些数据一旦泄露可用于社工攻击。
- **修复建议**:
  1. 列表接口默认脱敏敏感字段（如 `email: "a***@*.com"`）
  2. 仅特定管理角色可查看完整信息
  3. `phone` 和 `wechat_id` 不应在列表接口返回

---

### 🟠 HIGH-01: VRF密钥使用 time.time() 作为熵源
- **文件**: `02-algorithm/debate/random_lottery.py:88-92`
- **严重程度**: 🟠 HIGH
- **描述**: VRF 引擎的密钥对生成使用 `time.time()` 作为唯一熵源，完全可预测。
  ```python
  def _generate_keypair(self) -> Tuple[str, str]:
      secret = hashlib.sha256(f"vrf_secret_{time.time()}".encode()).hexdigest()
      public = hashlib.sha256(secret.encode()).hexdigest()
      return secret, public
  ```
  攻击者如果知道系统启动时间，可以推导出 VRF 私钥，进而预测所有抽签结果，完全破坏公民大会抽签的公平性。
- **修复建议**: 使用 `secrets.token_hex(32)` 替代 `time.time()` 作为密钥种子。

### 🟠 HIGH-02: DID签名方案非密码学安全
- **文件**: `02-algorithm/did/did.py:262-287`
- **严重程度**: 🟠 HIGH
- **描述**: `sign()` 方法使用 `blake2b(message + private_key)` 的HMAC风格进行签名，而非真正的 Ed25519 非对称签名。`verify()` 方法内部直接调用 `self.sign()` 加载私钥验证，导致：
  1. 验证者必须拥有私钥才能验证签名（完全违背非对称签名原则）
  2. 签名无法被第三方独立验证
  3. 不满足 W3C DID 标准的安全要求
- **修复建议**:
  1. 引入 `ed25519` 或 `nacl` 库实现真正的非对称签名
  2. `verify()` 应使用公钥验证而非调用 `self.sign()`
  3. 当前代码注释标注"简化版/生产环境用ed25519库"，应尽快替换

### 🟠 HIGH-03: DID私钥存储目录权限过于宽松
- **文件**: `02-algorithm/did/did.py:61-62`
- **严重程度**: 🟠 HIGH
- **描述**: `DIDManager.__init__` 创建存储目录时使用 `os.makedirs(self.storage_path, exist_ok=True)`，默认模式为 `0o777`（受umask限制，通常为 `0o755`）。虽然私钥文件本身设置了 `0o600`，但目录的宽松权限可能允许同系统其他用户访问私钥文件。
- **修复建议**: 显式设置目录权限：
  ```python
  os.makedirs(self.storage_path, mode=0o700, exist_ok=True)
  ```

### 🟠 HIGH-04: 无输入路径验证可能导致路径遍历
- **文件**: `02-algorithm/did/did.py:76-78`
- **严重程度**: 🟠 HIGH
- **描述**: `_save_key()` 和 `_load_key()` 使用用户控制的 `did` 字符串拼接文件路径，未做任何路径遍历防护。
  ```python
  key_dir = Path(self.storage_path) / did
  key_file = key_dir / f"{key_id}.key"
  ```
  如果 `did` 包含 `../` 或绝对路径，可能写入/读取任意文件。
- **修复建议**: 
  1. 验证 `did` 仅包含安全字符（`did:` 格式正则校验）
  2. 使用 `os.path.abspath()` 解析后检查是否仍在允许的目录内

### 🟠 HIGH-05: 文件创建为明文且无加密
- **文件**: `02-algorithm/did/did.py:78-80`
- **严重程度**: 🟠 HIGH
- **描述**: 私钥以明文形式直接写入文件系统。
  ```python
  key_file.write_text(private_key)
  ```
  任何能访问文件系统的进程或用户都可以读取私钥。注释中提到"生产环境用 HSM/安全硬件"，但当前实现完全依赖文件系统权限保护。
- **修复建议**: 至少对私钥进行 AES 加密后存储，密钥派生自用户密码或系统密钥链。

---

### 🟡 MEDIUM-01: 智能合约部署脚本保留真实RPC地址
- **文件**: `02-algorithm/voting/deploy_vote_sepolia.py:8`
- **严重程度**: 🟡 MEDIUM
- **描述**: 公开的 RPC 地址硬编码在脚本中。
  ```python
  RPC = "https://ethereum-sepolia-rpc.publicnode.com"
  ```
  虽然这是公共 RPC，但硬编码不利于环境灵活性。

### 🟡 MEDIUM-02: verification_key 硬编码
- **文件**: `02-algorithm/zkp/membership_verifier.py:143`
- **严重程度**: 🟡 MEDIUM
- **描述**: 验证密钥使用固定字符串。
  ```python
  self.verification_key: str = verification_key or "PETREL_AI_PARTY_VK_001"
  ```
  任何知道该字符串的人可能能伪造验证。

### 🟡 MEDIUM-03: 错误信息泄露内部状态
- **文件**: `02-algorithm/voting/voting_kernel.py:319-321`
- **严重程度**: 🟡 MEDIUM
- **描述**: 投票函数中的错误消息泄露了内部状态信息（如提案不存在 vs 提案状态不允许投票），可能被用于信息收集攻击。
- **修复建议**: 对外暴露的接口应返回统一错误码，不暴露具体原因。

### 🟡 MEDIUM-04: 数据库连接未使用连接池
- **文件**: `05-tool/membership/member_db.py:28-32`
- **严重程度**: 🟡 MEDIUM
- **描述**: 每个函数都创建一个新的 SQLite 连接，高并发下可能导致数据库锁竞争。
- **修复建议**: 使用连接池或单例模式管理数据库连接。

---

### 🔵 LOW-01: 无操作日志审计
- **严重程度**: 🔵 LOW
- **描述**: 所有模块均无操作审计日志（谁在什么时间做了什么操作）。
- **修复建议**: 添加结构化审计日志。

### 🔵 LOW-02: 注释残留敏感信息
- **文件**: `02-algorithm/voting/deploy_vote_sepolia.py:58`
- **严重程度**: 🔵 LOW
- **描述**: 注释中提及"先用较少 gas 部署测试版本"，指示了合约部署策略。

---

## 按严重程度排序的完整问题列表

| # | 严重程度 | 文件 | 行号 | 问题类型 | 描述 |
|---|----------|------|------|----------|------|
| 1 | 🔴 CRITICAL | deploy_vote_sepolia.py | 6-7 | 硬编码凭据 | 以太坊私钥和账户地址明文硬编码 |
| 2 | 🔴 CRITICAL | membership_api.py | 全局 | 未授权访问 | 所有API函数无认证/授权 |
| 3 | 🔴 CRITICAL | membership_api.py | 288-297 | PII泄露 | email/github_id等敏感字段直接返回 |
| 4 | 🟠 HIGH | random_lottery.py | 88-92 | 不安全的随机数 | VRF密钥使用time.time()作为熵源 |
| 5 | 🟠 HIGH | did.py | 262-287 | 弱签名方案 | HMAC风格签名非真正非对称签名 |
| 6 | 🟠 HIGH | did.py | 61-62 | 不安全文件权限 | 私钥存储目录权限过于宽松 |
| 7 | 🟠 HIGH | did.py | 76-78 | 输入验证不足 | 无路径遍历防护 |
| 8 | 🟠 HIGH | did.py | 78-80 | 明文密钥存储 | 私钥明文写入磁盘 |
| 9 | 🟡 MEDIUM | deploy_vote_sepolia.py | 8 | 配置硬编码 | RPC服务器地址硬编码 |
| 10 | 🟡 MEDIUM | membership_verifier.py | 143 | 验证密钥硬编码 | verification_key使用固定字符串 |
| 11 | 🟡 MEDIUM | voting_kernel.py | 319-321 | 信息泄露 | 错误消息暴露内部状态 |
| 12 | 🟡 MEDIUM | member_db.py | 28-32 | 性能/安全 | 无连接池管理 |
| 13 | 🔵 LOW | 所有模块 | - | 审计缺失 | 无操作审计日志 |

---

## 目录级统计

| 目录 | 文件数 | CRITICAL | HIGH | MEDIUM | LOW | 评分 |
|------|--------|----------|------|--------|-----|------|
| did/ | 2 | 0 | 4 | 0 | 0 | C |
| zkp/ | 4 | 0 | 0 | 1 | 0 | B |
| voting/ | 5 | 0 | 0 | 1 | 0 | B |
| sybil/ | 4 | 0 | 0 | 0 | 0 | A |
| treasury/ | 2 | 0 | 0 | 0 | 0 | A |
| debate/ | 3 | 0 | 1 | 0 | 0 | C |
| membership/ | 5 | 3 | 0 | 1 | 0 | D |
| **总计** | **25** | **3** | **5** | **3** | **1** | **D** |

---

## 总结

**最严重问题集中在两个领域：**

1. **`05-tool/membership/`（入党管理系统）**: 完全无认证的系统，所有API可被任意调用，存储的个人身份信息（邮箱、微信、手机号、GitHub ID）直接暴露。这是最严重的安全隐患，紧急程度最高。

2. **`02-algorithm/voting/deploy_vote_sepolia.py`**: 硬编码了真实的以太坊私钥，任何人拿到该文件即可控制对应账户。虽然该脚本是测试网部署，但形成恶劣的安全习惯。

3. **`02-algorithm/did/did.py`（DID身份系统）**: 签名方案非密码学安全、密钥明文存储、目录权限宽松、无路径遍历防护——四个 HIGH 级别问题。

4. **`02-algorithm/debate/random_lottery.py`（抽签器）**: VRF 使用可预测的熵源生成密钥，可被完全破解，破坏抽签公平性。

**该项目代码质量整体较高**（良好的类型注解、清晰的文档、结构化的代码），但**安全方面存在严重的意识和实践差距**。核心问题在于：
- 将"模拟/简化版"密码学实现用于实际功能路径
- 完全没有认证/授权机制
- 密钥管理实践不符合行业标准
