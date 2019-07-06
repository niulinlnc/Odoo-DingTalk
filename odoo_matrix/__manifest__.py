# -*- coding: utf-8 -*-
{
    'name': "Odoo Matrix",

    'summary': """Odoo企业版破解""",

    'description': """本模块仅供参考学习使用, 请在下载后24小时内删除, 因使用本模块引发的法律纠纷与作者无关。""",

    'author': "block-cat",
    'website': "https://github.com/block-cat",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ]
}