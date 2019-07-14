# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.addons.ali_dindin.dingtalk.main import get_client, stamp_to_time, list_cut, day_cut


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    def dingding_attendance_action_employee(self):
        for res in self:
            action = self.env.ref(
                'dindin_attendance.dingding_attendance_action').read()[0]
            action['domain'] = [('emp_id', '=', res.id)]
            return action


class DingDingAttendance(models.Model):
    _name = "dingding.attendance"
    _rec_name = 'emp_id'
    _description = "钉钉出勤"

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
        ('odoo', 'Odoo系统'),
    ]
    emp_id = fields.Many2one(comodel_name='hr.employee',
                             string=u'员工', required=True)
    check_in = fields.Datetime(
        string="打卡时间", default=fields.Datetime.now, required=True)
    ding_group_id = fields.Many2one(
        comodel_name='dindin.simple.groups', string=u'钉钉考勤组')
    recordId = fields.Char(string='记录ID')
    workDate = fields.Datetime(string=u'工作日')
    checkType = fields.Selection(string=u'考勤类型', selection=[
                                 ('OnDuty', '上班'), ('OffDuty', '下班')])
    timeResult = fields.Selection(string=u'时间结果', selection=TimeResult)
    locationResult = fields.Selection(string=u'位置结果', selection=LocationResult)
    baseCheckTime = fields.Datetime(string=u'基准时间')
    sourceType = fields.Selection(string=u'数据来源', selection=SourceType)
    attendance_id = fields.Char(string='钉钉id')


