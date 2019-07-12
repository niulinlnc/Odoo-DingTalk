# -*- coding: utf-8 -*-
import json
import logging
import requests
import time
from requests import ReadTimeout
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.ali_dindin.models.dingtalk_client import get_client, stamp_to_time

_logger = logging.getLogger(__name__)


class DingDingReportUser(models.Model):
    _name = 'dingding.report.user'
    _description = "用户日志"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string=u'日志名称', required=True)
    report_type = fields.Many2one(comodel_name='dingding.report.template', string=u'日志类型')
    department_id = fields.Many2one(comodel_name='hr.department', string=u'部门')
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', domain=[('din_id', '!=', '')], required=True)
    report_id = fields.Char(string='日志Id')
    remark = fields.Text(string='日志备注')
    report_date = fields.Date(string=u'创建日期')
    company_id = fields.Many2one('res.company', string='公司', default=lambda self: self.env.user.company_id.id)
    line_ids = fields.One2many(comodel_name='dingding.report.user.line', inverse_name='rep_id', string=u'日志列表')
    read_num = fields.Integer(string='已读人数', default=0)
    comment_num = fields.Integer(string='评论个数', default=0)
    comment_user_num = fields.Integer(string='去重后评论数', default=0)
    like_num = fields.Integer(string='点赞人数', default=0)
    people_read_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_read_list_rel',
                                        column1='report_id', column2='emp_id', string=u'已读人员')
    people_receive_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_receive_list_rel',
                                           column1='report_id', column2='emp_id', string=u'日志接收人')
    people_like_list = fields.Many2many(comodel_name='hr.employee', relation='d_report_user_and_like_list_rel',
                                        column1='report_id', column2='emp_id', string=u'点赞人员')
    comment_ids = fields.One2many(comodel_name='dingding.report.comments.list', inverse_name='rep_id', string=u'评论列表')

    @api.multi
    def get_report_number_info(self):
        """
        获取日志统计数据（已读人数、评论个数、去重个数、点赞人数）
        :return:
        """
        for res in self:
            report_id = res.report_id
            try:
                client = get_client(self)
                result = client.report.statistics(report_id)
                logging.info(">>>获取日志统计数据返回结果{}".format(result))
                d_res = result
                data = {
                    'read_num': d_res.get('read_num'),
                    'comment_num': d_res.get('comment_num'),
                    'comment_user_num': d_res.get('comment_user_num'),
                    'like_num': d_res.get('like_num'),
                }
                res.write(data)
            except Exception as e:
                raise UserError(e)
            # 获取日志相关人员列表
            self.get_report_receivers(res)
            # 获取日志接收人列表
            self.get_report_receives(res)
            # 获取评论详情
            self.get_report_comments(res)

    @api.model
    def get_report_receivers(self, res):
        """
        获取获取已读人员与点赞人员列表
        :param res:
        :return:
        """
        # 获取已读人员
        report_id = res.report_id
        _type = 0
        try:
            client = get_client(self)
            result = client.report.statistics_listbytype(report_id, _type, offset=0, size=100)
            logging.info(">>>获取已读人员列表返回结果{}".format(result))
            d_res = result.get('userid_list')
            if d_res:
                people_read_list = list()
                for user_id in d_res.get('string'):
                    emp = self.env['hr.employee'].search([('din_id', '=', user_id)])
                    if emp:
                        people_read_list.append(emp.id)
                res.write({'people_read_list': [(6, 0, people_read_list)]})
        except Exception as e:
            raise UserError(e)
        # 获取点赞人员
        report_id = res.report_id
        _type = 2
        try:
            client = get_client(self)
            result = client.report.statistics_listbytype(report_id, _type, offset=0, size=100)            
            logging.info(">>>获取点赞人员列表返回结果{}".format(result))
            d_res = result.get('userid_list')
            if d_res:
                people_like_list = list()
                for user_id in d_res.get('string'):
                    emp = self.env['hr.employee'].search([('din_id', '=', user_id)])
                    if emp:
                        people_like_list.append(emp.id)
                res.write({'people_like_list': [(6, 0, people_like_list)]})
        except Exception as e:
            raise UserError(e)
        return True

    @api.model
    def get_report_receives(self, res):
        """
        获取日志接收人（分享人）列表
        :param res:
        :return:
        """
        report_id = res.report_id
        try:
            client = get_client(self)
            result = client.report.receiver_list(report_id, offset=0, size=100)  
            logging.info(">>>获取分享人员列表返回结果{}".format(result))
            d_res = result.get('userid_list')
            if d_res:
                people_receive_list = list()
                for user_id in d_res.get('string'):
                    emp = self.env['hr.employee'].search([('din_id', '=', user_id)])
                    if emp:
                        people_receive_list.append(emp.id)
                res.write({'people_receive_list': [(6, 0, people_receive_list)]})
        except Exception as e:
            raise UserError(e)
        return True

    @api.model
    def get_report_comments(self, res):
        """
        获取日志评论详情
        :param res:
        :return:
        """
        report_id = res.report_id
        try:
            client = get_client(self)
            result = client.report.comment_list(report_id, offset=0, size=20)  
            logging.info(">>>获取日志评论详情返回结果{}".format(result))
            d_res = result.get('comments')
            if d_res:
                comment_list = list()
                for comment in d_res.get('report_comment_vo'):
                    emp = self.env['hr.employee'].sudo().search([('din_id', '=', comment.get('userid'))])
                    if emp:
                        comment_list.append((0, 0, {
                            'emp_id': emp[0].id,
                            'report_comment': comment.get('content'),
                            'report_create_time': comment.get('create_time'),
                            'rep_id': res.id,
                        }))
                res.comment_ids = False
                res.write({'comment_ids': comment_list})
        except Exception as e:
            raise UserError(e)
        return True


