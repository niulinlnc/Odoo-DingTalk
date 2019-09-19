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
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# 拓展员工
class HrEmployee2(models.Model):
    _inherit = 'hr.employee'

    attendance_group_id = fields.Many2one(comodel_name='hr.attendance.group', string=u'考勤组')


class HrAttendanceGroup(models.Model):
    _name = 'hr.attendance.group'
    _rec_name = 'group_name'
    _description = '考勤组'

    ATTENDANCETYPE = [
        ('FIXED', '固定排班'),
        ('TURN', '轮班排班'),
        ('NONE', '无班次')
    ]

    group_name = fields.Char(string='考勤组名称', index=True)
    dept_name_list = fields.Many2many('hr.department', string=u'参与考勤部门')
    emp_ids = fields.One2many(comodel_name='hr.employee', inverse_name='attendance_group_id', string=u'成员列表')
    member_count = fields.Integer(string=u'成员人数')
    no_attendance_emp_ids = fields.Many2many(
        string=u'无需考勤人员',
        comodel_name='hr.employee',
        relation='hr_attendance_group_hr_employee_rel',
        column1='group_id',
        column2='emp_id',
    )
    attendance_type = fields.Selection(string=u'考勤类型', selection=ATTENDANCETYPE, default='NONE')
    manager_list = fields.Many2many('hr.employee', string=u'考勤组负责人', index=True)
    week_classes_list = fields.Char(string='班次时间展示')
    is_default = fields.Boolean(string=u'是否默认考勤组')
    default_class_id = fields.Char(string='默认班次ID')

    # 固定班制
    work_day_list = fields.One2many(comodel_name='hr.attendance.group.class.list', inverse_name='attendance_group_id', string='周班次列表')
    # monday_class_id = fields.Many2one(string=u'周一班次', comodel_name='hr.attendance.class', ondelete='set null')
    # tuesday_class_id = fields.Many2one(string=u'周二班次', comodel_name='hr.attendance.class', ondelete='set null')
    # wednesday_class_id = fields.Many2one(string=u'周三班次', comodel_name='hr.attendance.class', ondelete='set null')
    # thursday_class_id = fields.Many2one(string=u'周四班次', comodel_name='hr.attendance.class', ondelete='set null')
    # friday_class_id = fields.Many2one(string=u'周五班次', comodel_name='hr.attendance.class', ondelete='set null')
    # saturday_class_id = fields.Many2one(string=u'周六班次', comodel_name='hr.attendance.class', ondelete='set null')
    # sunday_class_id = fields.Many2one(string=u'周日班次', comodel_name='hr.attendance.class', ondelete='set null')
    is_auto_holiday = fields.Boolean(string=u'节假日自动排休')
    no_work_days = fields.One2many(comodel_name='hr.employee', inverse_name='attendance_group_id', string=u'必须打卡日期')
    need_work_days = fields.One2many(comodel_name='hr.employee', inverse_name='attendance_group_id', string=u'不用打卡日期')

    # 排班制
    # class_ids = fields.One2many(comodel_name='hr.attendance.group.class.list',
    #                             inverse_name='group_id', string=u'班次列表' help="考勤组中的班次列表")
    # class_run_days = fields.Char(string='排班周期')

    # 自由排班

    @api.model
    def get_dingding_groups(self):
        """
        获取钉钉考勤组
        :return:
        """
        raise UserError("暂未实现！！！")

    @api.model
    def get_sim_emps(self):
        """
        获取钉钉考勤组成员
        :return:
        """
        raise UserError("暂未实现！！！")


class HrAttendanceGroupClassList(models.Model):
    _description = "考勤组内一周班次列表"
    _name = 'hr.attendance.group.class.list'
    _rec_name = 'week_name'

    attendance_group_id = fields.Many2one(comodel_name='hr.attendance.group', string=u'考勤组', index=True)
    week_name = fields.Char(string='星期')
    class_id = fields.Char(string='班次Id', index=True)
