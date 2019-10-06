/**
 *    Copyright (C) 2019 OnGood
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 **/

odoo.define('og_attendance_count.attendance.info.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let OdooHrAttendanceInfoViewController = ListController.extend({
        buttons_template: 'OdooHrManageListView.hr_attendance_info_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let self = this;
                this.$buttons.on('click', '.compute_attendance_info_buttons_but_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'hr.attendance.info.tran',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let OdooHrAttendanceInfoManageListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: OdooHrAttendanceInfoViewController,
        }),
    });

    viewRegistry.add('hr_attendance_info_js_class', OdooHrAttendanceInfoManageListView);
});
