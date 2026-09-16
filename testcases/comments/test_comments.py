"""评论模块测试用例。"""
import allure
import pytest

from common.assert_util import AssertUtil
from common.data_util import case_ids, load_yaml
from testcases.comments.comments_api import CommentsApi

DATA = load_yaml("data/comments_data.yaml")
COMMENT_FIELDS = ["postId", "id", "name", "email", "body"]


@allure.feature("评论模块")
class TestComments:
    """JSONPlaceholder /comments 接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = CommentsApi()

    @allure.story("查询评论")
    @allure.title("获取评论列表：返回 500 条且字段完整")
    def test_get_comment_list(self):
        response = self.api.get_comment_list()

        AssertUtil.assert_status_code(response, 200)
        body = response.json()
        AssertUtil.assert_equal(len(body), 500, "评论总数")
        # 校验首条评论的字段完整性（body 是列表，交由 assert_schema 内部取首元素）
        AssertUtil.assert_schema(response, COMMENT_FIELDS, module="comments[0]")

    @allure.story("查询评论")
    @allure.title("获取评论详情-数据驱动")
    @pytest.mark.parametrize("case", DATA["get_comment_cases"], ids=case_ids(DATA["get_comment_cases"]))
    def test_get_comment_detail(self, case):
        response = self.api.get_comment_detail(case["comment_id"])

        AssertUtil.assert_status_code(response, case["expected_status"])

        if case["expected_status"] == 200:
            # 字段存在性校验：assert_in(容器, 元素) —— 元素在前是常见误用，注意顺序
            for field in COMMENT_FIELDS:
                AssertUtil.assert_in(response.json(), field, f"评论详情应含 {field}")
            # 业务断言：返回的 id 与请求一致，且 postId 正确归属
            AssertUtil.assert_field_equals(
                response, "id", case["comment_id"], module="comment_detail"
            )
            AssertUtil.assert_field_equals(
                response, "postId", case["expected_postId"], module="comment_detail"
            )
            # 业务规则：评论邮箱格式必须合法
            AssertUtil.assert_true(
                "@" in response.json()["email"],
                f"评论邮箱格式非法：{response.json()['email']}",
            )

    @allure.story("查询评论")
    @allure.title("按条件筛选评论-数据驱动")
    @pytest.mark.parametrize("case", DATA["filter_cases"], ids=case_ids(DATA["filter_cases"]))
    def test_filter_comments(self, case):
        response = self.api.get_comment_list(**{case["param"]: case["value"]})

        AssertUtil.assert_status_code(response, case["expected_status"])
        body = response.json()
        AssertUtil.assert_not_empty(body, f"筛选条件 {case['param']}={case['value']}")
        # 业务断言：筛选参数必须真正生效，每条结果都符合条件
        for comment in body:
            AssertUtil.assert_equal(
                comment[case["param"]], case["value"], f"筛选字段 {case['param']}"
            )
