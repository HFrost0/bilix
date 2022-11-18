from rich.progress import TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from .cli_progress import CLIProgress

# todo singleton
_progress = CLIProgress(
    TextColumn("[progress.description]{task.description}"),
    TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    'ETA',
    TimeRemainingColumn(), transient=True
)


def get_progress():
    _progress.start()
    return _progress


def close_progress():
    _progress.stop()
