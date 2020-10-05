# -*- coding: utf-8 -*-

import logging
import time
from datetime import datetime, timedelta
from odoo import fields
from dingtalk.client import AppKeyClient
from dingtalk.storage.memorystorage import MemoryStorage
from odoo.exceptions import UserError
from odoo.http import request
import hmac
import hashlib
import base64
from urllib.parse import quote
import pytz

mem_storage = MemoryStorage()
_logger = logging.getLogger(__name__)


def get_client(self, config):
    """
    得到客户端
    :param self: 当自动任务时获取客户端时需传入一个对象，否则会报对象无绑定的错误
    :param config:
    :return:
    """
    corp_id = config.corp_id.replace(' ', '')
    app_key = config.app_key.replace(' ', '')
    app_secret = config.app_secret.replace(' ', '')
    return AppKeyClient(corp_id, app_key, app_secret, storage=mem_storage)


def get_dingtalk_config(self, company):
    """
    获取配置项
    :return:
    """
    config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)])
    if not config:
        raise UserError("没有为:(%s)配置钉钉参数！" % company.name)
    return config


def get_config_is_delete(self, company):
    """
    返回对应公司钉钉配置项中是否"删除基础数据自动同步"字段
    :return:
    """
    config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)])
    if not config:
        raise UserError("没有为:(%s)配置钉钉参数！" % company.name)
    return config.delete_is_sy


def timestamp_to_local_date(time_num, obj=None):
    """
    将13位毫秒时间戳转换为本地日期(+8h)
    :param time_num:
    :param obj: object
    :return: string datetime
    """
    if not time_num:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    to_second_timestamp = float(time_num / 1000)  # 毫秒转秒
    to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
    to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    to_local_datetime = fields.Datetime.context_timestamp(obj, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return to_str_datetime


def get_time_stamp(timeNum):
    """
    将13位时间戳转换为时间utc=0
    :param timeNum:
    :return: "%Y-%m-%d %H:%M:%S"
    """
    timeStamp = float(timeNum / 1000)
    timeArray = time.gmtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def datetime_to_stamp(time_num):
    """
    将时间转成13位时间戳
    :param time_num:
    :return: date_stamp
    """
    date_str = fields.Datetime.to_string(time_num)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)


def utc2local(utc_dtm):
    """
    UTC 时间转本地时间（ +8:00 ）
    :param utc_dtm:
    :return:
    """
    local_tm = datetime.fromtimestamp(0)
    utc_tm = datetime.utcfromtimestamp(0)
    offset = local_tm - utc_tm
    return utc_dtm + offset


def local2utc(local_dtm):
    """
    本地时间转 UTC 时间（ -8:00 ）
    :param local_dtm:
    :return:
    """
    return datetime.utcfromtimestamp(local_dtm.timestamp())


def list_cut(mylist, limit):
    """
    列表分段
    :param mylist:列表集
    :param limit: 子列表元素限制数量
    :return:
    """
    length = len(mylist)
    cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
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
    begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
    end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
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
        # t1 = t2 + timedelta(seconds=1)
        t1 = t2 + timedelta(days=1)
    return cut_day


def user_info_by_dingtalk_code(self, code, company):
    """
    根据扫码或账号密码登录返回的code获取用户信息
    :param self:
    :param code: code  账号或扫码登录返回的code
    :param company: 公司
    :return:
    """
    client = get_client(self, get_dingtalk_config(self, company))
    config = request.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)], limit=1)
    login_id = config.login_id
    login_secret = config.login_secret
    milli_time = lambda: int(round(time.time() * 1000))
    timestamp = str(milli_time())
    signature = hmac.new(login_secret.encode('utf-8'), timestamp.encode('utf-8'), hashlib.sha256).digest()
    signature = quote(base64.b64encode(signature), 'utf-8')
    url = "sns/getuserinfo_bycode?signature={}&timestamp={}&accessKey={}".format(signature, timestamp, config.login_id)
    result = client.post(url, {
        'tmp_auth_code': code,
        'signature': signature,
        'timestamp': timestamp,
        'accessKey': login_id
    })
    return result.user_info


# ux扩展
def get_config_is_hiding(self, company):
    """
    返回对应公司钉钉配置项中是否"禁止同步隐藏部门的员工"字段
    :return:
    """
    config = self.env['dingtalk.mc.config'].sudo().search([('company_id', '=', company.id)])
    if not config:
        raise UserError("没有为:(%s)配置钉钉参数！" % company.name)
    return config.not_update_emp_in_hidden_dep


def utc_datetime_to_local_timestamp(self, utc_date_time):
    """
    将utc=0的时间转成13位时间戳(本地时间戳：+8H)
    :param utc_date_time:utc=0的时间格式
    :return: local_timestamp:13位本地时间戳
    """
    to_datetime = fields.Datetime.from_string(utc_date_time)
    to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)
    date_str = fields.Datetime.to_string(to_local_datetime)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)


def utc_datetime_to_utc_timestamp(utc_date_time):
    """
    将utc=0的时间转成13位时间戳(utc=0)
    :param utc_date_time:utc=0的时间格式
    :return: utc_timestamp:13位utc=0时间戳
    """
    date_str = fields.Datetime.to_string(utc_date_time)
    date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
    date_stamp = date_stamp * 1000
    return int(date_stamp)


def utc_timestamp_to_utc_datetime(timeNum):
    """
    将13位时间戳utc=0转换为时间格式utc=0
    :param timeNum:
    :return:
    """
    timeStamp = float(timeNum / 1000)
    timeArray = time.gmtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def utc_timestamp_to_local_datetime(self, utc_time_num):
    """
    将13位毫秒时间戳(utc=0)转换为本地时间字符串(+8h)
    :param time_num:
    :return: string datetime
    """
    to_second_timestamp = float(utc_time_num / 1000)  # 毫秒转秒
    to_utc_date_time = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
    to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_date_time)  # 将时间元组转成指定格式日期字符串
    to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
    to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
    to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
    return to_str_datetime


def to_utc_datetime(self, str_datetime):
    """
    将本地时间字符串转换为utc=0时间格式
    :param time_num:
    :return: string datetime
    """
    to_datetime = fields.Datetime.from_string(str_datetime)
    timezone = self._context.get('tz') or self.env.user.tz
    datetime_tz = timezone and pytz.timezone(timezone) or pytz.UTC
    return datetime_tz.localize(to_datetime.replace(tzinfo=None), is_dst=False).astimezone(pytz.UTC).replace(tzinfo=None)