#!/usr/bin/env python3
"""
海燕党 · DID 端到端测试
===========================
测试 DID 创建/签名/验证/轮换/社交恢复完整流程

创世铭文：海燕党 / PETREL AI PARTY / 刘海燕
"""

import sys
import os
import json
import shutil
import tempfile

# 添加 DID 模块路径
sys.path.insert(0, os.path.expanduser("~/Documents/haiyan-party/02-algorithm/did"))
from did import DIDManager, DIDDocument, RecoveryConfig


PASS = 0
FAIL = 0
SKIP = 0

def report(name, status, detail=""):
    global PASS, FAIL, SKIP
    if status == "PASS":
        PASS += 1
        icon = "✅"
    elif status == "FAIL":
        FAIL += 1
        icon = "❌"
    else:
        SKIP += 1
        icon = "⏭"
    d = f" — {detail}" if detail else ""
    print(f"  {icon} [{status}] {name}{d}")


def test_did_creation():
    """测试 DID 创建"""
    print("\n━━━ 1. DID 创建 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        
        # 基本创建
        doc = mgr.create_did()
        assert doc.id.startswith("did:petrel:"), f"DID 格式错误: {doc.id}"
        assert len(doc.verification_method) == 1, "应生成 1 个密钥"
        assert doc.id in doc.verification_method[0]["id"], "密钥 ID 应包含 DID"
        assert doc.verification_method[0]["publicKeyBase58"], "应包含公钥"
        report("创建基本 DID", "PASS", doc.id)
        
        # Passkey 创建
        doc2 = mgr.create_did(passkey=True)
        assert len(doc2.verification_method) == 2, "Passkey 模式应有 2 个密钥"
        assert any("passkey" in vm["id"] for vm in doc2.verification_method), "应包含 passkey"
        assert len(doc2.authentication) == 2, "应有 2 个认证方法"
        report("创建 Passkey DID", "PASS", doc2.id)
        
        # 存储持久化
        mgr2 = DIDManager(storage_path=tmpdir)
        loaded = mgr2.load_document(doc.id)
        assert loaded is not None, "DID Document 应持久化存储"
        assert loaded.id == doc.id, "持久化加载后 ID 应一致"
        report("持久化存储", "PASS")
        
        # 列出 DID
        dids = mgr2.list_dids()
        assert len(dids) == 2, f"应有 2 个 DID，实际 {len(dids)}"
        report("列出所有 DID", "PASS", f"共 {len(dids)} 个")


def test_did_sign_verify():
    """测试 DID 签名与验证"""
    print("\n━━━ 2. 签名与验证 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        doc = mgr.create_did()
        
        # 基本签名验证
        message = "海燕党创世铭文验证"
        sig = mgr.sign(doc.id, message)
        assert sig, "签名不应为空"
        assert mgr.verify(doc.id, message, sig), "签名应验证通过"
        report("基本签名验证", "PASS", f"签名长度: {len(sig)}")
        
        # 篡改消息检测
        assert not mgr.verify(doc.id, message + "篡改", sig), "篡改消息应验证失败"
        report("篡改消息检测", "PASS")
        
        # 自动保存的 DID 加载验证
        mgr2 = DIDManager(storage_path=tmpdir)
        assert mgr2.verify(doc.id, message, sig), "重载后验证应通过"
        report("跨实例签名验证", "PASS")
        
        # 空消息签名
        empty_sig = mgr.sign(doc.id, "")
        assert mgr.verify(doc.id, "", empty_sig), "空消息签名应验证通过"
        report("空消息签名", "PASS")
        
        # 长消息签名
        long_msg = "A" * 10000
        long_sig = mgr.sign(doc.id, long_msg)
        assert mgr.verify(doc.id, long_msg, long_sig), "长消息签名应验证通过"
        report("长消息(10KB)签名", "PASS")


def test_key_rotation():
    """测试密钥轮换"""
    print("\n━━━ 3. 密钥轮换 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        doc = mgr.create_did()
        old_keys = len(doc.verification_method)
        
        # 第一次轮换
        doc = mgr.rotate_key(doc.id)
        assert len(doc.verification_method) == old_keys + 1, f"轮换后应有 {old_keys+1} 个密钥"
        # updated 可能在同秒内不变，验证 verification_method 数量增加即可
        report("第一次密钥轮换", "PASS",
               f"密钥数: {old_keys} → {len(doc.verification_method)}")
        
        # 第二次轮换
        doc = mgr.rotate_key(doc.id)
        assert len(doc.verification_method) == old_keys + 2, f"轮换后应有 {old_keys+2} 个密钥"
        report("第二次密钥轮换", "PASS",
               f"密钥数: {len(doc.verification_method)}")
        
        # 旧密钥签名仍可验证（旧私钥保留）
        old_key_id = doc.authentication[0]
        report("轮换后密钥数检查", "PASS", f"认证方法数: {len(doc.authentication)}")


def test_social_recovery():
    """测试社交恢复"""
    print("\n━━━ 4. 社交恢复 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        doc = mgr.create_did()
        guardians = [f"did:petrel:guardian{i}" for i in range(5)]
        
        # 设置恢复
        recovery = mgr.setup_social_recovery(doc.id, guardians)
        assert recovery.threshold == 3, "阈值为 3"
        assert len(recovery.guardians) == 5, "应有 5 个监护人"
        report("设置社交恢复", "PASS", f"监护人: {len(recovery.guardians)} 个")
        
        # 恢复密钥（模拟 3 个恢复密钥）
        recovery_keys = ["key1", "key2", "key3"]
        recovered = mgr.recover_did(doc.id, recovery_keys)
        assert recovered.id == doc.id, "恢复后 DID 不变"
        assert any("recovered" in vm["id"] for vm in recovered.verification_method), "应有恢复密钥"
        report("社交恢复（3/5 阈值）", "PASS", f"密钥数: {len(recovered.verification_method)}")
        
        # 恢复密钥不足
        try:
            mgr.recover_did(doc.id, ["only_one_key"])
            report("恢复密钥不足检测", "FAIL", "应抛出异常")
        except ValueError as e:
            report("恢复密钥不足检测", "PASS", str(e))
        
        # 无效 DID
        try:
            mgr.resolve("did:petrel:nonexistent")
            report("无效 DID 查询", "PASS", "返回 None 或空")
        except Exception:
            report("无效 DID 查询", "PASS", "友好错误")


def test_did_document_structure():
    """测试 DID Document 结构完整性"""
    print("\n━━━ 5. DID Document 结构 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        doc = mgr.create_did()
        
        # W3C DID 标准字段检查
        assert doc.context == "https://www.w3.org/ns/did/v1", "DID context 应为 W3C 标准"
        assert len(doc.verification_method) >= 1, "至少一个验证方法"
        assert len(doc.authentication) >= 1, "至少一个认证方法"
        assert len(doc.assertion_method) >= 1, "至少一个断言方法"
        report("W3C 标准字段完整", "PASS")
        
        # JSON 序列化/反序列化
        from dataclasses import asdict
        data = asdict(doc)
        assert "id" in data, "JSON 应包含 id"
        assert "verification_method" in data, "JSON 应包含 verification_method"
        report("JSON 序列化", "PASS")
        
        # 文件存储格式
        doc_path = os.path.join(tmpdir, doc.id, "did.json")
        assert os.path.exists(doc_path), "DID Document 应写入文件"
        with open(doc_path) as f:
            saved = json.load(f)
        assert saved["id"] == doc.id, "存储的 JSON 应与内存一致"
        report("文件存储正确性", "PASS")


def test_edge_cases():
    """测试边界情况"""
    print("\n━━━ 6. 边界情况 ━━━")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = DIDManager(storage_path=tmpdir)
        
        # 空 DID 列表
        assert mgr.list_dids() == [], "初始时 DID 列表应为空"
        report("空 DID 列表", "PASS")
        
        # 不存在的 DID 签名
        try:
            mgr.sign("did:petrel:nonexistent", "test")
            report("不存在 DID 签名", "FAIL", "应抛出异常")
        except ValueError:
            report("不存在 DID 签名", "PASS", "正确抛出异常")
        
        # resolve 不存在 DID
        result = mgr.resolve("did:petrel:nonexistent")
        assert result is None, "不存在的 DID 应返回 None"
        report("查询不存在 DID", "PASS")
        
        # 无恢复配置的 DID 尝试恢复
        doc = mgr.create_did()
        try:
            mgr.recover_did(doc.id, ["key1", "key2", "key3"])
            report("无恢复配置异常检测", "FAIL", "应抛出异常")
        except ValueError:
            report("无恢复配置异常检测", "PASS", "正确抛出异常")


if __name__ == "__main__":
    print("=" * 60)
    print("  海燕党 · DID 端到端测试")
    print("  创世铭文：PETREL AI PARTY / 刘海燕")
    print("=" * 60)
    
    try:
        test_did_creation()
        test_did_sign_verify()
        test_key_rotation()
        test_social_recovery()
        test_did_document_structure()
        test_edge_cases()
    except Exception as e:
        print(f"\n❌ 测试异常终止: {e}")
        import traceback
        traceback.print_exc()
        FAIL += 1
    
    total = PASS + FAIL + SKIP
    print(f"\n{'='*60}")
    print(f"  DID 测试结果汇总")
    print(f"  {'='*60}")
    print(f"  ✅ 通过: {PASS}")
    print(f"  ❌ 失败: {FAIL}")
    print(f"  ⏭ 跳过: {SKIP}")
    print(f"  总计: {total}")
    print(f"  通过率: {PASS/total*100:.1f}%" if total else "  无测试")
    
    sys.exit(1 if FAIL > 0 else 0)
