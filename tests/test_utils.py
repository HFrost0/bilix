from bilix.utils import parse_bytes_str, legal_title


def test_legal_file_name():
    pass


def test_parse_bytes():
    assert parse_bytes_str('10KB') == 10 * 1000 ** 1
    assert parse_bytes_str('10.56MB') == 10.56 * 1000 ** 2
    assert parse_bytes_str('10.56 M') == 10.56 * 1000 ** 2
