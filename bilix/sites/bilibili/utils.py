import re


def parse_ids_from_url(url_or_string: str):
    """
    aid, bvid, page_num = parse_ids_from_url(url_or_string)

    例如：
    ```
    [0] https://www.bilibili.com/video/av170001
    > aid = 170001, bvid = None, page_num = None
    [1] http://www.bilibili.com/video/BV1Xx41117Tz/?ba=labala&p=3#time=1234
    > aid = None, bvid = "BV1Xx41117Tz", page_num = 3
    [2] av170001
    > aid = 170001, bvid = None, page_num = None
    [3] BV1sE411w7tQ?p=2
    > aid = None, bvid = "BV1sE411w7tQ", page_num = 2
    ```
    """

    bvid = aid = page_num = None
    if re.match(r'https?://www.bilibili.com/video/BV\w+', url_or_string) or re.match(r'BV\w+', url_or_string):
        bvid = re.search(r'BV(\w+)', url_or_string).groups()[0]
        assert bvid.isalnum()
        assert isinstance(bvid, str)
    elif re.match(r'https?://www.bilibili.com/video/av\d+', url_or_string) or re.match(r'av\d+', url_or_string):
        aid = re.search(r'av(\d+)', url_or_string).groups()[0]
        assert aid.isdigit()
        aid = int(aid)

    # ?p=123 or &p=123
    if re.match(r'.*[?&]p=(\d+)', url_or_string):
        page_num = int(re.search(r'.*[?&]p=(\d+)', url_or_string).groups()[0])

    assert bvid or aid, "url is not a valid bilibili video url"

    return aid, bvid, page_num
