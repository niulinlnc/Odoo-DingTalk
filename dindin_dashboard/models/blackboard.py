# -*- coding: utf-8 -*-
import logging

import requests
from odoo import api, models
from odoo.addons.ali_dindin.dingtalk.main import client

_logger = logging.getLogger(__name__)


class DinDinBlackboard(models.TransientModel):
    _description = '获取公告信息'
    _name = 'dindin.blackboard'

    @api.model
    def get_blackboard_by_user(self):
        """
        根据当前用户获取公告信息
        :return:
        """

        uid = self.env.user.id
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', uid)])
        if emp:
            try:
                result = client.blackboard.listtopten(emp.din_id)
                logging.info(">>>获取公告返回结果:%s", result)
                if result.get('errcode') == 0:
                    line_list = list()
                    for line in result.get('blackboard_list'):
                        line_list.append(line)
                    return {'state': True, 'data': line_list, 'msg': '', 'number': len(line_list)}
                else:
                    return {'state': False, 'msg': '获取公告失败,详情为:{}'.format(result.get('errmsg'))}
            except Exception as e:
                return {'state': False, 'msg': "获取用户'{}'的公告失败，原因：{}".format(self.env.user.name, e)}
        else:
            return {'state': False, 'msg': '当前登录用户不存在关联员工!'}

    @api.model
    def get_update_information(self):
        """
        获取更新公告信息
        :return:
        """
        try:
            url = self.env['ali.dindin.system.conf'].search(
                [('key', '=', 'get_manage_version_info')]).value
            result = requests.get(url=url, timeout=2)
            return result.text
        except Exception as e:
            return {"获取更新公告信息失败!,详情:%s", e}
