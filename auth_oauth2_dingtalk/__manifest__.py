# -*- encoding: utf-8 -*-
{
    "name": "Dingtalk Oauth2",
    "version": "12.1.9.7.21",
    "license": "AGPL-3",
    "depends": ["base", "auth_oauth", "base_setup", "ali_dindin"],
    "author": "OnGood",
    'website': 'http://www.ongood.cn',
    "category": "Tools",
    "description": """用钉钉账号密码/扫码登陆odoo，应用内免登
    """,
    "data": [
        'data/auth_oauth_data.xml',
        'views/auto_templates.xml',
        'views/auth_oauth_templates.xml',
    ],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
    'images': ['static/description/banner.jpg', 'static/description/main_screenshot.png'],
    'installable': True,
    'active': False,
}
