"""统一日志：同时输出到控制台和 logs/ 目录下的文件。

日志文件按天切分，保留最近 7 天，方便排查测试失败原因。
"""
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name="api_test"):
    """获取一个配置好的 logger。

    重复调用同名 logger 不会重复加 handler（通过标记位判断）。
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # 控制台输出
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # 文件输出：按天切分，保留 7 天
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "test.log", when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger._configured = True
    return logger


logger = get_logger()
