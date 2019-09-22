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
import json
import logging
import time
import requests
from requests import ReadTimeout
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    def og_attendance_count_action_employee(self):
        for res in self:
            action = self.env.ref('og_attendance_count.hr_attendance_info_action').read()[0]
            action['domain'] = [('emp_id', '=', res.id)]
            return action


class HrAttendanceInfo(models.Model):
    _name = "hr.attendance.info"
    _rec_name = 'emp_id'
    _description = "员工考勤日报"

    TimeResult = [
        ('Normal', '正常'),
        ('Early', '早退'),
        ('Late', '迟到'),
        ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'),
        ('NotSigned', '未打卡'),
        ('Leave', '事假缺卡'),
        ('Holiday', '节日休息'),
    ]
    LocationResult = [
        ('Normal', '范围内'), ('Outside', '范围外'), ('NotSigned', '未打卡'),
    ]
    SourceType = [
        ('ATM', '考勤机'),
        ('BEACON', 'IBeacon'),
        ('DING_ATM', '钉钉考勤机'),
        ('USER', '用户打卡'),
        ('BOSS', '老板改签'),
        ('APPROVE', '审批系统'),
        ('SYSTEM', '考勤系统'),
        ('AUTO_CHECK', '自动打卡')
    ]
    DATESTATUS = [
        ('00', '工作日'),
        ('01', '休息日'),
        ('02', '节假日'),
        ('06', '其他')
    ]

    NOTSIGNEDORIGIN = [
        ('Forget', '漏打'),
        ('Leave', '请假'),
        ('Public', '公出'),
        ('Trip', '出差'),
        ('Change', '调休'),
        ('Annual', '年休假'),
        ('Holiday', '节假日'),
    ]

    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True, index=True)
    attendance_group_id = fields.Many2one(comodel_name='hr.attendance.group', string=u'考勤组')
    attendance_plan_id = fields.Many2one(comodel_name='hr.attendance.plan', string=u'排班ID')
    ding_plan_id = fields.Char(string='钉钉排班ID')
    record_id = fields.Char(string='唯一标识ID', help="钉钉设置的值为id，odoo中为record_id")
    work_date = fields.Date(string=u'工作日')
    work_month = fields.Char(string='年月字符串', help="为方便其他模块按照月份获取数据时使用", index=True)
    check_type = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')], index=True)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    approveId = fields.Char(string='关联的审批id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关")
    procInstId = fields.Char(string='审批实例id', help="当该字段非空时，表示打卡记录与请假、加班等审批有关。可以与获取单个审批数据配合使用")
    procInst_title = fields.Char(string='审批标题')
    baseCheckTime = fields.Datetime(string=u'基准时间', help="计算迟到和早退，基准时间")
    check_time = fields.Datetime(string="实际打卡时间", required=True, help="实际打卡时间,  用户打卡时间的毫秒数")
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult, index=True)
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    attendance_date_status = fields.Selection(string=u'日期性质', selection=DATESTATUS)
    not_signed_origin = fields.Selection(string=u'缺卡原因', selection=NOTSIGNEDORIGIN)

    # @api.model
    # def create(self, values):
    #     """
    #     创建时触发
    #     :param values:
    #     :return:
    #     """
    #     if values['work_date']:
    #         values.update({'work_month': "{}/{}".format(values['work_date'][:4], values['work_date'][5:7])})
    #     return super(HrAttendanceInfo, self).create(values)


