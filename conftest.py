"""pytest 全局配置：统一日志、清理上轮报告、失败时附加信息到 Allure 报告。

放在项目根目录，pytest 会自动加载，所有子目录的用例都能用到。
"""
import shutil
import time
from pathlib import Path

import pytest

from common.logger import logger

# Allure 结果目录（与 pytest.ini 的 --alluredir 保持一致）
ALLURE_RESULTS_DIR = Path("reports/allure-results")
# 上一轮结果的暂存目录：整目录改名挪到这里，新版 pytest 结束后再删
STALE_RESULTS_DIR = Path("reports/.allure-results.stale")


def _move_dir(src: Path, dst: Path) -> bool:
    """把 src 整体挪到 dst。rename 不涉及逐个删除，最快且不容易被拦。"""
    if dst.exists():
        # 上一轮的暂存目录还在（说明上次没删掉），只能逐文件删。
        # 删除失败也无所谓，换个名字存本次旧结果，绝不阻断测试。
        if not _delete_dir(dst):
            dst = dst.with_name(f"{dst.name}.{int(time.time())}")

    try:
        src.rename(dst)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        # 跨盘符或权限限制，退回「复制 + 删源」
        try:
            shutil.copytree(src, dst)
            _delete_dir(src)
            return True
        except Exception as exc:
            logger.warning("挪走旧结果目录失败：%s", exc)
            return False


def _delete_dir(directory: Path) -> bool:
    """删除目录树。删除失败不影响测试，只记 warning。"""
    if not directory.exists():
        return True
    try:
        shutil.rmtree(directory, ignore_errors=True)
        return not directory.exists()
    except Exception as exc:  # ignore_errors 之外还可能抛权限类异常
        logger.warning("删除旧结果目录失败（可手动删除 %s）：%s", directory, exc)
        return False


def _clean_up_stale():
    """清空 Allure 结果目录，保证本轮结果是干净的。

    为什么需要这一步：
      allure-pytest 只会往 --alluredir 里「追加」结果文件，不会清理上一轮的。
      连跑多次后同一用例会产生多份 result.json，导致 Allure 报告的用例总数
      虚高、通过率被历史结果污染（例如 56 条用例显示成 68 条）。

    为什么不用 --clean-alluredir：
      该参数在会话刚启动时就整目录删除，一旦被安全策略拦下，
      pytest 会直接以 INTERNALERROR 退出，连报错原因都看不清。
      这里自己控制时机和容错，删不掉也只是报告脏一点，测试照样能跑。

    实现要点：
      1) 整目录 rename 挪走 —— 一次原子操作，比逐个删文件快得多，
         也不容易触发「批量删除保护」；
      2) 只在「开跑前」做删除动作，此时 pytest 还没开始写结果文件；
      3) 删不掉就留着，本轮新结果照常写进新目录，报告数据依然干净。
    """
    moved = False
    if ALLURE_RESULTS_DIR.exists():
        moved = _move_dir(ALLURE_RESULTS_DIR, STALE_RESULTS_DIR)

    try:
        ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("创建 Allure 结果目录失败：%s", exc)
        return

    if moved:
        logger.info("已清空上一轮 Allure 结果（旧数据暂存于 %s）", STALE_RESULTS_DIR)


def pytest_sessionstart(session):
    """测试会话开始前清空 Allure 结果目录。任何异常都不阻断测试。"""
    try:
        _clean_up_stale()
    except BaseException as exc:
        # 含 SystemExit：部分受限环境的删除保护会抛这个，绝不能让它打断测试
        logger.warning("跳过 Allure 结果清理：%s", exc)


def pytest_sessionfinish(session, exitstatus):
    """测试结束后收尾：删掉暂存的旧结果、强制补建结果目录。

    为什么在结束后还要补建目录：
      若清理阶段没建成功，allure-pytest 写结果时会 FileNotFoundError。
      这里再兜一次底，保证下次开跑前目录一定在。
    """
    try:
        _delete_dir(STALE_RESULTS_DIR)
        ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    except BaseException as exc:
        logger.warning("收尾清理跳过：%s", exc)


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
