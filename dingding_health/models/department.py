# -*- coding: utf-8 -*-
import datetime
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.dingtalk.main import get_client

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dd_step_count = fields.Integer(string=u'运动步数', compute='get_dept_today_health')

    @api.multi
    def get_dept_today_health(self):
        """
        获取部门在今日的步数
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_dept_health_info'):
            client = get_client(self)
            for res in self:
                if res.din_id:
                    today = datetime.date.today()
                    formatted_today = today.strftime('%Y%m%d')
                    _type = 1
                    object_id = res.din_id
                    stat_dates = formatted_today
                    try:
                        result = client.health.stepinfo_list(_type, object_id, stat_dates)
                        logging.info(">>>获取部门在今日的步数返回结果:{}".format(result))
                        if result['stepinfo_list']:
                            for stepinfo_list in result['stepinfo_list']['basic_step_info_vo']:
                                res.update({'dd_step_count': stepinfo_list['step_count']})
                        else:
                            res.update({'dd_step_count': 0})
                    except Exception as e:
                        raise UserError(e)
                else:
                    res.update({'dd_step_count': 0})
