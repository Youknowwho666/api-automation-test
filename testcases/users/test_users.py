"""用户模块测试用例。"""
import allure
import pytest

from common.assert_util import AssertUtil
from common.data_util import case_ids, load_yaml
from testcases.users.users_api import UsersApi

DATA = load_yaml("data/users_data.yaml")
USER_FIELDS = ["id", "name", "username", "email", "address", "phone", "website", "company"]


@allure.feature("用户模块")
class TestUsers:
    """JSONPlaceholder /users 接口测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.api = UsersApi()

    @allure.story("查询用户")
    @allure.title("获取用户列表：返回 10 个用户且字段完整")
    def test_get_user_list(self):
        response = self.api.get_user_list()

        AssertUtil.assert_status_code(response, 200)
        body = response.json()
        AssertUtil.assert_equal(len(body), 10, "用户总数")
        # assert_schema 会自动取列表首元素校验字段，无需手动包装
        AssertUtil.assert_schema(response, USER_FIELDS, module="users[0]")

    @allure.story("查询用户")
    @allure.title("获取用户详情-数据驱动")
    @pytest.mark.parametrize("case", DATA["get_user_cases"], ids=case_ids(DATA["get_user_cases"]))
    def test_get_user_detail(self, case):
        response = self.api.get_user_detail(case["user_id"])

        AssertUtil.assert_status_code(response, case["expected_status"])

        if case["expected_status"] == 200:
            AssertUtil.assert_schema(response, USER_FIELDS, module="user_detail")
            # 业务断言：username 必须匹配（验证返回的是请求的那个人）
            AssertUtil.assert_field_equals(
                response, "username", case["expected_username"], module="user_detail"
            )

    @allure.story("用户关联资源")
    @allure.title("用户关联资源查询-数据驱动")
    @pytest.mark.parametrize("case", DATA["user_relations"], ids=case_ids(DATA["user_relations"]))
    def test_user_relations(self, case):
        api = self.api
        resource = case["resource"]
        method = {
            "posts": api.get_user_posts,
            "albums": api.get_user_albums,
            "todos": api.get_user_todos,
        }[resource]

        response = method(case["user_id"])

        AssertUtil.assert_status_code(response, case["expected_status"])
        body = response.json()
        AssertUtil.assert_not_empty(body, f"用户{case['user_id']}的{resource}")
        # 业务断言：关联资源的 userId 必须与请求一致
        for item in body:
            AssertUtil.assert_equal(item["userId"], case["user_id"], f"{resource}.userId")

    @allure.story("创建用户")
    @allure.title("创建用户成功并回写 id")
    @pytest.mark.parametrize("case", DATA["create_user_cases"], ids=case_ids(DATA["create_user_cases"]))
    def test_create_user(self, case):
        response = self.api.create_user(case["data"])

        AssertUtil.assert_status_code(response, case["expected_status"])
        # 业务断言：创建后返回体应包含提交的 name 与服务端生成的 id
        AssertUtil.assert_field_equals(response, "name", case["data"]["name"], module="create_user")
        AssertUtil.assert_field_equals(
            response, "username", case["data"]["username"], module="create_user"
        )
        AssertUtil.assert_not_empty(response.json().get("id"), "新建用户的id")
