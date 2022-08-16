import re
import httpx
from bilix.download import *
from bilix.log import logger


def assign(**kwargs):
    key = kwargs['key']
    if 'jable' in key or re.match(r"[A-Za-z]+-\d+", key):
        logger.info("Assign to jable")
        return assign2jable(**kwargs)
    elif 'yhdmp' in key:
        logger.info("Assign to yhdmp")
        return assign2yhdmp(**kwargs)
    elif '.m3u8' in key:
        logger.info("Assing to m3u8")
        return assign2m3u8(**kwargs)
    else:
        # logger.info("Assign to bilibili")
        return assign2bilibili(**kwargs)


def assign2m3u8(**kwargs):
    d = BaseDownLoaderM3u8(httpx.AsyncClient(), videos_dir=kwargs['videos_dir'],
                           part_concurrency=kwargs['part_concurrency'])
    method = kwargs['method']
    if method == 'get_video' or method == 'v':
        cor = d.get_m3u8_video(kwargs['key'], "unnamed")
    else:
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
    return cor, d


def assign2bilibili(
        method: str,
        key: str,
        videos_dir: str,
        video_concurrency: int,
        part_concurrency: int,
        cookie: str,
        quality: int,
        days: int,
        num: int,
        order: str,
        keyword: str,
        no_series: bool,
        hierarchy: bool,
        image: bool,
        subtitle: bool,
        dm: bool,
        only_audio: bool,
        p_range,
):
    d = DownloaderBilibili(videos_dir=videos_dir,
                           video_concurrency=video_concurrency,
                           part_concurrency=part_concurrency,
                           sess_data=cookie)
    if method == 'get_series' or method == 's':
        cor = d.get_series(key, quality=quality, image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                           p_range=p_range, hierarchy=hierarchy)
    elif method == 'get_video' or method == 'v':
        cor = d.get_video(key, quality=quality,
                          image=image, subtitle=subtitle, dm=dm, only_audio=only_audio)
    elif method == 'get_up' or method == 'up':
        cor = d.get_up_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy
        )
    elif method == 'get_cate' or method == 'cate':
        cor = d.get_cate_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, days=days, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    elif method == 'get_favour' or method == 'fav':
        cor = d.get_favour(key, quality=quality, num=num, keyword=keyword, series=no_series,
                           image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    elif method == 'get_collect' or method == 'col':
        cor = d.get_collect_or_list(key, quality=quality,
                                    image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                                    hierarchy=hierarchy)
    else:
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
    return cor, d


def assign2jable(
        method: str,
        key: str,
        videos_dir: str,
        video_concurrency: int,
        part_concurrency: int,
        cookie: str,
        quality: int,
        days: int,
        num: int,
        order: str,
        keyword: str,
        no_series: bool,
        hierarchy: bool,
        image: bool,
        subtitle: bool,
        dm: bool,
        only_audio: bool,
        p_range,
):
    d = DownloaderJable(videos_dir=videos_dir, video_concurrency=video_concurrency, part_concurrency=part_concurrency)
    if method == 'get_video' or method == 'v':
        cor = d.get_video(key, image=image, hierarchy=hierarchy)
    else:
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
    return cor, d


def assign2yhdmp(
        method: str,
        key: str,
        videos_dir: str,
        video_concurrency: int,
        part_concurrency: int,
        cookie: str,
        quality: int,
        days: int,
        num: int,
        order: str,
        keyword: str,
        no_series: bool,
        hierarchy: bool,
        image: bool,
        subtitle: bool,
        dm: bool,
        only_audio: bool,
        p_range,
):
    d = DownloaderYhdmp(videos_dir=videos_dir, video_concurrency=video_concurrency, part_concurrency=part_concurrency)
    if method == 'get_series' or method == 's':
        cor = d.get_series(key, p_range=p_range, hierarchy=hierarchy)
    elif method == 'get_video' or method == 'v':
        cor = d.get_video(key)
    else:
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
    return cor, d
