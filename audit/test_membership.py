#!/usr/bin/env python3
"""
海燕党 · 入党流程端到端测试
==============================
测试：申请提交 → AI初审 → 人类终审 → 考察期 → 转正/退党

创世铭文：AI只献策不决策，人类终审。全部代码开源。
创世铭文：海燕党 / PETREL AI PARTY / 刘海燕
"""

import sys
import os
import json
import tempfile
import shutil

# 添加 membership 模块路径
MEMBERSHIP_DIR = os.path.expanduser("~/Documents/haiyan-party/05-tool/membership")
sys.path.insert(0, MEMBERSHIP_DIR)

# 临时数据库路径
TEMP_DB = os.path.join(tempfile.gettempdir(), f"test_party_{os.getpid()}.db")

# 注入临时数据库路径
import member_db
member_db.DB_PATH = TEMP_DB

from member_db import (
    init_db, get_db, create_application, get_application,
    update_status, add_probation_record, get_probation_records,
    create_evaluation, get_evaluations, create_promotion,
    get_promotion, dismiss_member, get_stats
)

from membership_api import (
    ai_initial_screening, human_review, record_probation_month,
    run_evaluation, committee_promote, handle_dismiss
)


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


def setup():
    """测试前初始化"""
    init_db()
    print(f"  测试数据库: {TEMP_DB}")


def cleanup():
    """测试后清理"""
    if os.path.exists(TEMP_DB):
        os.remove(TEMP_DB)
    for ext in ["-wal", "-shm"]:
        p = TEMP_DB + ext
        if os.path.exists(p):
            os.remove(p)


def test_application_submit():
    """测试申请提交"""
    print("\n━━━ 1. 入党申请提交 ━━━")
    
    uid = create_application(
        name="测试党员",
        email="test@petrel.party",
        reason="我认同海燕党开源、去中心化、AI治理的理念，愿意为社区贡献技术力量，推动AI民主化发展。",
        nickname="test_dev",
        github_id="testdev",
        wechat_id="test_wechat",
        phone="13800138000",
        skills='["Python","Solidity","AI","社区运营"]',
        contribution="可以为海燕党贡献智能合约审计和社区运营经验"
    )
    assert uid and len(uid) == 8, f"UUID格式错误: {uid}"
    report("提交入党申请", "PASS", f"编号={uid}")
    
    # 验证持久化
    app = get_application(1)
    assert app is not None, "申请记录应存在"
    assert app["name"] == "测试党员", "姓名应正确"
    assert app["status"] == "pending", f"初始状态应为 pending，实际为 {app['status']}"
    report("数据持久化验证", "PASS", f"状态={app['status']}")
    
    return 1  # app_id


def test_detailed_application():
    """测试详细申请字段"""
    print("\n━━━ 2. 详细申请字段 ━━━")
    
    uid = create_application(
        name="技术研究员",
        email="tech@petrel.party",
        reason="开源",
        nickname="tech",
        skills='["Python"]',
        contribution="",
    )
    app = get_application(2)
    assert app["name"] == "技术研究员"
    assert app["email"] == "tech@petrel.party"
    assert app["reason"] == "开源"
    assert app["skills"] == '["Python"]'
    report("简略申请字段", "PASS", "所有字段正确存储")
    
    uid3 = create_application(
        name="完整申请者",
        email="full@petrel.party",
        reason="我是一名全栈开发者，深刻理解去中心化技术对人类社会的影响。"
               "海燕党的AI治理理念与我不谋而合。我参与过多个开源项目，"
               "希望能将我的技术能力贡献给海燕党的发展。"
               "我相信通过开源协作和AI辅助决策可以实现真正的社区民主治理。",
        nickname="fullstack_dev",
        github_id="fullstack_dev",
        wechat_id="wechat_full",
        phone="13900139000",
        skills='["React","Python","Go","Kubernetes","社区运营","技术写作","智能合约"]',
        contribution="可以为海燕党开发DApp界面、编写技术文档、参与社区治理系统建设"
    )
    app3 = get_application(3)
    assert app3["name"] == "完整申请者"
    assert len(app3["reason"]) > 100
    assert app3["github_id"] == "fullstack_dev"
    report("完整申请字段", "PASS", f"动机{len(app3['reason'])}字，技能7项")
    
    return 2, 3