class DingDingReportUserLine(models.Model):
    _name = 'dingding.report.user.line'
    _description = "日志列表"
    _rec_name = 'rep_id'

    rep_id = fields.Many2one(comodel_name='dingding.report.user', string=u'用户日志', ondelete='cascade')
    sequence = fields.Integer(string=u'序号')
    title = fields.Char(string='标题')
    content = fields.Text(string=u'内容')


class GetUserDingDingReportList(models.TransientModel):
    _name = 'get.dingding.user.report.list'
    _description = "获取员工日志列表"
    _rec_name = 'start_time'

    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'员工', domain=[('din_id', '!=', '')])
    start_time = fields.Datetime(string=u'开始日期', required=True, default=str(fields.datetime.now()))
    end_time = fields.Datetime(string=u'结束日期', required=True, default=str(fields.datetime.now()))
    report_type = fields.Many2one(comodel_name='dingding.report.template', string=u'日志类型')

    @api.multi
    def get_report_by_user(self):
        """
        查询企业员工发出的日志列表

        :param start_time: 查询起始时间
        :param end_time: 查询截止时间
        :param cursor: 查询游标，初始传入0，后续从上一次的返回值中获取
        :param size: 每页数据量
        :param template_name: 要查询的模板名称（可选）
        :param userid: 员工的userid（可选）
        """
        for res in self:
            group = self.env.user.has_group('dindin_report.dd_get_user_report_list')
            if not group:
                raise UserError("不好意思，你没有权限进行本操作！")
            cursor = 0
            size = 20
            while True:
                start_time = self.start_time
                end_time = self.end_time
                cursor = cursor
                size = size
                userid = res.employee_id.din_id if res.employee_id else ''
                template_name = res.report_type.name if res.report_type else ''
                logging.info(">>>查询游标返回结果:{}".format(cursor))
                try:
                    client = get_client(self)
                    result = client.report.list(start_time, end_time, cursor=cursor, size=size, template_name=template_name, userid=userid)
                    logging.info(">>>获取日志列表返回结果:{}".format(result))
                    d_res = result.get('data_list')
                    for data_list in d_res['report_oapi_vo']:
                        emp = self.env['hr.employee'].search([('name', '=', data_list.get('creator_name'))])
                        template = self.env['dingding.report.template'].search([('name', '=', data_list.get('template_name'))])
                        data = {
                            'name': data_list.get('template_name'),
                            'report_type': template[0].id if template else False,
                            'remark': data_list.get('remark'),
                            'report_id': data_list.get('report_id'),
                            'department_id': emp[0].department_id.id if emp and emp.department_id else False,
                            'employee_id': emp[0].id if emp else False,
                            'report_date': stamp_to_time(data_list.get('create_time')),
                        }
                        report_list = list()
                        for content in data_list['contents']['json_object']:
                            report_list.append((0, 0, {
                                'sequence': int(content.get('sort')),
                                'title': content.get('key'),
                                'content': content.get('value'),
                            }))
                        data.update({'line_ids': report_list})
                        report = self.env['dingding.report.user'].search([('report_id', '=', data_list.get('report_id'))])
                        if report:
                            report.line_ids = False
                            report.write(data)
                        else:
                            self.env['dingding.report.user'].create(data)

                    if result.get('has_more'):
                        cursor = result.get('next_cursor')
                        size = 20
                    else:
                        break
                    
                except Exception as e:
                    raise UserError(e)
        action = self.env.ref('dindin_report.dingding_report_user_action').read()[0]
        return action

class DingDingReportCommentsList(models.Model):
    _name = 'dingding.report.comments.list'
    _description = "日志评论列表"
    _rec_name = 'rep_id'

    sequence = fields.Integer(string=u'序号')
    emp_id = fields.Many2one('hr.employee', string='评论人', required=True)
    report_comment = fields.Text(string='评论内容')
    report_create_time = fields.Char(string='评论时间')
    rep_id = fields.Many2one('dingding.report.user', string='用户日志')
