# -*- coding: utf-8 -*-
import logging
from dingtalk.client import AppKeyClient
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def get_client(obj):
    """钉钉客户端初始化
       安装 pip3 install dingtalk-sdk
       手动尝新：pip3 install -U https://github.com/007gzs/dingtalk-sdk/archive/master.zip
    """
    din_corpid = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
    din_appkey = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appkey')
    din_appsecret = obj.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_appsecret')
    if not din_appkey and not din_appsecret and not din_corpid:
        raise UserError('钉钉设置项中的CorpId、AppKey和AppSecret不能为空')
    else:
        return AppKeyClient(din_corpid, din_appkey, din_appsecret)

