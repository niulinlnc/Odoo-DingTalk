# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.dingtalk.main import get_client

_logger = logging.getLogger(__name__)


class DingTalkApprovalList(models.Model):
    _name = 'dindin.approval.list'
    _description = "审批实例列表"
    _rec_name = 'name'

    name = fields.Char(string='审批实例标题', required=True)
    process_code = fields.Char(string='模板唯一标识')
    process_instance_id = fields.Char(string='审批实例id')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_processinstance(self, pid):
        """
        获取单个审批实例详情

        :param process_instance_id: 审批实例id
        :return:
        """
