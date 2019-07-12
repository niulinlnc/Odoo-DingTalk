# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time

import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client, stamp_to_time

_logger = logging.getLogger(__name__)


class DinDinDepartmentSign(models.Model):
    _name = 'dindin.department.signs'
    _description = "部门签到记录"
    _rec_name = 'department_id'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', required=True)
    is_root = fields.Boolean(string=u'根部门', default=False)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True)
    line_ids = fields.One2many(comodel_name='dindin.department.signs.line', inverse_name='signs_id', string=u'列表')

    @api.multi
    def find_department_sign(self):
        """
        获得签到数据

        :param department_id: 部门id（1 表示根部门）
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param offset: 偏移量
        :param size: 分页大小
        :param order_asc: 是否正序排列
        :return:
        """
        logging.info(">>>获取部门用户签到记录...")
        for res in self:
            res.line_ids = False
            start_time = res.start_time
            end_time = res.end_time
            if res.is_root:
                department_id = '1'
            else:
                department_id = res.department_id.din_id
            try:
                client = get_client(self)
                result = client.checkin.record(department_id, start_time, end_time, offset=0, size=100, order_asc=True)
                logging.info(">>>获得签到数据返回结果{}".format(result))
                line_list = list()
                for data in result:
                    emp = self.env['hr.employee'].sudo().search([('din_id', '=', data.get('userId'))])
                    timestamp = stamp_to_time(data.get('timestamp'))
                    line_list.append({
                        'emp_id': emp.id if emp else False,
                        'timestamp': timestamp,
                        'place': data.get('place'),
                        'detailPlace': data.get('detailPlace'),
                        'remark': data.get('remark'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'avatar': data.get('avatar'),
                    })
                res.line_ids = line_list
            except Exception as e:
                raise UserError(e)

class DinDinDepartmentSignLine(models.Model):
    _name = 'dindin.department.signs.line'
    _description = "部门签到记录列表"
    _rec_name = 'emp_id'

    signs_id = fields.Many2one(comodel_name='dindin.department.signs', string=u'签到', ondelete='cascade')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    timestamp = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detailPlace = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    latitude = fields.Char(string='纬度')
    longitude = fields.Char(string='经度')
    avatar = fields.Char(string='头像url')
