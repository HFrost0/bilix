import html
import re


def legal_title(title, add_name=''):
    """

    :param title: 主标题
    :param add_name: 分P名
    :return:
    """
    title, add_name = _replace(title), _replace(add_name)
    title = _truncate(title)  # avoid OSError caused by title too long
    return f'{title}-{add_name}' if add_name else title


def _replace(s: str):
    s = s.strip()
    s = html.unescape(s)  # handel & "... # todo remove
    s = re.sub(r"[/\\:*?\"<>|]", '', s)  # replace illegal filename character
    return s


def _truncate(s: str, target=150):
    while len(s.encode('utf8')) > target - 3:
        s = s[:-1]
    return s
