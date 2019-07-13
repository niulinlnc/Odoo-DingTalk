# -*- coding: utf-8 -*-
import json
import logging
import random
import string
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.ali_dindin.models.dingtalk_client import get_client

_logger = logging.getLogger(__name__)


class DinDinCallback(models.Model):
    _name = 'dindin.users.callback'
    _inherit = ['mail.thread']
    _description = "钉钉回调管理"
    _rec_name = 'company_id'

    @api.model
    def _get_default_aes_key(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 43))

    @api.model
    def _get_default_token(self):
        return ''.join(random.sample(string.ascii_letters + string.digits, 10))

    @api.model
    def _get_default_localhost(self):
        return "{}callback/eventreceive".format(request.httprequest.host_url)

    ValueType = [
        ('all', '所有事件'),
        ('00', '通讯录事件'),
        ('01', '群会话事件'),
        ('02', '签到事件'),
        ('03', '审批事件'),
    ]

    company_id = fields.Many2one(comodel_name='res.company', string=u'公司',
                                 default=lambda self: self.env.user.company_id.id)
    call_id = fields.Many2one(comodel_name='dindin.users.callback.list', string=u'回调类型', ondelete='cascade')
    value_type = fields.Selection(string=u'注册事件类型', selection=ValueType, default='all', copy=False)
    token = fields.Char(string='Token', default=_get_default_token, size=50)
    aes_key = fields.Char(string='数据加密密钥', default=_get_default_aes_key, size=50)
    url = fields.Char(string='回调URL', size=200, default=_get_default_localhost)
    state = fields.Selection(string=u'状态', selection=[('00', '未注册'), ('01', '已注册')], default='00', copy=False)
    call_ids = fields.Many2many(comodel_name='dindin.users.callback.list', relation='dindin_users_callback_and_list_ref',
                                column1='call_id', column2='list_id', string=u'回调类型列表', copy=False)
    
    _sql_constraints = [
        ('value_type_uniq', 'unique(value_type)', u'事件类型重复!'),
    ]

    @api.onchange('value_type')
    def onchange_value_type(self):
        if self.value_type:
            call_ids = list()
            if self.value_type == 'all':
                for li in self.env['dindin.users.callback.list'].sudo().search([]):
                    call_ids.append(li.id)
            else:
                for li in self.env['dindin.users.callback.list'].sudo().search([('value_type', '=', self.value_type)]):
                    call_ids.append(li.id)
            self.call_ids = [(6, 0, call_ids)]

    @api.multi
    def register_call_back(self):
        """
        注册事件
        :return:
        """
        client = get_client(self)
        logging.info(">>>注册事件...")
        for res in self:
            call_list = list()
            for call in res.call_ids:
                call_list.append(call.value)
            call_back_tags = call_list if call_list else ''
            token = res.token if res.token else ''
            aes_key = res.aes_key if res.aes_key else ''
            url = res.url if res.url else ''
            try:
                result = client.callback.register_call_back(call_back_tags, token, aes_key, url)
                logging.info(">>>注册回调事件返回结果:{}".format(result))
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                    self.message_post(body=u"注册事件成功")
                else:
                    raise UserError("注册失败！原因:{}".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)
        logging.info(">>>注册事件End...")

    @api.multi
    def update_call_back(self):
        """
        更新事件
        :return:
        """
        client = get_client(self)
        for res in self:
            call_list = list()
            for call in res.call_ids:
                call_list.append(call.value)
            call_back_tags = call_list if call_list else ''
            token = res.token if res.token else ''
            aes_key = res.aes_key if res.aes_key else ''
            url = res.url if res.url else ''
            try:
                result = client.callback.update_call_back(call_back_tags, token, aes_key, url)
                logging.info(">>>更新回调事件返回结果:{}".format(result))
                if result.get('errcode') == 0:
                    self.write({'state': '01'})
                    self.message_post(body=u"更新事件成功")
                else:
                    raise UserError("更新失败！原因:{}".format(result.get('errmsg')))
            except Exception as e:
                raise UserError(e)

    @api.multi
    def unlink(self):
        """
        重写删除方法
        :return:
        """
        for res in self:
            if res.state == '01':
                self.delete_call_back(res.token)
        super(DinDinCallback, self).unlink()

    @api.model
    def delete_call_back(self, call_token):
        client = get_client(self)
        logging.info(">>>删除事件...")
        try:
            result = client.callback.delete_call_back()
            logging.info(">>>删除回调事件返回结果:{}".format(result))
            if result.get('errcode') == 0:
                logging.info("已删除token为{}的回调事件".format(call_token))
            else:
                pass
        except Exception as e:
            logging.info("Token为{}的回调事件删除异常，详情为:{}".format(call_token,e))
            self.state == '00'
            # raise UserError(e)
        logging.info(">>>删除事件End...")

    @api.model
    def get_all_call_back(self):
        """
        获取所有回调列表
        :return:
        """
        client = get_client(self)
        try:
            result = client.callback.get_call_back()
            logging.info(">>>获取所有回调事件返回结果:{}".format(result))
            if result.get('errcode') != 0:
                return {'state': False, 'msg': result.get('errmsg')}
            else:
                tag_list = list()
                for tag in result.get('call_back_tag'):
                    callback_list = self.env['dindin.users.callback.list'].search([('value', '=', tag)])
                    if callback_list:
                        tag_list.append(callback_list[0].id)
                callback = self.env['dindin.users.callback'].search([('company_id', '=', self.env.user.company_id.id)])
                data = {
                    'call_ids': [(6, 0, tag_list)],
                    'url': result.get('url'),
                    'aes_key': result.get('aes_key'),
                    'token': result.get('token'),
                    'company_id': self.env.user.company_id.id,
                    'state': '01',
                }
                if callback:
                    callback.write(data)
                else:
                    self.env['dindin.users.callback'].create(data)
                return {'state': True}
        except Exception as e:
            raise UserError(e)
