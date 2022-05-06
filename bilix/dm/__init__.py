import json
from google.protobuf.json_format import MessageToJson
from .reply_pb2 import DmSegMobileReply
from .view_pb2 import DmWebViewReply


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


def seg2json(content: bytes) -> bytes:
    seg = DmSegMobileReply()
    seg.ParseFromString(content)
    seg = MessageToJson(seg)
    return seg.encode('utf-8')
