# -*- coding: utf-8 -*-
import logging
import time
from datetime import datetime, timedelta

from dingtalk.client import AppKeyClient
from dingtalk.storage.kvstorage import KvStorage
import redis

from odoo import fields, tools

_logger = logging.getLogger(__name__)


"""
钉钉开发平台>首页>查看：CorpId
钉钉开发平台>H5微应用>基础信息>查看：AgentId,AppKey,AppSecret
在odoo.conf添加配置参数:
din_agentid = AgentId值
din_corpid = CorpId值
din_appkey = AppKey值
din_appsecret = AppSecret值
安装 pip3 install dingtalk-sdk
升级 pip3 install -U dingtalk-sdk
从master升级：pip3 install -U https://github.com/007gzs/dingtalk-sdk/archive/master.zip
"""

DIN_CORPID = tools.config.get('din_corpid', '').strip()
DIN_APPKEY = tools.config.get('din_appkey', '').strip()
DIN_APPSECRET = tools.config.get('din_appsecret', '').strip()
REDIS_IP = tools.config.get('redis_host', 'localhost')
REDIS_PORT = int(tools.config.get('redis_port', 6379))
DINGTALK_REDIS_DB = int(tools.config.get('dingtalk_redis_db', 1))
SESSION_MANAGER = redis.Redis(host=REDIS_IP, port=REDIS_PORT, db=DINGTALK_REDIS_DB)

client = AppKeyClient(DIN_CORPID, DIN_APPKEY, DIN_APPSECRET, storage=KvStorage(SESSION_MANAGER))

# def get_client(obj):
#     """钉钉客户端初始化
#        安装 pip3 install dingtalk-sdk
#        升级 pip3 install -U dingtalk-sdk
#        从master升级：pip3 install -U https://github.com/007gzs/dingtalk-sdk/archive/master.zip
#     """
#     din_corpid = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.din_corpid')
#     din_appkey = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.din_appkey')
#     din_appsecret = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.din_appsecret')
#     dingtalk_redis_ip = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.dingtalk_redis_ip')
#     dingtalk_redis_port = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.dingtalk_redis_port')
#     dingtalk_redis_db = obj.env['ir.config_parameter'].sudo(
#     ).get_param('ali_dindin.dingtalk_redis_db')
#     session_manager = redis.Redis(
#         host=dingtalk_redis_ip, port=dingtalk_redis_port, db=dingtalk_redis_db)
#     if not din_appkey or not din_appsecret or not din_corpid:
#         raise UserError(_('钉钉设置项中的CorpId、AppKey和AppSecret不能为空'))
#     return AppKeyClient(din_corpid, din_appkey, din_appsecret, storage=KvStorage(session_manager))


def list_cut(mylist, limit):
    """
    列表分段
    :param mylist:列表集
    :param limit: 子列表元素限制数量
    :return:
    """
    cut_list = [mylist[i:i + limit] for i in range(0, len(mylist), limit)]
    return cut_list


def day_cut(begin_time, end_time, days):
    """
    日期分段
    :param begin_date:开始日期
    :param end_date:结束日期
    :param days: 最大间隔时间
    :return:
    """
    cut_day = []
    begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(str(end_time), "%Y-%m-%d %H:%M:%S")
    delta = timedelta(days=days)
    t1 = begin_time
    while t1 <= end_time:
        if end_time < t1 + delta:
            t2 = end_time
        else:
            t2 = t1 + delta
        t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
        t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
        cut_day.append([t1_str, t2_str])
        t1 = t2 + timedelta(seconds=1)
    return cut_day


def stamp_to_time(time_num):
    """
    将13位时间戳转换为时间
    :param time_num:
    :return:
    """
    time_stamp = float(time_num / 1000)
    time_array = time.localtime(time_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_array)


def time_to_stamp(mytime):
    """
    将时间转成13位时间戳
    :param date:
    :return:
    """
    time_str = fields.Datetime.to_string(mytime)
    time_stamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M:%S"))
    time_stamp = time_stamp * 1000
    return time_stamp

