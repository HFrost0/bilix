import html
import re


def legal_title(title, add_name=''):
    """

    :param title: 主标题
    :param add_name: 分P名
    :return:
    """
    title = title.strip()
    add_name = add_name.strip()
    if add_name:
        title = f'{title}-{add_name}'
    title = html.unescape(title)  # handel & "...
    title = re.sub(r"[/\\:*?\"<>|]", '', title)  # replace illegal file character
    # todo 标题过长时引发系统错误
    return title
