# -*- coding: utf-8 -*-
import logging
import time
import redis
from odoo import api, fields, models
from dingtalk.client import AppKeyClient
from dingtalk.storage.kvstorage import KvStorage
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def get_client(obj):
    """钉钉客户端初始化
       安装 pip3 install dingtalk-sdk
       手动尝新：pip3 install -U https://github.com/007gzs/dingtalk-sdk/archive/master.zip
    """
    din_corpid = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
    din_appkey = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appkey')
    din_appsecret = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appsecret')
    dingtalk_redis_ip = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.dingtalk_redis_ip')
    dingtalk_redis_port = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.dingtalk_redis_port')
    dingtalk_redis_db = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.dingtalk_redis_db')
    session_manager = redis.Redis(host=dingtalk_redis_ip, port=dingtalk_redis_port, db=dingtalk_redis_db)
    if not din_appkey and not din_appsecret and not din_corpid:
        raise UserError('钉钉设置项中的CorpId、AppKey和AppSecret不能为空')
    else:
        return AppKeyClient(din_corpid, din_appkey, din_appsecret, storage=KvStorage(session_manager))

def grouped_list(all_list, limit):
    """
    根据输入的列表和单个列表限制元素个数，对列表进行分组后输出
    :param all_data_list:列表集
    :param limit: 单个列表最大包含元素数量
    :return:
    """
    user_list = list()
    if len(all_list) > limit:
        n = 1
        e_list = list()
        for user in all_list:
            if n <= limit:
                e_list.append(user)
                n = n + 1
            else:
                user_list.append(e_list)
                e_list = list()
                e_list.append(user)
                n = 2
        user_list.append(e_list)
    else:
        for user in all_list:
            user_list.append(user)
    return user_list

def stamp_to_time(time_num):
    """
    将13位时间戳转换为时间
    :param time_num:
    :return:
    """
    time_stamp = float(time_num / 1000) 
    time_array = time.localtime(time_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

def time_to_stamp(time):
    """
    将时间转成13位时间戳
    :param date:
    :return:
    """
    time_str = fields.Datetime.to_string(time)
    time_stamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M:%S"))
    time_stamp = time_stamp * 1000
    return time_stamp