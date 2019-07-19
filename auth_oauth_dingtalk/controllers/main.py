# -*- coding: utf-8 -*-
import json
import logging
import urllib

import requests
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest
import pycompat

from odoo import http
from odoo.addons.auth_oauth.controllers.main import \
    OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.ali_dindin.dingtalk.main import client
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):
    def list_providers(self):
        result = super(OAuthLogin, self).list_providers()

        for provider in result:
            if 'dingtalk' in provider['auth_endpoint']:
                return_url = request.httprequest.url_root + 'dingtalk/auth_oauth/signin/' + str(provider['id'])
                state = self.get_state(provider)
                params = dict(
                    response_type='code',
                    appid=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state='STATE',
                )
                provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))

        return result

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        user_agent = request.httprequest.user_agent.string.lower()

        if not request.session.uid and 'dingtalk' in user_agent:
            providers = request.env['auth.oauth.provider'].sudo().search([('auth_endpoint', 'ilike', 'dingtalk')])
            if not providers:
                return super(OAuthLogin, self).web_client(s_action, **kw)
            provider_id = providers[0].id

            icp = request.env['ir.config_parameter'].sudo()
            appid = icp.get_param('ali_dindin.din_login_appid')
            # 应用内免登
            # 构造如下跳转链接，此链接处理成功后，会重定向跳转到指定的redirect_uri，并向url追加临时授权码code及state两个参数。
            url = "https://oapi.dingtalk.com/connect/oauth2/sns_authorize?appid=%s&response_type=code&scope=snsapi_auth&state=STATE&redirect_uri=" % (
                appid)
            return self.redirect_dingtalk(url, provider_id)
        else:
            return super(OAuthLogin, self).web_client(s_action, **kw)

    def redirect_dingtalk(self, url, provider_id):
        url = pycompat.to_text(url).strip()
        if werkzeug.urls.url_parse(url, scheme='http').scheme not in ('http', 'https'):
            url = u'http://' + url
        url = url.replace("'", "%27").replace("<", "%3C")

        redir_url = "encodeURIComponent('%sdingtalk/auth_oauth/signin/%d' + location.hash.replace('#','?'))" % (
            request.httprequest.url_root, provider_id)
        return "<html><head><script>window.location = '%s' +%s;</script></head></html>" % (url, redir_url)


class OAuthController(Controller):

    @http.route('/dingtalk/auth_oauth/signin/<int:provider_id>', type='http', auth='none')
    def signin(self, provider_id, **kw):

        code = kw.get('code', "")
        logging.info('>>>:返回的code结果{}'.format(code))
        unionid = client.user.getuserinfo(code)
        logging.info('>>>:返回的unionid结果{}'.format(unionid))
        userid = client.user.get_userid_by_unionid(unionid)
        logging.info('>>>:返回的unionid结果{}'.format(userid))
        try:
            _logger.info("track...........")
            _logger.info("cre:%s:%s", str(provider_id), str(userid))
            credentials = request.env['res.users'].sudo().auth_oauth_dingtalk(provider_id, userid)
            _logger.info("credentials: %s", credentials)
            url = '/web'
            hash = ""
            for key in kw.keys():
                if key not in ['code', 'state']:
                    hash += '%s=%s&' % (key, kw.get(key, ""))
            if hash:
                hash = hash[:-1]
                url = '/web#' + hash
            uid = request.session.authenticate(*credentials)
            if uid is not False:
                request.params['login_success'] = True
                return http.redirect_with_hash(url)
        except AttributeError:
            url = "/web/login?oauth_error=1"
        except AccessDenied:
            # oauth credentials not valid, user could be on a temporary session
            _logger.info(
                'OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
            url = "/web/login?oauth_error=3"
            redirect = werkzeug.utils.redirect(url, 303)
            redirect.autocorrect_location_header = False
            return redirect
        except Exception as e:
            # signup error
            _logger.exception("OAuth2: %s", str(e))
            url = "/web/login?oauth_error=2"

    # def getuserinfo(self, code):
    #     """
    #     通过CODE换取用户身份

    #     :param code: requestAuthCode接口中获取的CODE
    #     :return:
    #     """
    #     try:
    #         result = client.user.getuserinfo(code)
    #         logging.info(">>>通过CODE换取用户身份返回结果:%s", result)
    #         return result
    #     except Exception as e:
    #         raise UserError(e)

    # def get_userid_by_unionid(self, unionid):
    #     """
    #     根据unionid获取成员的userid

    #     :param unionid: 用户在当前钉钉开放平台账号范围内的唯一标识
    #     :return:
    #     """
    #     try:
    #         result = client.user.get_userid_by_unionid(unionid)
    #         logging.info(">>>根据unionid获取成员的userid返回结果:%s", result)
    #         return result
    #     except Exception as e:
    #         raise UserError(e)
