# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client

_logger = logging.getLogger(__name__)


class DinDinSignList(models.Model):
    _name = 'dindin.signs.list'
    _description = "签到记录列表"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    checkin_time = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detail_place = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    latitude = fields.Char(string='纬度')
    longitude = fields.Char(string='经度')
    visit_user = fields.Char(string='拜访对象')

    @api.model
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime

    @api.model
    def get_signs_by_user(self, userid, signtime):
        """
        获取多个用户的签到记录 (如果是取1个人的数据，时间范围最大到10天，如果是取多个人的数据，时间范围最大1天。)

        :param userid_list: 需要查询的用户列表
        :param start_time: 起始时间
        :param end_time: 截止时间
        :param offset: 偏移量
        :param size: 分页大小
        :return:
        """
        start_time = int(signtime) - 1002
        end_time = int(signtime) + 1002

        userid_list = userid
        start_time = str(start_time)
        end_time = str(end_time)
        cursor = 0
        size = 100

        try:
            client = get_client(self)
            result = client.checkin.record_get(userid_list, start_time, end_time, offset=cursor, size=size)
            logging.info(">>>获取多个用户的签到记录结果{}".format(result))
            if result.get('errcode') == 0:
                r_result = result.get('result')
                for data in r_result.get('page_list'):
                    emp = self.env['hr.employee'].sudo().search([('din_id', '=', data.get('userid'))])
                    self.env['dindin.signs.list'].create({
                        'emp_id': emp.id if emp else False,
                        'checkin_time': self.get_time_stamp(data.get('checkin_time')),
                        'place': data.get('place'),
                        'visit_user': data.get('visit_user'),
                        'detail_place': data.get('detail_place'),
                        'remark': data.get('remark'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                    })
            else:
                logging.info(">>>获取用户签到记录失败,原因:{}".format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)
