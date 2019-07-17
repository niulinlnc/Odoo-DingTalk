# -*- coding:utf-8 -*-
import logging

from odoo import api, fields, models, tools
from odoo.addons.ali_dindin.dingtalk.main import client
from odoo.exceptions import UserError
from ..models.hrm_dimission_list import GetDingDingHrmDimissionList

_logger = logging.getLogger(__name__)


class HrEmployeeReport(models.Model):
    _name = 'hr_employee_dingding_report'
    _auto = False
    _description = u"员工入职状态"

    id = fields.Integer(string='序号')
    company_id = fields.Many2one(comodel_name='res.company', string='公司')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='员工')
    department_id = fields.Many2one(comodel_name='hr.department', string='部门')
    work_status = fields.Selection(string='入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')])

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_employee_dingding_report')
        self._cr.execute("""
            CREATE VIEW hr_employee_dingding_report AS (
                SELECT
                    emp.id as id,
                    emp.company_id as company_id,
                    emp.id as employee_id,
                    emp.department_id as department_id,
                    emp.work_status as work_status
                FROM
                    hr_employee emp
        )""")


class GetHrEmployeeStauts(models.TransientModel):
    _name = 'get.hrm.employee.state'
    _description = '查询员工入职状态'

    @api.multi
    def get_hrm_employee_state(self):
        self.ensure_one()
        # 更新待入职员工
        # self.get_query_preentry()
        # 更新在职员工
        self.get_queryonjob()
        # 更新离职员工
        self.get_querydimission()

    @api.model
    def get_query_preentry(self):
        """
        更新待入职员工
        :return:
        """
        
        offset = 0
        size = 50
        while True:
            try:
                result = client.employeerm.querypreentry(offset=offset, size=size)
                logging.info(">>>查询待入职员工列表返回结果%s", result)
                # if result['data_list']['string']:
                #     pre_entry_list = result['data_list']['string']
                #     for data_list in pre_entry_list:
                #         sql = """UPDATE hr_employee SET work_status='1' WHERE din_id='%s'""", (data_list,)
                #         self._cr.execute(sql)
                #     if 'next_cursor' in result['data_list']:
                #         offset = result['data_list']['next_cursor']
                #     else:
                #         break
                # else:
                #     raise UserError(_("更新失败,原因:{}\r").format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        return True

    @api.model
    def get_queryonjob(self):
        """
        更新在职员工,在职员工子状态筛选: 2，试用期；3，正式；5，待离职；-1，无状态
        :return:
        """
        
        status_arr = ['2', '3', '5', '-1']
        for arr in status_arr:
            offset = 0
            size = 20
            while True:
                try:
                    result = client.employeerm.queryonjob(status_list=arr, offset=offset, size=size)
                    logging.info(">>>更新在职员工子状态[%s]返回结果%s", arr, result)
                    if result['data_list']:
                        result_list = result['data_list']['string']
                        for data_list in result_list:
                            sql = """UPDATE hr_employee SET work_status='2',office_status={} WHERE din_id='{}'""".format(arr, data_list)
                            self._cr.execute(sql)
                        if 'next_cursor' in result:
                            offset = result['next_cursor']
                        else:
                            break
                    else:
                        break
                except Exception as e:
                    raise UserError(e)
        return True

    @api.model
    def get_querydimission(self):
        """
        更新离职员工
        :return:
        """
        
        offset = 0
        size = 50
        while True:
            try:
                result = client.employeerm.querydimission(offset=offset, size=size)
                logging.info(">>>获取离职员工列表返回结果%s", result)
                if result['data_list']:
                    result_list = result['data_list']['string']
                    GetDingDingHrmDimissionList.dimission_list(self, result_list)
                    for data_list in result_list:
                        sql = """UPDATE hr_employee SET work_status='3' WHERE din_id='{}'""".format(data_list)
                        self._cr.execute(sql)
                    if 'next_cursor' in result:
                        offset = result['next_cursor']
                    else:
                        break
                else:
                    break
            except Exception as e:
                raise UserError(e)
        return True
