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
{
    'name': "钉钉集成服务-一键安装",
    'summary': """钉钉集成服务""",
    'description': """ 提供便捷的一键安装服务，同时对各模块的菜单进行相应的调整。""",
    'author': "SuXueFeng",
    'website': "https://www.sxfblog.com",
    'category': 'dingding',
    'version': '2.0',
    'depends': ['dingding_base',
                'dingding_message',
                'oa_base',
                'oa_leave_attendance',
                'oa_leave_attendance',
                'dingding_hrm',
                'dingding_attendance',
                'dingding_attendance_ext',
                'odoo_wage_manage',
                ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'views/menu.xml',
    ],
    'qweb': [

    ],
}
