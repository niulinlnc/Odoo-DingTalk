odoo.define('dingding.health.list.tree', function (require) {
    "use strict";

    let core = require('web.core');
    let ListController = require('web.ListController');
    let ListView = require('web.ListView');
    let viewRegistry = require('web.view_registry');
    let qweb = core.qweb;

    let DingDingHealthListController = ListController.extend({
        buttons_template: 'HealthListView.health_list_buttons',
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_get_dingding_health_list', function () {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'dingding.get.health.list',
                        target: 'new',
                        views: [[false, 'form']],
                        context: [],
                    });
                });
            }
        }
    });

    let GetDingDingHealthListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DingDingHealthListController,
        }),
    });

    viewRegistry.add('dingding_health_list_tree', GetDingDingHealthListView);
});
