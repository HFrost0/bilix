# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: reply.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0breply.proto\x12 bilibili.community.service.dm.v1\"L\n\x0b\x44mSegSDKReq\x12\x0b\n\x03pid\x18\x01 \x01(\x03\x12\x0b\n\x03oid\x18\x02 \x01(\x03\x12\x0c\n\x04type\x18\x03 \x01(\x05\x12\x15\n\rsegment_index\x18\x04 \x01(\x03\"]\n\rDmSegSDKReply\x12\x0e\n\x06\x63losed\x18\x01 \x01(\x08\x12<\n\x05\x65lems\x18\x02 \x03(\x0b\x32-.bilibili.community.service.dm.v1.DanmakuElem\"L\n\x0b\x44mSegOttReq\x12\x0b\n\x03pid\x18\x01 \x01(\x03\x12\x0b\n\x03oid\x18\x02 \x01(\x03\x12\x0c\n\x04type\x18\x03 \x01(\x05\x12\x15\n\rsegment_index\x18\x04 \x01(\x03\"]\n\rDmSegOttReply\x12\x0e\n\x06\x63losed\x18\x01 \x01(\x08\x12<\n\x05\x65lems\x18\x02 \x03(\x0b\x32-.bilibili.community.service.dm.v1.DanmakuElem\"g\n\x0e\x44mSegMobileReq\x12\x0b\n\x03pid\x18\x01 \x01(\x03\x12\x0b\n\x03oid\x18\x02 \x01(\x03\x12\x0c\n\x04type\x18\x03 \x01(\x05\x12\x15\n\rsegment_index\x18\x04 \x01(\x03\x12\x16\n\x0eteenagers_mode\x18\x05 \x01(\x05\"\xa1\x01\n\x10\x44mSegMobileReply\x12<\n\x05\x65lems\x18\x01 \x03(\x0b\x32-.bilibili.community.service.dm.v1.DanmakuElem\x12\r\n\x05state\x18\x02 \x01(\x05\x12@\n\x07\x61i_flag\x18\x03 \x01(\x0b\x32/.bilibili.community.service.dm.v1.DanmakuAIFlag\"X\n\tDmViewReq\x12\x0b\n\x03pid\x18\x01 \x01(\x03\x12\x0b\n\x03oid\x18\x02 \x01(\x03\x12\x0c\n\x04type\x18\x03 \x01(\x05\x12\r\n\x05spmid\x18\x04 \x01(\t\x12\x14\n\x0cis_hard_boot\x18\x05 \x01(\x05\"\xf0\x03\n\x0b\x44mViewReply\x12\x0e\n\x06\x63losed\x18\x01 \x01(\x08\x12\x39\n\x04mask\x18\x02 \x01(\x0b\x32+.bilibili.community.service.dm.v1.VideoMask\x12\x41\n\x08subtitle\x18\x03 \x01(\x0b\x32/.bilibili.community.service.dm.v1.VideoSubtitle\x12\x13\n\x0bspecial_dms\x18\x04 \x03(\t\x12\x44\n\x07\x61i_flag\x18\x05 \x01(\x0b\x32\x33.bilibili.community.service.dm.v1.DanmakuFlagConfig\x12N\n\rplayer_config\x18\x06 \x01(\x0b\x32\x37.bilibili.community.service.dm.v1.DanmuPlayerViewConfig\x12\x16\n\x0esend_box_style\x18\x07 \x01(\x05\x12\r\n\x05\x61llow\x18\x08 \x01(\x08\x12\x11\n\tcheck_box\x18\t \x01(\t\x12\x1a\n\x12\x63heck_box_show_msg\x18\n \x01(\t\x12\x18\n\x10text_placeholder\x18\x0b \x01(\t\x12\x19\n\x11input_placeholder\x18\x0c \x01(\t\x12\x1d\n\x15report_filter_content\x18\r \x03(\t\"\xa8\x03\n\x0e\x44mWebViewReply\x12\r\n\x05state\x18\x01 \x01(\x05\x12\x0c\n\x04text\x18\x02 \x01(\t\x12\x11\n\ttext_side\x18\x03 \x01(\t\x12=\n\x06\x64m_sge\x18\x04 \x01(\x0b\x32-.bilibili.community.service.dm.v1.DmSegConfig\x12\x41\n\x04\x66lag\x18\x05 \x01(\x0b\x32\x33.bilibili.community.service.dm.v1.DanmakuFlagConfig\x12\x13\n\x0bspecial_dms\x18\x06 \x03(\t\x12\x11\n\tcheck_box\x18\x07 \x01(\x08\x12\r\n\x05\x63ount\x18\x08 \x01(\x03\x12?\n\ncommandDms\x18\t \x03(\x0b\x32+.bilibili.community.service.dm.v1.CommandDm\x12M\n\rplayer_config\x18\n \x01(\x0b\x32\x36.bilibili.community.service.dm.v1.DanmuWebPlayerConfig\x12\x1d\n\x15report_filter_content\x18\x0b \x03(\t\"\xa1\x01\n\tCommandDm\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0b\n\x03oid\x18\x02 \x01(\x03\x12\x0b\n\x03mid\x18\x03 \x01(\t\x12\x0f\n\x07\x63ommand\x18\x04 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x05 \x01(\t\x12\x10\n\x08progress\x18\x06 \x01(\x05\x12\r\n\x05\x63time\x18\x07 \x01(\t\x12\r\n\x05mtime\x18\x08 \x01(\t\x12\r\n\x05\x65xtra\x18\t \x01(\t\x12\r\n\x05idStr\x18\n \x01(\t\"/\n\x0b\x44mSegConfig\x12\x11\n\tpage_size\x18\x01 \x01(\x03\x12\r\n\x05total\x18\x02 \x01(\x03\"S\n\tVideoMask\x12\x0b\n\x03\x63id\x18\x01 \x01(\x03\x12\x0c\n\x04plat\x18\x02 \x01(\x05\x12\x0b\n\x03\x66ps\x18\x03 \x01(\x05\x12\x0c\n\x04time\x18\x04 \x01(\x03\x12\x10\n\x08mask_url\x18\x05 \x01(\t\"o\n\rVideoSubtitle\x12\x0b\n\x03lan\x18\x01 \x01(\t\x12\x0e\n\x06lanDoc\x18\x02 \x01(\t\x12\x41\n\tsubtitles\x18\x03 \x03(\x0b\x32..bilibili.community.service.dm.v1.SubtitleItem\"\x8f\x03\n\x14\x44\x61nmuWebPlayerConfig\x12\x11\n\tdm_switch\x18\x01 \x01(\x08\x12\x11\n\tai_switch\x18\x02 \x01(\x08\x12\x10\n\x08\x61i_level\x18\x03 \x01(\x05\x12\x10\n\x08\x62locktop\x18\x04 \x01(\x08\x12\x13\n\x0b\x62lockscroll\x18\x05 \x01(\x08\x12\x13\n\x0b\x62lockbottom\x18\x06 \x01(\x08\x12\x12\n\nblockcolor\x18\x07 \x01(\x08\x12\x14\n\x0c\x62lockspecial\x18\x08 \x01(\x08\x12\x14\n\x0cpreventshade\x18\t \x01(\x08\x12\r\n\x05\x64mask\x18\n \x01(\x08\x12\x0f\n\x07opacity\x18\x0b \x01(\x02\x12\x0e\n\x06\x64marea\x18\x0c \x01(\x05\x12\x11\n\tspeedplus\x18\r \x01(\x02\x12\x10\n\x08\x66ontsize\x18\x0e \x01(\x02\x12\x12\n\nscreensync\x18\x0f \x01(\x08\x12\x11\n\tspeedsync\x18\x10 \x01(\x08\x12\x12\n\nfontfamily\x18\x11 \x01(\t\x12\x0c\n\x04\x62old\x18\x12 \x01(\x08\x12\x12\n\nfontborder\x18\x13 \x01(\x05\x12\x11\n\tdraw_type\x18\x14 \x01(\t\"\x9a\x01\n\x0cSubtitleItem\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0e\n\x06id_str\x18\x02 \x01(\t\x12\x0b\n\x03lan\x18\x03 \x01(\t\x12\x0f\n\x07lan_doc\x18\x04 \x01(\t\x12\x14\n\x0csubtitle_url\x18\x05 \x01(\t\x12:\n\x06\x61uthor\x18\x06 \x01(\x0b\x32*.bilibili.community.service.dm.v1.UserInfo\"\\\n\x08UserInfo\x12\x0b\n\x03mid\x18\x01 \x01(\x03\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0b\n\x03sex\x18\x03 \x01(\t\x12\x0c\n\x04\x66\x61\x63\x65\x18\x04 \x01(\t\x12\x0c\n\x04sign\x18\x05 \x01(\t\x12\x0c\n\x04rank\x18\x06 \x01(\x05\"\xd6\x01\n\x0b\x44\x61nmakuElem\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x10\n\x08progress\x18\x02 \x01(\x05\x12\x0c\n\x04mode\x18\x03 \x01(\x05\x12\x10\n\x08\x66ontsize\x18\x04 \x01(\x05\x12\r\n\x05\x63olor\x18\x05 \x01(\r\x12\x0f\n\x07midHash\x18\x06 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x07 \x01(\t\x12\r\n\x05\x63time\x18\x08 \x01(\x03\x12\x0e\n\x06weight\x18\t \x01(\x05\x12\x0e\n\x06\x61\x63tion\x18\n \x01(\t\x12\x0c\n\x04pool\x18\x0b \x01(\x05\x12\r\n\x05idStr\x18\x0c \x01(\t\x12\x0c\n\x04\x61ttr\x18\r \x01(\x05\"\xa0\x0b\n\x11\x44mPlayerConfigReq\x12\n\n\x02ts\x18\x01 \x01(\x03\x12\x45\n\x06switch\x18\x02 \x01(\x0b\x32\x35.bilibili.community.service.dm.v1.PlayerDanmakuSwitch\x12N\n\x0bswitch_save\x18\x03 \x01(\x0b\x32\x39.bilibili.community.service.dm.v1.PlayerDanmakuSwitchSave\x12[\n\x12use_default_config\x18\x04 \x01(\x0b\x32?.bilibili.community.service.dm.v1.PlayerDanmakuUseDefaultConfig\x12\x61\n\x15\x61i_recommended_switch\x18\x05 \x01(\x0b\x32\x42.bilibili.community.service.dm.v1.PlayerDanmakuAiRecommendedSwitch\x12_\n\x14\x61i_recommended_level\x18\x06 \x01(\x0b\x32\x41.bilibili.community.service.dm.v1.PlayerDanmakuAiRecommendedLevel\x12I\n\x08\x62locktop\x18\x07 \x01(\x0b\x32\x37.bilibili.community.service.dm.v1.PlayerDanmakuBlocktop\x12O\n\x0b\x62lockscroll\x18\x08 \x01(\x0b\x32:.bilibili.community.service.dm.v1.PlayerDanmakuBlockscroll\x12O\n\x0b\x62lockbottom\x18\t \x01(\x0b\x32:.bilibili.community.service.dm.v1.PlayerDanmakuBlockbottom\x12S\n\rblockcolorful\x18\n \x01(\x0b\x32<.bilibili.community.service.dm.v1.PlayerDanmakuBlockcolorful\x12O\n\x0b\x62lockrepeat\x18\x0b \x01(\x0b\x32:.bilibili.community.service.dm.v1.PlayerDanmakuBlockrepeat\x12Q\n\x0c\x62lockspecial\x18\x0c \x01(\x0b\x32;.bilibili.community.service.dm.v1.PlayerDanmakuBlockspecial\x12G\n\x07opacity\x18\r \x01(\x0b\x32\x36.bilibili.community.service.dm.v1.PlayerDanmakuOpacity\x12S\n\rscalingfactor\x18\x0e \x01(\x0b\x32<.bilibili.community.service.dm.v1.PlayerDanmakuScalingfactor\x12\x45\n\x06\x64omain\x18\x0f \x01(\x0b\x32\x35.bilibili.community.service.dm.v1.PlayerDanmakuDomain\x12\x43\n\x05speed\x18\x10 \x01(\x0b\x32\x34.bilibili.community.service.dm.v1.PlayerDanmakuSpeed\x12W\n\x0f\x65nableblocklist\x18\x11 \x01(\x0b\x32>.bilibili.community.service.dm.v1.PlayerDanmakuEnableblocklist\x12^\n\x19inlinePlayerDanmakuSwitch\x18\x12 \x01(\x0b\x32;.bilibili.community.service.dm.v1.InlinePlayerDanmakuSwitch\")\n\x08Response\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\")\n\x0b\x44\x61nmakuFlag\x12\x0c\n\x04\x64mid\x18\x01 \x01(\x03\x12\x0c\n\x04\x66lag\x18\x02 \x01(\r\"K\n\x11\x44\x61nmakuFlagConfig\x12\x10\n\x08rec_flag\x18\x01 \x01(\x05\x12\x10\n\x08rec_text\x18\x02 \x01(\t\x12\x12\n\nrec_switch\x18\x03 \x01(\x05\"P\n\rDanmakuAIFlag\x12?\n\x08\x64m_flags\x18\x01 \x03(\x0b\x32-.bilibili.community.service.dm.v1.DanmakuFlag\"\xb1\x02\n\x15\x44\x61nmuPlayerViewConfig\x12\x61\n\x1d\x64\x61nmuku_default_player_config\x18\x01 \x01(\x0b\x32:.bilibili.community.service.dm.v1.DanmuDefaultPlayerConfig\x12R\n\x15\x64\x61nmuku_player_config\x18\x02 \x01(\x0b\x32\x33.bilibili.community.service.dm.v1.DanmuPlayerConfig\x12\x61\n\x1d\x64\x61nmuku_player_dynamic_config\x18\x03 \x03(\x0b\x32:.bilibili.community.service.dm.v1.DanmuPlayerDynamicConfig\"\xa1\x04\n\x18\x44\x61nmuDefaultPlayerConfig\x12)\n!player_danmaku_use_default_config\x18\x01 \x01(\x08\x12,\n$player_danmaku_ai_recommended_switch\x18\x04 \x01(\x08\x12+\n#player_danmaku_ai_recommended_level\x18\x05 \x01(\x05\x12\x1f\n\x17player_danmaku_blocktop\x18\x06 \x01(\x08\x12\"\n\x1aplayer_danmaku_blockscroll\x18\x07 \x01(\x08\x12\"\n\x1aplayer_danmaku_blockbottom\x18\x08 \x01(\x08\x12$\n\x1cplayer_danmaku_blockcolorful\x18\t \x01(\x08\x12\"\n\x1aplayer_danmaku_blockrepeat\x18\n \x01(\x08\x12#\n\x1bplayer_danmaku_blockspecial\x18\x0b \x01(\x08\x12\x1e\n\x16player_danmaku_opacity\x18\x0c \x01(\x02\x12$\n\x1cplayer_danmaku_scalingfactor\x18\r \x01(\x02\x12\x1d\n\x15player_danmaku_domain\x18\x0e \x01(\x02\x12\x1c\n\x14player_danmaku_speed\x18\x0f \x01(\x05\x12$\n\x1cinline_player_danmaku_switch\x18\x10 \x01(\x08\"\xab\x05\n\x11\x44\x61nmuPlayerConfig\x12\x1d\n\x15player_danmaku_switch\x18\x01 \x01(\x08\x12\"\n\x1aplayer_danmaku_switch_save\x18\x02 \x01(\x08\x12)\n!player_danmaku_use_default_config\x18\x03 \x01(\x08\x12,\n$player_danmaku_ai_recommended_switch\x18\x04 \x01(\x08\x12+\n#player_danmaku_ai_recommended_level\x18\x05 \x01(\x05\x12\x1f\n\x17player_danmaku_blocktop\x18\x06 \x01(\x08\x12\"\n\x1aplayer_danmaku_blockscroll\x18\x07 \x01(\x08\x12\"\n\x1aplayer_danmaku_blockbottom\x18\x08 \x01(\x08\x12$\n\x1cplayer_danmaku_blockcolorful\x18\t \x01(\x08\x12\"\n\x1aplayer_danmaku_blockrepeat\x18\n \x01(\x08\x12#\n\x1bplayer_danmaku_blockspecial\x18\x0b \x01(\x08\x12\x1e\n\x16player_danmaku_opacity\x18\x0c \x01(\x02\x12$\n\x1cplayer_danmaku_scalingfactor\x18\r \x01(\x02\x12\x1d\n\x15player_danmaku_domain\x18\x0e \x01(\x02\x12\x1c\n\x14player_danmaku_speed\x18\x0f \x01(\x05\x12&\n\x1eplayer_danmaku_enableblocklist\x18\x10 \x01(\x08\x12$\n\x1cinline_player_danmaku_switch\x18\x11 \x01(\x08\x12$\n\x1cinline_player_danmaku_config\x18\x12 \x01(\x05\"K\n\x18\x44\x61nmuPlayerDynamicConfig\x12\x10\n\x08progress\x18\x01 \x01(\x05\x12\x1d\n\x15player_danmaku_domain\x18\x02 \x01(\x02\"7\n\x13PlayerDanmakuSwitch\x12\r\n\x05value\x18\x01 \x01(\x08\x12\x11\n\tcanIgnore\x18\x02 \x01(\x08\"(\n\x17PlayerDanmakuSwitchSave\x12\r\n\x05value\x18\x01 \x01(\x08\".\n\x1dPlayerDanmakuUseDefaultConfig\x12\r\n\x05value\x18\x01 \x01(\x08\"1\n PlayerDanmakuAiRecommendedSwitch\x12\r\n\x05value\x18\x01 \x01(\x08\"0\n\x1fPlayerDanmakuAiRecommendedLevel\x12\r\n\x05value\x18\x01 \x01(\x08\"&\n\x15PlayerDanmakuBlocktop\x12\r\n\x05value\x18\x01 \x01(\x08\")\n\x18PlayerDanmakuBlockscroll\x12\r\n\x05value\x18\x01 \x01(\x08\")\n\x18PlayerDanmakuBlockbottom\x12\r\n\x05value\x18\x01 \x01(\x08\"+\n\x1aPlayerDanmakuBlockcolorful\x12\r\n\x05value\x18\x01 \x01(\x08\")\n\x18PlayerDanmakuBlockrepeat\x12\r\n\x05value\x18\x01 \x01(\x08\"*\n\x19PlayerDanmakuBlockspecial\x12\r\n\x05value\x18\x01 \x01(\x08\"%\n\x14PlayerDanmakuOpacity\x12\r\n\x05value\x18\x01 \x01(\x02\"+\n\x1aPlayerDanmakuScalingfactor\x12\r\n\x05value\x18\x01 \x01(\x02\"$\n\x13PlayerDanmakuDomain\x12\r\n\x05value\x18\x01 \x01(\x02\"#\n\x12PlayerDanmakuSpeed\x12\r\n\x05value\x18\x01 \x01(\x05\"-\n\x1cPlayerDanmakuEnableblocklist\x12\r\n\x05value\x18\x01 \x01(\x08\"*\n\x19InlinePlayerDanmakuSwitch\x12\r\n\x05value\x18\x01 \x01(\x08*L\n\tDMAttrBit\x12\x14\n\x10\x44MAttrBitProtect\x10\x00\x12\x15\n\x11\x44MAttrBitFromLive\x10\x01\x12\x12\n\x0e\x44MAttrHighLike\x10\x02\x32\xaa\x04\n\x02\x44M\x12s\n\x0b\x44mSegMobile\x12\x30.bilibili.community.service.dm.v1.DmSegMobileReq\x1a\x32.bilibili.community.service.dm.v1.DmSegMobileReply\x12\x64\n\x06\x44mView\x12+.bilibili.community.service.dm.v1.DmViewReq\x1a-.bilibili.community.service.dm.v1.DmViewReply\x12q\n\x0e\x44mPlayerConfig\x12\x33.bilibili.community.service.dm.v1.DmPlayerConfigReq\x1a*.bilibili.community.service.dm.v1.Response\x12j\n\x08\x44mSegOtt\x12-.bilibili.community.service.dm.v1.DmSegOttReq\x1a/.bilibili.community.service.dm.v1.DmSegOttReply\x12j\n\x08\x44mSegSDK\x12-.bilibili.community.service.dm.v1.DmSegSDKReq\x1a/.bilibili.community.service.dm.v1.DmSegSDKReplyb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'reply_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _DMATTRBIT._serialized_start=7024
  _DMATTRBIT._serialized_end=7100
  _DMSEGSDKREQ._serialized_start=49
  _DMSEGSDKREQ._serialized_end=125
  _DMSEGSDKREPLY._serialized_start=127
  _DMSEGSDKREPLY._serialized_end=220
  _DMSEGOTTREQ._serialized_start=222
  _DMSEGOTTREQ._serialized_end=298
  _DMSEGOTTREPLY._serialized_start=300
  _DMSEGOTTREPLY._serialized_end=393
  _DMSEGMOBILEREQ._serialized_start=395
  _DMSEGMOBILEREQ._serialized_end=498
  _DMSEGMOBILEREPLY._serialized_start=501
  _DMSEGMOBILEREPLY._serialized_end=662
  _DMVIEWREQ._serialized_start=664
  _DMVIEWREQ._serialized_end=752
  _DMVIEWREPLY._serialized_start=755
  _DMVIEWREPLY._serialized_end=1251
  _DMWEBVIEWREPLY._serialized_start=1254
  _DMWEBVIEWREPLY._serialized_end=1678
  _COMMANDDM._serialized_start=1681
  _COMMANDDM._serialized_end=1842
  _DMSEGCONFIG._serialized_start=1844
  _DMSEGCONFIG._serialized_end=1891
  _VIDEOMASK._serialized_start=1893
  _VIDEOMASK._serialized_end=1976
  _VIDEOSUBTITLE._serialized_start=1978
  _VIDEOSUBTITLE._serialized_end=2089
  _DANMUWEBPLAYERCONFIG._serialized_start=2092
  _DANMUWEBPLAYERCONFIG._serialized_end=2491
  _SUBTITLEITEM._serialized_start=2494
  _SUBTITLEITEM._serialized_end=2648
  _USERINFO._serialized_start=2650
  _USERINFO._serialized_end=2742
  _DANMAKUELEM._serialized_start=2745
  _DANMAKUELEM._serialized_end=2959
  _DMPLAYERCONFIGREQ._serialized_start=2962
  _DMPLAYERCONFIGREQ._serialized_end=4402
  _RESPONSE._serialized_start=4404
  _RESPONSE._serialized_end=4445
  _DANMAKUFLAG._serialized_start=4447
  _DANMAKUFLAG._serialized_end=4488
  _DANMAKUFLAGCONFIG._serialized_start=4490
  _DANMAKUFLAGCONFIG._serialized_end=4565
  _DANMAKUAIFLAG._serialized_start=4567
  _DANMAKUAIFLAG._serialized_end=4647
  _DANMUPLAYERVIEWCONFIG._serialized_start=4650
  _DANMUPLAYERVIEWCONFIG._serialized_end=4955
  _DANMUDEFAULTPLAYERCONFIG._serialized_start=4958
  _DANMUDEFAULTPLAYERCONFIG._serialized_end=5503
  _DANMUPLAYERCONFIG._serialized_start=5506
  _DANMUPLAYERCONFIG._serialized_end=6189
  _DANMUPLAYERDYNAMICCONFIG._serialized_start=6191
  _DANMUPLAYERDYNAMICCONFIG._serialized_end=6266
  _PLAYERDANMAKUSWITCH._serialized_start=6268
  _PLAYERDANMAKUSWITCH._serialized_end=6323
  _PLAYERDANMAKUSWITCHSAVE._serialized_start=6325
  _PLAYERDANMAKUSWITCHSAVE._serialized_end=6365
  _PLAYERDANMAKUUSEDEFAULTCONFIG._serialized_start=6367
  _PLAYERDANMAKUUSEDEFAULTCONFIG._serialized_end=6413
  _PLAYERDANMAKUAIRECOMMENDEDSWITCH._serialized_start=6415
  _PLAYERDANMAKUAIRECOMMENDEDSWITCH._serialized_end=6464
  _PLAYERDANMAKUAIRECOMMENDEDLEVEL._serialized_start=6466
  _PLAYERDANMAKUAIRECOMMENDEDLEVEL._serialized_end=6514
  _PLAYERDANMAKUBLOCKTOP._serialized_start=6516
  _PLAYERDANMAKUBLOCKTOP._serialized_end=6554
  _PLAYERDANMAKUBLOCKSCROLL._serialized_start=6556
  _PLAYERDANMAKUBLOCKSCROLL._serialized_end=6597
  _PLAYERDANMAKUBLOCKBOTTOM._serialized_start=6599
  _PLAYERDANMAKUBLOCKBOTTOM._serialized_end=6640
  _PLAYERDANMAKUBLOCKCOLORFUL._serialized_start=6642
  _PLAYERDANMAKUBLOCKCOLORFUL._serialized_end=6685
  _PLAYERDANMAKUBLOCKREPEAT._serialized_start=6687
  _PLAYERDANMAKUBLOCKREPEAT._serialized_end=6728
  _PLAYERDANMAKUBLOCKSPECIAL._serialized_start=6730
  _PLAYERDANMAKUBLOCKSPECIAL._serialized_end=6772
  _PLAYERDANMAKUOPACITY._serialized_start=6774
  _PLAYERDANMAKUOPACITY._serialized_end=6811
  _PLAYERDANMAKUSCALINGFACTOR._serialized_start=6813
  _PLAYERDANMAKUSCALINGFACTOR._serialized_end=6856
  _PLAYERDANMAKUDOMAIN._serialized_start=6858
  _PLAYERDANMAKUDOMAIN._serialized_end=6894
  _PLAYERDANMAKUSPEED._serialized_start=6896
  _PLAYERDANMAKUSPEED._serialized_end=6931
  _PLAYERDANMAKUENABLEBLOCKLIST._serialized_start=6933
  _PLAYERDANMAKUENABLEBLOCKLIST._serialized_end=6978
  _INLINEPLAYERDANMAKUSWITCH._serialized_start=6980
  _INLINEPLAYERDANMAKUSWITCH._serialized_end=7022
  _DM._serialized_start=7103
  _DM._serialized_end=7657
# @@protoc_insertion_point(module_scope)
