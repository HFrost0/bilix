"""
ffmpeg should be installed
pip install 'httpx[http2]' rich json5
"""
import asyncio
import anyio
import httpx
import re
import random
import json
import json5
from datetime import datetime, timedelta
import os
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby


def get_live(room_id):
    cookies = {'SESSDATA': ''}
    headers = {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}
    client = httpx.Client(headers=headers, http2=True, cookies=cookies)
    params = {
        'room_id': room_id,
        'protocol': '0,1',
        'format': '0,1,2',
        'codec': '0,1',
        # 'qn': 10000
    }
    res = client.get('https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo', params=params)
    data = json.loads(res.text)
    play_info = data['data']['playurl_info']['playurl']['stream'][-1]['format'][-1]['codec'][-1]
    host = play_info['url_info'][0]['host']
    extra = play_info['url_info'][0]['extra']
    url = host + play_info['base_url'] + extra
    print(url)


if __name__ == '__main__':
    get_live('5050')
