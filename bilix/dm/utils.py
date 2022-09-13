import asyncio
import json
import functools
from google.protobuf.json_format import MessageToJson
from .reply_pb2 import DmSegMobileReply
from .view_pb2 import DmWebViewReply
from bilix.process import SingletonPPE
from biliass import Danmaku2ASS


def parse_view(content: bytes) -> dict:
    dm_view = DmWebViewReply()
    dm_view.ParseFromString(content)
    dm_view = json.loads(MessageToJson(dm_view))
    return dm_view


def parse_seg(content: bytes) -> dict:
    seg = DmSegMobileReply()
    seg.ParseFromString(content)
    seg = json.loads(MessageToJson(seg))
    return seg


def dm2json(content: bytes) -> bytes:
    seg = DmSegMobileReply()
    seg.ParseFromString(content)
    seg = MessageToJson(seg)
    return seg.encode('utf-8')


def dm2ass_factory(width, height):
    async def dm2ass(protobuf_bytes: bytes) -> bytes:
        loop = asyncio.get_event_loop()
        f = functools.partial(Danmaku2ASS,
                              protobuf_bytes,
                              width,
                              height,
                              input_format="protobuf",
                              reserve_blank=0,
                              font_face="sans-serif",
                              font_size=width / 40,
                              text_opacity=0.8,
                              duration_marquee=15.0,
                              duration_still=10.0,
                              comment_filter=None,
                              is_reduce_comments=False,
                              progress_callback=None, )
        content = await loop.run_in_executor(SingletonPPE(), f)
        return content.encode('utf-8')

    return dm2ass
