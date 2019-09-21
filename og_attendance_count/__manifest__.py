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
    'name': "OG出品-通用考勤计算",
    'summary': """通用考勤规则与统计""",
    'description': """ 通用考勤规则与统计 """,
    'author': "OnGood",
    'website': "https://www.ongood.cn",
    'category': 'attendance',
    'version': '2.0',
    'depends': ['base', 'hr', 'web_time_widget'],
    'installable': True,
    'application': False,
    'auto_install': True,
    'data': [
        'security/attendance_security.xml',
        'security/ir.model.access.csv',
        # 'data/attendance_parameter.xml',
        'views/asset.xml',
        'views/menu.xml',
        'views/hr_attendance_group.xml',
        'views/hr_attendance_class.xml',
        'views/hr_attendance_plan.xml',
        # 'views/hr_leaves_list.xml',
        # 'views/hr_attendance_result.xml',
        # 'views/hr_attendance_record.xml',
        # 'views/user_sign_list.xml',
        'views/hr_attendance_rules.xml',
        'wizard/hr_attendance_total.xml',
    ],
    'qweb': [
        'static/xml/*.xml'
    ]

}
