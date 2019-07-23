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
import logging
from odoo import api, models
from odoo.exceptions import UserError
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.constrains('oauth_uid')
    def constrains_login_phone(self):
        """
        检查手机是否重复
        :return:
        """
        for res in self:
            if res.oauth_uid:
                users = self.env['res.users'].sudo().search([('oauth_uid', '=', res.oauth_uid)])
                if len(users) > 1:
                    raise UserError("抱歉！{}手机号码（令牌）已被'{}'占用,请解除或更换号码!".format(res.oauth_uid, users[0].name))

    @api.model
    def auth_oauth_sms(self, provide_id, oauth_uid):
        if provide_id == 'sms':
            user_ids = self.search([('oauth_uid', '=', oauth_uid)])
        else:
            user_ids = self.search([('oauth_provider_id', '=', provide_id), ('oauth_uid', '=', oauth_uid)])
        _logger.info("user: %s", user_ids)
        if not user_ids or len(user_ids) > 1:
            raise AccessDenied()
        return (self.env.cr.dbname, user_ids[0].login, oauth_uid)

    @api.model
    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_uid', '=', password)])
            if not res:
                raise
