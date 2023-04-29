"""
just some useful ffmpeg commands wrapped in python
"""
import os
from anyio import run_process
from typing import List
from pathlib import Path
import tempfile


async def concat(path_lst: List[Path], output_path: Path, remove=True):
    with tempfile.NamedTemporaryFile('w', dir=output_path.parent, delete=False) as fp:
        for path in path_lst:
            fp.write(f"file '{path.name}'\n")
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', fp.name, '-c', 'copy', '-loglevel', 'quiet',
               str(output_path)]
        # print(' '.join(map(lambda x: f'"{x}"', cmd)))
    await run_process(cmd)
    os.remove(fp.name)
    if remove:
        for path in path_lst:
            os.remove(path)


async def combine(path_lst: List[Path], output_path: Path, remove=True):
    cmd = ['ffmpeg']
    for path in path_lst:
        cmd.extend(['-i', str(path)])
    # for flac, use -strict -2
    cmd.extend(['-c', 'copy', '-strict', '-2', '-loglevel', 'quiet', str(output_path)])
    # print(' '.join(map(lambda x: f'"{x}"', cmd)))
    await run_process(cmd)
    if remove:
        for path in path_lst:
            os.remove(path)


async def time_range_clip(input_path: Path, start: int, t: int, output_path: Path, remove=True):
    # for flac, use -strict -2
    cmd = ['ffmpeg', '-ss', f'{start:.1f}', '-t', f'{t:.1f}', '-i', str(input_path), '-codec', 'copy', '-strict', '-2',
           '-loglevel', 'quiet', '-f', 'mp4', str(output_path)]
    # print(' '.join(map(lambda x: f'"{x}"', cmd)))
    await run_process(cmd)
    if remove:
        os.remove(input_path)
