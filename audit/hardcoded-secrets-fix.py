#!/usr/bin/env python3
"""
海燕党 · 硬编码凭据扫描与修复工具
========================================
扫描项目中所有 .py 文件，检测硬编码的私钥、API密钥、密码等敏感信息。
提供自动修复功能（将硬编码凭据替换为环境变量读取）。

发现日期: 2026-07-26
安全审计: 海燕党安全审计报告 CRITICAL-01 修复

使用方法:
    python3 hardcoded-secrets-fix.py scan          # 扫描所有文件
    python3 hardcoded-secrets-fix.py fix           # 自动修复（创建 .env 文件 + 替换硬编码）
    python3 hardcoded-secrets-fix.py check         # 验证修复结果
"""

import ast
import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ── 项目根目录 ──
PROJECT_ROOT = Path(os.path.expanduser("~/Documents/haiyan-party"))

# ── 要扫描的目录 ──
SCAN_DIRS = [
    "02-algorithm",
    "05-tool",
]

# ── 敏感信息正则模式 ──
SECRET_PATTERNS = {
    "ETH_PRIVATE_KEY": re.compile(
        r'''['"]?(?:PRIVATE_KEY|private_key|privateKey)['"]?\s*[:=]\s*['"]([0-9a-fA-F]{64})['"]'''
    ),
    "ETH_ADDRESS": re.compile(
        r'''['"]?(?:ACCOUNT|account|from_address|to_address)['"]?\s*[:=]\s*['"](0x[0-9a-fA-F]{40})['"]'''
    ),
    "API_KEY": re.compile(
        r'''['"](?:api_key|API_KEY|apikey|token|TOKEN)['"]?\s*[:=]\s*['"]([A-Za-z0-9_\-]{20,})['"]'''
    ),
    "PASSWORD": re.compile(
        r'''['"]?(?:password|PASSWORD|passwd|secret)['"]?\s*[:=]\s*['"]([^'"]{8,})['"]'''
    ),
    "RPC_URL": re.compile(
        r'''['"](?:rpc|RPC|rpc_url|RPC_URL|endpoint|ENDPOINT)['"]?\s*[:=]\s*['"](https?://[^'"]+)['"]'''
    ),
    "SEED_PHRASE": re.compile(
        r'''['"](?:mnemonic|seed|SEED|MNEMONIC)['"]?\s*[:=]\s*['"]([A-Za-z ]{20,})['"]'''
    ),
}

# ── 安全的环境变量名映射 ──
ENV_VAR_MAP = {
    "ETH_PRIVATE_KEY": "ETH_PRIVATE_KEY",
    "ETH_ACCOUNT": "ETH_ACCOUNT",
    "ETH_RPC_URL": "ETH_RPC_URL",
    "VERIFICATION_KEY": "VERIFICATION_KEY",
}


def scan_file(filepath: Path) -> List[Dict]:
    """扫描单个文件中的硬编码凭据"""
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  ⚠ 无法读取 {filepath}: {e}")
        return findings

    lines = content.split("\n")

    for pattern_name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(content):
            line_no = content[:match.start()].count("\n") + 1
            line = lines[line_no - 1] if line_no <= len(lines) else ""
            secret_value = match.group(1) if match.groups() else match.group(0)

            # 过滤误报：仅包含常见库名、版本号的不是密钥
            if len(secret_value) < 16 and pattern_name != "ETH_ADDRESS":
                continue
            # 排除常见的非密钥字符串
            if secret_value in ("placeholder", "pending", "locked", "active",
                                "draft", "submitted", "created", "updated"):
                continue

            findings.append({
                "file": str(filepath.relative_to(PROJECT_ROOT)),
                "line": line_no,
                "pattern": pattern_name,
                "match": line.strip()[:120],
                "severity": _get_severity(pattern_name, secret_value),
            })
    return findings


def _get_severity(pattern: str, value: str) -> str:
    """根据检测到的模式判断严重程度"""
    if pattern == "ETH_PRIVATE_KEY":
        return "CRITICAL"
    elif pattern == "ETH_ADDRESS":
        return "HIGH"
    elif pattern == "API_KEY":
        return "CRITICAL"
    elif pattern == "PASSWORD" and len(value) >= 20:
        return "HIGH"
    elif pattern == "SEED_PHRASE":
        return "CRITICAL"
    elif pattern == "RPC_URL":
        return "MEDIUM"
    return "LOW"


