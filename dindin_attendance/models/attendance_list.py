# -*- coding: utf-8 -*-
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client, stamp_to_time

_logger = logging.getLogger(__name__)
# 已弃用，已经钉钉考勤整合至odoo考勤


class DinDinAttendanceList(models.Model):
    _name = 'dindin.attendance.list'
    _description = '打卡列表'
    _rec_name = 'emp_id'

    TimeResult = [
        ('Normal', '正常'),
        ('Early', '早退'),
        ('Late', '迟到'),
        ('SeriousLate', '严重迟到'),
        ('Absenteeism', '旷工迟到'),
        ('NotSigned', '未打卡'),
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
        ('AUTO_CHECK', '自动打卡'),
    ]

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    group_id = fields.Many2one(comodel_name='dindin.simple.groups', string=u'考勤组')
    recordId = fields.Char(string='记录ID')
    workDate = fields.Date(string=u'工作日')
    emp_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', required=True)
    checkType = fields.Selection(string=u'考勤类型', selection=[('OnDuty', '上班'), ('OffDuty', '下班')])
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    baseCheckTime = fields.Datetime(string=u'基准时间')
    userCheckTime = fields.Datetime(string=u'实际打卡时间')
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)

    @api.model
    def get_attendance_list(self, start_date, end_date, user=None):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        if not start_date and not end_date:
            raise UserError("必须选择要查询的开始日期和结束日期!")
        logging.info(">>>开始获取员工打卡信息...")
        user_list = list()
        if user:
            h_emp = self.env['hr.employee'].sudo().search([('name', '=', user)])
            if not h_emp:
                raise UserError("员工{}不存在！".format(user))
            for h in h_emp:
                if not h.din_id:
                    raise UserError("员工{}的钉钉ID无效,请输入其他员工或不填！".format(user))
                user_list.append(h.din_id)
        else:
            emps = self.env['hr.employee'].sudo().search([('din_id', '!=', '')])
            emp_len = len(emps)
            if emp_len <= 50:
                for e in emps:
                    user_list.append(e.din_id)
            elif emp_len > 50:
                n = 1
                e_list = list()
                for e in emps:
                    if n <= 50:
                        e_list.append(e.din_id)
                        n = n + 1
                    else:
                        user_list.append(e_list)
                        e_list = list()
                        e_list.append(e.din_id)
                        n = 2
                user_list.append(e_list)
        logging.info(user_list)
        for u in user_list:
            if isinstance(u, str):
                offset = 0
                limit = 50
                while True:
                    workDateFrom = start_date + ' 00:00:00'  # 开始日期
                    workDateTo = end_date + ' 00:00:00'  # 结束日期
                    userIdList = user_list  # 员工列表
                    offset = offset  # 开始日期
                    limit = limit  # 开始日期
                    has_more = self.attendance_list(workDateFrom, workDateTo, user_ids=userIdList, offset=offset, limit=limit)
                    if not has_more:
                        break
                    else:
                        offset = offset + limit
                break
            elif isinstance(u, list):
                offset = 0
                limit = 50
                while True:
                    workDateFrom = start_date + ' 00:00:00'  # 开始日期
                    workDateTo = end_date + ' 00:00:00'  # 结束日期
                    userIdList = u  # 员工列表
                    offset = offset  # 开始日期
                    limit = limit  # 开始日期
                    has_more = self.attendance_list(workDateFrom, workDateTo, user_ids=userIdList, offset=offset, limit=limit)
                    if not has_more:
                        break
                    else:
                        offset = offset + limit
        logging.info(">>>根据日期获取员工打卡信息结束...")
        return {'state': True, 'msg': '执行成功'}

    @api.model
    def attendance_list(self, work_date_from, work_date_to, user_ids=(), offset=0, limit=50):
        """
        考勤打卡数据开放
        :param work_date_from: 查询考勤打卡记录的起始工作日
        :param work_date_to: 查询考勤打卡记录的结束工作日
        :param user_ids: 员工在企业内的UserID列表，企业用来唯一标识用户的字段
        :param offset: 表示获取考勤数据的起始点，第一次传0，如果还有多余数据，下次获取传的offset值为之前的offset+limit
        :param limit: 表示获取考勤数据的条数，最大不能超过50条
        :return:
        """
        try:
            client = get_client(self)
            result = client.attendance.list(work_date_from, work_date_to, user_ids=user_ids, offset=offset, limit=limit)
            logging.info(">>>获取考勤返回结果{}".format(result))
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                    data = {
                        'recordId': rec.get('recordId'),
                        'workDate': stamp_to_time(rec.get('workDate')),  # 工作日
                        'checkType': rec.get('checkType'),  # 考勤类型
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤类型
                        'baseCheckTime': stamp_to_time(rec.get('baseCheckTime')),  # 基准时间
                        'userCheckTime': stamp_to_time(rec.get('userCheckTime')),  # 实际打卡时间
                        'sourceType': rec.get('sourceType'),  # 数据来源
                    }
                    groups = self.env['dindin.simple.groups'].sudo().search([('group_id', '=', rec.get('groupId'))])
                    if groups:
                        data.update({'group_id': groups[0].id})
                    emp_id = self.env['hr.employee'].sudo().search([('din_id', '=', rec.get('userId'))])
                    if emp_id:
                        data.update({'emp_id': emp_id[0].id})
                    a_list = self.env['dindin.attendance.list'].search(
                        [('recordId', '=', rec.get('recordId')),('emp_id', '=',  emp_id[0].id),  ('baseCheckTime', '=', stamp_to_time(rec.get('baseCheckTime')))])
                    if a_list:
                        a_list.sudo().write(data)
                    else:
                        self.env['dindin.attendance.list'].sudo().create(data)
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)

