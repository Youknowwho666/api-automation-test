"""商品列表与购物车 UI 测试用例（SauceDemo）。

这些用例使用 logged_in_page fixture —— 登录态由 storageState 复用，
不再重复执行登录流程，这正是 POM + storageState 组合的价值。
"""
import allure
import pytest

from testcases.ui.pages.inventory_page import InventoryPage

pytestmark = pytest.mark.ui


def _go_inventory(page) -> InventoryPage:
    """打开商品页并把购物车复位，保证用例从干净状态开始。"""
    inv = InventoryPage(page)
    inv.open()
    inv.clear_cart()
    return inv


@allure.feature("UI 自动化 - 商品与购物车")
class TestInventory:
    """商品列表页测试。"""

    @allure.story("商品列表")
    @allure.title("登录后商品列表展示 6 件商品且标题正确")
    @pytest.mark.smoke
    def test_inventory_loaded(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        with allure.step("校验页面标题"):
            assert inv.get_text(inv.title) == "Products", "页面标题应为 Products"

        with allure.step("校验商品数量"):
            names = inv.get_item_names()
            assert len(names) == 6, f"商品数量应为 6，实际 {len(names)}"

    @allure.story("商品列表")
    @allure.title("按价格从低到高排序生效")
    def test_sort_by_price_low_to_high(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        with allure.step("选择价格升序排序"):
            inv.sort_by("lohi")

        with allure.step("校验价格确实是升序"):
            prices = [float(p.replace("$", "")) for p in inv.get_item_prices()]
            assert prices == sorted(prices), f"价格未升序排列: {prices}"

    @allure.story("商品列表")
    @allure.title("按名称 Z-A 排序生效")
    def test_sort_by_name_desc(self, logged_in_page):
        inv = _go_inventory(logged_in_page)
        inv.sort_by("za")

        names = inv.get_item_names()
        assert names == sorted(names, reverse=True), f"名称未降序排列: {names}"

    @allure.story("购物车")
    @allure.title("加入单件商品后购物车角标显示 1")
    @pytest.mark.smoke
    def test_add_single_item_to_cart(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        with allure.step("把背包加入购物车"):
            inv.add_item_to_cart(inv.add_backpack)

        with allure.step("校验购物车角标为 1"):
            assert inv.get_cart_count() == 1, "购物车角标应为 1"

    @allure.story("购物车")
    @allure.title("加入两件商品后购物车角标显示 2")
    def test_add_two_items_to_cart(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        with allure.step("加入背包与车灯"):
            inv.add_item_to_cart(inv.add_backpack)
            inv.add_item_to_cart(inv.add_bike_light)

        with allure.step("校验购物车角标为 2"):
            count = inv.get_cart_count()
            assert count == 2, f"购物车角标应为 2，实际 {count}"

    @allure.story("购物车")
    @allure.title("点击购物车图标可进入购物车页面")
    def test_navigate_to_cart(self, logged_in_page):
        inv = _go_inventory(logged_in_page)
        inv.add_item_to_cart(inv.add_backpack)
        inv.go_to_cart()

        assert "/cart.html" in inv.current_url(), f"未进入购物车页: {inv.current_url()}"

    @allure.story("购物车")
    @allure.title("移除商品后购物车角标消失")
    def test_remove_item_from_cart(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        with allure.step("先加入背包"):
            inv.add_item_to_cart(inv.add_backpack)
            assert inv.get_cart_count() == 1, "前置条件失败：商品未成功加入"

        with allure.step("再移除背包"):
            inv.remove_item_from_cart(
                logged_in_page.locator("[data-test='remove-sauce-labs-backpack']")
            )

        with allure.step("校验购物车已清空"):
            assert inv.get_cart_count() == 0, "移除商品后购物车角标应消失"

    @allure.story("页面元素")
    @allure.title("商品列表页核心元素正常展示")
    def test_inventory_elements(self, logged_in_page):
        inv = _go_inventory(logged_in_page)

        assert inv.is_visible(inv.title), "页面标题不可见"
        assert inv.is_visible(inv.sort_dropdown), "排序下拉框不可见"
        assert inv.is_visible(inv.cart_link), "购物车图标不可见"

        inv.screenshot("商品列表页")
