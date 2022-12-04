from typing import Optional, Any
from ..log import logger


class BaseProgress:
    def __init__(self, holder=None):
        self._holder = holder

    @property
    def holder(self):
        return self._holder

    @holder.setter
    def holder(self, holder):
        if self._holder:  # ensure holder can be only set once
            raise Exception("progress holder already exists")
        self._holder = holder

    @property
    def holder_speed(self):
        raise NotImplemented

    def dynamic_sleep_time(self, chunk_size):
        t_tgt = chunk_size / self.holder.speed_limit * self.holder.stream_num
        t_real = chunk_size / self.holder_speed
        t = t_tgt - t_real
        # logger.debug(f"chunk size: {self.holder.chunk_size} lt: {t} stream_num: {self.holder.stream_num}")
        return t

    @property
    def tasks(self):
        raise NotImplemented

    async def add_task(
            self,
            description: str,
            start: bool = True,
            total: Optional[float] = 100.0,
            completed: int = 0,
            visible: bool = True,
            **fields: Any,
    ) -> int:
        raise NotImplemented

    async def update(
            self,
            task_id: int,
            *,
            total: Optional[float] = None,
            completed: Optional[float] = None,
            advance: Optional[float] = None,
            description: Optional[str] = None,
            visible: Optional[bool] = None,
            refresh: bool = False,
            **fields: Any,
    ) -> None:
        raise NotImplemented
