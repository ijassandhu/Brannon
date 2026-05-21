odoo.define('mtr_module.mtr_join_report_refresh_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.$buttons || this.modelName !== 'mtr.inventory.join.report') {
                return;
            }
            if (this.$buttons.find('.o_mtr_join_report_refresh').length) {
                return;
            }

            var $btn = $('<button>', {
                type: 'button',
                class: 'btn btn-primary o_mtr_join_report_refresh',
            }).text(_t('Refresh Join Report'));

            $btn.on('click', this._onRefreshJoinReport.bind(this));

            var $create = this.$buttons.find('.o_list_button_add');
            if ($create.length) {
                $create.after($btn);
                return;
            }
            this.$buttons.append($btn);
        },

        _onRefreshJoinReport: function () {
            var self = this;
            return this._rpc({
                model: 'mtr.inventory.join.report',
                method: 'refresh_view',
                args: [],
            }).then(function () {
                self.do_notify(_t('Join Report'), _t('The join report has been refreshed.'));
                return self.reload();
            }).guardedCatch(function (err) {
                if (err && err.data) {
                    self.call('crash_manager', 'rpc_error', err);
                } else {
                    self.do_warn(_t('Join Report'), _t('Refresh failed. Please check server logs.'));
                }
            });
        },
    });
});
