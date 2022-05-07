import html
import re


def legal_title(title, add_name=''):
    """

    :param title: 主标题
    :param add_name: 分P名
    :return:
    """

    title, add_name = _replace(title), _replace(add_name)
    title = _truncation(title)  # avoid OSError caused by title too long
    return f'{title}-{add_name}' if add_name else title


def _replace(s: str):
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|]", '', s)  # replace illegal filename character
    return s


def _truncation(s: str, target=150):
    while len(s.encode('utf8')) > target - 3:
        s = s[:-1]
    return s


if __name__ == '__main__':
    a = legal_title("【Udemy付费课程】Node JS 高级概念-进阶课程 学习使用 Redis 进行缓存，通过集群加速，使用 S3 和 Node 添加图片上传！（中英文字幕）",
                    "P80-082 Solving Authentication Issues with")
    print(a)
