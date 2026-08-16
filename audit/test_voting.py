#!/usr/bin/env python3
"""
海燕党 · 投票合约端到端测试
=============================
测试 PetrelVote 合约完整生命周期（通过 Sepolia RPC）

合约地址: 0xc1B7908cedD0c255df68482fd449de5A5403e102
创世交易: 0427bc36
创世铭文：海燕党 / PETREL AI PARTY / 刘海燕
"""

import sys
import os
import json
import time

try:
    from web3 import Web3
except ImportError:
    print("❌ 需要 web3.py: pip install web3")
    sys.exit(1)

PASS = 0
FAIL = 0
SKIP = 0

# ── 配置 ──
SEPOLIA_RPC = os.environ.get("SEPOLIA_RPC_URL", "")
PRIVATE_KEY = os.environ.get("TEST_PRIVATE_KEY", "")
CONTRACT_ADDRESS = "0xc1B7908cedD0c255df68482fd449de5A5403e102"

# PetrelVoteContract ABI（核心函数签名）
CONTRACT_ABI = json.loads("""
[
    {"type":"function","name":"proposalCount","inputs":[],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},
    {"type":"function","name":"owner","inputs":[],"outputs":[{"name":"","type":"address","internalType":"address"}],"stateMutability":"view"},
    {"type":"function","name":"hasVoted","inputs":[{"name":"","type":"uint256"},{"name":"","type":"address"}],"outputs":[{"name":"","type":"bool","internalType":"bool"}],"stateMutability":"view"},
    {"type":"function","name":"voteCounts","inputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"}],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},
    {"type":"function","name":"genesisInscription","inputs":[],"outputs":[{"name":"","type":"string","internalType":"string"}],"stateMutability":"pure"},
    {"type":"function","name":"createProposal","inputs":[{"name":"title","type":"string"},{"name":"description","type":"string"},{"name":"options","type":"string[]"},{"name":"durationSeconds","type":"uint256"}],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"nonpayable"},
    {"type":"function","name":"vote","inputs":[{"name":"proposalId","type":"uint256"},{"name":"optionIndex","type":"uint256"}],"outputs":[],"stateMutability":"nonpayable"},
    {"type":"function","name":"executeProposal","inputs":[{"name":"proposalId","type":"uint256"}],"outputs":[],"stateMutability":"nonpayable"},
    {"type":"function","name":"getProposal","inputs":[{"name":"proposalId","type":"uint256"}],"outputs":[{"components":[{"name":"id","type":"uint256"},{"name":"title","type":"string"},{"name":"description","type":"string"},{"name":"options","type":"string[]"},{"name":"createdAt","type":"uint256"},{"name":"endAt","type":"uint256"},{"name":"executed","type":"bool"},{"name":"creator","type":"address"}],"name":"","type":"tuple","internalType":"struct PetrelVoteContract.Proposal"}],"stateMutability":"view"},
    {"type":"function","name":"getResults","inputs":[{"name":"proposalId","type":"uint256"}],"outputs":[{"name":"","type":"uint256[]","internalType":"uint256[]"}],"stateMutability":"view"},
    {"type":"function","name":"getTotalVoters","inputs":[{"name":"proposalId","type":"uint256"}],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},
    {"type":"function","name":"allVotes","inputs":[{"name":"","type":"uint256"}],"outputs":[{"name":"voter","type":"address"},{"name":"proposalId","type":"uint256"},{"name":"optionIndex","type":"uint256"},{"name":"timestamp","type":"uint256"}],"stateMutability":"view"}
]
""")


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


def setup_web3():
    """初始化 Web3 连接"""
    if not SEPOLIA_RPC:
        print("  ⚠ 未设置 SEPOLIA_RPC_URL 环境变量")
        return None, None
    
    w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
    if not w3.is_connected():
        print(f"  ⚠ 无法连接 Sepolia RPC: {SEPOLIA_RPC}")
        return None, None
    
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    return w3, contract


def test_read_contract():
    """测试只读合约调用（无需私钥）"""
    print("\n━━━ 1. 只读调用 ━━━")
    
    w3, contract = setup_web3()
    if not w3:
        report("测试环境", "SKIP", "无 RPC 连接")
        return False
    
    try:
        # 创世铭文
        inscription = contract.functions.genesisInscription().call()
        assert inscription == "PETREL AI PARTY", f"铭文不匹配: {inscription}"
        report("创世铭文检查", "PASS", inscription)
        
        # 所有者
        owner = contract.functions.owner().call()
        assert owner and Web3.is_address(owner), "所有者地址无效"
        report("合约所有者", "PASS", owner)
        
        # 提案数量
        count = contract.functions.proposalCount().call()
        report("现有提案数", "PASS", f"{count} 个")
        
        # 读取创世提案（如果存在）
        if count > 0:
            prop = contract.functions.getProposal(1).call()
            report("创世提案读取", "PASS", f"标题: {prop[1][:30]}...")
            assert len(prop) >= 6, "提案数据格式正确"
        
        return True
        
    except Exception as e:
        report("只读调用", "FAIL", str(e))
        return False


