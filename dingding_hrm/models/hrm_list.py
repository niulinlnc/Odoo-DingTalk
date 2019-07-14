# -*- coding: utf-8 -*-
import json
import logging
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.dingtalk.main import get_client, list_cut

_logger = logging.getLogger(__name__)


class DingDingHrmList(models.Model):
    _name = 'dingding.hrm.list'
    _description = "获取员工花名册"
    _rec_name = 'emp_id'

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门')
    line_ids = fields.One2many(comodel_name='dingding.hrm.list.line', inverse_name='list_is', string=u'信息列表')
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)


class DingDingHrmListline(models.Model):
    _name = 'dingding.hrm.list.line'
    _description = "获取员工花名册明细"
    _rec_name = 'list_is'

    list_is = fields.Many2one(comodel_name='dingding.hrm.list', string=u'获取员工花名册', ondelete='cascade')
    sequence = fields.Integer(string=u'序号')
    group_id = fields.Char(string='字段分组ID')
    value = fields.Char(string='值')
    label = fields.Char(string='参照值')
    field_code = fields.Char(string='字段编码')
    field_name = fields.Char(string='字段名')


class GetDingDingHrmList(models.TransientModel):
    _name = 'dingding.get.hrm.list'
    _description = '获取钉钉员工花名册'

    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='dingding_hrm_list_and_hr_employee_rel',
                               column1='list_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('din_id', '!=', '')])
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_hrm_list(self):
        """
        批量获取员工花名册

        """
        logging.info(">>>获取钉钉员工花名册start")
        din_ids = list()
        for user in self.emp_ids:
            din_ids.append(user.din_id)         
        user_list = list_cut(din_ids, 20)
        for u in user_list:
            self.hrm_list(u)
        logging.info(">>>获取钉钉员工花名册end")
        action = self.env.ref('dingding_hrm.dingding_hrm_list_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def hrm_list(self, userid_list):
        """
        批量获取员工花名册字段信息
        智能人事业务，企业/ISV根据员工id批量访问员工花名册信息

        :param userid_list: 员工id列表
        :param field_filter_list: 需要获取的花名册字段信息
        """
        client = get_client(self)
        if len(userid_list) > 20:
            raise UserError("钉钉仅支持批量查询小于等于20个员工!")
        try:
            result = client.employeerm.list(userid_list, field_filter_list=())
            # logging.info(">>>批量获取员工花名册返回结果{}".format(result))
            if result.get('emp_field_info_v_o'):
                for res in result.get('emp_field_info_v_o'):
                    line_list = list()
                    for field_list in res['field_list']['emp_field_v_o']:
                        line_list.append((0, 0, {
                            'group_id': field_list.get('group_id'),
                            'value': field_list.get('value'),
                            'label': field_list.get('label'),
                            'field_code': field_list.get('field_code'),
                            'field_name': field_list.get('field_name'),
                        }))
                    emp = self.env['hr.employee'].search([('din_id', '=', res.get('userid'))])
                    if emp:
                        hrm = self.env['dingding.hrm.list'].search([('emp_id', '=', emp[0].id)])
                        if hrm:
                            hrm.write({
                                'department_id': emp[0].department_id.id,
                                'line_ids': line_list
                            })
                        else:
                            self.env['dingding.hrm.list'].sudo().create({
                                'emp_id': emp[0].id,
                                'department_id': emp[0].department_id.id,
                                'line_ids': line_list
                            })
        except Exception as e:
            raise UserError(e)
        
