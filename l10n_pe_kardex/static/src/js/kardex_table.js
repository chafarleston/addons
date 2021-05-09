odoo.define('l10n_pe_kardex.kardex_table', function (require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var FieldManagerMixin = require('web.FieldManagerMixin');
    var FieldMany2one = require('web.relational_fields').FieldMany2One;
    var FieldDate = require('web.basic_fields').FieldDate;
    var rpc = require('web.rpc');
    var session = require('web.session')

    var _t = core._t;
    var QWeb = core.qweb;
    var kardex;

    FieldMany2one.include({
        _onFieldChanged: function(ev){
            var res = this._super.apply(this, ev);
            if (this.model == 'report.report_xlsx.kardex'){
                if(this.name == 'product_id'){
                    kardex.set_product_value(this.lastSetValue.id)
                }
                else if(this.name == 'location_id'){
                    kardex.set_location_value(this.lastSetValue.id)
                }
                else if(this.name == 'lot_id'){
                    kardex.set_lot_value(this.lastSetValue.id)
                }
                else if(this.name == 'category_id'){
                    kardex.set_category_value(this.lastSetValue.id)
                }
                else if(this.name == 'lot_id'){
                    kardex.set_lot_value(this.lastSetValue.id)
                }
                else if(this.name == 'company_id'){
                    kardex.set_company_value(this.lastSetValue.id)
                }
            }
            return res;
        }
    });

    FieldDate.include({
        _onFieldChanged: function (event) {
            var res = this._super.apply(this);
            if (this.model == 'report.report_xlsx.kardex'){
                var date_start = this.name == 'date_start'? event.data.changes.date_start._i: false;
                var date_end = this.name == 'date_end'? event.data.changes.date_end._i: false;
                kardex.set_date_value(date_start, date_end);
            }
            return res;
        },
    });

    var KardexTable = Widget.extend(FieldManagerMixin, {
        template: 'kardex',
        events: {
        'click .invoice_number': '_onClickInvoiceNumber',
        'click .btn-generate': '_onClickGenerate',
        },
        init: function (parent, value) {
            this._super(parent);
            this.date_start = value.data.date_start._i;
            this.date_end = value.data.date_end._i;
            kardex = this;
        },
        set_product_value: function(product_id){
            this.product_id = product_id;
        },
        set_location_value: function(location_id){
            this.location_id = location_id;
        },
        set_lot_value: function(lot_id){
            this.lot_id = lot_id;
        },
        set_category_value: function(category_id){
            this.category_id = category_id;
        },
        set_company_value: function(company_id){
            this.company_id = company_id;
        },
        set_date_value: function(date_start, date_end){
            this.date_start = date_start? date_start: this.date_start;
            this.date_end = date_end? date_end: this.date_end;
        },
        _onClickGenerate : function(){
             var self = this;
             $('.product_table_body tr.product-item').remove();
             rpc.query({
                model: 'report.report_xlsx.kardex',
                method: 'get_products',
                args: [self.product_id, self.location_id, self.date_start, self.date_end, self.lot_id, self.category_id, self.company_id]
             }).then(function(result){
                this.$product_table_body = $('.product_table_body');
                var first_row = $('<tr class="product-item"></tr>').appendTo(this.$product_table_body) 
                var fr_celd = $('<td colspan=12 class="text-right"></td</td>')
                fr_celd.append(`<b>Cantidadidad de Producto al&nbsp; ${(result[0] ? result[0].date_operation : '')}:&nbsp; ${(result[0] ? result[0].r_qty : '0')}</b>`)
                fr_celd.appendTo(first_row)
                for (var item in result){
                    var row = $('<tr class="product-item"></tr>').appendTo(this.$product_table_body);
                    $('<td></td>').text(result[item]['date_operation']).appendTo(row);

                    if(Array.isArray(result[item]['invoice_number'])){
                        var inv_list = result[item]['invoice_number']
                        var td = $('<td></td>')
                        inv_list.forEach(function(il){
                            $('<a style="cursor: pointer;" class="invoice_number" model="account.invoice"></a>')
                            .attr('id', il[0]).text(il[1])
                            .appendTo(td);
                            $('<br/>').appendTo(td)
                        })
                        td.appendTo(row)
                    } else {
                        $('<a style="cursor: pointer;" class="invoice_number" model="account.invoice"></a>')
                        .attr('type', result[item]['invoice_type'])
                        .attr('id', result[item]['invoice_id'])
                        .text(result[item]['invoice_number'])
                        .appendTo($('<td></td>').appendTo(row));
                    }

                    $('<a style="cursor: pointer;" class="invoice_number" model="stock.picking"></a>').attr('id', result[item]['obj_id']).text(result[item]['obj_number']).appendTo($('<td></td>').appendTo(row));
                    $('<a style="cursor: pointer;" class="invoice_number" model="res.partner"></a>').attr('id', result[item]['partner_id']).text(result[item]['partner']).appendTo($('<td></td>').appendTo(row));
                    $('<td></td>').text(result[item]['op']).appendTo(row);
                    $('<a style="cursor: pointer;" class="invoice_number" model="product.template"></a>').attr('id', result[item]['product_id']).text(result[item]['barcode']).appendTo($('<td></td>').appendTo(row));
                    $('<td></td>').text(result[item]['qty_in']).appendTo(row);
                    $('<td></td>').text(result[item]['qty_out']).appendTo(row);
                    $('<td></td>').text(result[item]['total_qty']).appendTo(row);
                    $('<td></td>').text(result[item]['doc_origin']).appendTo(row);
                }
             });
        },
        _onClickInvoiceNumber : function(ev){
            var self = this;
            rpc.query({
                model: 'report.report_xlsx.kardex',
                method: 'action_view',
                args: [
                    ev.currentTarget.textContent,
                    ev.currentTarget.attributes.model.textContent,
                    parseInt(ev.currentTarget.id),
                    ev.currentTarget.type
                   ]
            }).then(function(result){
                self.do_action(result, {mode: 'readonly'});
            });
        }
    });

    widgetRegistry.add('kardex_table', KardexTable);
});
