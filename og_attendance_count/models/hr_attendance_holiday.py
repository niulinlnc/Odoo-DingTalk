# -*- coding: utf-8 -*-
###################################################################################
# Copyright (C) 2019 OnGood
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################
import calendar
import logging
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAttendanceHoliday(models.Model):
    _description = '法定节假日'
    _name = 'hr.attendance.holiday'
    _rec_name = 'holiday_name'

    HOLIDAYSTATUS = [
        ('00', '未使用'),
        ('01', '使用中'),
        ('02', '已失效')
    ]

    holiday_name = fields.Char('法定节假日名称')
    holiday_date = fields.Date('法定节假日')
    is_active = fields.Boolean(string=u'启用')
    