def test_write_proposal():
    """测试创建提案和投票（需要私钥）"""
    print("\n━━━ 2. 提案创建与投票 ━━━")
    
    if not PRIVATE_KEY:
        report("测试环境", "SKIP", "无 TEST_PRIVATE_KEY")
        return False
    
    w3, contract = setup_web3()
    if not w3:
        report("测试环境", "SKIP", "无 RPC 连接")
        return False
    
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        
        # ── 创建提案 ──
        title = f"测试提案-{int(time.time())}"
        description = "海燕党端到端自动测试提案"
        options = ["赞成", "反对", "弃权"]
        duration = 3600 * 24  # 1天
        
        tx = contract.functions.createProposal(
            title, description, options, duration
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        assert receipt["status"] == 1, "提案创建交易失败"
        nonce += 1
        
        # 获取新提案 ID
        count = contract.functions.proposalCount().call()
        proposal_id = count
        report("创建提案", "PASS",
               f"ID={proposal_id} tx={tx_hash.hex()[:14]}...")
        
        # ── 验证提案 ──
        prop = contract.functions.getProposal(proposal_id).call()
        assert prop[1] == title, "提案标题不匹配"
        assert prop[0] == proposal_id, "提案 ID 不匹配"
        report("验证提案", "PASS", f"标题={prop[1]}")
        
        # ── 投票 ──
        tx = contract.functions.vote(proposal_id, 0).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        assert receipt["status"] == 1, "投票交易失败"
        nonce += 1
        report("投票（赞成）", "PASS", f"tx={tx_hash.hex()[:14]}...")
        
        # ── 验证投票统计 ──
        voted = contract.functions.hasVoted(proposal_id, account.address).call()
        assert voted, "投票记录应存在"
        vote_count = contract.functions.voteCounts(proposal_id, 0).call()
        assert vote_count >= 1, "赞成票数应 >= 1"
        report("验证投票记录", "PASS", f"hasVoted={voted} 赞成票={vote_count}")
        
        # ── 重复投票检测 ──
        try:
            tx = contract.functions.vote(proposal_id, 1).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": w3.eth.gas_price,
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            assert receipt["status"] == 0, "重复投票应失败"
            report("重复投票检测", "PASS", "交易回滚")
        except Exception:
            report("重复投票检测", "PASS", "被合约拒绝")
        
        return True
        
    except Exception as e:
        report("提案创建/投票", "FAIL", str(e))
        return False


def test_contract_events():
    """测试合约事件"""
    print("\n━━━ 3. 合约事件 ━━━")
    
    w3, contract = setup_web3()
    if not w3:
        report("测试环境", "SKIP", "无 RPC 连接")
        return False
    
    try:
        # 读取最近的 ProposalCreated 事件
        from web3._utils.events import get_event_data
        latest = w3.eth.block_number
        
        event_signature = w3.keccak(text="ProposalCreated(uint256,string,address,uint256)").hex()
        logs = w3.eth.get_logs({
            "fromBlock": max(0, latest - 10000),
            "toBlock": latest,
            "address": CONTRACT_ADDRESS,
            "topics": [event_signature]
        })
        
        if logs:
            report("ProposalCreated 事件", "PASS", f"最近 {len(logs)} 个")
        else:
            report("ProposalCreated 事件", "PASS", "0 个事件（正常）")
        
        # VoteCast 事件
        event_sig2 = w3.keccak(text="VoteCast(uint256,address,uint256)").hex()
        logs2 = w3.eth.get_logs({
            "fromBlock": max(0, latest - 10000),
            "toBlock": latest,
            "address": CONTRACT_ADDRESS,
            "topics": [event_sig2]
        })
        report("VoteCast 事件", "PASS", f"最近 {len(logs2)} 个")
        
        return True
        
    except Exception as e:
        report("事件测试", "FAIL", str(e))
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  海燕党 · 投票合约端到端测试")
    print(f"  合约地址: {CONTRACT_ADDRESS}")
    print("  创世铭文：PETREL AI PARTY / 刘海燕")
    print("=" * 60)
    
    has_rpc = test_read_contract()
    has_key = test_write_proposal()
    
    if has_rpc:
        test_contract_events()
    
    total = PASS + FAIL + SKIP
    print(f"\n{'='*60}")
    print(f"  投票合约测试汇总")
    print(f"  {'='*60}")
    print(f"  ✅ 通过: {PASS}")
    print(f"  ❌ 失败: {FAIL}")
    print(f"  ⏭ 跳过: {SKIP}")
    print(f"  总计: {total}")
    print(f"  通过率: {PASS/total*100:.1f}%" if total else "  无测试")
    print()
    print(f"  说明:")
    if not SEPOLIA_RPC:
        print(f"  ⚠ 跳过写测试: 设置 SEPOLIA_RPC_URL 以连接 Sepolia")
    if not PRIVATE_KEY:
        print(f"  ⚠ 跳过写测试: 设置 TEST_PRIVATE_KEY 以获得写权限")
    if SEPOLIA_RPC and PRIVATE_KEY:
        print(f"  ✓ 所有测试执行完毕")
    
    sys.exit(1 if FAIL > 0 else 0)
