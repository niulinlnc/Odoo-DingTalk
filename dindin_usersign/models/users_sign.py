# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.dingtalk.main import get_client, stamp_to_time

_logger = logging.getLogger(__name__)


class DinDinUsersSign(models.Model):
    _name = 'dindin.users.signs'
    _description = "用户签到记录"
    _rec_name = 'start_time'

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='users_sign_and_employee_to_rel',
                               column1='sign_id', column2='emp_id', string=u'员工', required=True)
    start_time = fields.Datetime(string=u'开始时间', required=True)
    end_time = fields.Datetime(string=u'结束时间', required=True)
    line_ids = fields.One2many(comodel_name='dindin.users.signs.line', inverse_name='signs_id', string=u'列表')

    @api.multi
    def find_users_sign(self):
        """
        获取多个用户的签到记录 (如果是取1个人的数据，时间范围最大到10天，如果是取多个人的数据，时间范围最大1天。)

        :param userid_list: 需要查询的用户列表
        :param start_time: 起始时间
        :param end_time: 截止时间
        :param offset: 偏移量
        :param size: 分页大小
        :return:
        """
        client = get_client(self)
        logging.info(">>>获取用户签到记录...")
        for res in self:
            res.line_ids = False
            start_time = res.start_time
            end_time = res.end_time
            userid_list = list()
            for user in self.emp_ids:
                userid_list.append(user.din_id)
            cursor = 0
            size = 100
            try:
                result = client.checkin.record_get(userid_list, start_time, end_time, cursor=cursor, size=size)
                logging.info(">>>获取多个用户的签到记录结果{}".format(result))

                line_list = list()
                r_result = result.get('result')
                for data in r_result['page_list']['checkin_record_vo']:
                    emp = self.env['hr.employee'].sudo().search([('din_id', '=', data.get('userid'))])
                    line_list.append({
                        'emp_id': emp.id if emp else False,
                        'checkin_time': stamp_to_time(data.get('checkin_time')),
                        'place': data.get('place'),
                        'detail_place': data.get('detail_place'),
                        'remark': data.get('remark'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                    })
                res.line_ids = line_list
            except Exception as e:
                raise UserError(e)

class DinDinUsersSignLine(models.Model):
    _name = 'dindin.users.signs.line'
    _description = "用户签到记录列表"
    _rec_name = 'emp_id'

    signs_id = fields.Many2one(comodel_name='dindin.users.signs', string=u'签到', ondelete='cascade')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    checkin_time = fields.Datetime(string=u'签到时间')
    place = fields.Char(string='签到地址')
    detail_place = fields.Char(string='签到详细地址')
    remark = fields.Char(string='签到备注')
    latitude = fields.Char(string='纬度')
    longitude = fields.Char(string='经度')
    visit_user = fields.Char(string='拜访对象')
