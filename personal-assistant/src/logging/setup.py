import os
import re
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class SLF4JFormatter(logging.Formatter):
    """SLF4J 风格的日志格式化器，支持 SLF4J 格式转换为 Python 格式"""

    def __init__(self, fmt: Optional[str] = None):
        if fmt is None:
            fmt = "%(asctime)s [%(threadName)s] %(levelname)-5s %(name)s - %(message)s"
        else:
            fmt = self._convert_slf4j_format(fmt)
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def _convert_slf4j_format(self, fmt: str) -> str:
        """将 SLF4J 格式转换为 Python logging 格式"""
        replacements = [
            (r"%d\{yyyy-MM-dd HH:mm:ss\}", "%(asctime)s"),
            (r"%d\{yyyy-MM-dd HH:mm\}", "%(asctime)s"),
            (r"%d\{HH:mm:ss\}", "%(asctime)s"),
            (r"%d\{[^}]+\}", "%(asctime)s"),
            (r"%d(?![{])", "%(asctime)s"),
            (r"%-5level", "%(levelname)-5s"),
            (r"%level", "%(levelname)s"),
            (r"%logger\{36\}", "%(name)s"),
            (r"%logger\{[^}]+\}", "%(name)s"),
            (r"%logger", "%(name)s"),
            (r"%thread", "%(threadName)s"),
            (r"%msg", "%(message)s"),
            (r"%n", "\n"),
        ]

        result = fmt
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/assistant.log",
    log_format: Optional[str] = None,  # 改为 Optional，内部使用默认格式
) -> logging.Logger:
    """
    配置日志系统，同时输出到控制台和文件
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = SLF4JFormatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    return logging.getLogger(name)