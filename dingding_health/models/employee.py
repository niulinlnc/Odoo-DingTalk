# -*- coding: utf-8 -*-
import datetime
import logging

from odoo import api, fields, models
from odoo.addons.ali_dindin.dingtalk.main import get_client

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    health_state = fields.Selection(string='运动状态', selection=[
                                    ('open', '开启'), ('close', '关闭')], default='open')
    dd_step_count = fields.Integer(
        string='运动步数', compute='_compute_get_user_today_health')

    @api.multi
    def _compute_get_user_today_health(self):
        """
        获取员工在今日的步数
        :return:
        """
        if self.env['ir.config_parameter'].sudo().get_param('dingding_health.auto_user_health_info'):
            client = get_client(self)
            for res in self:
                if res.din_id and res.active:
                    today = datetime.date.today()
                    formatted_today = today.strftime('%Y%m%d')
                    _type = 0
                    object_id = res.din_id
                    stat_dates = formatted_today
                    try:
                        result = client.health.stepinfo_list(
                            _type, object_id, stat_dates)
                        logging.info(">>>获取员工在今日的步数返回结果:%s", result)
                        if result['stepinfo_list']:
                            for stepinfo_list in result['stepinfo_list']['basic_step_info_vo']:
                                res.update(
                                    {'dd_step_count': stepinfo_list['step_count']})
                        else:
                            res.update({'dd_step_count': 0})
                    except Exception as e:
                        # raise UserError(e)
                        res.message_post(body="获取失败，原因：{}".format(
                            e), message_type='notification')
                else:
                    res.update({'dd_step_count': 0})

    @api.multi
    def get_user_health_state(self):
        """
        获取选定范围员工钉钉运动开启状态
        :param userid: 用户id
        """
        for res in self:
            if res.din_id and res.active:
                userid = res.din_id
                result = self.get_health_state(userid)
                if result:
                    res.update({'health_state': 'open'})
                else:
                    res.update({'health_state': 'close'})

    @api.multi
    def get_all_user_health_state(self):
        """
        获取所有员工钉钉运动开启状态
        :param userid: 用户id
        """
        din_ids = self.env['hr.employee'].search_read(
            [('din_id', '!=', '')], fields=['din_id'])
        for emp in din_ids:
            user_id = emp.get('din_id')
            result = self.get_health_state(user_id)
            emp = self.env['hr.employee'].search([('din_id', '=', user_id)])
            if result:
                emp.update({'health_state': 'open'})
            else:
                emp.update({'health_state': 'close'})

    @api.model
    def get_health_state(self, userid):
        """
        获取员工钉钉运动开启状态
        :param userid: 用户id
        """
        client = get_client(self)
        try:
            result = client.health.stepinfo_getuserstatus(userid)
            logging.info(">>>获取id:%s钉钉运动开启状态返回结果:%s", userid, result)
            return result
        except Exception as e:
            logging.info(">>>获取失败，原因：%s", e)