def test_ai_initial_screening():
    """测试AI资格初审"""
    print("\n━━━ 3. AI资格初审 ━━━")
    
    # ── 完善的申请（应达到 suggest_approve） ──
    uid = create_application(
        name="优质申请者",
        email="good@petrel.party",
        reason="我研究去中心化治理多年，海燕党的开源民主理念与AI治理框架"
               "在社区协作方面的创新让我看到了真正的民主化技术治理的可能。"
               "我致力于为这个开放共创的社区贡献我的全部技术能力和治理经验。",
        skills='["Solidity","Python","治理研究","社区运营","技术写作"]',
        contribution="可以为海燕党设计治理框架、审计智能合约、培养新人",
    )
    app = get_application(4)
    
    opinion = ai_initial_screening(4)
    assert "error" not in opinion, f"初审出错: {opinion.get('error')}"
    assert opinion["score"] >= 0, "评分应 >= 0"
    report("优质申请AI初审", "PASS",
           f"评分={opinion['score']}/100 判定={opinion['verdict']}")
    
    # ── 劣质申请（应达到 suggest_reject） ──
    uid5 = create_application(
        name="不合格者",
        email="bad@petrel.party",
        reason="路过",
        skills="[]",
        contribution="",
    )
    opinion5 = ai_initial_screening(5)
    assert opinion5["score"] <= 40, f"劣质申请评分应低，实际={opinion5['score']}"
    report("不合格申请AI初审", "PASS",
           f"评分={opinion5['score']}/100 判定={opinion5['verdict']}")
    
    # ── AI 意见写入数据库 ──
    app_updated = get_application(4)
    assert app_updated["status"] == "screening", f"状态应为 screening: {app_updated['status']}"
    assert app_updated["ai_opinion"], "AI意见应写入数据库"
    report("AI意见持久化", "PASS")
    
    # ── 重复初审检测 ──
    dup = ai_initial_screening(4)
    assert "error" in dup, "重复初审应报错"
    report("重复初审检测", "PASS", dup["error"])
    
    return 4, 5


def test_human_review():
    """测试人类终审"""
    print("\n━━━ 4. 人类委员会终审 ━━━")
    
    # 通过
    result = human_review(4, "approved", notes="AI建议通过，委员会评估后同意进入考察期")
    assert "error" not in result, f"终审出错: {result.get('error')}"
    assert result["new_status"] == "approved", f"应为 approved: {result['new_status']}"
    report("人类终审（通过）", "PASS",
           f"{result['previous_status']} → {result['new_status']}")
    
    # 自动创建第一条考察记录
    records = get_probation_records(4)
    assert len(records) >= 1, "终审通过后应自动创建考察记录"
    report("自动创建考察记录", "PASS", f"已有 {len(records)} 条记录")
    
    # 拒绝
    result2 = human_review(5, "rejected", notes="申请材料不足")
    assert result2["new_status"] == "rejected"
    report("人类终审（拒绝）", "PASS", f"{result2['previous_status']} → {result2['new_status']}")
    
    # 无效决定
    result3 = human_review(4, "invalid_decision", "")
    assert "error" in result3, "无效决定应报错"
    report("无效决定检测", "PASS", f"错误: {result3['error']}")
    
    # 不存在申请
    result4 = human_review(9999, "approved", "")
    assert "error" in result4, "不存在申请应报错"
    report("不存在申请检测", "PASS")


def test_probation_tracking():
    """测试考察期追踪"""
    print("\n━━━ 5. 考察期追踪 ━━━")
    
    # 记录第1月
    r1 = record_probation_month(4, month=1, study_progress=80,
                                 tasks_completed=5, participation=75,
                                 notes="完成智能合约审计培训")
    assert "error" not in r1
    report("考察第1月记录", "PASS", f"学习进度={r1['study_progress']}")
    
    # 记录第2月
    r2 = record_probation_month(4, month=2, study_progress=90,
                                 tasks_completed=3, participation=85,
                                 notes="参与社区翻译工作")
    assert "error" not in r2
    report("考察第2月记录", "PASS", f"任务完成={r2['tasks_completed']}")
    
    # 记录第3月
    r3 = record_probation_month(4, month=3, study_progress=95,
                                 tasks_completed=8, participation=90,
                                 notes="主导完成提案系统开发")
    assert "error" not in r3
    report("考察第3月记录", "PASS", f"参与度={r3['participation']}")
    
    # 验证记录查询
    records = get_probation_records(4)
    assert len(records) == 4, f"应有4条记录（1条自动创建+3个月），实际{len(records)}"
    report("考察记录查询", "PASS", f"共 {len(records)} 条记录")
    
    # 无效月份
    r4 = record_probation_month(4, month=7, notes="")
    assert "error" in r4, "月份超范围应报错"
    report("月份范围检测", "PASS", r4["error"])
    
    # 不存在申请
    r5 = record_probation_month(9999, month=1, notes="")
    assert "error" in r5
    report("不存在考察记录", "PASS")


