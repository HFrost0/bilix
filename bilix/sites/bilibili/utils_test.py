from bilix.sites.bilibili.utils import parse_ids_from_url


def test_parse_ids_from_url():
    strings = [
        "https://www.bilibili.com/video/av170001",
        "http://www.bilibili.com/video/BV1Xx41117Tz/?ba=labala&p=3#time=1234",
        "av170001",
        "BV1sE411w7tQ?p=2&from=search",
        "https://www.bilibili.com/video/BV1xx411c7HW?p=1"
    ]
    results = [
        (170001, None, 1),
        (None, 'BV1Xx41117Tz', 3),
        (170001, None, 1),
        (None, 'BV1sE411w7tQ', 2),
        (None, 'BV1xx411c7HW', 1)
    ]
    for index, string in enumerate(strings):
        assert parse_ids_from_url(string) == results[index]
