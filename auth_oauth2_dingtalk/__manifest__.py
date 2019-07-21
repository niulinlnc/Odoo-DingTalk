# -*- encoding: utf-8 -*-
{
    "name": "Dingtalk Oauth2",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base", "auth_oauth", "base_setup"],
    "author": "OnGood",
    'website': 'http://www.ongood.cn',
    "category": "Tools",
    "description": """用钉钉账号密码登陆odoo
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
