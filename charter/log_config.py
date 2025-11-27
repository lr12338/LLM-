import logging
from logging.handlers import TimedRotatingFileHandler
import os


def get_logger(name, log_file, log_dir="logs"):
    """

    参数:
        name: logger 名称，避免冲突（比如 'main', 'charter'）
        log_file: 日志文件名（如 vessel_charter.log）
        log_dir: 日志文件存放路径

    返回:
        logging.Logger 实例
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        log_path = os.path.join(log_dir, log_file)
        handler = TimedRotatingFileHandler(
            log_path, when="midnight", interval=1, backupCount=7, encoding="utf-8", utc=True
        )
        handler.suffix = "%Y-%m-%d.log"
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

