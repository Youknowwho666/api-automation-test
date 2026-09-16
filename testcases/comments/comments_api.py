"""评论模块（/comments）业务 API 封装。"""
from common.base_api import BaseApi


class CommentsApi(BaseApi):
    """JSONPlaceholder 评论模块接口。"""

    MODULE = "/comments"

    def get_comment_list(self, **params):
        """获取评论列表。"""
        return self.get(self.MODULE, params=params or None)

    def get_comment_detail(self, comment_id):
        """获取单条评论详情。"""
        return self.get(f"{self.MODULE}/{comment_id}")

    def get_comments_by_post(self, post_id):
        """按帖子 id 筛选评论。"""
        return self.get(self.MODULE, params={"postId": post_id})

    def get_comments_by_email(self, email):
        """按邮箱筛选评论（用于校验查询参数是否真正生效）。"""
        return self.get(self.MODULE, params={"email": email})
