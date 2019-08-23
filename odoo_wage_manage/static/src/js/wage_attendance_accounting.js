/**
 *    Copyright (C) 2019 SuXueFeng
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

odoo.define('odoo.wage.attendance.accounting.tree.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');

    let OdooWageManageAttendanceAccountingViewController = ListController.extend({
        buttons_template: 'OdooWageManageListView.wage_attendance_accounting_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                let self = this;
                this.$buttons.on('click', '.wage_attendance_accounting_but_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'wage.attendance.accounting.transient',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
                this.$buttons.on('click', '.push_down_the_pay_slip_but_class', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'wage.attendance.accounting.to.payslip.transient',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let OdooWageAttendanceAccountingListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: OdooWageManageAttendanceAccountingViewController,
        }),
    });

    viewRegistry.add('compute_wage_attendance_accounting', OdooWageAttendanceAccountingListView);
});
