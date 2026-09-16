"""登录页对象（SauceDemo）。

元素定位优先用 get_by_* 语义化方法（get_by_placeholder / get_by_role），
比 CSS 路径稳定得多 —— 这是 Playwright 官方推荐的做法。
"""
from testcases.ui.pages.base_page import BasePage


class LoginPage(BasePage):
    """SauceDemo 登录页 https://www.saucedemo.com"""

    url_path = "/"

    def __init__(self, page):
        super().__init__(page)
        # 元素定位集中在这里，页面改版只需改这一处
        self.username_input = page.get_by_placeholder("Username")
        self.password_input = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error_message = page.locator("[data-test='error']")

    def login(self, username, password):
        """执行登录流程。"""
        self.fill(self.username_input, username, desc="用户名")
        self.fill(self.password_input, password, desc="密码")
        self.click(self.login_button, desc="登录按钮")
        return self

    def get_error_text(self):
        """获取登录错误提示文本。"""
        return self.get_text(self.error_message, desc="错误提示")

    def has_error(self):
        """是否出现错误提示。"""
        return self.is_visible(self.error_message)
