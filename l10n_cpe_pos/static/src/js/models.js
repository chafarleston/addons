odoo.define('l10n_pe_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var qweb = core.qweb;

    var _super_Order = models.Order.prototype;
    var _super_PosModel = models.PosModel.prototype;

    models.load_fields('res.company', ['street', 'city', 'state_id', 'zip', 'l10n_pe_document_number']);
    models.load_fields('res.partner', ['name','street','state_id','country_id','vat', 'phone','zip','mobile','email','barcode','write_date',
        'property_account_position_id','property_product_pricelist', 'l10n_pe_district_id', 'l10n_pe_province_id', 'l10n_pe_document_type',
         'l10n_pe_document_number', 'l10n_pe_legal_name', 'l10n_pe_tradename']);
    models.load_fields('account.journal', ['type', 'sequence', 'l10n_pe_document_type_id']);
    models.load_fields('product.product', ['display_name', 'list_price', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id', 'taxes_id',
                 'barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description',
                 'product_tmpl_id','tracking', 'l10n_pe_product_sunat_code_id', 'l10n_pe_type_operation_sunat']);

    models.load_fields('uom.uom', ['l10n_pe_sunat_code_id']);

    models.load_models([{
        model:  'l10n_pe.res.country.province',
        fields: ['name', 'code', 'state_id'],
        domain: function(self){ return [['country_id','=',self.company.country_id[0]]]; },
        loaded: function(self, provinces){
            self.l10n_pe_provinces = provinces;
        },
    },{
        model:  'res.country.state',
        fields: ['name', 'code', 'country_id'],
        domain: function(self){ return [['country_id','=',self.company.country_id[0]]]; },
        loaded: function(self, states){
            self.l10n_pe_states = states;
        },
    },{
        model:  'l10n_pe.res.country.district',
        fields: ['name', 'province_id'],
        loaded: function(self, districts){
            self.l10n_pe_districts = districts;
        },
    },{
        model: 'account.journal',
        fields: [],
        domain: function (self) {
            return [['id', 'in', self.config.l10n_pe_invoice_journal_ids]];
        },
        loaded: function (self, journals) {
            self.journals = journals;
            self.journal_by_id = {};
            for (var i = 0; i < journals.length; i++) {
                self.journal_by_id[journals[i]['id']] = journals[i];
            }
        }
    },{
        model: 'l10n_pe.datas',
        fields: ['name', 'code', 'table_code'],
        domain: [['table_code', 'in', ['PE.CPE.CATALOG6']]],
        loaded: function (self, partner_document_types) {
            self.partner_document_types = partner_document_types;
        }
    }
    ]);

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            if (this.pos.config.l10n_pe_pos_auto_invoice) {
                this.to_invoice = true;
            }
        },
        init_from_JSON: function (json) {
            var res = _super_Order.init_from_JSON.apply(this, arguments);
            if (json.to_invoice) {
                this.to_invoice = json.to_invoice;
            }
            if (json.l10n_pe_invoice_journal_id) {
                this.l10n_pe_invoice_journal_id = json.l10n_pe_invoice_journal_id;
            }
            return res;
        },
        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            if (this.l10n_pe_invoice_journal_id) {
                json.l10n_pe_invoice_journal_id = this.l10n_pe_invoice_journal_id;
            }
            return json;
        },
        set_l10n_pe_invoice_journal: function(l10n_pe_invoice_journal_id){
            this.assert_editable();
            this.set('l10n_pe_invoice_journal_id', l10n_pe_invoice_journal_id);
        },
        get_l10n_pe_invoice_journal: function(){
            return this.get('l10n_pe_invoice_journal_id');
        },
    });

    models.Orderline = models.Orderline.extend({
        set_quantity_by_amount: function (amount) {
            this.set_quantity(amount);
            this.trigger('change',this);
        }
    });

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var partner_model = _.find(this.models, function (model) {
                return model.model === 'res.partner';
            });
            partner_model.fields.push('vat');
            _super_PosModel.initialize.apply(this, arguments);
        },
        push_and_invoice_pos_order: function (order) {
            var self = this;
            var invoiced = new $.Deferred();

            if (!order.get_client()) {
                invoiced.reject({code: 400, message: 'Missing Customer', data: {}});
                return invoiced;
            }
            var order_id = this.db.add_order(order.export_as_JSON());
            this.flush_mutex.exec(function () {
                var done = new $.Deferred(); // holds the mutex
                var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout: 30000, to_invoice: true});
                transfer.fail(function (error) {
                    invoiced.reject(error);
                    done.reject();
                });
                transfer.pipe(function (order_server_id) {
                    invoiced.resolve();
                    done.resolve();
                });
                return done;
            });
            return invoiced;
        },
        push_and_invoice_order: function () {
            var self = this;
            return self.push_and_invoice_pos_order.apply(this, arguments).then(function () {
                var order = self.get_order();
                self.order = order;
                if (order.is_to_invoice()) {
                    return rpc.query({
                        model: 'pos.order',
                        method: 'search_read',
                        domain: [['pos_reference', '=', order['name']]],
                        fields: ['invoice_id'],
                    }).then(function (orders) {
                        if (orders.length >= 1) {
                            var invoice = orders[0]['invoice_id'];
                            return rpc.query({
                                model: 'account.invoice',
                                method: 'search_read',
                                domain: [['id', '=', invoice[0]]],
                                fields: ['number', 'journal_id', 'l10n_pe_amount_text','l10n_pe_facturalo_hash'],
                            }).then(function (invoices) {
                                if (invoices.length >= 1) {
                                    self.order.invoice_number = invoices[0]['number'].toUpperCase();
                                    self.order.l10n_pe_amount_text = invoices[0]['l10n_pe_amount_text'].toUpperCase();
                                    self.order.l10n_pe_facturalo_hash = invoices[0]['l10n_pe_facturalo_hash'];
                                    return rpc.query({
                                        model: 'account.journal',
                                        method: 'search_read',
                                        domain: [['id', '=', invoices[0]['journal_id'][0]]],
                                        fields: ['l10n_pe_sunat_code', 'name'],
                                    }).then(function (journals) {
                                        self.order.l10n_pe_invoice_journal_id = journals[0]['l10n_pe_invoice_journal_id'];
                                        self.order.journal_name = journals[0]['name'].toUpperCase();
                                    }).fail(function (error) {
                                    })
                                }
                            }).fail(function (error) {
                                console.log(error);
                            })
                        }
                    }).fail(function (error) {
                        console.log(error);
                    })
                }
            });
        }
    });
});
