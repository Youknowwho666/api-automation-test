"""全局配置：优先读环境变量，其次读 config.yaml，最后用默认值。

环境变量可覆盖任意配置项，方便在 CI 中切换测试环境，无需改代码。
"""
import os
import yaml
from pathlib import Path

# 项目根目录（本文件位于 common/ 下，向上一级即项目根）
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config" / "config.yaml"


class Config:
    """配置读取器，支持 环境变量 > config.yaml > 默认值 三级优先级。"""

    _defaults = {
        "base_url": "https://jsonplaceholder.typicode.com",
        "timeout": 30,
        "verify_ssl": True,
        "retry_times": 2,
        "retry_delay": 1,
        "max_response_time": 15.0,
        # UI 自动化配置
        "ui_base_url": "https://www.saucedemo.com",
        "ui_headless": True,
        "ui_timeout": 15000,
    }

    def __init__(self):
        self._file_config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._file_config = yaml.safe_load(f) or {}

    def get(self, key, default=None):
        """读取配置项。优先级：环境变量 > 配置文件 > 内置默认值。"""
        env_key = f"TEST_{key.upper()}"
        if env_key in os.environ:
            return self._cast(os.environ[env_key])
        if key in self._file_config:
            return self._file_config[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    @staticmethod
    def _cast(value):
        """把环境变量里的字符串转成合适的类型。"""
        if not isinstance(value, str):
            return value
        lowered = value.strip().lower()
        if lowered in ("true", "false"):
            return lowered == "true"
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            return value

    # 常用配置项的便捷属性：实际是调用 get()，所以环境变量能覆盖
    @property
    def base_url(self):
        return self.get("base_url")

    @property
    def timeout(self):
        return self.get("timeout")

    @property
    def retry_times(self):
        return self.get("retry_times")

    @property
    def retry_delay(self):
        return self.get("retry_delay")

    @property
    def max_response_time(self):
        return self.get("max_response_time")

    @property
    def ui_base_url(self):
        return self.get("ui_base_url")

    @property
    def ui_headless(self):
        return self.get("ui_headless")

    @property
    def ui_timeout(self):
        return self.get("ui_timeout")


# 单例，全项目共用一份配置
config = Config()
