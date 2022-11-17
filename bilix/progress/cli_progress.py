import asyncio
from typing import NewType, Optional, Any
from functools import wraps

from rich.progress import Progress, TaskID


class CLIProgress(Progress):
    @wraps(Progress.add_task)
    async def add_task(
            self,
            description: str,
            start: bool = True,
            total: Optional[float] = 100.0,
            completed: int = 0,
            visible: bool = True,
            **fields: Any,
    ) -> TaskID:
        return super(CLIProgress, self).add_task(description=description, start=start, total=total, completed=completed,
                                                 visible=visible, **fields)

    @wraps(Progress.update)
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
        return super().update(task_id, total=total, completed=completed, advance=advance, description=description,
                              visible=visible, refresh=refresh, **fields)


def main():
    pass


if __name__ == '__main__':
    p = CLIProgress()
