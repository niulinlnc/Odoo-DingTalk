# -*- coding: utf-8 -*-
import base64
import functools
import hashlib
import hmac
import json
import logging
import time
from urllib.parse import quote

import requests
import werkzeug.urls
import werkzeug.utils
from requests import ReadTimeout
from werkzeug.exceptions import BadRequest

from odoo import SUPERUSER_ID, api, http
from odoo import registry as registry_get
from odoo import tools
from odoo.addons.ali_dindin.dingtalk.main import client
from odoo.addons.auth_oauth.controllers.main import \
    OAuthController as Controller
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
from odoo.addons.web.controllers.main import (login_and_redirect,
                                              set_cookie_and_redirect)
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.tools import pycompat
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# helpers
# ----------------------------------------------------------


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        kw.pop('debug', False)
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper


class OAuthLogin(Home):
    def list_providers(self):
        """
        oauth2登录入口
        :param kw:
        :return:
        """
        result = super(OAuthLogin, self).list_providers()
        for provider in result:
            if 'dingtalk' in provider['auth_endpoint']:
                return_url = request.httprequest.url_root + 'dingding/auto/login'
                state = self.get_state(provider)
                params = dict(
                    response_type='code',
                    appid=provider['client_id'],  # appid 是钉钉移动应用的appId
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))

        return result


class OAuthController(Controller):
    @http.route('/dingding/auto/login/in', type='http', auth='none')
    def dingding_auto_login(self, **kw):
        """
        免登入口
        :param kw:
        :return:
        """
        logging.info(">>>用户正在使用免登...")
        data = {'corp_id': tools.config.get('din_corpid', '')}
        return request.render('auth_oauth2_dingtalk.dingding_auto_login', data)

    @http.route('/dingding/auto/login', type='http', auth='none')
    @fragment_to_query_string
    def auto_signin(self, **kw):
        """
        通过得到的【免登授权码或者临时授权码】获取用户信息
        :param kw:
        :return:
        """
        if kw.get('authcode'):  # 免登
            auth_code = kw.get('authcode')
            _logger.info("获得的auth_code: %s", auth_code)
            userinfo = self.get_user_info_by_auth_code(auth_code)
            userid = userinfo.get('userid')
            state = dict(
                d=request.session.db,
                p='dingtalk',
            )

        elif kw.get('code'):  # 扫码或密码登录
            code = kw.get('code', "")
            _logger.info("获得的code: %s", code)
            userinfo = self.get_userid_by_unionid(code)
            unionid = userinfo.get('unionid')
            userid = client.user.get_userid_by_unionid(unionid).get('userid')
            state = json.loads(kw['state'])

        mobile = client.user.get(userid).get('mobile')
        dbname = state['d']
        if not http.db_filter([dbname]):
            return BadRequest()
        provider = 'dingtalk'
        # provider = state['p']
        context = state.get('c', {})
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth_dingtalk(provider, mobile)
                cr.commit()
                action = state.get('a')
                menu = state.get('m')
                redirect = werkzeug.url_unquote_plus(state['r']) if state.get('r') else False
                url = '/web'
                if redirect:
                    url = redirect
                elif action:
                    url = '/web#action=%s' % action
                elif menu:
                    url = '/web#menu_id=%s' % menu
                resp = login_and_redirect(*credentials, redirect_url=url)
                # Since /web is hardcoded, verify user has right to land on it
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                return resp
            except AttributeError:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
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
                _logger.exception("OAuth2: %s" % str(e))
                url = "/web/login?oauth_error=2"

        return set_cookie_and_redirect(url)

    def get_userid_by_unionid(self, tmp_auth_code):
        """
        根据返回的【临时授权码】获取用户信息
        :param code:
        :return:
        """
        url = 'https://oapi.dingtalk.com/sns/getuserinfo_bycode?'
        login_appid = request.env['ir.config_parameter'].sudo(
        ).get_param('ali_dindin.din_login_appid')
        key = request.env['ir.config_parameter'].sudo(
        ).get_param('ali_dindin.din_login_appsecret')
        msg = pycompat.to_text(int(time.time() * 1000))
        _logger.info("时间戳:%s", msg)
        # ------------------------
        # 签名
        # ------------------------
        signature = hmac.new(key.encode('utf-8'), msg.encode('utf-8'),
                             hashlib.sha256).digest()
        signature = quote(base64.b64encode(signature), 'utf-8')
        data = {
            'tmp_auth_code': tmp_auth_code
        }
        headers = {'Content-Type': 'application/json'}
        new_url = "{}signature={}&timestamp={}&accessKey={}".format(
            url, signature, msg, login_appid)
        _logger.info("new_url:%s", new_url)
        try:
            result = requests.post(
                url=new_url, headers=headers, data=json.dumps(data), timeout=15)
            result = json.loads(result.text)
            logging.info(">>>钉钉登录获取用户信息返回结果%s", result)
            if result.get('errcode') == 0:
                return result.get('user_info')
            raise BadRequest(result)

        except ReadTimeout:
            return {'state': False, 'msg': '网络连接超时'}

    def get_user_info_by_auth_code(self, auth_code):
        """
        根据返回的【免登授权码】获取用户信息
        :param auth_code:免登授权码
        :return:
        """
        try:
            result = client.user.getuserinfo(auth_code)
            logging.info(">>>获取用户信息返回结果:%s", result)
            if result.get('errcode') != 0:
                return {'state': False, 'msg': "钉钉接口错误:{}".format(result.get('errmsg'))}
            return {'state': True, 'userid': result.get('userid')}
        except Exception as e:
            return {'state': False, 'msg': "登录失败,异常信息:{}".format(str(e))}


