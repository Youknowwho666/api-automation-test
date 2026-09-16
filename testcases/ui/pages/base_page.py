"""BasePage：所有页面对象的父类。

封装 Playwright 的通用操作（点击、输入、取值、等待），
子类只关心「这个页面有哪些元素」，不用重复写等待和异常处理。

这是 POM 模式的核心价值：页面元素变了，只改页面对象，用例不动。
"""
import allure
from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from common.config import config
from common.logger import logger


class BasePage:
    """页面基类，提供通用操作方法。"""

    #: 子类覆盖，例如 "/inventory.html"
    url_path = "/"

    def __init__(self, page: Page):
        self.page = page
        self.timeout = config.ui_timeout

    # ---------- 导航 ----------

    def open(self, url_path=None):
        """打开页面。Playwright 内置自动等待，不需要手动 sleep。"""
        path = url_path or self.url_path
        full_url = config.ui_base_url.rstrip("/") + path
        logger.info("打开页面: %s", full_url)
        self.page.goto(full_url, wait_until="domcontentloaded")
        return self

    def title(self):
        """获取页面标题。"""
        return self.page.title()

    def current_url(self):
        """获取当前 URL。"""
        return self.page.url

    # ---------- 元素操作 ----------

    def click(self, locator, desc=""):
        """点击元素。locator 传 Playwright 的 Locator 对象。"""
        logger.info("点击: %s", desc or locator)
        locator.click(timeout=self.timeout)
        return self

    def fill(self, locator, text, desc=""):
        """输入文本（会先清空原内容）。"""
        logger.info("输入 [%s]: %s", desc or locator, text)
        locator.fill(text, timeout=self.timeout)
        return self

    def get_text(self, locator, desc=""):
        """获取元素文本。"""
        text = locator.inner_text(timeout=self.timeout)
        logger.info("读取文本 [%s]: %s", desc or locator, text)
        return text

    def is_visible(self, locator):
        """判断元素是否可见（用于断言）。"""
        try:
            return locator.is_visible(timeout=self.timeout)
        except PWTimeoutError:
            return False

    def count(self, locator):
        """统计元素数量。"""
        return locator.count()

    # ---------- 断言辅助 ----------

    def wait_for_url(self, pattern):
        """等待 URL 匹配指定模式。"""
        self.page.wait_for_url(pattern, timeout=self.timeout)
        return self

    @allure.step("截图并附加到报告：{name}")
    def screenshot(self, name="页面截图"):
        """截图并挂到 Allure 报告，失败排查时非常有用。"""
        try:
            data = self.page.screenshot(full_page=True)
            allure.attach(data, name=name, attachment_type=allure.attachment_type.PNG)
            logger.info("已截图: %s", name)
        except Exception as e:
            logger.warning("截图失败: %s", e)
        return self
