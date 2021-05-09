odoo.define('hw_restaurant_ip_printer.multiprint', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var mixins = require('web.mixins');
    var Session = require('web.Session');
    var session = require('web.session');

    var QWeb = core.qweb;

    var Printer = core.Class.extend(mixins.PropertiesMixin,{
        init: function(parent,options){
            mixins.PropertiesMixin.init.call(this);
            this.setParent(parent);
            options = options || {};
            var url = options.url || 'http://localhost:8069';
            this.connection = new Session(undefined,url, { use_cors: true});
            this.host       = url;
            this.receipt_queue = [];
        },
        print: function(receipt){
            var self = this;
            console.log(this)
            if(receipt){
                this.receipt_queue.push(receipt);
            }
            function send_printing_job(){
                if(self.receipt_queue.length > 0){
                    var params = {}
                    var k = self.config.proxy_ip;
                    var r = self.receipt_queue.shift();
                    var options = {shadow: true, timeout: 5000};
                    params.ip = k.trim() !== "" ? k.split(":").slice(0,1)[0] : '127.0.0.1'
                    params.port = (k.indexOf(":") > 0 && k.split(":").slice(-1)[0] !== "") ? k.split(":").slice(-1)[0] : '9100'
                    params.receipt = r
                    session.rpc('/hw_net_printer/print_xml_receipt', params, options)
                    //self.connection.rpc('/hw_proxy/print_xml_receipt', {receipt: r}, options)
                        .then(function(){
                            send_printing_job();
                        },function(error, event){
                            self.receipt_queue.unshift(r);
                            console.log('There was an error while trying to print the order:');
                            console.log(error);
                        });
                }
            }
            send_printing_job();
        },
    });
models.load_models({
    model: 'restaurant.printer',
    fields: ['name','proxy_ip','product_categories_ids'],
    domain: null,
    loaded: function(self,printers){
        var active_printers = {};
        for (var i = 0; i < self.config.printer_ids.length; i++) {
            active_printers[self.config.printer_ids[i]] = true;
        }

        self.printers = [];
        self.printers_categories = {}; // list of product categories that belong to
                                       // one or more order printer

        for(var i = 0; i < printers.length; i++){
            if(active_printers[printers[i].id]){
                var url = printers[i].proxy_ip || '';
                if(url.indexOf('//') < 0){
                    url = 'http://'+url;
                }
                if(url.indexOf(':',url.indexOf('//')+2) < 0){
                    url = url+':8069';
                }
                var printer = new Printer(self,{url:url});
                printer.config = printers[i];
                self.printers.push(printer);

                for (var j = 0; j < printer.config.product_categories_ids.length; j++) {
                    self.printers_categories[printer.config.product_categories_ids[j]] = true;
                }
            }
        }
        self.printers_categories = _.keys(self.printers_categories);
        self.config.iface_printers = !!self.printers.length;
    },
});

});