def scan_all() -> List[Dict]:
    """扫描所有指定目录"""
    all_findings = []
    for scan_dir in SCAN_DIRS:
        dir_path = PROJECT_ROOT / scan_dir
        if not dir_path.exists():
            print(f"  ⚠ 目录不存在: {dir_path}")
            continue
        for py_file in sorted(dir_path.rglob("*.py")):
            findings = scan_file(py_file)
            all_findings.extend(findings)
    return all_findings


def generate_env_template(findings: List[Dict]) -> str:
    """生成 .env 模板"""
    env_lines = [
        "# ═══════════════════════════════════════════════",
        "# 海燕党(PETREL AI PARTY) 安全配置",
        "# 创世铭文：AI只献策不决策，人类终审。全部代码开源。",
        "# 警告：此文件包含敏感信息，请勿提交到版本控制系统！",
        "# ═══════════════════════════════════════════════",
        "",
    ]
    seen_vars = set()
    for f in findings:
        if f["pattern"] == "ETH_PRIVATE_KEY" and "ETH_PRIVATE_KEY" not in seen_vars:
            env_lines.append(
                "# 以太坊私钥 — 从 deploy_vote_sepolia.py 中提取\n"
                '# ETH_PRIVATE_KEY="你的私钥"\n'
                "ETH_PRIVATE_KEY=\n"
            )
            seen_vars.add("ETH_PRIVATE_KEY")
        elif f["pattern"] == "ETH_ADDRESS" and "ETH_ACCOUNT" not in seen_vars:
            env_lines.append(
                "# 以太坊账户地址\n"
                '# ETH_ACCOUNT="0x..."\n'
                "ETH_ACCOUNT=\n"
            )
            seen_vars.add("ETH_ACCOUNT")
        elif f["pattern"] == "RPC_URL" and "ETH_RPC_URL" not in seen_vars:
            env_lines.append(
                "# 以太坊 RPC 端点\n"
                '# ETH_RPC_URL="https://..."\n'
                "ETH_RPC_URL=\n"
            )
            seen_vars.add("ETH_RPC_URL")

    return "\n".join(env_lines)


def fix_file(filepath_rel: str, findings: List[Dict]) -> bool:
    """修复特定文件中的硬编码凭据"""
    filepath = PROJECT_ROOT / filepath_rel
    if not filepath.exists():
        print(f"  ✗ 文件不存在: {filepath_rel}")
        return False

    content = filepath.read_text(encoding="utf-8", errors="ignore")
    original = content
    env_file = PROJECT_ROOT / ".env"
    changes = []

    for f in findings:
        if f["file"] != filepath_rel:
            continue
        pattern = f["pattern"]

        if pattern == "ETH_PRIVATE_KEY":
            # 替换为环境变量读取
            old_privkey = f["match"].split("=", 1)[1].strip().strip('"').strip("'") if '"' in f["match"] else f["match"]
            old_line = f'PRIVATE_KEY = "{old_privkey}"'
            content = content.replace(
                old_line,
                'PRIVATE_KEY = os.environ.get("ETH_PRIVATE_KEY", "")',
            )
            changes.append("PRIVATE_KEY → os.environ.get('ETH_PRIVATE_KEY')")
            # 确保已导入 os
            if "import os" not in content:
                content = content.replace(
                    "import json, os, sys, time, hashlib",
                    "import json, os, sys, time, hashlib"
                )

        elif pattern == "ETH_ADDRESS":
            old_token = f["match"].split("=", 1)[1].strip().strip('"').strip("'") if '"' in f["match"] else f["match"]
            old_line = f'ACCOUNT = "{old_token}"'
            content = content.replace(
                old_line,
                'ACCOUNT = os.environ.get("ETH_ACCOUNT", "")',
            )
            changes.append("ACCOUNT → os.environ.get('ETH_ACCOUNT')")

        elif pattern == "RPC_URL":
            old_token = f["match"].split("=", 1)[1].strip().strip('"').strip("'") if '"' in f["match"] else f["match"]
            old_line = f'RPC = "{old_token}"'
            content = content.replace(
                old_line,
                'RPC = os.environ.get("ETH_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")',
            )
            changes.append("RPC → os.environ.get('ETH_RPC_URL')")

    if content != original:
        # 确保文件头部有 os 导入
        if "import os" not in content and "os.environ" in content:
            # 加在文件头部的 import 区域
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("import "):
                    lines.insert(i + 1, "import os")
                    break
            content = "\n".join(lines)

        filepath.write_text(content)
        print(f"  ✓ 已修复: {filepath_rel}")
        for c in changes:
            print(f"    • {c}")
        return True
    return False


