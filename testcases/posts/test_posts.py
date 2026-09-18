"""帖子模块测试用例。

分层原则：用例只做「调接口 + 断言」，请求细节在 posts_api.py，
断言逻辑在 assert_util.py，测试数据在 data/posts_data.yaml。
"""
import allure
import pytest

from common.assert_util import AssertUtil
from common.config import config
from common.data_util import case_ids, load_yaml
from testcases.posts.posts_api import PostsApi

DATA = load_yaml("data/posts_data.yaml")
POST_FIELDS = ["userId", "id", "title", "body"]


@allure.feature("帖子模块")
class TestPosts:
    """JSONPlaceholder /posts 接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个用例独立的 API 实例。"""
        self.api = PostsApi()

    # ---------------- 查询类 ----------------

    @allure.story("查询帖子")
    @allure.title("获取帖子列表：状态码 200 且返回 100 条数据")
    def test_get_post_list(self):
        response = self.api.get_post_list()

        AssertUtil.assert_status_code(response, 200)
        body = response.json()
        AssertUtil.assert_true(isinstance(body, list), "返回结果应为列表")
        AssertUtil.assert_equal(len(body), 100, "帖子总数")
        # 业务断言：列表第一条必须包含帖子完整字段
        AssertUtil.assert_schema(response, POST_FIELDS, module="posts[0]")
        AssertUtil.assert_response_time(response, config.max_response_time)

    @allure.story("查询帖子")
    @allure.title("分页查询：_limit=5 只返回 5 条")
    def test_get_post_list_with_limit(self):
        response = self.api.get_post_list(_limit=5)

        AssertUtil.assert_status_code(response, 200)
        AssertUtil.assert_equal(len(response.json()), 5, "分页返回条数")

    @allure.story("查询帖子")
    @allure.title("按用户筛选：userId=1 的帖子全部属于用户 1")
    def test_get_posts_by_user(self):
        response = self.api.get_posts_by_user(1)

        AssertUtil.assert_status_code(response, 200)
        body = response.json()
        AssertUtil.assert_not_empty(body, "用户1的帖子列表")
        # 业务断言：每一条的 userId 都必须是 1，验证筛选参数真正生效
        for post in body:
            AssertUtil.assert_field_equals(
                _DummyResponse(post), "userId", 1, module="posts_by_user"
            )

    @allure.story("查询帖子")
    @allure.title("获取帖子详情-数据驱动")
    @pytest.mark.parametrize("case", DATA["get_post_cases"], ids=case_ids(DATA["get_post_cases"]))
    def test_get_post_detail(self, case):
        with allure.step(f"请求帖子详情 id={case['post_id']}"):
            response = self.api.get_post_detail(case["post_id"])

        AssertUtil.assert_status_code(response, case["expected_status"])

        if case["expected_status"] == 200:
            AssertUtil.assert_schema(response, POST_FIELDS, module="post_detail")
            # 业务断言：返回的 id 必须和请求的一致
            AssertUtil.assert_field_equals(response, "id", case["post_id"], module="post_detail")
            AssertUtil.assert_field_equals(
                response, "userId", case["expected_userId"], module="post_detail"
            )

    @allure.story("查询帖子")
    @allure.title("获取帖子下的评论列表")
    def test_get_post_comments(self):
        response = self.api.get_post_comments(1)

        AssertUtil.assert_status_code(response, 200)
        body = response.json()
        AssertUtil.assert_not_empty(body, "帖子1的评论")
        # 业务断言：评论的 postId 必须都是 1
        for comment in body:
            AssertUtil.assert_equal(comment["postId"], 1, "comment.postId")

    # ---------------- 创建类 ----------------

    @allure.story("创建帖子")
    @allure.title("创建帖子-数据驱动")
    @pytest.mark.parametrize("case", DATA["create_post_cases"], ids=case_ids(DATA["create_post_cases"]))
    def test_create_post(self, case):
        with allure.step(f"提交创建请求：{case['name']}"):
            response = self.api.create_post(case["data"])

        AssertUtil.assert_status_code(response, case["expected_status"])

        # 字段校验分两档：
        # - 正常数据：按接口契约校验完整字段
        # - 残缺数据（如故意不传 title）：只校验服务端确实回写了字段，不要求补齐
        if case.get("schema_complete", True):
            AssertUtil.assert_schema(response, POST_FIELDS, module="create_post")
        AssertUtil.assert_schema_subset(
            response, case.get("expected_fields", POST_FIELDS), module="create_post"
        )

        # 业务断言：服务端应回写自增 id
        AssertUtil.assert_not_empty(response.json().get("id"), "新建帖子的id")

    # ---------------- 更新类 ----------------

    @allure.story("更新帖子")
    @allure.title("全量更新帖子-PUT-数据驱动")
    @pytest.mark.parametrize("case", DATA["update_post_cases"], ids=case_ids(DATA["update_post_cases"]))
    def test_update_post(self, case):
        response = self.api.update_post(case["post_id"], case["data"])

        AssertUtil.assert_status_code(response, case["expected_status"])
        # 业务断言：更新后返回的 title 必须是新值，这是「真正改成功了」的证据
        AssertUtil.assert_field_equals(response, "title", case["data"]["title"], module="update_post")
        AssertUtil.assert_field_equals(response, "body", case["data"]["body"], module="update_post")

    @allure.story("更新帖子")
    @allure.title("局部更新帖子-PATCH-数据驱动")
    @pytest.mark.parametrize("case", DATA["patch_post_cases"], ids=case_ids(DATA["patch_post_cases"]))
    def test_patch_post(self, case):
        response = self.api.patch_post(case["post_id"], case["data"])

        AssertUtil.assert_status_code(response, case["expected_status"])
        # PATCH 只改传入的字段，校验该字段已更新
        for field, expected in case["data"].items():
            AssertUtil.assert_field_equals(response, field, expected, module="patch_post")

    # ---------------- 删除类 ----------------

    @allure.story("删除帖子")
    @allure.title("删除帖子返回 200 且响应体为空对象")
    def test_delete_post(self):
        response = self.api.delete_post(1)

        AssertUtil.assert_status_code(response, 200)
        # 业务断言：JSONPlaceholder 删除成功返回空对象 {}
        AssertUtil.assert_equal(response.json(), {}, "删除响应体")

    @allure.story("删除帖子")
    @allure.title("删除不存在的帖子：接口幂等仍返回 200")
    def test_delete_post_not_found(self):
        response = self.api.delete_post(999)

        AssertUtil.assert_status_code(response, 200)

    # ---------------- 异常与边界 ----------------

    @allure.story("异常场景")
    @allure.title("异常-更新不存在的帖子：返回 5xx 服务端错误")
    def test_update_post_not_found(self):
        """更新一个不存在的资源，服务端未做参数校验，直接抛 500。

        这里不断言精确的 500，而是断言「属于 5xx」：
        服务端错误码可能因版本调整，锁定具体数字会让用例无谓地变脆。
        """
        response = self.api.update_post(999, {"title": "x", "body": "y", "userId": 1})

        AssertUtil.assert_true(
            500 <= response.status_code < 600,
            f"更新不存在的帖子应返回 5xx 服务端错误，实际 {response.status_code}",
        )

    @allure.story("异常场景")
    @allure.title("异常-对帖子集合使用未实现的 DELETE 返回 404")
    def test_invalid_method_on_collection(self):
        # 对集合用 DELETE 是 JSONPlaceholder 未实现的语义，用于验证错误码分支
        response = self.api.delete("/posts")

        AssertUtil.assert_status_code(response, 404)

    @allure.story("性能兜底")
    @allure.title("响应时间：帖子列表接口在阈值内返回")
    def test_response_time_within_threshold(self):
        response = self.api.get_post_list(_limit=10)

        AssertUtil.assert_status_code(response, 200)
        AssertUtil.assert_response_time(response, config.max_response_time)


class _DummyResponse:
    """把 dict 包装成 response.json() 的接口，方便复用 AssertUtil 的字段断言。"""

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data
