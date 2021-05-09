odoo.define('hw_escpos_network_printer.devices', function (require) {
"use strict";
    var session = require('web.session');
    var PosDevices = require('point_of_sale.devices');

    // this object interfaces with the local network printer to print xml receipt.
    // overrides to direct network printng to 'hw_net_printer'
    PosDevices.ProxyDevice.include({

        message : function(name,params){
            var self = this
            var callbacks = this.notifications[name] || [];
            for(var i = 0; i < callbacks.length; i++){
                callbacks[i](params);
            }
            if(this.pos.config.iface_enable_network_printing && params){
                params.ip = this.pos.config.iface_network_printer_ip_address
                params.port = this.pos.config.iface_network_printer_port
                return session.rpc('/hw_net_printer/' + name, params || {}, {shadow: true}).then(function(results){
                    if(results.error){
                        self.pos.gui.show_popup('error', {title: _('Network Printer Error'), body: JSON.stringify(results.message, null, '..........')})
                    }
                });
            }else{
                if(this.get('status').status !== 'disconnected'){
                    return this.connection.rpc('/hw_proxy/' + name, params || {}, {shadow: true});
                }else{
                    return (new $.Deferred()).reject();
                }
            }
        },
    });
});
