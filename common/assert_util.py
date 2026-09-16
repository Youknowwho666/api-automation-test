"""断言工具：把重复的业务校验抽成可复用方法，让用例代码更短、报错更清晰。

所有断言失败都会带上「期望值 vs 实际值」和接口原始响应，排查时不用重新跑。
"""
import json

from common.logger import logger


class AssertUtil:
    """接口测试常用断言集合。"""

    @staticmethod
    def assert_status_code(response, expected):
        """校验 HTTP 状态码。"""
        actual = response.status_code
        assert actual == expected, (
            f"状态码断言失败：期望 {expected}，实际 {actual}\n"
            f"响应内容：{_safe_body(response)}"
        )

    @staticmethod
    def assert_in(container, member, msg=""):
        """校验 member 在 container 中（用于校验字段存在性）。

        调用约定：assert_in(容器, 被包含的元素)
        例：assert_in(["id", "title"], "id")  或  assert_in({"id": 1}, "id")
        """
        # 常见误用防御：参数传反会得到莫名其妙的 TypeError，这里直接给出可读提示
        if isinstance(member, (dict, list)) and not isinstance(container, (dict, list)):
            raise AssertionError(
                f"assert_in 参数疑似传反：container={container!r}，member={member!r}。"
                f"正确用法为 assert_in(容器, 元素)"
            )
        assert member in container, (
            f"断言失败：{msg or f'{member!r} 应存在于 {type(container).__name__} 中'}；"
            f"实际内容：{container}"
        )

    @staticmethod
    def assert_equal(actual, expected, field=""):
        """校验两个值相等，field 用于描述是哪个字段，便于定位。"""
        assert actual == expected, (
            f"字段断言失败 [{field}]：期望 {expected!r}，实际 {actual!r}"
        )

    @staticmethod
    def assert_true(condition, msg=""):
        """校验条件为真。"""
        assert condition, f"断言失败：{msg}"

    @staticmethod
    def assert_not_empty(data, field=""):
        """校验结果非空（列表/字符串/字典）。"""
        assert data, f"断言失败 [{field}]：结果为空，期望非空"

    # ---------- 组合断言：业务测试最常用的两个 ----------

    @staticmethod
    def assert_schema(response, required_fields, module=""):
        """校验响应 JSON 包含所有必需字段。

        这是「业务断言」的基础：只校验状态码 200 是不够的，
        必须确认返回的数据结构符合接口契约。

        支持响应体是 dict（取顶层字段）或 list（取第一条元素）。
        """
        body = response.json()
        target = body[0] if isinstance(body, list) and body else body
        if not isinstance(target, dict):
            raise AssertionError(
                f"字段校验 [{module}] 失败：响应不是对象，无法校验字段，实际类型 {type(target).__name__}"
            )
        missing = [f for f in required_fields if f not in target]
        assert not missing, (
            f"字段缺失 [{module}]：缺少 {missing}，实际返回字段 {list(target.keys())}"
        )
        logger.info("字段校验通过 [%s]：%s", module, required_fields)

    @staticmethod
    def assert_schema_subset(response, fields_should_exist, module=""):
        """校验响应包含「期望存在的字段」（用于残缺/边界请求的场景）。

        与 assert_schema 的区别：assert_schema 要求字段完整（契约校验），
        本方法只要求指定字段存在，不关心是否缺少其他字段。
        """
        body = response.json()
        target = body[0] if isinstance(body, list) and body else body
        missing = [f for f in fields_should_exist if f not in target]
        assert not missing, (
            f"字段缺失 [{module}]：期望存在 {missing}，实际返回字段 {list(target.keys())}"
        )

    @staticmethod
    def assert_field_equals(response, field, expected, module=""):
        """校验响应中某个具体字段的值（业务规则校验）。"""
        body = response.json()
        actual = body.get(field)
        assert actual == expected, (
            f"业务字段断言失败 [{module}.{field}]：期望 {expected!r}，实际 {actual!r}\n"
            f"完整响应：{_safe_body(response)}"
        )
        logger.info("业务字段校验通过 [%s.%s] = %r", module, field, actual)

    @staticmethod
    def assert_field_in(response, fields, module=""):
        """校验响应中存在指定字段（字段存在性断言的语义化写法）。"""
        AssertUtil.assert_schema_subset(response, fields, module)

    @staticmethod
    def assert_response_time(response, max_seconds=3.0):
        """校验接口响应耗时在可接受范围内（性能兜底断言）。"""
        elapsed = response.elapsed.total_seconds()
        assert elapsed < max_seconds, (
            f"响应时间超标：{elapsed:.2f}s 超过阈值 {max_seconds}s"
        )


def _safe_body(response):
    """安全地取响应体用于报错信息，避免非 JSON 响应导致二次报错。"""
    try:
        return json.dumps(response.json(), ensure_ascii=False)[:500]
    except Exception:
        return response.text[:500]
