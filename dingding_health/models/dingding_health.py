# -*- coding: utf-8 -*-
import datetime
# from datetime import datetime
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models, tools
from odoo.modules import get_module_resource
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client
import base64

_logger = logging.getLogger(__name__)


class DingDingHealth(models.Model):
    _name = 'dingding.health'
    _description = '钉钉运动'
    _rec_name = 'emp_id'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    active = fields.Boolean(string=u'active', default=True)
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
    department_id = fields.Many2one('hr.department', string=u'部门', required=True)
    emp_id = fields.Many2one('hr.employee', string=u'员工', required=True)
    health_date = fields.Date(string=u'日期', required=True)
    health_count = fields.Integer(string=u'运动步数')
    image = fields.Binary("照片", default=_default_image, attachment=True)
    image_medium = fields.Binary("Medium-sized photo", attachment=True)
    image_small = fields.Binary("Small-sized photo", attachment=True)

    @api.model
    def create(self, values):
        tools.image_resize_images(values)
        return super(DingDingHealth, self).create(values)

    @api.multi
    def write(self, values):
        tools.image_resize_images(values)
        return super(DingDingHealth, self).write(values)


class GetDingDingHealthList(models.TransientModel):
    _name = 'dingding.get.health.list'
    _description = '获取钉钉员工运动数据'

    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_health_list_and_hr_employee_rel',
                               column1='list_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('din_id', '!=', '')])
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_health_list(self):
        """
        批量查询多个用户的钉钉运动步数

        :param userids: 员工userid列表，最多传50个
        :param stat_date: 时间
        """
        logging.info(">>>获取钉钉员工运动数据start")
        if len(self.emp_ids) > 50:
            raise UserError("钉钉仅支持批量查询小于等于50个员工!")

        userid_list = list()
        for user in self.emp_ids:
            userid_list.append(user.din_id)
        userids = userid_list
        today = datetime.date.today()
        formatted_today = today.strftime('%Y%m%d')
        stat_dates = formatted_today
        try:
            client = get_client(self)
            result = client.health.stepinfo_listbyuserid(userids, stat_dates)
            logging.info(">>>批量获取员工运动数据返回结果{}".format(result))
            basic_step_info_vo = result['stepinfo_list']['basic_step_info_vo']
            if basic_step_info_vo:
                for stepinfo_list in basic_step_info_vo:
                    data = {
                        'health_count': stepinfo_list['step_count'],
                        'health_date': datetime.datetime.strptime(str(stepinfo_list['stat_date']), "%Y%m%d"),
                    }
                    emp = self.env['hr.employee'].sudo().search([('din_id', '=', stepinfo_list.get('userid'))])
                    if emp:
                        data.update({'emp_id': emp.id, 'department_id': emp.department_id.id})
                        partner = self.env['dingding.health'].sudo().search([('emp_id', '=', emp.id)])
                        if partner:
                            partner.sudo().write(data)
                        else:
                            self.env['dingding.health'].sudo().create(data)
            else:
                raise UserError('未开通钉钉运动')
        except Exception as e:
            raise UserError(e)

        logging.info(">>>获取钉钉员工花名册end")
        action = self.env.ref('dingding_health.dingding_health_action')
        action_dict = action.read()[0]
        return action_dict