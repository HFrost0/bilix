"""
some useful functions
"""
import html
import json
import re
import time
from functools import wraps
from urllib.parse import quote_plus
from typing import Union, Sequence, Coroutine, List, Tuple, Optional
from bilix.log import logger


def cors_slice(cors: Sequence[Coroutine], p_range: Sequence[int]):
    h, t = p_range[0] - 1, p_range[1]
    assert 0 <= h <= t
    [cor.close() for idx, cor in enumerate(cors) if idx < h or idx >= t]  # avoid runtime warning
    cors = cors[h:t]
    return cors


def legal_title(*parts: str, join_str: str = '-'):
    """
    join several string parts to os illegal file/dir name (no illegal character and not too long).
    auto skip empty.

    :param parts:
    :param join_str: the string to join each part
    :return:
    """
    return join_str.join(filter(lambda x: len(x) > 0, map(replace_illegal, parts)))


def replace_illegal(s: str):
    """strip, unescape html and replace os illegal character in s"""
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n\t]", '', s)  # replace illegal filename character
    return s


def convert_size(total_bytes: int) -> str:
    unit, suffix = pick_unit_and_suffix(
        total_bytes, ["bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"], 1000
    )
    return f"{total_bytes / unit:,.2f}{suffix}"


def pick_unit_and_suffix(size: int, suffixes: List[str], base: int) -> Tuple[int, str]:
    """Borrowed from rich.filesize. Pick a suffix and base for the given size."""
    for i, suffix in enumerate(suffixes):
        unit = base ** i
        if size < unit * base:
            break
    else:
        raise ValueError('Invalid input')
    return unit, suffix


def valid_sess_data(sess_data: Optional[str]) -> str:
    """check and encode sess_data"""
    # url-encoding sess_data if it's not encoded
    # https://github.com/HFrost0/bilix/pull/114https://github.com/HFrost0/bilix/pull/114
    if sess_data and not re.search(r'(%[0-9A-Fa-f]{2})|(\+)', sess_data):
        sess_data = quote_plus(sess_data)
        logger.debug(f"sess_data encoded: {sess_data}")
    return sess_data


def t2s(t: int) -> str:
    return str(t)


def s2t(s: str) -> int:
    """
    :param s: hour:minute:second or xx(s) format input
    :return:
    """
    if ':' not in s:
        return int(s)
    h, m, s = map(int, s.split(':'))
    return h * 60 * 60 + m * 60 + s


def json2srt(data: Union[bytes, str, dict]):
    b = False
    if type(data) is bytes:
        data = data.decode('utf-8')
        b = True
    if type(data) is str:
        data = json.loads(data)

    def t2str(t):
        ms = int(round(t % 1, 3) * 1000)
        s = int(t)
        m = s // 60
        h = m // 60
        m, s = m % 60, s % 60
        t_str = f'{h:0>2}:{m:0>2}:{s:0>2},{ms:0>3}'
        return t_str

    res = ''
    for idx, i in enumerate(data['body']):
        from_time, to_time = t2str(i['from']), t2str(i['to'])
        content = i['content']
        res += f"{idx + 1}\n{from_time} --> {to_time}\n{content}\n\n"
    return res.encode('utf-8') if b else res


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic_ns()
        res = func(*args, **kwargs)
        logger.debug(
            f"{func.__name__} cost {time.monotonic_ns() - start} ns with args: {args}, kwargs: {kwargs} result: {res}")
        return res

    return wrapper
