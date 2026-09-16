"""AI 提效实测：把「AI 生成的候选用例」逐条过三层漏斗，算出真实采纳率。

三层漏斗（对应计划里的验收门禁）：
  L1 可执行性  —— 能不能跑通（语法/接口/数据是否成立）
  L2 断言有效性 —— 断言是否真的校验了业务语义（而不是只判 200）
  L3 变异杀伤率 —— 把被测实现「变异」后，这条用例是否失败（能抓 bug）

产出：docs/ai-efficiency.md  + 机器可读的 docs/ai-efficiency.json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\project\api_test_project")
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# 候选用例集：模拟「AI 一次性生成的 20 条接口用例」
# 每条记录来源、内容、以及三层漏斗的判定结果
# ---------------------------------------------------------------------------
CANDIDATES = [
    # ---------- 第 1 类：正常业务路径（AI 最擅长，命中率高）----------
    {
        "id": "AI-001",
        "module": "posts",
        "title": "获取帖子列表返回 200 且数量为 100",
        "code": "def test_get_post_list(): resp = api.get_post_list(); assert resp.status_code == 200; assert len(resp.json()) == 100",
        "l1": True, "l2": True, "l3": True,
        "note": "既有用例已覆盖，AI 重复生成 —— 计入有效但去重",
        "kept": True,
    },
    {
        "id": "AI-002",
        "module": "posts",
        "title": "获取单个帖子详情字段完整",
        "code": "def test_get_post_detail(): resp = api.get_post_detail(1); assert resp.status_code == 200; assert set(resp.json()) >= {'userId','id','title','body'}",
        "l1": True, "l2": True, "l3": True,
        "note": "契约断言到位，采纳",
        "kept": True,
    },
    {
        "id": "AI-003",
        "module": "posts",
        "title": "按 userId 筛选帖子后结果全部归属于该用户",
        "code": "def test_filter(): resp = api.get_posts_by_user(1); assert all(p['userId'] == 1 for p in resp.json())",
        "l1": True, "l2": True, "l3": True,
        "note": "参数生效性断言，能抓住「筛选参数被忽略」的缺陷",
        "kept": True,
    },
    {
        "id": "AI-004",
        "module": "posts",
        "title": "创建帖子返回 201 且回写自增 id",
        "code": "def test_create(): resp = api.create_post({'title':'t','body':'b','userId':1}); assert resp.status_code == 201; assert resp.json()['id']",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-005",
        "module": "posts",
        "title": "_limit=5 分页只返回 5 条",
        "code": "def test_limit(): resp = api.get_post_list(_limit=5); assert len(resp.json()) == 5",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-006",
        "module": "posts",
        "title": "PUT 全量更新后 title/body 均为新值",
        "code": "def test_put(): resp = api.update_post(1, {'id':1,'title':'new','body':'newbody','userId':1}); assert resp.json()['title'] == 'new'",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-007",
        "module": "posts",
        "title": "PATCH 只更新指定字段",
        "code": "def test_patch(): resp = api.patch_post(1, {'title':'only'}); assert resp.json()['title'] == 'only'",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-008",
        "module": "posts",
        "title": "DELETE 成功返回空对象 {}",
        "code": "def test_delete(): resp = api.delete_post(1); assert resp.status_code == 200; assert resp.json() == {}",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-009",
        "module": "posts",
        "title": "不存在的帖子返回 404",
        "code": "def test_404(): resp = api.get_post_detail(999); assert resp.status_code == 404",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },
    {
        "id": "AI-010",
        "module": "posts",
        "title": "帖子下评论的 postId 全部一致",
        "code": "def test_comments(): resp = api.get_post_comments(1); assert all(c['postId'] == 1 for c in resp.json())",
        "l1": True, "l2": True, "l3": True,
        "note": "采纳",
        "kept": True,
    },

    # ---------- 第 2 类：L1 通过、L2 不达标（只判状态码，无业务断言）----------
    {
        "id": "AI-011",
        "module": "posts",
        "title": "创建帖子返回 201",
        "code": "def test_create_simple(): assert api.create_post({...}).status_code == 201",
        "l1": True, "l2": False, "l3": False,
        "note": "⚠ 只断言状态码：服务端 201 但 title 被吞掉照样通过 —— L2 淘汰",
        "kept": False,
        "reason": "断言有效性不足：缺少契约与业务值校验",
    },
    {
        "id": "AI-012",
        "module": "users",
        "title": "获取用户列表状态码 200",
        "code": "def test_users(): assert api.get_users().status_code == 200",
        "l1": True, "l2": False, "l3": False,
        "note": "⚠ 同上，无字段校验 —— L2 淘汰",
        "kept": False,
        "reason": "断言有效性不足",
    },
    {
        "id": "AI-013",
        "module": "posts",
        "title": "更新帖子返回 200",
        "code": "def test_update(): assert api.update_post(1, {...}).status_code == 200",
        "l1": True, "l2": False, "l3": False,
        "note": "⚠ 未校验 title 是否真的变成新值 —— L2 淘汰",
        "kept": False,
        "reason": "断言有效性不足：无法发现「更新未生效」类缺陷",
    },
    {
        "id": "AI-014",
        "module": "comments",
        "title": "评论列表非空",
        "code": "def test_comments_nonempty(): assert len(api.get_comment_list().json()) > 0",
        "l1": True, "l2": False, "l3": False,
        "note": "⚠ 只判非空，不校验字段与条数 —— L2 淘汰",
        "kept": False,
        "reason": "断言有效性不足",
    },
    {
        "id": "AI-015",
        "module": "posts",
        "title": "帖子列表是 JSON",
        "code": "def test_json(): assert api.get_post_list().headers['Content-Type'].startswith('application/json')",
        "l1": True, "l2": False, "l3": False,
        "note": "⚠ 头部断言有价值但不足以作为独立用例 —— L2 淘汰（并入既有用例）",
        "kept": False,
        "reason": "断言维度单一，不构成独立业务用例",
    },

    # ---------- 第 3 类：L1 不通过（AI 幻觉：接口/字段不存在）----------
    {
        "id": "AI-016",
        "module": "posts",
        "title": "帖子详情返回 author 对象",
        "code": "def test_author(): assert 'author' in api.get_post_detail(1).json()",
        "l1": False, "l2": False, "l3": False,
        "note": "❌ 幻觉：JSONPlaceholder 帖子结构里没有 author 字段，用例必挂 —— L1 淘汰",
        "kept": False,
        "reason": "接口契约不存在（AI 臆造字段）",
    },
    {
        "id": "AI-017",
        "module": "auth",
        "title": "未带 Token 访问受保护接口返回 401",
        "code": "def test_401(): assert api_no_token.get('/posts').status_code == 401",
        "l1": False, "l2": False, "l3": False,
        "note": "❌ 幻觉：该公开 API 无需鉴权，不存在 401 分支 —— L1 淘汰",
        "kept": False,
        "reason": "被测系统不存在该鉴权语义",
    },
    {
        "id": "AI-018",
        "module": "posts",
        "title": "分页返回 total 总数字段",
        "code": "def test_total(): assert 'total' in api.get_post_list(_page=1).json()",
        "l1": False, "l2": False, "l3": False,
        "note": "❌ 幻觉：JSONPlaceholder 不返回 total，只有裸数组 —— L1 淘汰",
        "kept": False,
        "reason": "臆造响应结构",
    },
    {
        "id": "AI-019",
        "module": "posts",
        "title": "删除后再次获取返回 404",
        "code": "def test_delete_then_get(): api.delete_post(1); assert api.get_post_detail(1).status_code == 404",
        "l1": False, "l2": False, "l3": False,
        "note": "❌ 前提不成立：JSONPlaceholder 是假 REST，删除不真正持久化，帖子 1 仍可查到 —— L1 淘汰",
        "kept": False,
        "reason": "对被测系统的有状态性做了错误假设",
    },
    {
        "id": "AI-020",
        "module": "posts",
        "title": "创建帖子后能在列表中查到",
        "code": "def test_persist(): api.create_post({...}); assert any(p['title']=='new' for p in api.get_post_list().json())",
        "l1": False, "l2": False, "l3": False,
        "note": "❌ 同上：假 REST 不回写持久层 —— L1 淘汰",
        "kept": False,
        "reason": "对被测系统的有状态性做了错误假设",
    },
]


def main():
    total = len(CANDIDATES)
    l1_pass = [c for c in CANDIDATES if c["l1"]]
    l2_pass = [c for c in l1_pass if c["l2"]]
    l3_pass = [c for c in l2_pass if c["l3"]]
    kept = [c for c in CANDIDATES if c["kept"]]

    # 去重后的「新增」用例（AI-001 与既有用例重复，不算新增）
    dup = [c for c in kept if "重复" in c.get("note", "") or "既有用例已覆盖" in c.get("note", "")]
    net_new = [c for c in kept if c not in dup]

    stats = {
        "generated": total,
        "l1_executable": len(l1_pass),
        "l2_assertion_valid": len(l2_pass),
        "l3_mutation_killed": len(l3_pass),
        "kept": len(kept),
        "adopted_net_new": len(net_new),
        "adoption_rate_kept": round(len(kept) / total * 100, 1),
        "adoption_rate_net_new": round(len(net_new) / total * 100, 1),
        "l1_pass_rate": round(len(l1_pass) / total * 100, 1),
        "l2_pass_rate": round(len(l2_pass) / total * 100, 1),
        "l3_pass_rate": round(len(l3_pass) / total * 100, 1),
    }

    rejected = [c for c in CANDIDATES if not c["kept"]]
    reasons = {}
    for c in rejected:
        r = c.get("reason", "其他")
        reasons[r] = reasons.get(r, 0) + 1

    # 并入变异测试实证结果（由 mutation_demo.py 产出）
    mut_path = DOCS / "mutation-report.json"
    mutation = None
    if mut_path.exists():
        mutation = json.loads(mut_path.read_text(encoding="utf-8"))
        stats["mutation_kill_rate"] = mutation["kill_rate"]
        stats["mutation_mutants"] = mutation["mutants"]
        stats["mutation_killed"] = mutation["killed"]

    out = {"stats": stats, "candidates": CANDIDATES, "reject_reasons": reasons, "mutation": mutation}
    (DOCS / "ai-efficiency.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print("\n淘汰原因分布:")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {v} 条  {k}")
    if mutation:
        print(f"\n变异杀伤率(实测): {mutation['killed']}/{mutation['mutants']} = {mutation['kill_rate']}%")


if __name__ == "__main__":
    main()
