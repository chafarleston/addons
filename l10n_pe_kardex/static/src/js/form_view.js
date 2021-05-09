odoo.define('facturaloperu_kardex.form_view', function (require) {
    "use strict";
    var BasicView = require('web.BasicView');
    var Context = require('web.Context');
    var core = require('web.core');
    var FormController = require('web.FormController');
    var FormRenderer = require('web.FormRenderer');
    var FormView = require('web.FormView');

    var _lt = core._lt;
    FormView.include({
        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
            if ('action' in params && 'flags' in params.action && 'mode' in params.action.flags) {
                var mode = params.action.flags.mode;
                this.controllerParams.defaultButtons = false;
                this.controllerParams.mode = mode;
                this.rendererParams.mode = mode;
            }
        }
    });
});