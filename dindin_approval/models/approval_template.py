# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.addons.ali_dindin.dingtalk.main import get_client
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DinDinApprovalTemplate(models.Model):
    _name = 'dindin.approval.template'
    _description = "审批模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    process_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_template(self):
        """获取审批模板"""
        logging.info(">>>开始获取审批模板...")
        client = get_client(self)
        try:
            result = client.bpms.process_listbyuserid(userid='')
            logging.info(">>>获取审批模板返回结果%s", result)
            d_res = result.get('process_list')
            for process in d_res.get('process_top_vo'):
                data = {
                    'name': process.get('name'),
                    'icon_url': process.get('icon_url'),
                    'process_code': process.get('process_code'),
                    'url': process.get('url'),
                }
                template = self.env['dindin.approval.template'].search(
                    [('process_code', '=', process.get('process_code'))])
                if template:
                    template.write(data)
                else:
                    self.env['dindin.approval.template'].create(data)
        except Exception as e:
            raise UserError(e)
        logging.info(">>>获取审批模板结束...")

    @api.model
    def get_get_template_number_by_user(self):
        """
        根据当前用户获取该用户的待审批数量
        :return:
        """
        emp = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.din_id:
            try:
                client = get_client(self)
                result = client.bpms.dingtalk_oapi_process_gettodonum(
                    emp.din_id)
                logging.info(">>>获取待审批数量返回结果%s", result)
                if result.get('errcode') == 0:
                    return {'state': True, 'number': result.get('count')}
                else:
                    return {'state': False, 'number': 0, 'msg': result.get('errmsg')}
            except Exception as e:
                raise UserError(e)
        else:
            return {'state': False, 'number': 0, 'msg': 'None'}

    # TODO 需要进一步完善获取单个实例后写入到odoo对应的单据中
    @api.model
    def get_processinstance(self, pid, pcode):
        """
        获取单个审批实例详情
        :param pid:
        :param pcode:
        :return:
        """
        client = get_client(self)
        try:
            result = client.bpms.processinstance_get(pid)
            logging.info(">>>获取审批实例详情返回结果%s", result)
            if result.get('errcode') == 0:
                process_instance = result.get('process_instance')
                temp = self.env['dindin.approval.template'].sudo().search(
                    [('process_code', '=', pcode)])
                if temp:
                    appro = self.env['dindin.approval.control'].sudo().search(
                        [('template_id', '=', temp[0].id)])
                    if appro:
                        oa_model = self.env[appro.oa_model_id.model].sudo().search(
                            [('process_instance_id', '=', pid)])
                        if not oa_model:
                            # 获取发起人
                            emp = self.env['hr.employee'].sudo().search(
                                [('din_id', '=', process_instance.get("originator_userid"))])
                            data = {
                                'title': process_instance.get('title'),
                                'create_date': process_instance.get("create_time"),
                                'originator_user_id': emp.id if emp else False,
                            }
                            # 审批状态
                            if process_instance.get("status") == 'NEW':
                                data.update({'oa_state': '00'})
                            elif process_instance.get("status") == 'RUNNING':
                                data.update({'oa_state': '01'})
                            else:
                                data.update({'oa_state': '02'})

            else:
                logging.info(
                    '>>>获取单个审批实例-失败，原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)
