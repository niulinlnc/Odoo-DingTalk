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
import base64
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_phone = fields.Char(string='手机号码', help="用于使用手机验证码登录系统", copy=False)
    odoo_sms_token = fields.Char(string='SmsToken')

    @api.constrains('login_phone')
    def constrains_login_phone(self):
        """
        检查手机号码是否被占用
        :return:
        """
        for res in self:
            if res.login_phone:
                users = self.env['res.users'].sudo().search([('login_phone', '=', res.login_phone)])
                if len(users) > 1:
                    raise UserError("抱歉！{}手机号码已被'{}'占用,请解除或更换号码!".format(res.login_phone, users[0].name))

    def _set_password(self):
        for user in self:
            user.sudo().write({'odoo_sms_token': base64.b64encode(user.password.encode('utf-8'))})
        super(ResUsers, self)._set_password()
