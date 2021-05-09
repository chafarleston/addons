odoo.define('l10n_pe_pos.screens', function (require) {
    "use strict";

    var devices = require('point_of_sale.devices');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var screens = require('point_of_sale.screens');
    var qweb = core.qweb;
    var _t = core._t;

    screens.ReceiptScreenWidget.include({
        click_next: function(){
            this._super();
            if (this.pos.config.l10n_pe_default_partner) {
                var partner = this.pos.db.get_partner_by_id(this.pos.config.l10n_pe_default_partner[0]);
                this.pos.get_order().set_client(partner);
            }
        }
    });

    screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            this._super(parent, options);
            if (this.pos.config.l10n_pe_default_partner) {
                var partner = this.pos.db.get_partner_by_id(this.pos.config.l10n_pe_default_partner[0]);
                this.pos.get_order().set_client(partner);
            }
        },
        click_invoice_journal: function (journal) {
            var order = this.pos.get_order();

            order.l10n_pe_invoice_journal_id = journal.data('id');
            order.journal_sunat_code = journal.data('sunat-code');
            order.journal_sent_sunat = journal.data('send-sunat');
            order.journal_is_synchronous = journal.data('is-synchronous');

            $('.journal').removeClass('highlight');
            $('.journal').addClass('lowlight');
            var $journal_selected = $("[data-id='" +  order.l10n_pe_invoice_journal_id  + "']");
            $journal_selected.addClass('highlight');
        },
        render_invoice_journals: function () {
            var self = this;
            var methods = $(qweb.render('journal_list', {widget: this}));
            methods.on('click', '.journal', function () {
                self.click_invoice_journal($(this));
            });
            return methods;
        },
        validate_order: function(force_validation){
    		var self = this
    		var order = this.pos.get_order();
    		var total_paid = order.get_total_paid();
    		var client = order.get_client();

    		var confirm_popup = function(msg){
    			self.gui.show_popup('confirm',{
                    'title': _t('Please select the Customer'),
                    'body': _t('Debe seleccionar un cliente con ' + msg + ' antes de facturar un pedido'),
                    confirm: function(){
                        self.gui.show_screen('clientlist');
                    },
                });
    		};

            if(this.pos.config.l10n_pe_pos_auto_invoice){
                if(!order.journal_sunat_code){
                    this.gui.show_popup("error",{
                        "title": _t("Tipo de Documento"),
                        "body": _t("Tipo de documento es obligatorio"),
                    });
                    return;
                }
            }

    		if(client){
	    		if(!client.l10n_pe_document_type || !client.l10n_pe_document_number){
	    			confirm_popup('TIPO DE DOCUMENTO')
	    			return;
	    		}
	    		if(['03', '07', '08'].includes(order.journal_sunat_code) && order.journal_sent_sunat && total_paid >= 700 &&
	    		(!['1', '4', '7'].includes(client.l10n_pe_document_type) || client.l10n_pe_document_number.length != 8)){
	    			confirm_popup('DNI/CARNET/PASAPORTE')
	    			return;
	    		}

	    		if(['01', '07', '08'].includes(order.journal_sunat_code) && order.journal_sent_sunat &&
	    		(client.l10n_pe_document_type != '6' || client.l10n_pe_document_number.length != 11)){
	    			confirm_popup('RUC')
	    			return;
	    		}

	    		if(client.l10n_pe_document_type == '6' && !client.email){
	    			self.gui.show_popup('confirm',{
	                    'title': _t('Please select the Customer'),
	                    'body': _t('Debe seleccionar un cliente con Email  válido para realizar una factura.'),
	                    confirm: function(){
	                        self.gui.show_screen('clientlist')
	                    },
	                })
	                return;
	       		}
    		}
    		this._super(force_validation)
    	},
    	renderElement: function () {
            this._super();
            if (this.pos.config.l10n_pe_invoice_journal_ids && this.pos.config.l10n_pe_invoice_journal_ids.length > 0 && this.pos.journals) {
                var methods = this.render_invoice_journals();
                methods.appendTo(this.$('.invoice_journals'));
            }
        },

    });

    screens.OrderWidget.include({
        set_value: function(val) {
            var order = this.pos.get_order();
            if (order.get_selected_orderline()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity'){
                    order.get_selected_orderline().set_quantity(val);
                }else if( mode === 'discount'){
                    order.get_selected_orderline().set_discount(val);
                }else if( mode === 'quantity-by-price'){
                    order.get_selected_orderline().set_quantity_by_amount(val/order.get_selected_orderline().get_unit_price());
                }else if( mode === 'price'){
                    var selected_orderline = order.get_selected_orderline();
                    selected_orderline.price_manually_set = true;
                    selected_orderline.set_unit_price(val);
                }
            }
        }
    });

    screens.ClientListScreenWidget.include({
        save_client_details: function(partner){
            var l10n_pe_country = document.getElementsByClassName("client-address-country")[0],
                l10n_pe_state = document.getElementsByClassName("client-address-state")[0],
                l10n_pe_province = document.getElementsByClassName("client-address-province")[0],
                l10n_pe_district = document.getElementsByClassName("client-address-district")[0];

            if(!l10n_pe_district.value || !l10n_pe_state.value || !l10n_pe_province.value){
                this.gui.show_popup("error",{
                    "title": _t("CLIENTE"),
                    "body": _t("Departamento / provincia / distrito es obligatorio"),
                });
                return;
            }
            return this._super(partner);
        },
        change_l10n_pe_document_number: function(l10n_pe_document_type, l10n_pe_document_number) {
            var self = this;
            function get_partner_data(document_type, document_number) {
                var name = document.getElementsByClassName("name")[0],
                    address = document.getElementsByClassName("client-address-street")[0],
                    phone = document.getElementsByClassName("client-phone")[0],
                    email = document.getElementsByClassName("client-email")[0],
                    legal_name = document.getElementsByClassName("client-legal-name")[0],
                    trade_name = document.getElementsByClassName("client-trade-name")[0],
                    sunat_type = document.getElementsByClassName("client-sunat-type")[0],
                    sunat_state = document.getElementsByClassName("client-sunat-state")[0],
                    date_inscription = document.getElementsByClassName("client-date-inscription")[0],
                    date_start = document.getElementsByClassName("client-date-start")[0],
                    l10n_pe_country = document.getElementsByClassName("client-address-country")[0],
                    l10n_pe_state = document.getElementsByClassName("client-address-state")[0],
                    l10n_pe_province = document.getElementsByClassName("client-address-province")[0],
                    l10n_pe_district = document.getElementsByClassName("client-address-district")[0];

                return self._rpc({
                    model: 'res.partner',
                    method: 'l10n_pe_get_data',
                    args: [document_type, document_number]
                }).then(function (result) {
                    name.value = result.name || '';
                    address.value = result.street || '';
                    phone.value = result.phone || '';
                    email.value = result.email || '';
                    legal_name.value = result.l10n_pe_legal_name || '';
                    trade_name.value = result.l10n_pe_tradename ||  result.l10n_pe_legal_name || '';
                    l10n_pe_state.value = result.state_id;
                    l10n_pe_province.value = result.l10n_pe_province_id;
                    l10n_pe_district.value = result.l10n_pe_district_id;
                    document.getElementById("loading").classList.add('hide');
                }).fail(function (error) {
                    document.getElementById("loading").classList.add('hide');
                    alert("R.U.C, : " + document_number + " No exists!.");
                });
            }
            let document_type =  $(l10n_pe_document_type).children("option:selected").attr("code");
            if([6, 1].includes(parseInt(document_type))) {
                document.getElementById("loading").classList.remove('hide');
                get_partner_data(document_type, l10n_pe_document_number.value);
            }
        },
        change_l10n_pe_state: function(l10n_pe_state, l10n_pe_province, l10n_pe_district){
            let self = this;
            let state = $(l10n_pe_state).children("option:selected").val();
            $(l10n_pe_province).children('option').each(function(){
                if ($(this).attr("state") != state){
                   $(this).addClass("hide");
                }
                else{
                    $(this).removeClass('hide');
                    $(this).attr("selected","selected");
                }
            });
           self.change_l10n_pe_province(l10n_pe_province, l10n_pe_district);
        },
        change_l10n_pe_province: function(l10n_pe_province, l10n_pe_district){
            let self = this;
            let province = $(l10n_pe_province).children("option:selected").val();
            $(l10n_pe_district).children('option').each(function(){
                if ($(this).attr("province") != province){
                   $(this).addClass("hide");
                   $(this).prop("selected", false);
                }
                else{
                    $(this).removeClass('hide');
                    $(this).attr("selected","selected");
                }
            });
        },
        display_client_details: function(visibility,partner,clickpos){
            this._super(visibility,partner,clickpos);
            if (visibility === 'edit') {
                var contents = this.$('.client-details-contents');

                var l10n_pe_state = contents[0].childNodes[0].querySelector('.l10n_pe_state');
                var l10n_pe_province = contents[0].childNodes[0].querySelector('.l10n_pe_province');
                var l10n_pe_district = contents[0].childNodes[0].querySelector('.l10n_pe_district');
                var l10n_pe_document_type = contents[0].childNodes[0].querySelector('.l10n_pe_document_type');
                var l10n_pe_document_number = contents[0].childNodes[0].querySelector('.l10n_pe_document_number');

                l10n_pe_state.addEventListener("change", (function() {
                    this.change_l10n_pe_state(l10n_pe_state, l10n_pe_province, l10n_pe_district);
                }.bind(this)));
                l10n_pe_province.addEventListener("change", (function() {
                    this.change_l10n_pe_province(l10n_pe_province, l10n_pe_district);
                }.bind(this)));

                l10n_pe_document_number.addEventListener("change", (function() {
                    this.change_l10n_pe_document_number(l10n_pe_document_type, l10n_pe_document_number);
                }.bind(this)));

            }
        }
    });

    screens.ProductScreenWidget.include({
        click_product: function(product) {
            // if (!product.l10n_pe_product_sunat_code_id || !product.l10n_pe_type_operation_sunat){
            //     this.gui.show_popup('error',{
            //         'title': _t('FACTURACIÓN ELECTRÓNICA'),
            //         'body': _t('Configure código de producto sunat'),
            //     });
            //     return;
            // }
            if(product.to_weight && this.pos.config.iface_electronic_scale){
                this.gui.show_screen('scale',{product: product});
            }
            else{
                this.pos.get_order().add_product(product);
            }
        },
    });
});
