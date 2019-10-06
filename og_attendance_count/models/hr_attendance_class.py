# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (C) 2019 OnGood
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


class HrAttendanceClass(models.Model):
    _description = "班次"
    _name = 'hr.attendance.class'
    _rec_name = 'class_name'

    class_name = fields.Char(string='班次名称', index=True)
    work_time = fields.Char(string='工作时长', help="单位分钟，-1表示关闭该功能")
    is_default = fields.Boolean(string=u'是否默认班次')

    # 人性化班次设置
    permit_late_minutes = fields.Char(string='允许迟到分钟', default='0', help="允许迟到时长，单位分钟")
    serious_late_minutes = fields.Char(string='严重迟到分钟', default='60', help="严重迟到时长，单位分钟")
    absenteeism_late_minutes = fields.Char(string='旷工迟到分钟', default='120', help="旷工迟到时长，单位分钟")
    is_off_duty_free_check = fields.Selection(string=u'强制打卡', selection=[('Y', '下班不强制打卡'), ('N', '下班强制打卡')])
    is_late_check_in = fields.Boolean(string=u'允许晚走晚到')

    # 一天内上下班的次数
    attendance_times = fields.Selection(string=u'一天内上下班次数', selection=[
                                        ('1', '1天1次上下班'), ('2', '1天2次上下班'), ('3', '1天3次上下班')])
    is_across_control = fields.Boolean(string=u'打卡范围限制')

    # 休息时间，只有一个时间段的班次有
    rest_begin_time = fields.Float(string='休息开始时间', help="只有一个时间段的班次有")
    rest_end_time = fields.Float(string='休息结束时间', help="只有一个时间段的班次有")

    # # 上班1
    # onduty1 = fields.Char(string=u'第1次上班打卡')
    # onduty1_begin_min = fields.Char(string=u'第1次上班开始打卡时间')
    # onduty1_end_min = fields.Char(string=u'第1次上班结束打卡时间')
    # offduty1 = fields.Char(string=u'第1次下班打卡')
    # offduty1_begin_min = fields.Char(string=u'第1次下班开始打卡时间')
    # offduty1_end_min = fields.Char(string=u'第1次下班结束打卡时间')

    # # 上班2
    # onduty2 = fields.Char(string=u'第2次上班打卡')
    # onduty2_begin_min = fields.Char(string=u'第2次上班开始打卡时间')
    # onduty2_end_min = fields.Char(string=u'第2次上班结束打卡时间')
    # offduty2 = fields.Char(string=u'第2次下班打卡')
    # offduty2_begin_min = fields.Char(string=u'第2次下班开始打卡时间')
    # offduty2_end_min = fields.Char(string=u'第2次下班结束打卡时间')

    # # 上班3
    # onduty3 = fields.Char(string=u'第3次上班打卡')
    # onduty3_begin_min = fields.Char(string=u'第3次上班开始打卡时间')
    # onduty3_end_min = fields.Char(string=u'第3次上班结束打卡时间')
    # offduty3 = fields.Char(string=u'第3次下班打卡')
    # offduty3_begin_min = fields.Char(string=u'第3次下班开始打卡时间')
    # offduty3_end_min = fields.Char(string=u'第3次下班结束打卡时间')

    time_ids = fields.One2many(comodel_name='hr.attendance.class.time',
                               inverse_name='class_id', string=u'打卡时间段', help="一天内上下班的次数")


class HrattendanceClassTime(models.Model):
    _description = "班次内打卡时间段"
    _name = 'hr.attendance.class.time'
    _rec_name = 'name'

    name = fields.Char(string=u'时间段')
    class_id = fields.Many2one(comodel_name='hr.attendance.class', string=u'班次', index=True)
    across = fields.Char(string=u'打卡时间跨度')
    check_time = fields.Float(string=u'打卡时间')
    check_type = fields.Selection(string=u'打卡类型', selection=[('OnDuty', '上班打卡'), ('OffDuty', '下班打卡')])
    begin_time = fields.Float(string=u'提前打卡时间到')
    end_time = fields.Float(string=u'延后打卡时间至')


class HrAttendanceOvertimeRule(models.Model):
    _description = "加班规则"
    _name = 'hr.attendance.overtime.rule'
    _rec_name = 'rule_name'

    OVERTIMERULE = [
        ('00', '按审批时长计算'),
        ('01', '在审批时段内，按打卡时长计算'),
        ('02', '无需审批，按打卡时长计算')
    ]

    rule_name = fields.Char(string='加班规则名称', index=True)
    group_id = fields.Many2one(comodel_name='hr.attendance.groups', string=u'应用考勤组', index=True)
    # rule_for_workday = fields.Selection(string=u'工作日加班规则', selection=OVERTIMERULE, default='NONE')
    # rule_for_weekend = fields.Selection(string=u'休息日加班规则', selection=OVERTIMERULE, default='NONE')
    # rule_for_holiday = fields.Selection(string=u'节假日加班规则', selection=OVERTIMERULE, default='NONE')

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
