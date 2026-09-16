"""UI 自动化 fixture：管理 browser / context / page 生命周期。

关键设计：
1. session 级 browser：整个测试会话只启动一次浏览器，避免每条用例都开浏览器；
2. storageState 复用登录态：登录一次存到文件，后续用例直接加载，跳过登录步骤；
3. 失败自动截图：用例挂了自动把截图挂到 Allure 报告。
"""
import allure
import pytest
from playwright.sync_api import sync_playwright

from common.config import config
from common.logger import logger
from testcases.ui.pages.login_page import LoginPage

AUTH_STATE_FILE = "reports/auth_state.json"

# SauceDemo 的测试账号（官方公开的练习账号）
STANDARD_USER = "standard_user"
LOCKED_USER = "locked_out_user"
VALID_PASSWORD = "secret_sauce"


@pytest.fixture(scope="session")
def browser():
    """整个会话共用一个浏览器实例。"""
    with sync_playwright() as p:
        logger.info("启动浏览器 headless=%s", config.ui_headless)
        browser = p.chromium.launch(headless=config.ui_headless)
        yield browser
        browser.close()
        logger.info("浏览器已关闭")


@pytest.fixture(scope="session")
def context(browser):
    """会话级上下文：视口、超时等全局设置。"""
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        base_url=config.ui_base_url,
    )
    context.set_default_timeout(config.ui_timeout)
    yield context
    context.close()


@pytest.fixture()
def page(context):
    """每个用例独立的页面，保证用例之间互不干扰。"""
    page = context.new_page()
    page.set_default_timeout(config.ui_timeout)
    yield page
    page.close()


@pytest.fixture(scope="session")
def logged_in_context(browser):
    """已登录的上下文：登录一次，保存登录态供后续用例复用。

    这就是 storageState 的价值 —— 不用每条 UI 用例都跑一遍登录流程。
    """
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        base_url=config.ui_base_url,
    )
    context.set_default_timeout(config.ui_timeout)
    page = context.new_page()
    LoginPage(page).open().login(STANDARD_USER, VALID_PASSWORD)
    page.wait_for_url("**/inventory.html")
    # 保存登录态到文件，下次可直接复用
    context.storage_state(path=AUTH_STATE_FILE)
    page.close()
    yield context
    context.close()


@pytest.fixture()
def logged_in_page(logged_in_context):
    """带登录态的页面，UI 用例直接注入即可，无需再登录。"""
    page = logged_in_context.new_page()
    page.set_default_timeout(config.ui_timeout)
    yield page
    page.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """UI 用例失败时自动截图并附加到 Allure 报告。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page is not None:
            try:
                allure.attach(
                    page.screenshot(full_page=True),
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
            except Exception as e:
                logger.warning("失败截图附加失败: %s", e)
