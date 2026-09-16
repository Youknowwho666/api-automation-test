"""帖子模块（/posts）业务 API 封装。

只负责「拼接口、发请求」，不做断言 —— 断言属于测试用例层的职责。
"""
from common.base_api import BaseApi


class PostsApi(BaseApi):
    """JSONPlaceholder 帖子模块接口。"""

    MODULE = "/posts"

    def get_post_list(self, **params):
        """获取帖子列表，支持 _limit / _page 等查询参数。"""
        return self.get(self.MODULE, params=params or None)

    def get_post_detail(self, post_id):
        """获取单条帖子详情。"""
        return self.get(f"{self.MODULE}/{post_id}")

    def get_posts_by_user(self, user_id):
        """按用户筛选帖子（JSONPlaceholder 支持 ?userId=）。"""
        return self.get(self.MODULE, params={"userId": user_id})

    def create_post(self, post_data):
        """创建帖子。"""
        return self.post(self.MODULE, json=post_data)

    def update_post(self, post_id, update_data):
        """全量更新帖子。"""
        return self.put(f"{self.MODULE}/{post_id}", json=update_data)

    def patch_post(self, post_id, patch_data):
        """局部更新帖子。"""
        return self.patch(f"{self.MODULE}/{post_id}", json=patch_data)

    def delete_post(self, post_id):
        """删除帖子。"""
        return self.delete(f"{self.MODULE}/{post_id}")

    # 帖子下的关联资源
    def get_post_comments(self, post_id):
        """获取某条帖子的评论列表。"""
        return self.get(f"{self.MODULE}/{post_id}/comments")
