# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    health_state = fields.Selection(string=u'运动状态', selection=[('open', '开启'), ('close', '关闭')], default='open')
    dd_step_count = fields.Integer(string=u'运动步数', compute='get_user_today_health')

    @api.multi
    def get_user_today_health(self):
        """
        获取员工在今日的步数
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_user_health_info'):
            for res in self:
                if res.din_id and res.active:
                    today = datetime.date.today()
                    formatted_today = today.strftime('%Y%m%d')
                    _type = 0
                    object_id = res.din_id
                    stat_dates = formatted_today
                    try:
                        client = get_client(self)
                        result = client.health.stepinfo_list(_type, object_id, stat_dates)
                        logging.info(">>>获取员工在今日的步数返回结果:{}".format(result))
                        if result['stepinfo_list']:
                            for stepinfo_list in result['stepinfo_list']['basic_step_info_vo']:
                                res.update({'dd_step_count': stepinfo_list['step_count']})
                        else:
                            res.update({'dd_step_count': 0})
                    except Exception as e:
                        raise UserError(e)
                else:
                    res.update({'dd_step_count': 0})

    @api.multi
    def get_user_health_state(self):
        """
        获取员工钉钉运动开启状态
        :param userid: 用户id
        """
        for res in self:
            if res.din_id and res.active:
                userid = res.din_id
                try:
                    client = get_client(self)
                    result = client.health.stepinfo_getuserstatus(userid)
                    logging.info(">>>获取员工在今日的步数返回结果:{}".format(result))
                    if result:
                        res.update({'health_state': 'open'})
                    else:
                        res.update({'health_state': 'close'})
                except Exception as e:
                        raise UserError(e)

    @api.model
    def get_time_stamp(self, time_num):
        """
        将13位时间戳转换为时间
        :param time_num:
        :return:
        """
        time_stamp = float(time_num / 1000) 
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    # 把时间转成时间戳形式
    @api.model
    def date_to_stamp(self, date):
        """
        将时间转成13位时间戳
        :param time_num:
        :return:
        """
        date_str = fields.Datetime.to_string(date)
        date_stamp = time.mktime(time.strptime(date_str, "%Y-%m-%d %H:%M:%S"))
        date_stamp = date_stamp * 1000
        return date_stamp