def cmd_scan():
    """扫描所有文件中的硬编码凭据"""
    print("=" * 60)
    print("  海燕党 · 硬编码凭据扫描")
    print("=" * 60)
    print()

    findings = scan_all()

    if not findings:
        print("✅ 未发现硬编码凭据！")
        return

    print(f"⚠️  发现 {len(findings)} 个问题:\n")
    for f in findings:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
        print(f"  {icon.get(f['severity'], '•')} [{f['severity']}] {f['file']}:{f['line']}")
        print(f"    类型: {f['pattern']}")
        print(f"    内容: {f['match']}")
        print()

    # 统计
    by_severity = {}
    for f in findings:
        s = f["severity"]
        by_severity[s] = by_severity.get(s, 0) + 1
    print("--- 统计 ---")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev in by_severity:
            print(f"  {sev}: {by_severity[sev]}")
    print(f"  总计: {len(findings)}")


def cmd_fix():
    """自动修复硬编码凭据"""
    print("=" * 60)
    print("  海燕党 · 硬编码凭据自动修复")
    print("=" * 60)
    print()

    findings = scan_all()
    if not findings:
        print("✅ 未发现需要修复的问题")
        return

    # 1. 生成 .env 模板
    env_content = generate_env_template(findings)
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        env_path.write_text(env_content)
        print(f"  ✓ 已创建 {env_path}")
        print("  ⚠ 请编辑 .env 文件填入真实的密钥值！")
    else:
        print(f"  ℹ️  {env_path} 已存在，跳过创建")

    # 2. 创建 .gitignore 确保 .env 不被提交
    gitignore_path = PROJECT_ROOT / ".gitignore"
    env_ignored = False
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".env" in content:
            env_ignored = True
    if not env_ignored:
        with open(gitignore_path, "a") as f:
            f.write("\n# 安全配置 — 含私钥/API密钥\n.env\n")
        print(f"  ✓ 已将 .env 加入 {gitignore_path}")

    # 3. 修复文件
    print()
    fixed_files = set()
    for f in findings:
        fixed_files.add(f["file"])

    for filepath_rel in sorted(fixed_files):
        file_findings = [f for f in findings if f["file"] == filepath_rel]
        fix_file(filepath_rel, file_findings)

    print()
    print("=" * 60)
    print("  修复完成！")
    print()
    print("  后续步骤:")
    print("  1. 编辑 .env 填入真实密钥")
    print("  2. 检查替换后的代码是否正常工作")
    print("  3. 如果该私钥曾经用于主网，立即轮换！")
    print("=" * 60)


def cmd_check():
    """验证修复结果"""
    print("=" * 60)
    print("  海燕党 · 修复验证")
    print("=" * 60)
    print()

    findings = scan_all()
    if not findings:
        print("✅ 验证通过！无硬编码凭据残留。")
        return

    print(f"⚠️  仍有 {len(findings)} 个问题未修复:\n")
    for f in findings:
        print(f"  🔴 [{f['severity']}] {f['file']}:{f['line']}")
        print(f"    内容: {f['match']}")
        print()


def main():
    if len(sys.argv) < 2:
        print("用法: python3 hardcoded-secrets-fix.py <scan|fix|check>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "scan":
        cmd_scan()
    elif cmd == "fix":
        cmd_fix()
    elif cmd == "check":
        cmd_check()
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: scan, fix, check")
        sys.exit(1)


if __name__ == "__main__":
    main()
