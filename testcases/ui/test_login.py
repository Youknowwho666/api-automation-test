"""登录功能 UI 测试用例（SauceDemo）。

覆盖：正常登录、锁定账号、错误密码、空账号、空密码、元素可见性。
"""
import allure
import pytest

from testcases.ui.conftest import LOCKED_USER, STANDARD_USER, VALID_PASSWORD
from testcases.ui.pages.login_page import LoginPage

pytestmark = pytest.mark.ui


@allure.feature("UI 自动化 - 登录模块")
class TestLogin:
    """登录页测试。"""

    @allure.story("正常登录")
    @allure.title("标准用户登录成功并跳转到商品页")
    @pytest.mark.smoke
    def test_login_success(self, page):
        login_page = LoginPage(page)
        with allure.step("打开登录页"):
            login_page.open()
            assert "Swag Labs" in login_page.title(), "页面标题不正确"

        with allure.step("输入正确的账号密码并登录"):
            login_page.login(STANDARD_USER, VALID_PASSWORD)

        with allure.step("校验跳转到商品列表页"):
            assert "/inventory.html" in login_page.current_url(), (
                f"未跳转到商品页，当前 URL: {login_page.current_url()}"
            )

    @allure.story("异常登录")
    @allure.title("锁定账号登录失败并提示正确错误信息")
    def test_login_locked_user(self, page):
        login_page = LoginPage(page)
        login_page.open().login(LOCKED_USER, VALID_PASSWORD)

        assert login_page.has_error(), "锁定用户应显示错误提示"
        error = login_page.get_error_text()
        assert "locked out" in error.lower(), f"错误提示不符合预期: {error}"
        login_page.screenshot("锁定用户错误提示")

    @allure.story("异常登录")
    @allure.title("错误密码登录失败")
    def test_login_wrong_password(self, page):
        login_page = LoginPage(page)
        login_page.open().login(STANDARD_USER, "wrong_password")

        assert login_page.has_error(), "错误密码应显示错误提示"
        error = login_page.get_error_text()
        assert "username and password do not match" in error.lower(), (
            f"错误提示不符合预期: {error}"
        )

    @allure.story("异常登录")
    @allure.title("用户名为空时提示必填")
    def test_login_empty_username(self, page):
        login_page = LoginPage(page)
        login_page.open().login("", VALID_PASSWORD)

        assert login_page.has_error(), "空用户名应显示错误提示"
        assert "username is required" in login_page.get_error_text().lower()

    @allure.story("异常登录")
    @allure.title("密码为空时提示必填")
    def test_login_empty_password(self, page):
        login_page = LoginPage(page)
        login_page.open().login(STANDARD_USER, "")

        assert login_page.has_error(), "空密码应显示错误提示"
        assert "password is required" in login_page.get_error_text().lower()

    @allure.story("页面元素")
    @allure.title("登录页三个核心元素均正常展示")
    def test_login_page_elements(self, page):
        login_page = LoginPage(page)
        login_page.open()

        with allure.step("校验用户名、密码输入框与登录按钮可见"):
            assert login_page.is_visible(login_page.username_input), "用户名输入框不可见"
            assert login_page.is_visible(login_page.password_input), "密码输入框不可见"
            assert login_page.is_visible(login_page.login_button), "登录按钮不可见"

        login_page.screenshot("登录页元素")
