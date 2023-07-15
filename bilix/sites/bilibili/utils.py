import re


def parse_ids_from_url(url_or_string: str):
    bvid, aid, page_num = None, None, 1
    if re.match(r'https?://www.bilibili.com/video/BV\w+', url_or_string) or re.match(r'BV\w+', url_or_string):
        bvid = re.search(r'(BV\w+)', url_or_string).groups()[0]
        assert bvid.isalnum()
    elif re.match(r'https?://www.bilibili.com/video/av\d+', url_or_string) or re.match(r'av\d+', url_or_string):
        aid = re.search(r'av(\d+)', url_or_string).groups()[0]
        assert aid.isdigit()
        aid = int(aid)
    else:
        raise ValueError(f"{url_or_string} is not a valid bilibili video url")
    # ?p=123 or &p=123
    if m := re.match(r'.*[?&]p=(\d+)', url_or_string):
        page_num = int(m.groups()[0])
        assert page_num >= 1
    return aid, bvid, page_num
