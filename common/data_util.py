"""数据工具：统一加载 YAML / JSON 测试数据，并按用例名生成可读 id。

用例 id 会显示成 [正常获取帖子1] 这种形式，报告里一眼能看出哪条挂了。
"""
import json
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_yaml(file_path):
    """加载 YAML 文件，支持传相对路径（相对项目根）或绝对路径。"""
    path = _resolve(file_path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data is not None, f"数据文件为空: {path}"
    return data


def load_json(file_path):
    """加载 JSON 文件。"""
    path = _resolve(file_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def case_ids(cases, key="name"):
    """给 parametrize 生成可读的用例 id。

    用法：@pytest.mark.parametrize("case", data, ids=case_ids(data))
    """
    ids = []
    for index, case in enumerate(cases):
        name = case.get(key) if isinstance(case, dict) else None
        ids.append(name or f"case-{index}")
    return ids


def _resolve(file_path):
    path = Path(file_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    assert path.exists(), f"数据文件不存在: {path}"
    return path
