import json


def json2srt(data):
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
    return res
