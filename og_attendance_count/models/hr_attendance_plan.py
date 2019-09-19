# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 SuXueFeng
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import logging
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAttendancePlan(models.Model):
    _name = "hr.attendance.plan"
    _rec_name = 'emp_id'
    _description = "排班列表"

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    group_id = fields.Many2one(comodel_name='hr.attendance.group', string=u'考勤组')
    class_id = fields.Many2one(comodel_name='hr.attendance.class', string=u'班次')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
    approve_id = fields.Char(string='审批id', help="没有的话表示没有审批单")
    class_setting_id = fields.Char(string='班次配置id', help="没有的话表示使用全局班次配置")
    plan_check_time = fields.Datetime(string=u'打卡时间', help="数据库中存储为不含时区的时间UTC=0")
    begin_check_time = fields.Datetime(string=u'开始打卡时间')
    end_check_time = fields.Datetime(string=u'结束打卡时间')


class HrAttendancePlanTran(models.TransientModel):
    _name = "hr.attendance.plan.tran"
    _description = "排班列表查询与计算"

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_attendance_plan_tran_and_hr_employee_rel',
                               column1='plan_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        """
        获取全部钉钉员工
        :return:
        """
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.model
    def compute_attendance_plan(self, emp_list, start_date, end_date):
        """
        排班计算
        :return:
        """
        # self.ensure_one()
        # self.start_pull_dingding_plan_lists(self.start_date, self.stop_date)
        # action = self.env.ref('og_attendance_count.hr_attendance_plan_action')
        # action_dict = action.read()[0]

        for emp in emp_list:
            # 删除已存在的该员工考勤日报
            self.env['hr.attendance.plan'].sudo().search(
                [('emp_id', '=', emp.id), ('plan_check_time', '>=', start_date), ('plan_check_time', '<=', end_date)]).unlink()

            att_group = self.env['hr.employee'].search([('id', '=', emp.id)])
            att_class = self.env['hr.attendance.class'].sudo().search([('id', '=', att_group.monday_class_id.id)])
            plan_list = list()
            for work_date in self.date_range(start_date, end_date):
                if datetime.isoweekday(work_date) == '1':
                    class_id = att_group.monday_class_id.id
                    att_class = self.env['hr.attendance.class'].sudo().search([('id', '=', class_id)])


    @api.multi
    def clear_hr_attendance_plan(self):
        """
        清除已下载的所有钉钉排班记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_attendance_plan
        """)