class HrAttendanceTransient(models.TransientModel):
    _name = 'hr.attendance.tran'
    _description = '获取钉钉考勤信息'

    start_date = fields.Datetime(string=u'开始时间', required=True)
    stop_date = fields.Datetime(
        string=u'结束时间', required=True, default=str(fields.datetime.now()))
    emp_ids = fields.Many2many(comodel_name='hr.employee', relation='hr_dingding_attendance_and_hr_employee_rel',
                               column1='attendance_id', column2='emp_id', string=u'员工', required=True)
    is_all_emp = fields.Boolean(string=u'全部员工')

    @api.onchange('is_all_emp')
    def onchange_all_emp(self):
        if self.is_all_emp:
            emps = self.env['hr.employee'].search([('din_id', '!=', '')])
            if len(emps) <= 0:
                raise UserError("员工钉钉Id不存在！也许是你的员工未同步导致的！")
            self.emp_ids = [(6, 0, emps.ids)]

    @api.model
    def clear_attendance(self):
        """
        清除已下载的所有钉钉出勤记录（仅用于测试，生产环境慎用）
        """
        self._cr.execute("""
            delete from dingding_attendance
        """)

    @api.multi
    def get_attendance_list(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，
        钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        logging.info(">>>开始清空数据（仅用于测试）...")
        self.clear_attendance()
        client = get_client(self)
        logging.info(">>>开始获取员工打卡信息...")
        din_ids = list()
        for user in self.emp_ids:
            din_ids.append(user.din_id)
        user_list = list_cut(din_ids, 50)
        for u in user_list:
            logging.info(">>>开始获取{}员工段数据".format(u))
            date_list = day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                logging.info(">>>开始获取{}时间段数据".format(d))
                offset = 0
                limit = 50
                while True:
                    try:
                        result = client.attendance.list(
                            d[0], d[1], user_ids=u, offset=offset, limit=limit)
                        if result.get('errcode') == 0:
                            for rec in result.get('recordresult'):
                                data = {
                                    'recordId': rec.get('recordId'),
                                    # 工作日
                                    'workDate': stamp_to_time(rec.get('workDate')),
                                    # 时间结果
                                    'timeResult': rec.get('timeResult'),
                                    # 考勤结果
                                    'locationResult': rec.get('locationResult'),
                                    # 基准时间
                                    'baseCheckTime': stamp_to_time(rec.get('baseCheckTime')),
                                    # 数据来源
                                    'sourceType': rec.get('sourceType'),
                                    'checkType': rec.get('checkType'),
                                    'check_in': stamp_to_time(rec.get('userCheckTime')),
                                    'attendance_id': rec.get('id'),
                                }
                                groups = self.env['dindin.simple.groups'].sudo().search(
                                    [('group_id', '=', rec.get('groupId'))])
                                data.update(
                                    {'ding_group_id': groups[0].id if groups else False})
                                emp_id = self.env['hr.employee'].sudo().search(
                                    [('din_id', '=', rec.get('userId'))])
                                data.update(
                                    {'emp_id': emp_id[0].id if emp_id else False})
                                attendance = self.env['dingding.attendance'].sudo().search(
                                    [('emp_id', '=', emp_id[0].id),
                                     ('check_in', '=', stamp_to_time(
                                         rec.get('userCheckTime'))),
                                     ('checkType', '=', rec.get('checkType'))])
                                if not attendance:
                                    self.env['dingding.attendance'].sudo().create(
                                        data)
                            logging.info(">>>是否还有剩余数据：{}".format(
                                result.get('hasMore')))
                            if result.get('hasMore'):
                                offset = offset + limit
                                logging.info(">>>准备获取剩余数据中的第{}至{}条".format(
                                    offset+1, offset+limit))
                            else:
                                break
                        else:
                            raise UserError(
                                '请求失败,原因为:{}'.format(result.get('errmsg')))
                    except Exception as e:
                        raise UserError(e)

        logging.info(">>>根据日期获取员工打卡信息结束...")
        action = self.env.ref('dindin_attendance.dingding_attendance_action')
        action_dict = action.read()[0]
        return action_dict

    @api.multi
    def get_attendance_list_v2(self):
        """
        根据日期获取员工打卡信息，当user存在时将获取指定user的打卡，若不存在时，将获取所有员工的打卡信息，钉钉限制每次传递员工数最大为50个
        :param start_date:
        :param end_date:
        :param user:
        :return:
        """
        logging.info(">>>开始获取员工打卡信息...")
        din_ids = list()
        for user in self.emp_ids:
            din_ids.append(user.din_id)
        user_list = list_cut(din_ids, 50)
        for u in user_list:
            logging.info(">>>开始获取{}员工段数据".format(u))
            date_list = day_cut(self.start_date, self.stop_date, 7)
            for d in date_list:
                logging.info(">>>开始获取{}时间段数据".format(d))
                offset = 0
                limit = 50
                while True:
                    has_more = self.attendance_list(
                        d[0], d[1], user_ids=u, offset=offset, limit=limit)
                    logging.info(">>>是否还有剩余数据：{}".format(has_more))
                    if not has_more:
                        break
                    else:
                        offset = offset + limit
                        logging.info(">>>准备获取剩余数据中的第{}至{}条".format(
                            offset+1, offset+limit))
        logging.info(">>>根据日期获取员工打卡信息结束...")
        action = self.env.ref('dindin_attendance.dingding_attendance_action')
        action_dict = action.read()[0]
        return action_dict

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
        client = get_client(self)
        try:
            result = client.attendance.list(
                work_date_from, work_date_to, user_ids=user_ids, offset=offset, limit=limit)
            # logging.info(">>>获取考勤返回结果{}".format(result))
            if result.get('errcode') == 0:
                for rec in result.get('recordresult'):
                    data = {
                        'recordId': rec.get('recordId'),
                        'workDate': stamp_to_time(rec.get('workDate')),  # 工作日
                        'timeResult': rec.get('timeResult'),  # 时间结果
                        'locationResult': rec.get('locationResult'),  # 考勤结果
                        # 基准时间
                        'baseCheckTime': stamp_to_time(rec.get('baseCheckTime')),
                        'sourceType': rec.get('sourceType'),  # 数据来源
                        'checkType': rec.get('checkType'),
                        'check_in': stamp_to_time(rec.get('userCheckTime')),
                        'attendance_id': rec.get('id'),
                    }
                    groups = self.env['dindin.simple.groups'].sudo().search(
                        [('group_id', '=', rec.get('groupId'))])
                    data.update(
                        {'ding_group_id': groups[0].id if groups else False})
                    emp_id = self.env['hr.employee'].sudo().search(
                        [('din_id', '=', rec.get('userId'))])
                    data.update({'emp_id': emp_id[0].id if emp_id else False})
                    attendance = self.env['dingding.attendance'].sudo().search(
                        [('emp_id', '=', emp_id[0].id),
                         ('check_in', '=', stamp_to_time(
                             rec.get('userCheckTime'))),
                         ('checkType', '=', rec.get('checkType'))])
                    if not attendance:
                        self.env['dingding.attendance'].sudo().create(data)
                if result.get('hasMore'):
                    return True
                else:
                    return False
            else:
                raise UserError('请求失败,原因为:{}'.format(result.get('errmsg')))
        except Exception as e:
            raise UserError(e)
