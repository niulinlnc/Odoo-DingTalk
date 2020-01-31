# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2019 SuXueFeng GNU
###################################################################################

import logging
from ast import literal_eval
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.dingtalk_base.tools import dingtalk_api

_logger = logging.getLogger(__name__)


class DingTalkReportListTran(models.TransientModel):
    _name = 'dingtalk.report.list.tran'
    _description = "获取钉钉日志"

    category_id = fields.Many2one(comodel_name='dingtalk.report.category', string=u'系统日志类型')
    report_id = fields.Many2one(comodel_name='dingtalk.report.template', string=u'钉钉日志模板', required=True)
    start_time = fields.Date(string=u'开始时间', required=True)
    end_time = fields.Date(string=u'结束时间', required=True, default=fields.Datetime.now())
    emp_ids = fields.Many2many(comodel_name='hr.employee', string=u'员工', domain="[('ding_id', '!=', False)]")

    def get_user_report_list(self):
        """
        获取用户日志
        :return:
        """
        self.ensure_one()
        if not self.report_id.category_id:
            raise UserError(_("请先在钉钉日志模板中关联系统日志类型!"))
        user_list = list()
        if self.emp_ids:
            for emp in self.emp_ids:
                user_list.append(emp.ding_id)
        else:
            user_list.append('')
        date_list = dingtalk_api.day_cut(self.start_time, self.end_time, 180)
        for u in user_list:
            for date_arr in date_list:
                cursor = 0
                size = 20
                report_dict = self._get_report_dicts()
                while True:
                    try:
                        result = dingtalk_api.get_client(self).post('topapi/report/list', {
                            'start_time': dingtalk_api.datetime_to_local_stamp(self, date_arr[0]),
                            'end_time': dingtalk_api.datetime_to_local_stamp(self, date_arr[1]),
                            'template_name': self.report_id.name,
                            'userid': u,
                            'cursor': cursor,
                            'size': size
                        })
                    except Exception as e:
                        raise UserError(e)
                    if result.get('errcode') == 0:
                        result = result.get('result')
                        data_list = result.get('data_list')
                        for data in data_list:
                            # 封装字段数据
                            report_data = dict()
                            for contents in data.get('contents'):
                                report_data.update({report_dict.get(contents.get('key')): contents.get('value')})
                            # 读取创建人
                            employee = self.env['hr.employee'].search(
                                [('ding_id', '=', data.get('creator_id'))], limit=1)
                            report_data.update({
                                'name': data.get('template_name'),
                                'category_id': self.report_id.category_id.id or False,
                                'employee_id': employee.id or False,
                                'report_time': dingtalk_api.timestamp_to_utc_date(data.get('create_time')) or fields.datetime.now(),
                                'report_id': data.get('report_id'),
                            })
                            # 存储日志图片链接
                            if data.get('images'):
                                report_data.update({
                                    'image1_url': literal_eval(data['images'][0]).get('image'),
                                })
                                image_data = list()
                                for image in data.get('images'):
                                    image = literal_eval(image)
                                    image_data.append((0, 0, {
                                        'category_id': self.report_id.category_id.id,
                                        'report_image_url': image.get('image'),
                                        'dingtalk_report_id': data.get('report_id'),
                                        'report_time': dingtalk_api.timestamp_to_utc_date(data.get('create_time')),
                                    }))
                                report_data.update({'image_ids': image_data})
                            reports = self.env['dingtalk.report.report'].search(
                                [('report_id', '=', data.get('report_id'))])
                            if not reports:
                                self.env['dingtalk.report.report'].create(report_data)
                        # 是否还有下一页
                        if result.get('has_more'):
                            cursor = result.get('next_cursor')
                        else:
                            break
                    else:
                        raise UserError('获取用户日志失败，详情为:{}'.format(result.get('errmsg')))
        return {'type': 'ir.actions.act_window_close'}

    def _get_report_dicts(self):
        """
        将日志字段转换为dict
        :return:
        """
        report_model = self.env['ir.model'].sudo().search([('model', '=', 'dingtalk.report.report')])
        data_dict = dict()
        for field in report_model.field_id:
            if field.name[:4] != 'has_':
                data_dict.update({field.field_description: field.name})
        return data_dict

    @api.onchange('category_id')
    def onchange_category_id(self):
        '''选择系统日志类型自动填入已关联的钉钉日志模板（默认载入第一个）'''
        if self.category_id:
            tmp = self.env['dingtalk.report.template'].sudo().search(
                [('category_id', '=', self.category_id.id)], limit=1).id
            if tmp:
                self.report_id = tmp
            else:
                self.report_id = False
