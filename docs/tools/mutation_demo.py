"""变异测试实证：向业务 API 层注入缺陷，验证用例是否真的能抓住。

这是 AI 采纳率三层漏斗里 L3「变异杀伤率」的证据来源 —— 不是嘴上说能抓 bug，
而是真的注入 bug 跑一遍，看用例红不红。

做法：临时备份 posts_api.py，往里面注入一个缺陷，跑指定用例，
记录是否失败（failed = 被杀死 / passed = 存活），最后还原文件。

用法：python mutation_demo.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\project\api_test_project")
PY = r"D:\project\venv\Scripts\python.exe"
API = ROOT / "testcases" / "posts" / "posts_api.py"
BACKUP = ROOT / "testcases" / "posts" / "posts_api.py.bak"


def run_case(node_id: str) -> str:
    """跑单条用例，返回 passed / failed / error。"""
    r = subprocess.run(
        [PY, "-m", "pytest", node_id, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"(\d+) passed", out)
    f = re.search(r"(\d+) failed", out)
    e = re.search(r"(\d+) error", out)
    if f and int(f.group(1)) > 0:
        return "failed"
    if e and int(e.group(1)) > 0:
        return "error"
    if m and int(m.group(1)) > 0:
        return "passed"
    return "unknown"


# ---------------------------------------------------------------------------
# 变异体定义：每个变异体 = 一处「实现被改错」，看用例能否发现
# ---------------------------------------------------------------------------
MUTANTS = [
    {
        "id": "M1",
        "desc": "筛选参数 userId 被静默忽略（服务端 bug 的典型形态）",
        "target": "def get_posts_by_user(self, user_id):\n        \"\"\"按用户筛选帖子（JSONPlaceholder 支持 ?userId=）。\"\"\"\n        return self.get(self.MODULE, params={\"userId\": user_id})",
        "mutated": "def get_posts_by_user(self, user_id):\n        \"\"\"按用户筛选帖子（JSONPlaceholder 支持 ?userId=）。\"\"\"\n        return self.get(self.MODULE)",
        "case": "testcases/posts/test_posts.py::TestPosts::test_get_posts_by_user",
        "expect": "failed",
        "killed_by": "断言每条帖子 userId==1",
    },
    {
        "id": "M2",
        "desc": "更新接口把 title 写成了错误的字段名，导致更新丢失",
        "target": "    def update_post(self, post_id, update_data):\n        \"\"\"全量更新帖子。\"\"\"\n        return self.put(f\"{self.MODULE}/{post_id}\", json=update_data)",
        "mutated": "    def update_post(self, post_id, update_data):\n        \"\"\"全量更新帖子。\"\"\"\n        bad = {k: v for k, v in update_data.items() if k != 'title'}\n        return self.put(f\"{self.MODULE}/{post_id}\", json=bad)",
        "case": "testcases/posts/test_posts.py::TestPosts::test_update_post",
        "expect": "failed",
        "killed_by": "断言更新后 title 等于新值",
    },
    {
        "id": "M3",
        "desc": "分页参数 _limit 被丢弃，返回全量数据",
        "target": "    def get_post_list(self, **params):\n        \"\"\"获取帖子列表，支持 _limit / _page 等查询参数。\"\"\"\n        return self.get(self.MODULE, params=params or None)",
        "mutated": "    def get_post_list(self, **params):\n        \"\"\"获取帖子列表，支持 _limit / _page 等查询参数。\"\"\"\n        return self.get(self.MODULE)",
        "case": "testcases/posts/test_posts.py::TestPosts::test_get_post_list_with_limit",
        "expect": "failed",
        "killed_by": "断言分页返回条数 == 5",
    },
    {
        "id": "M4",
        "desc": "详情接口返回固定 id=1，忽略请求的 id",
        "target": "    def get_post_detail(self, post_id):\n        \"\"\"获取单条帖子详情。\"\"\"\n        return self.get(f\"{self.MODULE}/{post_id}\")",
        "mutated": "    def get_post_detail(self, post_id):\n        \"\"\"获取单条帖子详情。\"\"\"\n        return self.get(f\"{self.MODULE}/1\")",
        "case": "testcases/posts/test_posts.py::TestPosts::test_get_post_detail",
        "expect": "failed",
        "killed_by": "断言返回 id 等于请求 id",
    },
    {
        "id": "M5",
        "desc": "对照：完全不改代码（应通过），验证测试本身没坏",
        "target": None,
        "mutated": None,
        "case": "testcases/posts/test_posts.py::TestPosts::test_get_posts_by_user",
        "expect": "passed",
        "killed_by": "（基线对照）",
    },
]


def main():
    original = API.read_text(encoding="utf-8")
    shutil.copy2(API, BACKUP)
    results = []
    try:
        for m in MUTANTS:
            if m["target"] is None:
                # 基线：还原原文件跑一遍
                API.write_text(original, encoding="utf-8")
            else:
                if m["target"] not in original:
                    results.append({**m, "actual": "SKIP", "note": "未匹配到变异锚点"})
                    print(f"[{m['id']}] SKIP 锚点未匹配")
                    continue
                API.write_text(original.replace(m["target"], m["mutated"], 1), encoding="utf-8")

            actual = run_case(m["case"])
            killed = (actual == "failed") if m["expect"] == "failed" else (actual == "passed")
            results.append({**m, "actual": actual, "killed": killed})
            flag = "✅ 杀死" if killed else "❌ 存活/异常"
            print(f"[{m['id']}] {flag}  期望={m['expect']} 实际={actual}  —— {m['desc']}")
    finally:
        API.write_text(original, encoding="utf-8")
        if BACKUP.exists():
            BACKUP.unlink()
        print("\n已还原 posts_api.py")

    # 统计（排除基线对照）
    real = [r for r in results if r.get("target") is not None]
    killed = [r for r in real if r.get("killed")]
    summary = {
        "mutants": len(real),
        "killed": len(killed),
        "survived": len(real) - len(killed),
        "kill_rate": round(len(killed) / len(real) * 100, 1) if real else 0,
        "details": [
            {
                "id": r["id"], "desc": r["desc"], "expected": r["expect"],
                "actual": r.get("actual"), "killed": r.get("killed"),
                "caught_by": r.get("killed_by"),
            }
            for r in results
        ],
    }
    (ROOT / "docs" / "mutation-report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n变异杀伤率: {summary['killed']}/{summary['mutants']} = {summary['kill_rate']}%")


if __name__ == "__main__":
    main()
