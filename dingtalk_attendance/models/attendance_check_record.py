# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################
from odoo import models, fields, api


class HrAttendanceCheckRecord(models.Model):
    _name = "hr.attendance.check.record"
    _rec_name = 'userId'
    _description = "钉钉打卡记录"

    userId = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    groupId = fields.Many2one(comodel_name='dingtalk.simple.groups', string=u'考勤组', index=True)
    corpId = fields.Char(string='企业ID')
    locationMethod = fields.Selection(string=u'打卡方式', selection=[('MAP', '定位打卡'), ('WIFI', 'WIFI打卡')])
    userCheckTime = fields.Datetime(string="实际打卡时间", help="实际打卡时间,  用户打卡时间的毫秒数")
    userAddress = fields.Char(string='用户打卡地址')
    userLongitude = fields.Char(string='用户打卡经度')
    userLatitude = fields.Char(string='用户打卡纬度')
    outsideRemark = fields.Text(string='打卡备注')

    @api.model
    def get_signs_by_user(self, userid, signtime):
        """
        根据用户和签到日期获取签到信息
        :param userid:
        :param signtime:
        :return:
        """
        start_time = int(signtime) - 1002
        end_time = int(signtime) + 1002
        url, token = self.env['dingding.parameter'].get_parameter_value_and_token('get_user_checkin')
        data = {
            'userid_list': userid,
            'start_time': str(start_time),
            'end_time': str(end_time),
            'cursor': 0,
            'size': 100,
        }
        try:
            result = requests.get(url="{}{}".format(url, token), params=data, timeout=10)
            result = json.loads(result.text)
            # logging.info("获取用户签到结果:{}".format(result))
            if result.get('errcode') == 0:
                r_result = result.get('result')
                for data in r_result.get('page_list'):
                    emp = self.env['hr.employee'].sudo().search([('ding_id', '=', data.get('userid'))], limit=1)
                    self.env['dingtalk.signs.list'].create({
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
        except ReadTimeout:
            logging.info(">>>获取用户签到记录网络连接超时")