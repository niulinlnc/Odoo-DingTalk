# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
import logging
from odoo.exceptions import UserError
import traceback

_logger = logging.getLogger(__name__)

class EnterpriseHack(models.AbstractModel):

    _inherit = "publisher_warranty.contract"

    @api.model
    def _get_sys_logs(self):
        return {
            "messages":"register successed.",
            "enterprise_info":{
                "expiration_date":"2099-12-31",
                "expiration_reason":"svip will not expired.",
                "enterprise_code": "xxxx-xxx-xx-x-0000"
            }
        }
