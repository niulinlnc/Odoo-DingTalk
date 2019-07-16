# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.addons.ali_dindin.dingtalk.main import get_client
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingReportTemplate(models.Model):
    _name = 'dingding.report.template'
    _description = "日志模板"
    _rec_name = 'name'

    name = fields.Char(string='模板名', required=True)
    icon_url = fields.Char(string='图标url')
    report_code = fields.Char(string='模板唯一标识')
    url = fields.Char(string='模板跳转url')
    company_id = fields.Many2one(
        'res.company', string='公司', default=lambda self: self.env.user.company_id.id)

    @api.model
    def get_all_template(self):
        """
        根据用户id获取可见的日志模板列表
        根据用户userId获取当前企业下可见的日志模板列表
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=36909

        :param userid: 员工userId, 不传递表示获取所有日志模板
        :param offset: 分页游标，从0开始。根据返回结果里的next_cursor是否为空来判断是否还有下一页，
                        且再次调用时offset设置成next_cursor的值
        :param size: 分页大小，最大可设置成100
        """
        client = get_client(self)
        group = self.env.user.has_group(
            'dindin_report.dd_get_report_templategroup')
        if not group:
            raise UserError(_("不好意思，你没有权限进行本操作！"))
        try:
            result = client.report.template_listbyuserid()
            logging.info(">>>获取日志模板返回结果:%s", result)
            d_res = result['template_list']['report_template_top_vo']
            for report in d_res:
                data = {
                    'name': report.get('name'),
                    'icon_url': report.get('icon_url'),
                    'report_code': report.get('report_code'),
                    'url': report.get('url'),
                }
                template = self.env['dingding.report.template'].search(
                    [('report_code', '=', report.get('report_code'))])
                if template:
                    template.write(data)
                else:
                    self.env['dingding.report.template'].create(data)
        except Exception as e:
            raise UserError(e)

    @api.model
    def get_user_unread_count(self):
        """
        查询企业员工的日志未读数
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=37189

        :param userid: 员工id
        """
        client = get_client(self)
        emp = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.user.id)])
        if len(emp) > 1:
            return {'state': False, 'number': 0, 'msg': '登录用户关联了多个员工'}
        if emp and emp.din_id:
            try:
                result = client.report.getunreadcount(emp.din_id)
                logging.info(">>>查询员工未读日志数返回结果:%s", result)
                if result.get('errcode') == 0:
                    return {'state': True, 'number': result.get('count')}
                else:
                    return {'state': False, 'number': 0, 'msg': result.get('errmsg')}
            except Exception as e:
                return {'state': False, 'number': 0, 'msg': "网络连接失败，详情：{}".format(e)}
        else:
            return {'state': False, 'number': 0, 'msg': 'None'}
