odoo.define('dindin_calendar.pull.dindin.calendar.button', function (require) {
    "use strict";

    let ListController = require('web.ListController');
    let Dialog = require('web.Dialog');
    let core = require('web.core');
    let QWeb = core.qweb;
    let rpc = require('web.rpc');
    let viewRegistry = require('web.view_registry');
    let KanbanController = require('web.KanbanController');
    let KanbanView = require('web.KanbanView');

    let save_data = function () {
        this.do_notify("请稍后...", "查询完成后需要刷新界面方可查看！!");
        getCalendar();
    };

    let getCalendar = function () {
        let def = rpc.query({
            model: 'calendar.event',
            method: 'list_dindin_calendar',
            args: [],
        }).then(function () {
            console.log("查询成功");
            location.reload();
        });
    };

    ListController.include({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'calendar.event') {
                let but = "<button type=\"button\" t-if=\"widget.modelName == 'calendar.event'\" class=\"btn btn-secondary o_pull_dindin_calendar\">拉取钉钉日程</button>";
                let button2 = $(but).click(this.proxy('open_action'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        open_action: function () {
            new Dialog(this, {
                title: "拉取钉钉日程",
                size: 'medium',
                buttons: [
                    {
                        text: "开始拉取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDinDinCalendar', {widget: this, data: []}))
            }).open();
        },

    });

    let DingDingCalendarKanbanController = KanbanController.extend({
        renderButtons: function ($node) {
            let $buttons = this._super.apply(this, arguments);
            let tree_model = this.modelName;
            if (tree_model == 'calendar.event') {
                let but = "<button type=\"button\" class=\"btn btn-secondary\">拉取钉钉日程</button>";
                let button2 = $(but).click(this.proxy('getDingCalendarKanbanButton'));
                this.$buttons.append(button2);
            }
            return $buttons;
        },
        getDingCalendarKanbanButton: function () {
            new Dialog(this, {
                title: "拉取钉钉日程",
                size: 'medium',
                buttons: [
                    {
                        text: "拉取",
                        classes: 'btn-primary',
                        close: true,
                        click: save_data
                    }, {
                        text: "取消",
                        close: true
                    }
                ],
                $content: $(QWeb.render('PullDinDinCalendar', {widget: this, data: []}))
            }).open();
        },
    });

    let GetDingDingCalendarKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DingDingCalendarKanbanController,
        }),
    });

    viewRegistry.add('dindin_calendar_kanban', GetDingDingCalendarKanbanView);
});