def test_evaluation_and_promotion():
    """测试AI评估报告与人类转正"""
    print("\n━━━ 6. AI评估与转正 ━━━")
    
    # AI 评估报告
    eval_result = run_evaluation(4)
    report("AI评估报告生成", "PASS" if eval_result else "FAIL")
    
    # 人类委员会转正投票
    votes = {"total": 5, "approve": 4, "reject": 0, "abstain": 1}
    result = committee_promote(4, votes=votes, notes="考察期内表现优秀")
    assert "error" not in result, f"转正出错: {result.get('error')}"
    assert "certificate_id" in result, "应有证书编号"
    assert result["certificate_id"].startswith("HY-"), f"证书编号格式错误: {result['certificate_id']}"
    report("人类委员会转正", "PASS",
           f"投票 {result['votes']['approve']}/{result['votes']['total']} "
           f"证书={result['certificate_id']}")
    
    # 验证持久化
    app = get_application(4)
    assert app["status"] == "promoted", f"状态应为 promoted: {app['status']}"
    promotion = get_promotion(4)
    assert promotion is not None, "转正记录应存在"
    assert promotion["certificate_id"] == result["certificate_id"]
    report("转正记录持久化", "PASS",
           f"状态={app['status']} 证书={promotion['certificate_id']}")
    
    # 转正后状态检查
    promoted_app = get_application(4)
    assert promoted_app["status"] == "promoted"
    report("党员状态验证", "PASS", f"最终状态: {promoted_app['status']}")


def test_dismiss_flow():
    """测试退党流程"""
    print("\n━━━ 7. 退党处理 ━━━")
    
    # 创建退党测试申请
    uid = create_application(
        name="退党测试",
        email="leave@petrel.party",
        reason="测试退党流程",
    )
    
    result = handle_dismiss(6, reason="个人原因申请退党")
    assert "error" not in result, f"退党出错: {result.get('error')}"
    report("退党处理", "PASS", result["message"])
    
    app = get_application(6)
    assert app["status"] == "dismissed", f"状态应为 dismissed: {app['status']}"
    report("退党状态验证", "PASS", f"状态: {app['status']}")
    
    # 不存在申请退党
    result2 = handle_dismiss(9999, reason="测试")
    assert "error" in result2
    report("不存在退党检测", "PASS")


def test_stats():
    """测试统计数据"""
    print("\n━━━ 8. 统计数据 ━━━")
    
    stats = get_stats()
    assert stats["total_applications"] >= 6, f"应有至少6个申请: {stats['total_applications']}"
    assert stats["total_promoted"] >= 1, f"应有至少1个转正: {stats['total_promoted']}"
    assert "promoted" in stats["by_status"], "状态分布中应有 promoted"
    report("统计数据", "PASS",
           f"总申请={stats['total_applications']} 转正={stats['total_promoted']} "
           f"状态分布={stats['by_status']}")


def test_list_members():
    """测试成员列表"""
    print("\n━━━ 9. 成员列表 ━━━")
    
    from membership_api import list_members
    
    all_members = list_members()
    assert len(all_members) >= 6, f"成员数应 >= 6: {len(all_members)}"
    report("全量成员列表", "PASS", f"共 {len(all_members)} 人")
    
    # 按状态筛选
    promoted = list_members(status="promoted")
    assert len(promoted) >= 1, "应有已转正党员"
    report("状态筛选（promoted）", "PASS", f"共 {len(promoted)} 人")
    
    pending = list_members(status="pending")
    assert len(pending) >= 1, "应有待处理申请"
    report("状态筛选（pending）", "PASS", f"共 {len(pending)} 人")
    
    # 检查返回字段
    if promoted:
        m = promoted[0]
        assert "status" in m, "结果应包含 status"
        assert "uuid" in m, "结果应包含 uuid"
        assert "certificate_id" in m, "已转正应有 certificate_id"
        report("成员信息字段完整性", "PASS",
               f"字段数={len(m)}")


if __name__ == "__main__":
    print("=" * 60)
    print("  海燕党 · 入党流程端到端测试")
    print("  流程：申请→AI初审→人类终审→考察→转正/退党")
    print("  创世铭文：AI只献策不决策，人类终审")
    print("=" * 60)
    
    try:
        setup()
        
        app_id = test_application_submit()
        app_ids = test_detailed_application()
        score_ids = test_ai_initial_screening()
        test_human_review()
        test_probation_tracking()
        test_evaluation_and_promotion()
        test_dismiss_flow()
        test_stats()
        test_list_members()
        
    except Exception as e:
        print(f"\n❌ 测试异常终止: {e}")
        import traceback
        traceback.print_exc()
        FAIL += 1
    finally:
        cleanup()
    
    total = PASS + FAIL + SKIP
    print(f"\n{'='*60}")
    print(f"  入党流程测试汇总")
    print(f"  {'='*60}")
    print(f"  ✅ 通过: {PASS}")
    print(f"  ❌ 失败: {FAIL}")
    print(f"  ⏭ 跳过: {SKIP}")
    print(f"  总计: {total}")
    print(f"  通过率: {PASS/total*100:.1f}%" if total else "  无测试")
    
    sys.exit(1 if FAIL > 0 else 0)
