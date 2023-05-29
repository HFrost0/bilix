from abc import ABC, abstractmethod
from typing import Optional, Any


class Progress(ABC):
    """Abstract Class for bilix download progress, checkout to design your own progress"""

    @classmethod
    @abstractmethod
    def start(cls):
        """start to show the progress"""

    @classmethod
    @abstractmethod
    def stop(cls):
        """stop to show the progress"""

    @abstractmethod
    def tasks(self):
        """return the tasks"""

    @abstractmethod
    def active_speed(self) -> Optional[float]:
        """return current active speed (bit/s)"""

    @abstractmethod
    async def add_task(
            self,
            description: str,
            start: bool = True,
            total: Optional[float] = None,
            completed: int = 0,
            visible: bool = True,
            **fields,
    ):
        """async add a task to progress"""

    @abstractmethod
    async def update(
            self,
            task_id,
            *,
            total: Optional[float] = None,
            completed: Optional[float] = None,
            advance: Optional[float] = None,
            description: Optional[str] = None,
            visible: Optional[bool] = None,
            refresh: bool = False,
            **fields: Any
    ):
        """async update a task status"""
