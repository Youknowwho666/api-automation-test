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
        self.add_backpack = page.locator("[data-test='add-to-cart-sauce-labs-backpack']")
        self.add_bike_light = page.locator("[data-test='add-to-cart-sauce-labs-bike-light']")
        self.menu_button = page.get_by_role("button", name="Open Menu")

    def add_item_to_cart(self, item_locator):
        """把商品加入购物车。"""
        self.click(item_locator, desc="加入购物车")
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
