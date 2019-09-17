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
import calendar
import logging
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrLegalHoliday(models.Model):
    _description = '法定节假日'
    _name = 'hr.legal.holiday'
    _rec_name = 'legal_holiday_name'

    legal_holiday_name = fields.Char('法定节假日名称')
    legal_holiday = fields.Date('法定节假日')
    status = fields.Char('法定节假日状态', selection=[('0', '未使用'), ('1', '使用中'), ('2', '已失效')])


class HrAttendanceTotal(models.Model):
    _description = '员工考勤统计'
    _name = 'hr.attendance.total'
    _rec_name = 'employee_id'
    _order = 'id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.model
    def _get_default_date(self):
        return str(fields.date.today())

    company_id = fields.Many2one('res.company', '公司', default=_get_default_company, index=True, required=True)
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门', index=True, track_visibility='onchange')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工',
                                  required=True, index=True, track_visibility='onchange')
    job_id = fields.Many2one(comodel_name='hr.job', string=u'在职岗位')
    employee_number = fields.Char(string='员工工号')
    attendance_month = fields.Date(string=u'考勤日期', required=True, index=True, default=_get_default_date)
    attend_code = fields.Char(string='考勤期间', index=True)
    # 加班
    work_overtime_hour = fields.Float(string=u'工作日加班(小时)', digits=(10, 1))
    weekend_overtime_hour = fields.Float(string=u'周末加班(小时)', digits=(10, 1))
    holiday_overtime_hour = fields.Float(string=u'节假日加班(小时)', digits=(10, 1),)
    # 缺勤
    leave_absence_hour = fields.Float(string=u'事假缺勤(小时)', digits=(10, 1))
    sick_absence_hour = fields.Float(string=u'病假缺勤(小时)', digits=(10, 1))
    # 打卡
    late_attendance_num = fields.Integer(string=u'迟到次数')
    notsigned_attendance_num = fields.Integer(string=u'忘记打卡次数')
    early_attendance_num = fields.Integer(string=u'早退次数')

    arrive_total = fields.Float('应到天数')
    real_arrive_total = fields.Float('实到天数')
    absenteeism_total = fields.Float('旷工天数')
    late_total = fields.Float('迟到/早退次数')
    sick_leave_total = fields.Float('病假天数')
    personal_leave_total = fields.Float('事假天数')
    annual_leave_total = fields.Float('年假天数')
    marriage_leave_total = fields.Float('婚假天数')
    bereavement_leave_total = fields.Float('丧假天数')
    paternity_leave_total = fields.Float('陪产假天数')
    maternity_leave_total = fields.Float('产假天数')
    work_related_injury_leave_total = fields.Float('工伤假天数')
    home_leave_total = fields.Float('探亲假天数')
    travelling_total = fields.Float('出差天数')
    other_leave_total = fields.Float('其他假天数')

    @api.constrains('attendance_month')
    @api.onchange('attendance_month')
    def _constrains_attendance_month(self):
        for res in self:
            if res.attendance_month:
                month_date = str(res.attendance_month)
                res.attend_code = "{}/{}".format(month_date[:4], month_date[5:7])

    @api.constrains('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for res in self:
            if res.employee_id:
                res.job_id = res.employee_id.job_id.id
                res.department_id = res.employee_id.department_id.id
                res.employee_number = res.employee_id.din_jobnumber


class HrAttendanceAnnal(models.TransientModel):
    _description = '计算考勤结果'
    _name = 'hr.attendance.total.transient'

    SourceType = [
        ('dingding', '钉钉考勤结果'),
        ('odoo', 'Odoo出勤记录'),
        ('and', '两者同时获取')
    ]

    soure_type = fields.Selection(string=u'考勤结果来源', selection=SourceType, default='dingding', required=True)
    start_date = fields.Date(string=u'考勤开始日期', required=True)
    end_date = fields.Date(string=u'考勤结束日期', required=True)
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_attendance_total_and_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.onchange('start_date')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date:
                firstDay, lastDay = self.getMonthFirstDayAndLastDay(
                    year=rec.start_date.year, month=rec.start_date.month)
                rec.end_date = lastDay

    @api.multi
    def compute_attendance_result(self):
        """
        立即计算考勤结果
        :return:
        """
        if self.soure_type == 'dingding':
            self.attendance_total_cal_dingding(self.emp_ids, self.start_date, self.end_date)
        elif self.soure_type == 'odoo':
            raise UserError("暂未实现！！！")
        elif self.soure_type == 'and':
            raise UserError("暂未实现！！！")

        # 计算后重载考勤统计列表
        action = self.env.ref('dingding_attendance.hr_attendance_total_action')
        action_dict = action.read()[0]
        return action_dict

    def attendance_total_cal_dingding(self, emp_list, start_date, end_date):
        """
        考勤汇总计算(考勤数据来源钉钉考勤结果)
        :return:
        """
        self.ensure_one()
        # self.attendance_cal(emp_list, start_date, end_date)
        attendance_total_ins_list = []
        for emp in emp_list:
            # 获取年月，取得区间月份
            month = 0
            if end_date.year - start_date.year == 0:
                month = end_date.month - start_date.month
            elif end_date.year - start_date.year >= 1:
                month = end_date.month - start_date.month + (end_date.year - start_date.year) * 12
            start_date_tmp = start_date.replace(day=1)
            for num in range(month + 1):
                current_month_num = calendar.monthrange(start_date_tmp.year, start_date_tmp.month)[1]
                # 删除原有记录
                self.env['hr.attendance.total'].sudo().search(
                    [('employee_id', '=', emp.id), ('attend_code', '=', start_date_tmp.strftime('%Y/%m'))]).unlink()
                attendance_info_dict_list = self.env['hr.attendance'].sudo().search([('employee_id', '=', emp.id), (
                    'workDate', '>=', start_date_tmp), ('workDate', '<=', start_date_tmp.replace(day=current_month_num))])
                # check_status_choice = (('0', '正常'), ('1', '迟到'), ('2', '早退'), ('3', '旷工'))
                logging.info(">>>获取的考勤结果:%s", attendance_info_dict_list)
                attendance_total_ins = self.attendance_total_cal_sum(emp, start_date_tmp, attendance_info_dict_list)
                attendance_total_ins_list.append(attendance_total_ins)
                start_date_tmp += timedelta(days=current_month_num)
        self.env['hr.attendance.total'].sudo().create(attendance_total_ins_list)

    def attendance_total_cal_odoo(self, emp_list, start_date, end_date):
        """
        考勤汇总计算(考勤数据来源odoo考勤)
        :return:
        """
        self.ensure_one()
        attendance_total_ins_list = []
        for emp in emp_list:
            # 获取年月，取得区间月份
            month = 0
            if end_date.year - start_date.year == 0:
                month = end_date.month - start_date.month
            elif end_date.year - start_date.year >= 1:
                month = end_date.month - start_date.month + (end_date.year - start_date.year) * 12
            start_date_tmp = start_date.replace(day=1)
            for num in range(month + 1):
                current_month_num = calendar.monthrange(start_date_tmp.year, start_date_tmp.month)[1]
                # 删除原有记录
                self.env['hr.attendance.total'].sudo().search(
                    [('employee_id', '=', emp.id), ('attend_code', '=', start_date_tmp.strftime('%Y/%m'))]).unlink()
                attendance_info_dict_list = self.env['hr.attendance'].sudo().search([('employee_id', '=', emp.id), (
                    'workDate', '>=', start_date_tmp), ('workDate', '<=', start_date_tmp.replace(day=current_month_num))])
                # check_status_choice = (('0', '正常'), ('1', '迟到'), ('2', '早退'), ('3', '旷工'))
                logging.info(">>>获取的考勤结果:%s", attendance_info_dict_list)
                attendance_total_ins = self.attendance_total_cal_sum(emp, start_date_tmp, attendance_info_dict_list)
                attendance_total_ins_list.append(attendance_total_ins)
                start_date_tmp += timedelta(days=current_month_num)
        self.env['hr.attendance.total'].sudo().create(attendance_total_ins_list)

    @api.multi
    def attendance_cal(self, emp_list, start_date, end_date):
        """
        生成考勤日报表
        """
        # 获取排班信息 get_scheduling_info_dict
        # 获取班次信息 get_shift_info_dict
        # 获取签卡数据 get_edit_attendance_dict
        # 获取请假拆分后的数据 get_leave_detail_dict
        # TODO 获取出差数据
        # 获取原始打卡数据 get_original_card_dict
        # 数据整合 数据结构
        # 数据写入
        # 获取班次信息 get_shift_info_dict
        # shift_info_dict = get_shift_info_dict()
        # 考勤数据列表
        # attendance_info_list = []

        for emp in emp_list:
            # 删除已存在的该员工考勤日报
            self.env['hr.attendance'].sudo().search(
                [('employee_id', '=', emp.id), ('workDate', '>=', start_date), ('workDate', '<=', end_date)]).unlink()
            # # 获取排班信息 get_scheduling_info_dict
            # scheduling_info_dict = get_scheduling_info_dict(emp, start_date, end_date)
            # # 获取签卡数据 get_edit_attendance_dict
            # edit_attendance_dict = get_edit_attendance_dict(emp, start_date, end_date)
            # 获取请假拆分后的数据 get_leave_detail_dict
            # leave_detail_dict = get_leave_detail_dict(emp, start_date, end_date)
            # 获取原始打卡数据 get_original_card_dict
            # original_card_dict = self.get_original_card_dict(emp, start_date, end_date)
            # 整合打卡、签卡、请假数据，赋值
            # print(scheduling_info_dict, edit_attendance_dict, leave_detail_dict, original_card_dict)

            for work_date in self.date_range(start_date, end_date):
                # work_date_attendance_result = self.env['hr.attendance.result'].sudo().search(
                #     [('emp_id', '=', emp.id), ('work_date', '>=', start_date), ('work_date', '<=', end_date)])
                work_date_attendance_result = self.env['hr.attendance.result'].sudo().search(
                    [('emp_id', '=', emp.id), ('work_date', '=', work_date)], order='check_type, check_in')
                OnDuty_list = list()
                OffDuty_list = list()
                for rec in work_date_attendance_result:
                    data = {
                        'employee_id': emp.id,
                        'workDate': rec.work_date,  # 工作日
                        'ding_group_id': rec.ding_group_id.id,
                        'attendance_date_status': '00',
                    }
                    # 判断是否周末加班
                    if datetime.isoweekday(rec.work_date) in (6, 7):
                        data.update({'attendance_date_status': '01'})
                    # 判断是否节假日加班
                    elif self.env['hr.legal.holiday'].sudo().search([('legal_holiday', '=', rec.work_date)]):
                        data.update({'attendance_date_status': '02'})
                    if rec.check_type == 'OnDuty':
                        data.update({
                            'check_in': rec.check_in,
                            'on_planId': rec.plan_id.plan_id if rec.plan_id else rec.ding_plan_id,
                            'on_timeResult': rec.timeResult,
                            'on_baseCheckTime': rec.baseCheckTime,
                            'on_sourceType': rec.sourceType,
                            'on_procInstId': rec.procInstId
                        })
                        OnDuty_list.append(data)
                    elif rec.check_type == 'OffDuty':
                        data.update({
                            'check_out': rec.check_in,
                            'off_planId': rec.plan_id.plan_id if rec.plan_id else rec.ding_plan_id,
                            'off_timeResult': rec.timeResult,
                            'off_baseCheckTime': rec.baseCheckTime,
                            'off_sourceType': rec.sourceType,
                            'off_procInstId': rec.procInstId
                        })
                        OffDuty_list.append(data)
                # 上班考勤结果列表与下班考勤结果列表按时间排序后合并
                OnDuty_list.sort(key=lambda x: x['check_in'])
                # logging.info(">>>获取OnDuty_list结果%s", OnDuty_list)
                OffDuty_list.sort(key=lambda x: x['check_out'])
                # logging.info(">>>获取OffDuty_list结果%s", OffDuty_list)

                duty_list = list()
                on_planId_list = list()
                for onduty in OnDuty_list:
                    for offduty in OffDuty_list:
                        datetime_check_out = offduty.get('check_out')
                        datetime_check_in = onduty.get('check_in')
                        if onduty.get('on_planId') not in on_planId_list and \
                            offduty.get('workDate') == onduty.get('workDate') and \
                            (int(offduty.get('off_planId')) == int(onduty.get('on_planId')) + 1 or
                             datetime_check_out > datetime_check_in):
                            duty_tmp = dict(onduty, **offduty)
                            duty_list.append(duty_tmp)
                            on_planId_list.append(onduty.get('on_planId'))

                # 剩余还未匹配到下班记录的考勤（如当天）
                for onduty in OnDuty_list:
                    if onduty.get('on_planId') not in on_planId_list:
                        duty_list.append(onduty)
                # 将合并的考勤导入odoo考勤
                duty_list.sort(key=lambda x: x['check_in'])
                logging.info(">>>获取duty_list结果%s", duty_list)

                # 判断是否在请假期间
                leave_delta = False
                duty_info = []
                for duty in duty_list:
                    if datetime.isoweekday(duty['workDate']) not in (7,) and \
                            not self.env['hr.legal.holiday'].sudo().search([('legal_holiday', '=', duty['workDate'])]):
                        on_duty = duty['on_baseCheckTime'] if 'on_baseCheckTime' in duty else duty['workDate']
                        off_duty = duty['off_baseCheckTime'] if 'off_baseCheckTime' in duty else duty['workDate'] + \
                            timedelta(hours=24)
                        domain1 = [('user_id', '=', emp.id), ('start_time',
                                                              '<=', on_duty), ('end_time', '>=', off_duty)]
                        domain2 = [('user_id', '=', emp.id), ('start_time', '>', on_duty),
                                   ('start_time', '<', off_duty), ('end_time', '>', off_duty)]
                        domain3 = [('user_id', '=', emp.id), ('start_time', '<', on_duty),
                                   ('end_time', '>', on_duty), ('end_time', '<', off_duty)]
                        domain4 = [('user_id', '=', emp.id), ('start_time',
                                                              '>=', on_duty), ('end_time', '<=', off_duty)]
                        leave_info1 = self.env['hr.leaves.list'].sudo().search(domain1, limit=1)
                        leave_info2 = self.env['hr.leaves.list'].sudo().search(domain2, limit=1)
                        leave_info3 = self.env['hr.leaves.list'].sudo().search(domain3, limit=1)
                        leave_info4 = self.env['hr.leaves.list'].sudo().search(domain4, limit=1)
                        if len(leave_info1) > 0:
                            leave_delta = duty['off_baseCheckTime'] - duty['on_baseCheckTime']
                        elif len(leave_info2) > 0:
                            if duty['on_timeResult'] == 'NotSigned':
                                leave_delta = duty['off_baseCheckTime'] - duty['on_baseCheckTime']
                            else:
                                leave_delta = duty['off_baseCheckTime'] - leave_info2.start_time
                        elif len(leave_info3) > 0:
                            leave_delta = leave_info3.end_time - duty['on_baseCheckTime']
                        elif len(leave_info4) > 0:
                            if duty['on_timeResult'] == 'NotSigned':
                                leave_delta = leave_info4.end_time - duty['on_baseCheckTime']
                            else:
                                leave_delta = leave_info4.end_time - leave_info4.start_time  # 暂时以请假单为准，员工提前来了也不算？
                        else:
                            pass
                        if leave_delta:
                            leave_hours = leave_delta.total_seconds() / 3600.0
                            duty.update({'leave_hours': leave_hours, 'attendance_date_status': '03'})
                        duty_info.append(duty)
                    else:
                        duty_info.append(duty)
                self.env['hr.attendance'].sudo().create(duty_info)

    @api.multi
    def attendance_total_cal_sum(self, emp, start_date, attendance_info_dict_list):
        """
        统计月应出勤及请假天数
        :retur
        """
        notsigned_attendance_num = late_attendance_num = early_attendance_num = 0
        work_overtime_hour = weekend_overtime_hour = holiday_overtime_hour = 0
        arrive_total = real_arrive_total = 0
        leave_absence_hour = sick_absence_hour = 0
        leave_dict = {'病假': 0, '事假': 0, '年假': 0, '婚假': 0, '丧假': 0, '陪产假': 0, '产假': 0, '工伤假': 0, '探亲假': 0, '出差（请假）': 0,
                      '其他假': 0}
        for one in attendance_info_dict_list:
            # 统计平时加班、周末加班、节假日加班时数
            if one.attendance_date_status == '00' and one.worked_hours > one.base_work_hours:
                work_overtime_hour = work_overtime_hour + one.worked_hours - one.base_work_hours
            elif one.attendance_date_status == '01':
                weekend_overtime_hour = weekend_overtime_hour + one.worked_hours
            elif one.attendance_date_status == '02':
                holiday_overtime_hour = holiday_overtime_hour + one.worked_hours
            # 统计迟到早退缺卡次数
            if one.on_timeResult == 'NotSigned' and one.attendance_date_status != '03':
                notsigned_attendance_num = notsigned_attendance_num + 1
            elif one.on_timeResult == 'Late':
                late_attendance_num = late_attendance_num + 1
            if one.off_timeResult == 'NotSigned' and one.attendance_date_status != '03':
                notsigned_attendance_num = notsigned_attendance_num + 1
            elif one.off_timeResult == 'Early':
                early_attendance_num = early_attendance_num + 1
            # 统计请假小时（暂时都当成事假）
            if one.leave_hours:
                leave_absence_hour = leave_absence_hour + one.leave_hours
            # # 统计假期
            # if leave_dict.get(one.check_in_type_id) is not None:
            #     leave_dict[one.check_in_type_id] += 1
            # # 实到天数 real_arrive_total 非请假的所有出勤天数
            # elif one.attendance_date_status:
            #     if one.on_timeResult != 'NotSigned':
            #         real_arrive_total = real_arrive_total + 1
            # # if leave_dict.get(one.check_out_type_id) is not None:
            # #     leave_dict[one.check_out_type_id] = leave_dict[one.check_out_type_id] + 1
            # # 实到天数 real_arrive_total 非请假的所有出勤天数
            # elif one.attendance_date_status:
            #     if one.off_timeResult != 'NotSigned':
            #         real_arrive_total = real_arrive_total + 1

        attendance_total_ins = {'employee_id': emp.id,
                                'attendance_month': start_date,
                                'arrive_total': arrive_total,
                                'real_arrive_total': real_arrive_total,
                                'work_overtime_hour': work_overtime_hour,
                                'weekend_overtime_hour': weekend_overtime_hour,
                                'holiday_overtime_hour': holiday_overtime_hour,
                                'notsigned_attendance_num': notsigned_attendance_num,
                                'late_attendance_num': late_attendance_num,
                                'early_attendance_num': early_attendance_num,
                                'leave_absence_hour': leave_absence_hour,
                                'sick_leave_total': leave_dict['病假'],
                                'personal_leave_total': leave_dict['事假'],
                                'annual_leave_total': leave_dict['年假'],
                                'marriage_leave_total': leave_dict['婚假'],
                                'bereavement_leave_total': leave_dict['丧假'],
                                'paternity_leave_total': leave_dict['陪产假'],
                                'maternity_leave_total': leave_dict['产假'],
                                'work_related_injury_leave_total': leave_dict['工伤假'],
                                'home_leave_total': leave_dict['探亲假'],
                                'travelling_total': leave_dict['出差（请假）'],
                                'other_leave_total': leave_dict['其他假'],
                                }
        return attendance_total_ins

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

    @api.model
    def getMonthFirstDayAndLastDay(self, year=None, month=None):
        """
        :param year: 年份，默认是本年，可传int或str类型
        :param month: 月份，默认是本月，可传int或str类型
        :return: firstDay: 当月的第一天，datetime.date类型
                  lastDay: 当月的最后一天，datetime.date类型
        """
        if year:
            year = int(year)
        else:
            year = fields.Date.today().year
        if month:
            month = int(month)
        else:
            month = fields.Date.today().month
        # 获取当月第一天的星期和当月的总天数
        firstDayWeekDay, monthRange = calendar.monthrange(year, month)
        # 获取当月的第一天
        firstDay = date(year=year, month=month, day=1)
        lastDay = date(year=year, month=month, day=monthRange)
        return firstDay, lastDay

