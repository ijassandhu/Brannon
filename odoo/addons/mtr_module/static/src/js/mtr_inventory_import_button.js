odoo.define('mtr_module.mtr_inventory_import_button', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (!this.$buttons || this.modelName !== 'inventory.record') {
                return;
            }
            if (this.$buttons.find('.o_mtr_inventory_import').length) {
                return;
            }

            var $btn = $('<button>', {
                type: 'button',
                class: 'btn btn-secondary o_mtr_inventory_import',
            }).text(_t('Import Inventory'));

            $btn.on('click', this._onInventoryImport.bind(this));

            var $create = this.$buttons.find('.o_list_button_add');
            if ($create.length) {
                $create.after($btn);
                return;
            }
            this.$buttons.append($btn);
        },

        _onInventoryImport: function () {
            return this.do_action({
                type: 'ir.actions.act_window',
                name: _t('Import Inventory'),
                res_model: 'inventory.import.wizard',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        },
    });
});
