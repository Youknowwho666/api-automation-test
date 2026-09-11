import pytest
import yaml
from testcases.posts.posts_api import PostsApi

# 加载测试数据
with open("data/posts_data.yaml", "r", encoding="utf-8") as f:
    test_data = yaml.safe_load(f)

@pytest.fixture(scope="module")
def posts_api():
    """fixture：初始化 PostsApi 实例，整个模块复用"""
    return PostsApi()

class TestPosts:
    def test_get_post_list(self, posts_api):
        """测试获取帖子列表"""
        response = posts_api.get_post_list()
        assert response.status_code == 200
        assert len(response.json()) > 0

    @pytest.mark.parametrize("case", test_data["get_post_cases"], ids=lambda x: x["name"])
    def test_get_post_detail(self, posts_api, case):
        """测试获取帖子详情（数据驱动）"""
        response = posts_api.get_post_detail(case["post_id"])
        assert response.status_code == case["expected_status"]
        assert response.json()["userId"] == case["expected_userId"]

    @pytest.mark.parametrize("case", test_data["create_post_cases"], ids=lambda x: x["name"])
    def test_create_post(self, posts_api, case):
        """测试创建帖子（数据驱动）"""
        response = posts_api.create_post(case["data"])
        assert response.status_code == case["expected_status"]
        assert "id" in response.json()

    def test_update_post(self, posts_api):
        """测试更新帖子"""
        update_data = {"title": "updated title", "body": "updated body", "userId": 1}
        response = posts_api.update_post(1, update_data)
        assert response.status_code == 200
        assert response.json()["title"] == "updated title"

    def test_delete_post(self, posts_api):
        """测试删除帖子"""
        response = posts_api.delete_post(1)
        assert response.status_code == 200

    def test_get_post_not_found(self,posts_api):
        """异常入参:获取不存在的帖子(ID=999)"""
        response = posts_api.get_post_detail(999)
        assert response.status_code == 404

    def test_get_post_invalid_id_string(self,posts_api):
        """异常入参：获取帖子-非法字符ID("abc")"""
        response = posts_api.get_post_detail("abc")
        assert response.status_code == 404

    def test_get_post_negative_id(self, posts_api):
        """异常入参：获取帖子-负数ID"""
        response = posts_api.get_post_detail(-1)
        assert response.status_code == 404

    def test_create_post_empty_title(self, posts_api):
        """边界值：创建帖子-空标题"""
        response = posts_api.create_post({"title": "", "body": "test body", "userId": 1})
        assert response.status_code == 201
        assert response.json()["title"] == ""

    def test_create_post_empty_body(self, posts_api):
        """边界值：创建帖子-空body"""
        response = posts_api.create_post({"title": "test title", "body": "", "userId": 1})
        assert response.status_code == 201
        assert response.json()["body"] == ""

    def test_create_post_missing_title(self, posts_api):
        """异常入参：创建帖子-缺少title字段"""
        response = posts_api.create_post({"body": "test body", "userId": 1})
        assert response.status_code == 201

    def test_update_post_not_found(self, posts_api):
        """异常入参：更新不存在的帖子（ID=999）"""
        update_data = {"title": "new title", "body": "new body", "userId": 1}
        response = posts_api.update_post(999, update_data)
        assert response.status_code == 500

    def test_delete_post_not_found(self, posts_api):
        """异常入参：删除不存在的帖子（ID=999）"""
        response = posts_api.delete_post(999)
        assert response.status_code == 200


    