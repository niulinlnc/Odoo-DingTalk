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
import time
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

WEEKDAY = [
    ('1', '周一'),
    ('2', '周二'),
    ('3', '周三'),
    ('4', '周四'),
    ('5', '周五'),
    ('6', '周六'),
    ('7', '周日')
]


class HrAttendancePlan(models.Model):
    _name = "hr.attendance.plan"
    _rec_name = 'emp_id'
    _description = "排班列表"

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工')
    group_id = fields.Many2one(comodel_name='hr.attendance.group', string=u'考勤组')
    class_id = fields.Many2one(comodel_name='hr.attendance.class', string=u'班次')
    work_date = fields.Date(string=u'工作日')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
    approve_id = fields.Char(string='审批id', help="没有的话表示没有审批单")
    class_setting_id = fields.Char(string='班次配置id', help="没有的话表示使用全局班次配置")
    plan_check_time = fields.Datetime(string=u'打卡时间', help="数据库中存储为不含时区的时间UTC=0")
    begin_check_time = fields.Datetime(string=u'开始打卡时间')
    end_check_time = fields.Datetime(string=u'结束打卡时间')
    week_name = fields.Selection(string=u'星期', selection=WEEKDAY, default='1')


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

    @api.multi
    def compute_attendance_plan(self):
        """
        开始排班计算
        :return:
        """
        # self.ensure_one()
        # self.start_pull_dingding_plan_lists(self.start_date, self.stop_date)
        # action = self.env.ref('og_attendance_count.hr_attendance_plan_action')
        # action_dict = action.read()[0]
        emp_list = self.emp_ids
        start_date = self.start_date
        stop_date = self.stop_date

        for emp in emp_list:
            # 删除已存在的该员工考勤日报
            self.env['hr.attendance.plan'].sudo().search(
                [('emp_id', '=', emp.id), ('plan_check_time', '>=', start_date), ('plan_check_time', '<=', stop_date)]).unlink()
            for work_date in self.date_range(start_date, stop_date):
                plan = self.get_emp_attendance_plan(emp.id, work_date)
                if plan:
                    self.env['hr.attendance.plan'].sudo().create(plan)

        action = self.env.ref('og_attendance_count.hr_attendance_plan_action')
        action_dict = action.read()[0]
        return action_dict

    @api.multi
    def get_emp_attendance_plan(self, emp_id, work_date):
        """
        生成排班表
        (%s + interval '1' second  * t.check_time)
        """
        self._cr.execute(
            """SELECT %s AS work_date, e.group_id AS group_id, cl.class_id, e.emp_id, cl.week_name,
                TO_TIMESTAMP(%s + t.check_time) AT TIME ZONE 'utc' AS plan_check_time, t.check_type
                FROM (hr_attendance_group g
                INNER JOIN hr_attendance_group_and_employee_rel_01 e ON g.id = e.group_id)
                INNER JOIN ((hr_attendance_class c INNER JOIN hr_attendance_class_time t ON c.id = t.class_id)
                INNER JOIN hr_attendance_group_class_list cl ON c.id = cl.class_id) ON g.id = cl.attendance_group_id
                WHERE e.emp_id = %s AND cl.week_name = CAST(EXTRACT(ISODOW FROM TIMESTAMP %s) AS VARCHAR)
                """, (work_date, time.mktime(work_date.timetuple()), emp_id, work_date))
        res = self._cr.dictfetchall()
        if len(res) > 0:
            return res

    @api.model
    def date_range(self, start_date, end_date):
        """
        生成一个 起始时间 到 结束时间 的一个日期格式列表
        TODO 起始时间和结束时间相差过大时，考虑使用 yield
        :param start_date:
        :param end_date:
        :return:
        """
        date_tmp = [start_date, ]
        while date_tmp[-1] < end_date:
            date_tmp.append(date_tmp[-1] + timedelta(days=1))
        return date_tmp

    @api.multi
    def clear_hr_attendance_plan(self):
        """
        清除已下载的所有钉钉排班记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
                delete from hr_attendance_plan
            """)
