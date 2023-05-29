from bilix.progress.abc import Progress
from typing import Optional, Any, Set
from rich.theme import Theme
from rich.style import Style
from rich.spinner import Spinner
from rich.progress import Progress as RichProgress, TaskID, \
    TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, ProgressColumn


class SpinnerColumn(ProgressColumn):
    def __init__(self, style="progress.spinner", speed: float = 1.0):
        self.waiting = Spinner("dqpb", style=style)
        self.downloading = Spinner("dots", style=style, speed=speed)
        self.merging = Spinner("line", style=style, speed=speed)
        super().__init__()

    def render(self, task):
        t = task.get_time()
        if task.total is None:
            return self.waiting.render(t)
        elif task.finished:
            return self.merging.render(t)
        else:
            return self.downloading.render(t)


class CLIProgress(Progress):
    # Only one live display may be active at once
    _progress = RichProgress(
        SpinnerColumn(speed=2.),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TextColumn('ETA'),
        TimeRemainingColumn(),
        transient=True,
    )

    def __init__(self):
        self._active_ids: Set[TaskID] = set()

    @classmethod
    def start(cls):
        cls._progress.start()

    @classmethod
    def stop(cls):
        cls._progress.stop()

    @property
    def tasks(self):
        return self._progress.tasks

    @staticmethod
    def _cat_description(description, max_length=33):
        mid = (max_length - 3) // 2
        return description if len(description) < max_length else f'{description[:mid]}...{description[-mid:]}'

    async def add_task(
            self,
            description: str,
            start: bool = True,
            total: Optional[float] = None,
            completed: int = 0,
            visible: bool = True,
            **fields: Any,
    ) -> TaskID:
        task_id = self._progress.add_task(description=self._cat_description(description),
                                          start=start, total=total, completed=completed, visible=visible, **fields)
        self._active_ids.add(task_id)
        return task_id

    @property
    def active_speed(self):
        return sum(self._progress.tasks[task_id].speed for task_id in self._active_ids
                   if self._progress.tasks[task_id].speed)

    async def update(
            self,
            task_id: TaskID,
            *,
            total: Optional[float] = None,
            completed: Optional[float] = None,
            advance: Optional[float] = None,
            description: Optional[str] = None,
            visible: Optional[bool] = None,
            refresh: bool = False,
            **fields: Any,
    ) -> None:
        if description:
            description = self._cat_description(description)
        self._progress.update(task_id, total=total, completed=completed, advance=advance,
                              description=description, visible=visible, refresh=refresh, **fields)
        if self._progress.tasks[task_id].finished and task_id in self._active_ids:
            self._active_ids.remove(task_id)

    @classmethod
    def switch_theme(cls, bs="rgb(95,138,239)", gs="rgb(65,165,189)"):
        cls._progress.console.push_theme(Theme({
            # "progress.data.speed": Style(color=bs),
            "progress.download": Style(color=gs),
            "progress.percentage": Style(color=gs),
            "progress.spinner": Style(color=bs),
            "progress.remaining": Style(color=gs),
            # "bar.back": Style(color="grey23"),
            "bar.complete": Style(color=bs),
            "bar.finished": Style(color=gs),
            "bar.pulse": Style(color=bs),
        }))
