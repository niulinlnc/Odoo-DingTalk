# -*- coding: utf-8 -*-
import json
import logging
import urllib

import requests
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest
import pycompat

from odoo import http, tools
from odoo.addons.auth_oauth.controllers.main import \
    OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.ali_dindin.dingtalk.main import client
from dingtalk.client import SecretClient
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
        token = self.get_token()  # 不同于H5微应用获取的access_token
        openid, persistent_code = self.get_persistent_code(code, token)
        sns_token = self.get_sns_token(token, openid, persistent_code)
        userinfo = self.get_userinfo(sns_token)
        userid = client.user.get_userid_by_unionid(userinfo['unionid']).get('userid')
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

    def get_token(self):
        """
        获取钉钉移动应用的ACCESS_TOKEN
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=37175

        :param appid: 由钉钉开放平台提供给开放应用的唯一标识
        :param appsecret: 由钉钉开放平台提供的密钥
        """
        params = request.env['ir.config_parameter'].sudo()

        appid = params.get_param('ali_dindin.din_login_appid', default='')
        appscret = params.get_param('ali_dindin.din_login_appsecret', default='')
        if not appid or not appscret:
            raise werkzeug.exceptions.NotFound()

        params = dict(
            appid=appid,
            appsecret=appscret
        )
        url = "https://oapi.dingtalk.com/sns/gettoken"

        link = "%s?%s" % (url, werkzeug.url_encode(params))
        urlRequest = urllib.request.Request(link)
        urlResponse = urllib.request.urlopen(urlRequest).read()
        result = json.loads(str(urlResponse, encoding='utf-8'))
        if result['errcode'] == 0:
            return result['access_token']
        else:
            raise werkzeug.exceptions.BadRequest(result['errmsg'])

    def get_persistent_code(self, tmp_auth_code, token):
        """
        获取用户授权的持久授权码
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=37161

        :param tmp_auth_code: 用户授权给钉钉开放应用的临时授权码
        """
        params = dict(access_token=token)
        body = {"tmp_auth_code": tmp_auth_code}
        url = 'https://oapi.dingtalk.com/sns/get_persistent_code'
        link = "%s?%s" % (url, werkzeug.url_encode(params))

        result = requests.post(link, json=body, ).text
        result = json.loads(result)
        if result['errcode'] == 0:
            return result['openid'], result['persistent_code']
        else:
            raise werkzeug.exceptions.BadRequest(result['errmsg'])

    def get_sns_token(self, token, openid, persistent_code):
        """
        获取用户授权的SNS_TOKEN
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=37148

        :param persistent_code: 用户授权给钉钉开放应用的持久授权码
        :param openid: 用户的openid
        """
        params = dict(access_token=token)
        body = {
            "openid": openid,
            "persistent_code": persistent_code
        }
        url = 'https://oapi.dingtalk.com/sns/get_sns_token'
        link = "%s?%s" % (url, werkzeug.url_encode(params))

        result = requests.post(link, json=body, ).text
        result = json.loads(result)
        if result['errcode'] == 0:
            return result['sns_token']
        else:
            raise werkzeug.exceptions.BadRequest(result['errmsg'])

    def get_userinfo(self, sns_token):
        """
        获取用户授权的个人信息
        文档地址：https://open-doc.dingtalk.com/docs/api.htm?apiId=37160
        :param sns_token: 用户授权给开放应用的token
        """
        params = dict(sns_token=sns_token)

        url = 'https://oapi.dingtalk.com/sns/getuserinfo'

        result = requests.get(url, params).text
        result = json.loads(result)
        if result['errcode'] == 0:
            return result['user_info']
        else:
            raise werkzeug.exceptions.BadRequest(result['errmsg'])

    # def get_persistent_code(self, code):

    #     try:
    #         result = client.tbdingding.dingtalk_oapi_sns_get_persistent_code(tmp_auth_code=code)
    #         logging.info('>>>:获取persistent_code返回结果%s', result)
    #         return result['openid'], result['persistent_code']
    #     except Exception as e:
    #         raise UserError(e)

    # def get_sns_token(self, openid, persistent_code):

    #     try:
    #         result = client.tbdingding.dingtalk_oapi_sns_get_sns_token(persistent_code=persistent_code, openid=openid)
    #         logging.info('>>>:获取sns_token返回结果%s', result)
    #         return result['sns_token']
    #     except Exception as e:
    #         raise UserError(e)

    # def get_userinfo(self, sns_token):

    #     try:
    #         result = client.tbdingding.dingtalk_oapi_sns_getuserinfo(sns_token=sns_token)
    #         logging.info('>>>:获取user_info返回结果%s', result)
    #         return result['user_info']
    #     except Exception as e:
    #         raise UserError(e)

    # def get_userid_by_unionid(self, access_token, unionid):
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

    # def get_access_token(self):

    #     corp_id = tools.config.get('din_corpid', '').strip()
    #     corp_secret = tools.config.get('din_corp_secret', '').strip()
    #     try:
    #         result = SecretClient(corp_id, corp_secret)
    #         logging.info('>>>:获取user_info返回结果%s', result)
    #         return result['access_token']
    #     except Exception as e:
    #         raise UserError(e)
