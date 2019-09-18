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


class HrAttendanceOvertimeRule(models.Model):
    _description = "加班规则"
    _name = 'hr.attendance.overtime.rule'
    _rec_name = 'rule_name'

    rule_name = fields.Char(string='加班规则名称', index=True)
    group_id = fields.Many2one(comodel_name='hr.attendance.groups', string=u'应用考勤组', index=True)
    rule_for_workday = fields.Selection(string=u'工作日加班规则', selection=OVERTIMERULE, default='NONE')
    rule_for_weekend = fields.Selection(string=u'休息日加班规则', selection=OVERTIMERULE, default='NONE')
    rule_for_holiday = fields.Selection(string=u'节假日加班规则', selection=OVERTIMERULE, default='NONE')

    COMPUTETYPE = [
        ('00', '按审批时长计算'),
        ('01', '在审批时段内，按打卡时长计算'),
        ('02', '无需审批，按打卡时长计算')
    ]
    compute_type_for_workday = fields.Selection(string=u'工作日加班计算方式', selection=COMPUTETYPE, default='00')
    is_allow_work_overtime_for_workday = fields.Boolean(string=u'工作日是否允许加班')
    compute_type_for_weekend = fields.Selection(string=u'休息日加班计算方式', selection=COMPUTETYPE, default='00')
    is_allow_work_overtime_for_weekend = fields.Boolean(string=u'休息日是否允许加班')
    compute_type_for_holiday = fields.Selection(string=u'节假日加班计算方式', selection=COMPUTETYPE, default='00')
    is_allow_work_overtime_for_holiday = fields.Boolean(string=u'节假日是否允许加班')


# class HrAttendanceOvertimeRuleWorkday(models.Model):
#     _description = "工作日加班规则"
#     _name = 'hr.attendance.overtime.rule.workday'
#     _rec_name = 'rule_id'

#     rule_id = fields.Char(string='加班规则', index=True)
#     COMPUTETYPE = [
#         ('00', '按审批时长计算'),
#         ('01', '在审批时段内，按打卡时长计算'),
#         ('02', '无需审批，按打卡时长计算')
#     ]
#     compute_type = fields.Selection(string=u'计算方式', selection=COMPUTETYPE, default='00')
#     is_allow_work_overtime = fields.Boolean(string=u'是否允许加班')


# class HrAttendanceOvertimeRuleWeekend(models.Model):
#     _description = "休息日加班规则"
#     _name = 'hr.attendance.overtime.rule.weekend'
#     _rec_name = 'rule_id'

#     rule_id = fields.Char(string='加班规则', index=True)
#     COMPUTETYPE = [
#         ('00', '按审批时长计算'),
#         ('01', '在审批时段内，按打卡时长计算'),
#         ('02', '无需审批，按打卡时长计算')
#     ]
#     compute_type = fields.Selection(string=u'计算方式', selection=COMPUTETYPE, default='00')
#     is_allow_work_overtime = fields.Boolean(string=u'是否允许加班')


# class HrAttendanceOvertimeRuleHoliday(models.Model):
#     _description = "节假日加班规则"
#     _name = 'hr.attendance.overtime.rule.holiday'
#     _rec_name = 'rule_id'

#     rule_id = fields.Char(string='加班规则', index=True)
#     COMPUTETYPE = [
#         ('00', '按审批时长计算'),
#         ('01', '在审批时段内，按打卡时长计算'),
#         ('02', '无需审批，按打卡时长计算')
#     ]
#     compute_type = fields.Selection(string=u'计算方式', selection=COMPUTETYPE, default='00')
#     is_allow_work_overtime = fields.Boolean(string=u'是否允许加班')


