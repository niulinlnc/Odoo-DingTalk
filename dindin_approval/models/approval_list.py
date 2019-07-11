# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client

_logger = logging.getLogger(__name__)


class DingTalkApprovalList(models.Model):
    _name = 'dindin.approval.list'
    _description = "审批实例列表"
    _rec_name = 'name'

    name = fields.Char(string='审批实例标题', required=True)
    process_code = fields.Char(string='模板唯一标识')
    process_instance_id = fields.Char(string='审批实例id')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string=u'公司', default=lambda self: self.env.user.company_id.id)

 
    @api.model
    def get_processinstance(self, pid):
        """
        获取单个审批实例详情

        :param process_instance_id: 审批实例id
        :return:
        """
        # try:
        #     client = get_client(self)
        #     result = client.bpms.processinstance_get(pid)
        #     logging.info(">>>获取审批实例详情返回结果{}".format(result))
        #     if result.get('errcode') == 0:
        #         process_instance = result.get('process_instance')
        #         temp = self.env['dindin.approval.template'].sudo().search([('process_code', '=', pcode)])
        #         if temp:
        #             appro = self.env['dindin.approval.control'].sudo().search([('template_id', '=', temp[0].id)])
        #             if appro:
        #                 oa_model = self.env[appro.oa_model_id.model].sudo().search([('process_instance_id', '=', pid)])
        #                 if not oa_model:
        #                     # 获取发起人
        #                     emp = self.env['hr.employee'].sudo().search([('din_id', '=', process_instance.get("originator_userid"))])
        #                     data = {
        #                         'title': process_instance.get('title'),
        #                         'create_date': process_instance.get("create_time"),
        #                         'originator_user_id': emp.id if emp else False,
        #                     }
        #                     # 审批状态
        #                     if process_instance.get("status") == 'NEW':
        #                         data.update({'oa_state': '00'})
        #                     elif process_instance.get("status") == 'RUNNING':
        #                         data.update({'oa_state': '01'})
        #                     else:
        #                         data.update({'oa_state': '02'})

        #     else:
        #         logging.info('>>>获取单个审批实例-失败，原因为:{}'.format(result.get('errmsg')))
        # except Exception as e:
        #     raise UserError(e)
