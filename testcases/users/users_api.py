"""用户模块（/users）业务 API 封装。"""
from common.base_api import BaseApi


class UsersApi(BaseApi):
    """JSONPlaceholder 用户模块接口。"""

    MODULE = "/users"

    def get_user_list(self):
        """获取用户列表。"""
        return self.get(self.MODULE)

    def get_user_detail(self, user_id):
        """获取单个用户详情。"""
        return self.get(f"{self.MODULE}/{user_id}")

    def get_user_posts(self, user_id):
        """获取某个用户发布的帖子。"""
        return self.get(f"{self.MODULE}/{user_id}/posts")

    def get_user_albums(self, user_id):
        """获取某个用户的相册列表。"""
        return self.get(f"{self.MODULE}/{user_id}/albums")

    def get_user_todos(self, user_id):
        """获取某个用户的待办事项。"""
        return self.get(f"{self.MODULE}/{user_id}/todos")

    def create_user(self, user_data):
        """创建用户。"""
        return self.post(self.MODULE, json=user_data)
