# -*- coding: utf-8 -*-
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_calendar_event = fields.Boolean(string='自动上传日程')
    auto_del_calendar_event = fields.Boolean(string='自动删除日程')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            auto_calendar_event=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.auto_calendar_event'),
            auto_del_calendar_event=self.env['ir.config_parameter'].sudo(
            ).get_param('ali_dindin.auto_del_calendar_event'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.auto_calendar_event', self.auto_calendar_event)
        self.env['ir.config_parameter'].sudo().set_param(
            'ali_dindin.auto_del_calendar_event', self.auto_calendar_event)
