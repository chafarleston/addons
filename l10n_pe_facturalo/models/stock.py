from odoo import api, fields, models
from odoo.exceptions import ValidationError
from .account import REGISTER, FACTURALO_STATE
from .utils import get_response

import re
import json
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    l10n_pe_facturalo_pdf = fields.Binary(string='PDF', readonly=True, copy=False, help=u'Formato impreso de CPE')
    l10n_pe_facturalo_xml = fields.Binary(string='XML', readonly=True, copy=False, help=u'XML enviado a SUNAT')
    l10n_pe_facturalo_cdr = fields.Binary(string='CDR', readonly=True, copy=False, help=u'Constancia de respuesta SUNAT')
    l10n_pe_facturalo_filename_pdf = fields.Char(copy=False)
    l10n_pe_facturalo_filename_xml = fields.Char(copy=False)
    l10n_pe_facturalo_filename_cdr = fields.Char(copy=False)
    l10n_pe_facturalo_msg = fields.Char(string='Respuesta sunat', readonly=True, copy=False, help=u'Mensaje de respuesta de SUNAT')
    l10n_pe_facturalo_json = fields.Binary(string='JSON', readonly=True, copy=False)
    l10n_pe_facturalo_filename_json = fields.Char(copy=False)
    l10n_pe_facturalo_external = fields.Char(string='Facturalo external_id', copy=False)
    l10n_pe_facturalo_hash = fields.Char(string='Facturalo código hash', copy=False)
    l10n_pe_facturalo_state = fields.Selection(selection=FACTURALO_STATE, string='Estado CPE', default=REGISTER, copy=False,
                                            help=u'Estado de CPE según sunat')

    #mostrando empresa principal y no direccion de empresa en campo cliente
    @api.model
    def default_get(self, vals):
        res = super(StockPicking, self).default_get(vals)
        res.update({
            'partner_id': self.env["res.partner"].search([('is_company', '=', True),('id', '=', self.sale_id.partner_id.id)], limit=1, order='id').id
        })
        return res

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        self.l10n_pe_generate_correlative()
        return res

    @api.multi
    def l10n_pe_generate_correlative(self):
        sequence_id = self.picking_type_id.warehouse_id.l10n_pe_sequence_id
        if not self.l10n_pe_number and sequence_id:
            prefix = sequence_id.prefix
            number_next_actual = sequence_id.number_next_actual
            self.update({
                'l10n_pe_number': '{}{}'.format(prefix, number_next_actual),
            })
            sequence_id.next_by_id()

    @api.multi
    def l10n_pe_generate_correlative_sunat(self):
        sequence_id = self.picking_type_id.warehouse_id.l10n_pe_sequence_id
        if not self.l10n_pe_number and sequence_id:
            prefix = sequence_id.prefix
            number_next_actual = sequence_id.number_next_actual - 1
            self.update({
                'l10n_pe_number': '{}{}'.format(prefix, number_next_actual),
            })
            sequence_id.next_by_id()

    @api.multi
    def write_l10n_pe_facturalo_json(self):
        data = self.data_json()
        html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        sequence_id = self.picking_type_id.warehouse_id.l10n_pe_sequence_id
        prefix = sequence_id.prefix
        number_next_actual = sequence_id.number_next_actual - 1
        self.update({
            'l10n_pe_facturalo_json': base64.encodebytes(html_json.encode('utf-8')),
            'l10n_pe_facturalo_filename_json': '{}{}.json'.format(prefix, number_next_actual),
        })

    @api.multi
    def action_l10n_pe_validate_data_guide(self):
        if not self.l10n_pe_car_detail_ids:
            raise ValidationError(u'Ingrese al menos un vehículo')
        # if 'T' not in self.l10n_pe_number:
        #     raise ValidationError('Serie incorrecta')
        if not self.l10n_pe_addressee_id.l10n_pe_district_id or not self.l10n_pe_addressee_id.street:
            raise ValidationError(u'Verifique ubigeo y/o dirección del destinario')
        if self.l10n_pe_addressee_id.l10n_pe_district_id and len(self.l10n_pe_addressee_id.l10n_pe_district_id.code) != 8:
            raise ValidationError(u'Formato de ubigeo incorrecto del destinario')
        if not self.env.user.company_id.partner_id.l10n_pe_district_id or not \
                self.env.user.company_id.partner_id.street:
            raise ValidationError(u'Verifique ubigeo y/o domicilio del remitente')
        if self.env.user.company_id.partner_id.l10n_pe_district_id and \
                len(self.env.user.company_id.partner_id.l10n_pe_district_id.code) != 8:
            raise ValidationError(u'Formato de ubigeo incorrecto del remitente')
        if self.l10n_pe_related_document in ['01'] and not \
                re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{3}-[0-9]{4}$').match(self.l10n_pe_related_document_number):
            raise ValidationError(u'Verifique formato DAM')
        if self.l10n_pe_related_document in ['04'] and not \
                re.compile('[0-9]{3}-[0-9]{4}-[0-9]{4}').match(self.l10n_pe_related_document_number):
            raise ValidationError(u'Verifique formato numeración de manifiesto de carga')

        if not self.l10n_pe_driver_id.l10n_pe_document_number or not self.l10n_pe_driver_id.l10n_pe_document_number:
            raise ValidationError('Verifique RUC y/o tipo de documento del conductor')
        if not self.l10n_pe_carrier_id.l10n_pe_document_number or not self.l10n_pe_carrier_id.l10n_pe_document_type:
            raise ValidationError('Verifique RUC y/o tipo de documento del transportista')
        # if not self.l10n_pe_observation:
        #     raise ValidationError('Verifique campo observación')
        return True

    @api.multi
    def action_json_generate(self):
        data = self.data_json()
        if data:
            self.write_l10n_pe_facturalo_json()

    @api.multi
    def data_json(self):
        self.action_l10n_pe_validate_data_guide()
        company = self.env.user.company_id

        #guardado = self.l10n_pe_number
        return {
            'serie_documento': self.l10n_pe_number[:4],
            'numero_documento': self.l10n_pe_number[5:],
            'fecha_de_emision': self.l10n_pe_date_emission.strftime('%Y-%m-%d'),
            'hora_de_emision': self.l10n_pe_date_emission.strftime('%H:%M:%S'),
            'codigo_tipo_documento': '09',
            'datos_del_emisor': {
                'codigo_pais': company.country_id.code,
                'ubigeo': company.partner_id.zip,
                'direccion': company.street,
                'correo_electronico': company.email,
                'telefono': company.phone,
                'codigo_del_domicilio_fiscal': self.picking_type_id.warehouse_id.l10n_pe_code or '0000'
            },
            'datos_del_cliente_o_receptor': {
                'codigo_tipo_documento_identidad': self.partner_id.l10n_pe_document_type,
                'numero_documento': self.partner_id.l10n_pe_document_number,
                'apellidos_y_nombres_o_razon_social': self.partner_id.name or '',
                'nombre_comercial': self.partner_id.name or '',
                'codigo_pais': self.partner_id.country_id.code or '',
                'ubigeo': self.partner_id.zip or '',
                'direccion': self.partner_id.street or '',
                'correo_electronico': self.partner_id.email or '',
                'telefono': self.partner_id.phone or ''
            },
            'observaciones': self.note or '-',
            'codigo_modo_transporte': self.l10n_pe_model_move or '',
            'codigo_motivo_traslado': self.l10n_pe_operation_type or '',
            'descripcion_motivo_traslado': dict(self.fields_get(
                allfields=['l10n_pe_operation_type'])['l10n_pe_operation_type']['selection'])[
                self.l10n_pe_operation_type
            ],
            'fecha_de_traslado': self.l10n_pe_date_start.strftime('%Y-%m-%d'),
            'codigo_de_puerto': self.l10n_pe_shipment or '',
            'indicador_de_transbordo': 1 if self.l10n_pe_indicator else 0,
            'unidad_peso_total': 'KGM',
            'peso_total': self.l10n_pe_gross_weight,
            'numero_de_bultos': self.l10n_pe_number_of_packages,
            'numero_de_contenedor': self.l10n_pe_container or '',
            'direccion_partida': {
                'ubigeo': company.partner_id.l10n_pe_district_id.code[2:] or '',
                'direccion': company.street
            },
            'direccion_llegada': {
                'ubigeo': self.l10n_pe_addressee_id.l10n_pe_district_id.code[2:] or '',
                'direccion': self.l10n_pe_addressee_id.street
            },
            'transportista': {
                'codigo_tipo_documento_identidad': self.l10n_pe_carrier_id.l10n_pe_document_type,
                'numero_documento': self.l10n_pe_carrier_id.l10n_pe_document_number,
                'apellidos_y_nombres_o_razon_social': self.l10n_pe_carrier_id.name
            },
            'chofer': {
                'codigo_tipo_documento_identidad': self.l10n_pe_driver_id.l10n_pe_document_type,
                'numero_documento': self.l10n_pe_driver_id.l10n_pe_document_number
            },
            'numero_de_placa': self.l10n_pe_car_detail_ids and self.l10n_pe_car_detail_ids[0].code,
            'items': self.move_ids_without_package.mapped(lambda record: {
                'codigo_interno': record.product_id.default_code or '',
                'cantidad': record.quantity_done
            })
        }



    @api.multi
    def send_api_facturalo_document(self):
        data = self.data_json()
        values = get_response(self, 'dispatches', '',  data)
        self.write(values)
        self.write_l10n_pe_facturalo_json()
        # el generar de numero de documento
        self.l10n_pe_generate_correlative_sunat()
