from bilix.progress.abc import Progress
from typing import Optional, Any, Set
from rich.progress import Progress as RichProgress, TaskID, \
    TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn


class CLIProgress(Progress):
    # Only one live display may be active at once
    _progress = RichProgress(
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        'ETA',
        TimeRemainingColumn(), transient=True
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
            total: Optional[float] = 100.0,
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
