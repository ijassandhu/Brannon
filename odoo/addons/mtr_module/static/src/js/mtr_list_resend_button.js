odoo.define('mtr_module.mtr_list_resend_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.$buttons || this.modelName !== 'mtr.data') {
                return;
            }
            if (this.$buttons.find('.o_mtr_resend_pending').length) {
                return;
            }
            var $btn = $(core.qweb.render('mtr_module.MtrResendPendingButton'));
            $btn.on('click', this._onResendPending.bind(this));
            var $actionMenu = this.$buttons.find('.o_dropdown, .o-dropdown, .o_dropdown_more');
            if ($actionMenu.length) {
                $actionMenu.first().before($btn);
                return;
            }
            var $create = this.$buttons.find('.o_list_button_add');
            if ($create.length) {
                $create.after($btn);
                return;
            }
            this.$buttons.append($btn);
        },

        _onResendPending: function () {
            var self = this;
            return this._rpc({
                model: 'mtr.data',
                method: 'action_resend_pending_to_n8n',
                args: [[]],
            }).then(function (result) {
                if (result && result.type) {
                    return self.do_action(result);
                }
                self.do_notify(_t('Resend Pending'), _t('Request sent.'));
            }).guardedCatch(function (err) {
                if (err && err.data) {
                    self.call('crash_manager', 'rpc_error', err);
                } else {
                    self.do_warn(_t('Resend Pending'), _t('Request failed. Please check server logs.'));
                }
            });
        },
    });
});
