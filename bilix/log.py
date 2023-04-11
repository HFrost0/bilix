import logging
from rich.logging import RichHandler


def get_logger():
    bilix_logger = logging.getLogger("bilix")
    # 如果logger已经配置过handler，直接返回logger实例
    if bilix_logger.hasHandlers():
        return bilix_logger
    bilix_logger.setLevel(logging.INFO)
    # 创建自定义的RichHandler
    custom_rich_handler = RichHandler(
        show_time=False,
        show_path=False,
        markup=True,
        keywords=RichHandler.KEYWORDS + ['STREAM'],
        rich_tracebacks=True
    )
    # 设置日志格式
    formatter = logging.Formatter("{message}", style="{", datefmt="[%X]")
    custom_rich_handler.setFormatter(formatter)
    # 为logger添加自定义的RichHandler
    bilix_logger.addHandler(custom_rich_handler)
    return bilix_logger


logger = get_logger()
