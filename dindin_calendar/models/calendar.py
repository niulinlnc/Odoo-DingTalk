# -*- coding: utf-8 -*-
import datetime
import json
import logging
import time
import requests
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client

_logger = logging.getLogger(__name__)


class DinDinCalendarEvent(models.Model):
    _inherit = 'calendar.event'

    number = fields.Char(string='日程编号', copy=False)
    d_minutes = fields.Integer(string=u'前?分钟提醒')
    dingtalk_calendar_id = fields.Char(string='钉钉日历id')

    @api.model
    def create(self, values):
        if not values['number']:
            values['number'] = self.env['ir.sequence'].sudo().next_by_code('calendar.event.number')
        auto_calendar_event = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.auto_calendar_event')
        if auto_calendar_event:
            values['dingtalk_calendar_id'] = self.create_dindin_calendar(values)
            self.sudo().message_post(body=u"已同步上传至钉钉日程", message_type='notification')
        return super(DinDinCalendarEvent, self).create(values)

    @api.model
    def create_dindin_calendar(self, val):
        """
        创建钉钉日程
        :param val:
        :return:
        """
        client = get_client(self)
        start_time = datetime.datetime.strptime("{}.42".format(val.get('start')), "%Y-%m-%d %H:%M:%S.%f").timetuple()
        end_time = datetime.datetime.strptime("{}.42".format(str(val.get('stop'))), "%Y-%m-%d %H:%M:%S.%f").timetuple()
        user = self.env['res.users'].sudo().search([('id', '=', val.get('user_id'))])
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        userids = list()
        userids.append(employee.din_id)
        create_vo = {
            'summary': val.get('name'),  # 主题
            'minutes': val.get('d_minutes'),  # 前分钟提醒
            'remind_type': 'app',  # 提醒方式-固定值
            'location': val.get('location') if val.get('location') else '',  # 地点地址
            'receiver_userids': userids,  # 接收人列表string
            'end_time': {
                'unix_timestamp': "{}000".format(int(time.mktime(end_time))),  # 结束的unix时间戳 (单位:毫秒)
                'timezone': 'Shanghai',   # 时区
            },
            'calendar_type': 'notification',  # 提醒类型
            'start_time': {
                'unix_timestamp': "{}000".format(int(time.mktime(start_time))),  # 开始的unix时间戳
                'timezone': 'Shanghai',  # 时区
            },
            'source': {
                'title': 'OdooERP',
                'url': 'http://#',
            },
            'description': val.get('description') if val.get('description') else ' ',  # 备注
            'creator_userid': employee[0].din_id if employee[0].din_id else '',  # 创建人uid
            'uuid': val.get('number'),  # 流水号
            'biz_id': val.get('number'),  # 业务号
        }
        try:
            result = client.calendar.create(create_vo)
            logging.info(">>>创建日程返回结果:{}".format(result))
            return result.get('dingtalk_calendar_id')
        except Exception as e:
            raise UserError(e)


    # 重写删除方法
    @api.multi
    def unlink(self):
        for res in self:
            calendar_id = res.dingtalk_calendar_id
            userid = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)]).din_id   
            auto_del_calendar_event = self.env['ir.config_parameter'].sudo().get_param('ali_dindin.auto_del_calendar_event')
            if auto_del_calendar_event:
                self.delete_dindin_calendar(userid, calendar_id)
        return super(DinDinCalendarEvent, self).unlink()

    @api.model
    def delete_dindin_calendar(self, userid, calendar_id):
        """
        日程删除（该接口暂未开放）

        :param userid: 员工id
        :param calendar_id: 日程id
        """
        client = get_client(self)
        try:
            result = client.calendar.delete(userid=userid, calendar_id=calendar_id)
            logging.info(">>>删除日程返回结果:{}".format(result))
        except Exception as e:
            raise UserError(e)

    @api.model
    def list_dindin_calendar(self):
        """
        日程查询（该接口暂未开放）

        :param user_id: 员工ID
        :param calendar_folder_id: 钉钉日历文件夹的对外id，默认是自己的默认文件夹
        :param time_min: 查询时间下限
        :param i_cal_uid: 日程跨域唯一id，用于唯一标识一组关联日程事件
        :param single_events: 是否需要展开循环日程
        :param page_token: 查询对应页，值有上一次请求返回的结果里对应nextPageToken
        :param max_results: 结果返回的最多数量，默认250，最多返回2500
        :param time_max: 查询时间上限
        """
        client = get_client(self)
        user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).din_id
        calendar_folder_id=''
        time_min=None
        i_cal_uid=''
        single_events=''
        page_token=''
        max_results=250
        time_max=None
      
        try:
            result = client.calendar.list(user_id, calendar_folder_id=calendar_folder_id, time_min=time_min, i_cal_uid=i_cal_uid,
                single_events=single_events, page_token=page_token, max_results=max_results, time_max=time_max)
            logging.info(">>>查询日程返回结果:{}".format(result))
            # 测试接口，待完善
        except Exception as e:
            raise UserError(e)