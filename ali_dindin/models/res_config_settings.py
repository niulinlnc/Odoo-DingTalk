# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    din_agentid = fields.Char(string='AgentId')
    din_corpid = fields.Char(string='企业CorpId')
    din_appkey = fields.Char(string='AppKey')
    din_appsecret = fields.Char(string='AppSecret')
    din_token = fields.Boolean(string="自动获取Token")
    din_delete_extcontact = fields.Boolean(string='删除外部联系人')
    din_create_employee = fields.Boolean(string='添加员工')
    din_update_employee = fields.Boolean(string='修改员工')
    din_delete_employee = fields.Boolean(string='删除员工')
    din_create_department = fields.Boolean(string='添加部门')
    din_update_department = fields.Boolean(string='修改部门')
    din_delete_department = fields.Boolean(string='删除部门')
    din_not_get_hidden_department = fields.Boolean(string='不同步隐藏部门')
    din_login_appid = fields.Char(string='钉钉登录appId')
    din_login_appsecret = fields.Char(string='钉钉登录appSecret')
    dingtalk_redis_ip = fields.Char(string='Redis服务器IP')
    dingtalk_redis_port = fields.Char(string='Redis服务器端口')
    dingtalk_redis_db = fields.Char(string='Redis服务器数据库')

    # 安装钉钉模块
    module_dindin_attendance = fields.Boolean(
        '钉钉办公-考勤排班',
        help='钉钉办公-考勤排班.\n'
        '- This installs the module dindin_attendance.'
    )
    module_dindin_calendar = fields.Boolean(
        '钉钉办公-日程',
        help='钉钉办公-日程.\n'
        '- This installs the module dindin_calendar.'
    )
    module_dindin_approval = fields.Boolean(
        '钉钉办公-审批',
        help='钉钉办公-审批.\n'
        '- This installs the module dindin_approval.'
    )
    module_dindin_callback = fields.Boolean(
        '钉钉办公-回调管理',
        help='钉钉办公-回调管理.\n'
        '- This installs the module dindin_callback.'
    )
    module_dindin_dashboard = fields.Boolean(
        '钉钉办公-仪表盘',
        help='钉钉办公-仪表盘.\n'
        '- This installs the module dindin_dashboard.'
    )
    module_dindin_login = fields.Boolean(
        '钉钉办公-扫码与免登',
        help='钉钉办公-扫码与免登.\n'
        '- This installs the module dindin_login.'
    )
    module_dingding_hrm = fields.Boolean(
        '钉钉办公-智能人事',
        help='钉钉办公-智能人事.\n'
        '- This installs the module dingding_hrm.'
    )
    module_dindin_message = fields.Boolean(
        '钉钉办公-消息管理',
        help='钉钉办公-消息管理.\n'
        '- This installs the module dindin_message.'
    )
    module_dindin_message_template = fields.Boolean(
        '钉钉办公-消息模板',
        help='钉钉办公-消息模板.\n'
        '- This installs the module dindin_message_template.'
    )
    module_dindin_report = fields.Boolean(
        '钉钉办公-日志',
        help='钉钉办公-日志.\n'
        '- This installs the module dindin_report.'
    )

    module_dindin_usersign = fields.Boolean(
        '钉钉办公-签到',
        help='钉钉办公-签到.\n'
        '- This installs the module dindin_usersign.'
    )
    module_dindin_workrecord = fields.Boolean(
        '钉钉办公-待办事项',
        help='钉钉办公-待办事项.\n'
        '- This installs the module dindin_workrecord.'
    )
    module_dingding_health = fields.Boolean(
        '钉钉办公-运动',
        help='钉钉办公-运动.\n'
        '- This installs the module dingding_health.'
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            din_agentid=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_agentid'),
            din_corpid=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_corpid'),
            din_appkey=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_appkey'),
            din_appsecret=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_appsecret'),
            din_delete_extcontact=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_delete_extcontact'),
            din_create_employee=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_create_employee'),
            din_update_employee=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_update_employee'),
            din_delete_employee=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_delete_employee'),
            din_create_department=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_create_department'),
            din_update_department=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_update_department'),
            din_delete_department=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_delete_department'),
            din_not_get_hidden_department=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_not_get_hidden_department'),
            din_login_appid=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_login_appid'),
            din_login_appsecret=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.din_login_appsecret'),
            dingtalk_redis_ip=self.env['ir.config_parameter'].sudo().get_param(
                'ali_dindin.dingtalk_redis_ip', default='127.0.0.1'),
            dingtalk_redis_port=self.env['ir.config_parameter'].sudo().get_param(
                'ali_dindin.dingtalk_redis_port', default='6379'),
            dingtalk_redis_db=self.env['ir.config_parameter'].sudo().get_param(
                'ali_dindin.dingtalk_redis_db', default='0'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_agentid', self.din_agentid)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_corpid', self.din_corpid)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_appkey', self.din_appkey)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_appsecret', self.din_appsecret)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_delete_extcontact', self.din_delete_extcontact)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_create_employee', self.din_create_employee)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_update_employee', self.din_update_employee)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_delete_employee', self.din_delete_employee)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_create_department', self.din_create_department)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_update_department', self.din_update_department)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_delete_department', self.din_delete_department)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_not_get_hidden_department', self.din_not_get_hidden_department)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_login_appid', self.din_login_appid)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.din_login_appsecret', self.din_login_appsecret)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.dingtalk_redis_ip', self.dingtalk_redis_ip)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.dingtalk_redis_port', self.dingtalk_redis_port)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.dingtalk_redis_db', self.dingtalk_redis_db)