class HrAttendanceInfoTransient(models.TransientModel):
    _name = 'hr.attendance.info.tran'
    _description = '获取考勤结果'

    start_date = fields.Date(string=u'开始日期', required=True)
    stop_date = fields.Date(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_attendance_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('ding_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.multi
    def get_attendance_info_list(self):
        """
        从钉钉考勤详情获取考勤数据并生成考勤日报表
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        emp_list = self.emp_ids
        start_date = self.start_date
        stop_date = self.stop_date
        for emp in emp_list:
            # 删除数据
            self.env['hr.attendance.info'].sudo().search(
                [('emp_id', '=', emp.id), ('work_date', '>=', start_date), ('work_date', '<=', stop_date)]).unlink()
            attendance_list = self.env['hr.attendance.record'].sudo().search(
                [('userId', '=', emp.id), ('workDate', '>=', start_date), ('workDate', '<=', stop_date)], order='workDate')
            data_list = list()
            for rec in attendance_list:
                data = self.compute_attendance_result(rec.userId, rec.userCheckTime)
                if data:
                    date_status = self.compute_date_status(rec.userCheckTime)
                    data.update({
                        'locationResult': rec.locationResult,
                        'sourceType': rec.sourceType,
                        # 'procInstId': rec.procInstId if rec.procInstId else False,
                        # 'procInst_title': self.get_procInst_title(rec.procInstId) if rec.procInstId else False,
                        'attendance_date_status': date_status,
                    })
                    data_list.append(data)
            # 批量存储记录
            self.env['hr.attendance.info'].sudo().create(data_list)
            # 生成漏打卡
            self.get_not_signed_list(emp, start_date, stop_date)

        action = self.env.ref('og_attendance_count.hr_attendance_info_action')
        action_dict = action.read()[0]
        return action_dict

    @api.multi
    def compute_attendance_result(self, emp, check_time):
        """
        计算打卡结果
        :param emp_id: 员工
        :param check_time:  打卡时间
        :return data
        """
        work_date, begin_time, end_time = self.get_work_across(check_time)
        domain = [('emp_id', '=', emp.id), ('plan_check_time', '>=', begin_time), ('plan_check_time', '<=', end_time)]
        class_list = self.env['hr.attendance.plan'].sudo().search(domain, order='plan_check_time')
        for c in class_list:
            if c.begin_check_time and c.end_check_time and self.compare_time(check_time, c.begin_check_time, c.end_check_time):
                data = {
                    'emp_id': emp.id,
                    'check_type': c.check_type,
                    'work_date': work_date,
                    'check_time': check_time,
                    'attendance_group_id': c.group_id.id,
                    'attendance_plan_id': c.id,
                    'baseCheckTime': c.plan_check_time,
                    'timeResult': self.get_work_result(check_time, c),
                }
                return data
            else:
                pass

    def get_work_result(self, check_time, attendance_class):
        """
        根据check_time与对应班次判断考勤结果
        """
        c = attendance_class
        plan_check_time = fields.Datetime.from_string(c.plan_check_time)
        permit_late_time = plan_check_time + timedelta(minutes=int(c.class_id.permit_late_minutes) + 1)
        serious_late_time = plan_check_time + timedelta(minutes=int(c.class_id.serious_late_minutes))
        absenteeism_late_time = plan_check_time + timedelta(minutes=int(c.class_id.absenteeism_late_minutes))
        if c.check_type == 'OnDuty':
            if self.compare_time(check_time, c.begin_check_time, permit_late_time):
                result = 'Normal'
            elif self.compare_time(check_time, permit_late_time, serious_late_time):
                result = 'Late'
            elif self.compare_time(check_time, serious_late_time, absenteeism_late_time):
                result = 'SeriousLate'
            elif self.compare_time(check_time, absenteeism_late_time, c.end_check_time):
                result = 'Absenteeism'
        elif c.check_type == 'OffDuty':
            if self.compare_time(check_time, c.begin_check_time, c.plan_check_time):
                result = 'Early'
            elif self.compare_time(check_time, c.plan_check_time, c.end_check_time):
                result = 'Normal'
        return result

    def compare_time(self, check_time, start_time, end_time):
        """
        比较check_time 是否在时间区间[start_time, end_time]中
        """
        # get the seconds for specify date
        start_time = fields.Datetime.from_string(start_time)
        end_time = fields.Datetime.from_string(end_time)
        check_time = fields.Datetime.from_string(check_time)
        if check_time >= start_time and check_time <= end_time:
            return True
        return False

    def get_work_across(self, check_time):
        """
        根据check_time获取工作日与工作时段区间
        """
        work_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(check_time)).date()
        begin_time = self.date_to_datetime(check_time)
        end_time = begin_time + timedelta(days=1)

        return work_date, begin_time, end_time

    @api.multi
    def compute_date_status(self, check_time):
        """
        计算日期性质
        :param emp_id: 员工
        :param check_time:  打卡时间
        :return data
        """
        work_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(check_time)).date()
        if datetime.isoweekday(work_date) in (6, 7):
            date_status = '01'
        elif self.env['hr.attendance.holiday'].sudo().search([('holiday_date', '=', work_date)], limit=1):
            date_status = '02'
        else:
            date_status = '00'
        return date_status

    def get_procInst_title(self, procInstId):
        """
        获取审批标题
        """
        if procInstId:
            din_client = self.env['dingding.api.tools'].get_client()
            result = din_client.bpms.processinstance_get(procInstId)
            return result.get('title')

    def get_not_signed_list(self, emp, start_date, stop_date):
        """
        统计并标记缺卡
        """
        # 获取打卡记录
        attendance_list = self.env['hr.attendance.info'].sudo().search(
            [('emp_id', '=', emp.id), ('work_date', '>=', start_date), ('work_date', '<=', stop_date)], order='check_time').mapped('attendance_plan_id')
        # 获取排班表
        domain = [('emp_id', '=', emp.id), ('work_date', '>=', start_date), ('work_date', '<=', stop_date)]
        plan_list = self.env['hr.attendance.plan'].sudo().search(domain, order='plan_check_time')
        not_singned_list = list()
        for plan in plan_list:
            if plan not in attendance_list:
                data = {
                    'emp_id': emp.id,
                    'check_type': plan.check_type,
                    'work_date': plan.work_date,
                    'check_time': plan.plan_check_time,
                    'attendance_group_id': plan.group_id.id,
                    'attendance_plan_id': plan.id,
                    'baseCheckTime': plan.plan_check_time,
                    'timeResult': 'NotSigned',
                }
                not_singned_list.append(data)
        # 标记缺卡原因
        not_singned_list = self.get_not_signed_origin(not_singned_list)
        self.env['hr.attendance.info'].sudo().create(not_singned_list)

    @api.model
    def get_not_signed_origin(self, not_singned_list):
        """
        标记缺卡原因
        :param timeNum:
        :return:
        """
        data_list = list()
        for data in not_singned_list:
            domain = [('user_id', '=', data['emp_id']), ('start_time', '<=', data['check_time']),
                      ('end_time', '>=', data['check_time'])]
            leave_info = self.env['hr.leaves.list'].sudo().search(domain, limit=1)
            # 缺卡且基准时间在请假时间段内
            if len(leave_info) > 0:
                data.update({'not_signed_origin': 'Leave'})
            # 节假日
            elif self.env['hr.attendance.holiday'].sudo().search([('holiday_date', '=', data['work_date'])]):
                data.update({'not_signed_origin': 'Holiday'})
            else:
                data.update({'not_signed_origin': 'Forget'})
            data_list.append(data)
        return data_list

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
    def get_time_stamp(self, timeNum):
        """
        将13位时间戳转换为时间utc=0
        :param timeNum:
        :return:
        """
        timeStamp = float(timeNum / 1000)
        timeArray = time.gmtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime

    @api.model
    def timestamp_to_local_date(self, timeNum):
        """
        将13位毫秒时间戳转换为本地日期(+8h)
        :param timeNum:
        :return:
        """
        to_second_timestamp = float(timeNum / 1000)  # 毫秒转秒
        to_utc_datetime = time.gmtime(to_second_timestamp)  # 将时间戳转换为UTC时区（0时区）的时间元组struct_time
        to_str_datetime = time.strftime("%Y-%m-%d %H:%M:%S", to_utc_datetime)  # 将时间元组转成指定格式日期字符串
        to_datetime = fields.Datetime.from_string(to_str_datetime)  # 将字符串转成datetime对象
        to_local_datetime = fields.Datetime.context_timestamp(self, to_datetime)  # 将原生的datetime值(无时区)转换为具体时区的datetime
        to_str_datetime = fields.Datetime.to_string(to_local_datetime)  # datetime 转成 字符串
        return to_str_datetime

    @api.model
    def date_to_datetime(self, check_time):
        """
        将日期格式转换为时间格式utc=0
        :param timeNum:
        :return:
        """
        work_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(check_time)).date()
        work_timestamp = time.mktime(work_date.timetuple())
        timearray = time.gmtime(work_timestamp)
        str_utc_datetime = time.strftime("%Y-%m-%d %H:%M:%S", timearray)
        to_datetime = fields.Datetime.from_string(str_utc_datetime)
        return to_datetime

    @api.model
    def list_cut(self, mylist, limit):
        """
        列表分段
        :param mylist:列表集
        :param limit: 子列表元素限制数量
        :return:
        """
        length = len(mylist)
        cut_list = [mylist[i:i + limit] for i in range(0, length, limit)]
        return cut_list

    @api.model
    def day_cut(self, begin_time, end_time, days):
        """
        日期分段
        :param begin_date:开始日期
        :param end_date:结束日期
        :param days: 最大间隔时间
        :return:
        """
        cut_day = []
        begin_time = datetime.strptime(str(begin_time), "%Y-%m-%d")
        end_time = datetime.strptime(str(end_time), "%Y-%m-%d")
        delta = timedelta(days=days)
        t1 = begin_time
        while t1 <= end_time:
            if end_time < t1 + delta:
                t2 = end_time
            else:
                t2 = t1 + delta
            t1_str = t1.strftime("%Y-%m-%d %H:%M:%S")
            t2_str = t2.strftime("%Y-%m-%d %H:%M:%S")
            cut_day.append([t1_str, t2_str])
            t1 = t2 + timedelta(seconds=1)
        return cut_day

    @api.multi
    def clear_attendance_info(self):
        """
        清除已下载的所有钉钉出勤记录（仅用于测试，生产环境将删除该函数）
        """
        self._cr.execute("""
            delete from hr_attendance_info
        """)
