import logging
import locale
from typing import Literal, Dict
from rich.logging import RichHandler


class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.INFO, language: Literal['zh_CN', 'en_US', None] = None):
        super().__init__(name, level)
        self.language: Literal['zh_CN', 'en_US'] = language or locale.getdefaultlocale()[0] or 'en_US'
        if self.language not in self.word_map:  # ensure language is valid
            self.language = 'en_US'
        # add rich handler
        custom_rich_handler = RichHandler(
            show_time=False,
            show_path=True,
            markup=True,
            keywords=RichHandler.KEYWORDS + ['STREAM'],
            rich_tracebacks=True
        )
        formatter = logging.Formatter("{message}", style="{", datefmt="[%X]")
        custom_rich_handler.setFormatter(formatter)
        self.addHandler(custom_rich_handler)

    word_map: Dict[str, Dict[str, str]] = {
        'zh_CN': {'done': '已完成', 'exist': '已存在'},
        'en_US': {'done': 'Done', 'exist': 'Exist'}
    }

    @property
    def _width(self) -> int:
        return max(map(lambda x: len(x), self.word_map[self.language].values()))

    @property
    def words(self) -> Dict[str, str]:
        return self.word_map[self.language]

    def done(self, name: str):
        self.info(f"[cyan]{self.words['done']:{self._width}}[/cyan] {name}")

    def exist(self, name: str):
        self.info(f"[green]{self.words['exist']:{self._width}}[/green] {name}")

    def interrupted(self):
        if self.language == 'zh_CN':
            self.info('[yellow]用户中断，重复执行命令可继续下载')
        else:
            self.info('[yellow]Interrupted，repeating the command can continue the download')


logger = CustomLogger("bilix")
