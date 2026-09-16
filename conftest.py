"""pytest 全局配置：统一日志、失败时附加信息到 Allure 报告。

放在项目根目录，pytest 会自动加载，所有子目录的用例都能用到。
"""
import pytest

from common.logger import logger


def pytest_configure(config):
    """测试会话启动时打印分隔线，方便在日志里定位一轮测试的边界。"""
    logger.info("=" * 60)
    logger.info("自动化测试开始")
    logger.info("=" * 60)


@pytest.fixture(scope="session")
def api_config():
    """全局配置 fixture，需要读取配置的用例可以注入使用。"""
    from common.config import config
    return config


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时记录错误日志（Allure 可用时同时附加到报告）。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        logger.error("用例失败: %s", item.nodeid)
        try:
            import allure
            allure.attach(
                f"用例: {item.nodeid}\n失败阶段: {report.when}",
                name="失败信息",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            # Allure 未安装时静默跳过，不影响测试执行
            pass
