odoo.define('hw_escpos_network_printer.screens', function (require) {
"use strict";

    var PosScreenWidgets = require('point_of_sale.screens');
    var PosChromeWidget = require('point_of_sale.chrome');

    PosChromeWidget.Chrome.include({
        // This method instantiates all the screens, widgets, etc. 
        build_widgets: function() {
            var self = this
            _.each(this.widgets, function(widget) {
                // display the print icon for salesDetails widget if using network printer. 
                if(widget.name ==='sale_details'){
                    widget.condition = function(){ return self.pos.config.use_proxy || self.pos.config.iface_enable_network_printing; }
                }
            })
            this._super();

        },
    });


    PosScreenWidgets.ReceiptScreenWidget.include({
        print: function() {
            var self = this;
            if(self.pos.config.iface_enable_network_printing){
                this.print_xml();
                this.lock_screen(false);
            }else{
                this._super();
            }
        },
    });
});
