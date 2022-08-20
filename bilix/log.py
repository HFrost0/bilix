import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    style="{",
    format="{message}", datefmt="[%X]",
    handlers=[RichHandler(show_time=False, show_path=False, markup=True, keywords=RichHandler.KEYWORDS + ['STREAM'],
                          rich_tracebacks=True)]
)
logger = logging.getLogger("bilix")

if __name__ == '__main__':
    # logger.info("", exc_info=Exception(1))
    print(repr(IndexError))
    try:
        1 / 0
    except Exception as e:
        logger.warning(f"STREAM {e}")

    logger.warning("GET", exc_info=IndexError(123))
    # logger.warning("Hello, World! https://www.baidu.com")
    # logger.warning("Hello, World! https://www.baidu.com")
    # logger.error("Hello, World! https://www.baidu.com")
