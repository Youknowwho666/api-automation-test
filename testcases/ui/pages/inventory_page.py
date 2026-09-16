"""商品列表页对象（SauceDemo）。"""
from testcases.ui.pages.base_page import BasePage


class InventoryPage(BasePage):
    """登录后的商品列表页 /inventory.html"""

    url_path = "/inventory.html"

    def __init__(self, page):
        super().__init__(page)
        self.title = page.locator("[data-test='title']")
        self.items = page.locator("[data-test='inventory-item']")
        self.item_names = page.locator("[data-test='inventory-item-name']")
        self.item_prices = page.locator("[data-test='inventory-item-price']")
        self.sort_dropdown = page.locator("[data-test='product-sort-container']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")
        self.cart_link = page.locator("[data-test='shopping-cart-link']")
        self.menu_button = page.get_by_role("button", name="Open Menu")

        # 「加入购物车」按钮：点击后会变成「移除」按钮，所以两个定位器都要有
        self.add_backpack = page.locator("[data-test='add-to-cart-sauce-labs-backpack']")
        self.add_bike_light = page.locator("[data-test='add-to-cart-sauce-labs-bike-light']")
        # 所有「移除」按钮，用于每个用例前把购物车清空，保证用例间互不干扰
        self.remove_buttons = page.locator("button[data-test^='remove-']")

    def add_item_to_cart(self, item_locator):
        """把商品加入购物车。

        注意：点击后按钮本身会被替换为「移除」按钮，
        因此调用方不能在同一个用例里对同一商品重复点击。
        """
        self.click(item_locator, desc="加入购物车")
        return self

    def remove_item_from_cart(self, remove_locator):
        """把商品从购物车移除。"""
        self.click(remove_locator, desc="移除商品")
        return self

    def clear_cart(self):
        """清空购物车，保证用例之间相互独立。

        因为整个会话共用一个浏览器上下文，购物车状态会被带入下一条用例，
        所以每条用例开始时统一调用本方法复位。
        """
        while self.remove_buttons.count() > 0:
            self.remove_buttons.first.click()
        return self

    def get_cart_count(self):
        """获取购物车角标数量，没有角标时返回 0。"""
        if self.is_visible(self.cart_badge):
            return int(self.get_text(self.cart_badge, desc="购物车角标"))
        return 0

    def get_item_names(self):
        """获取所有商品名称。"""
        return self.item_names.all_inner_texts()

    def get_item_prices(self):
        """获取所有商品价格（字符串形式，如 $29.99）。"""
        return self.item_prices.all_inner_texts()

    def sort_by(self, option):
        """按指定方式排序。option 取值：az / za / lohi / hilo。"""
        self.sort_dropdown.select_option(option)
        return self

    def go_to_cart(self):
        """进入购物车页面。"""
        self.click(self.cart_link, desc="购物车图标")
        return self
