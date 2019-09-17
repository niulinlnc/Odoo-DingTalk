# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 SuXueFeng
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAttendanceRules(models.Model):
    _description = '考勤规则'
    _name = 'hr.attendance.rules'
    _rec_name = 'name'

    name = fields.Char(string='规则名称')
    notes = fields.Text(string=u'备注')
    work_time = fields.Float(string=u'正常工作时数（小时）', digits=(10, 1))
    # -----考勤信息-----
    ATTSELECTION = [('ding_att_record', '从钉钉考勤详情提取'),
                    ('ding_att_result', '从钉钉考勤结果提取'),
                    ('odoo_att', '从Odoo考勤提取')
                    ]
    attendance_information = fields.Selection(string=u'考勤信息', selection=ATTSELECTION, default='ding_att_result')
    # -----考勤组-----
    simple_ids = fields.Many2many(
        'dingding.simple.groups', 'att_rules_group_rel',
        'rule_id', 'simple_id',
        string='考勤组')
    # -----班次-----
    list_time_selection = [
        ('00', '关联钉钉班次'),
        ('01', '不关联钉钉班次'),
    ]
    list_time = fields.Selection(string=u'钉钉班次关联', selection=list_time_selection, default='00')
    # -----事假规则-----
    leave_minimum_unit_selection = [
        ('00', '按分钟请假'),
        ('01', '按半小时请假'),
        ('02', '按小时请假'),
        ('03', '按半天请假'),
        ('04', '按天请假'),
    ]
    leave_time_accounting_selection = [
        ('00', '按自然日计算'),
        ('01', '按工作日计算'),
    ]
    leave_minimum_unit = fields.Selection(string=u'最小请假单位', selection=leave_minimum_unit_selection, default='00')
    leave_time_accounting = fields.Selection(string=u'请假时长核算', selection=leave_time_accounting_selection, default='00')
    leave_oa_madel = fields.Many2one(comodel_name='dingding.approval.template', string=u'审批模型')

    # -----加班规则-----
    is_allow_overtime = fields.Boolean(string=u'允许加班')
    work_overtime_selection = [
        ('00', '按审批时长计算'),
        ('01', '在审批的时段内，按打卡时长计算'),
        ('02', '无需审批，按打卡时长计算'),
    ]
    work_overtime_deduction = fields.Selection(string=u'加班规则', selection=work_overtime_selection, default='00')
    work_overtime_minimum_time = fields.Float(string=u'最小加班时长（分钟）', digits=(10, 2))
    work_overtime_oa_madel = fields.Many2one(comodel_name='dingding.approval.template', string=u'审批模型')
    # -----迟到规则------
    late_attendance_selection = [
        ('00', '迟到扣出勤时间'),
        ('01', '不纳入统计'),
        ('02', '累计次数扣费'),
    ]
    onduty1_late_attendance_deduction = fields.Selection(
        string=u'上班1迟到规则', selection=late_attendance_selection, default='00')
    onduty1_late_attendance_time = fields.Float(string=u'允许迟到分钟', digits=(10, 2))
    onduty2_late_attendance_deduction = fields.Selection(
        string=u'上班2迟到规则', selection=late_attendance_selection, default='00')
    onduty2_late_attendance_time = fields.Float(string=u'允许迟到分钟', digits=(10, 2))
    onduty3_late_attendance_deduction = fields.Selection(
        string=u'上班3迟到规则', selection=late_attendance_selection, default='00')
    onduty3_late_attendance_time = fields.Float(string=u'允许迟到分钟', digits=(10, 2))
    # -----早退规则------
    early_selection = [
        ('00', '纳入统计'),
        ('01', '不纳入统计'),
        ('02', '累计次数扣费'),
    ]
    offduty1_early_deduction = fields.Selection(string=u'下班1早退规则', selection=early_selection, default='00')
    offduty1_early_time = fields.Float(string=u'允许早退分钟', digits=(10, 2))
    offduty2_early_deduction = fields.Selection(string=u'下班2早退规则', selection=early_selection, default='00')
    offduty2_early_time = fields.Float(string=u'允许早退分钟', digits=(10, 2))
    offduty3_early_deduction = fields.Selection(string=u'下班3早退规则', selection=early_selection, default='00')
    offduty3_early_time = fields.Float(string=u'允许早退分钟', digits=(10, 2))
    # -----漏打卡------
    notsigned_selection = [
        ('00', '漏打卡按次扣款，但不扣出勤时数'),
        ('01', '漏打卡扣出勤时数'),
    ]
    onduty1_notsigned_rule = fields.Selection(string=u'上班1漏打卡规则', selection=notsigned_selection, default='00')
    onduty1_notsigned_rule = fields.Selection(string=u'上班1漏打卡规则', selection=notsigned_selection, default='00')
    offduty1_notsigned_rule = fields.Selection(string=u'下班1漏打卡规则', selection=notsigned_selection, default='00')
    onduty2_notsigned_rule = fields.Selection(string=u'上班2漏打卡规则', selection=notsigned_selection, default='00')
    offduty2_notsigned_rule = fields.Selection(string=u'下班2漏打卡规则', selection=notsigned_selection, default='00')
    onduty3_notsigned_rule = fields.Selection(string=u'上班3漏打卡规则', selection=notsigned_selection, default='00')
    offduty3_notsigned_rule = fields.Selection(string=u'下班3漏打卡规则', selection=notsigned_selection, default='00')
    onduty1_notsigned_money = fields.Float(string=u'上班1漏打卡扣费', digits=(10, 2))
    onduty1_notsigned_money = fields.Float(string=u'上班1漏打卡扣费', digits=(10, 2))
    offduty1_notsigned_money = fields.Float(string=u'下班1漏打卡扣费', digits=(10, 2))
    onduty2_notsigned_money = fields.Float(string=u'上班2漏打卡扣费', digits=(10, 2))
    offduty2_notsigned_money = fields.Float(string=u'下班2漏打卡扣费', digits=(10, 2))
    onduty3_notsigned_money = fields.Float(string=u'上班3漏打卡扣费', digits=(10, 2))
    offduty3_notsigned_money = fields.Float(string=u'下班3漏打卡扣费', digits=(10, 2))

    # @api.multi
    # def _compute_leave_deduction(self, base_wage, days, hours):
    #     """
    #     计算事假时长
    #     :param base_wage: 基本工资
    #     :param days:  出勤天数
    #     :param hours: 事假缺勤小时
    #     :return:
    #     """


    # @api.multi
    # def _compute_sick_absence(self, base_wage, days, hours):
    #     """
    #     计算病假时长
    #     :param base_wage:
    #     :param days:
    #     :param hours:
    #     :return:
    #     """
 

    # @api.multi
    # def _compute_work_overtime(self, base_wage, days, hours):
    #     """
    #     计算工作日加班时长
    #     :param base_wage:
    #     :param days:
    #     :param hours:
    #     :return:
    #     """
 

    # @api.multi
    # def _compute_weekend_overtime(self, base_wage, days, hours):
    #     """
    #     计算周末加班时长
    #     :param base_wage:
    #     :param days:
    #     :param hours:
    #     :return:
    #     """
 

    # @api.multi
    # def _compute_holiday_overtime(self, base_wage, days, hours):
    #     """
    #     计算节假日加班时长
    #     :param base_wage:
    #     :param days:
    #     :param hours:
    #     :return:
    #     """
 

    # @api.multi
    # def _compute_late_attendance(self, attendance_num):
    #     """
    #     计算迟到时长
    #     :param attendance_num:
    #     :return:
    #     """
  

    # @api.multi
    # def _compute_notsigned_attendance(self, attendance_num):
    #     """
    #     计算忘记打卡次数
    #     :param attendance_num:
    #     :return:
    #     """
    
    # @api.multi
    # def _compute_early_attendance(self, attendance_num):
    #     """
    #     计算早退时长
    #     :param attendance_num:
    #     :return:
    #     """
  
