# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError, Warning
from .utils import get_response, send_request

import base64
import json
import requests
import urllib3
import re

REGISTER = 'register'
SEND = 'send'
SUCCESS = 'success'
OBSERVED = 'observed'
REJECT = 'reject'
NULL = 'null'
NULLABLE = 'nullable'

FACTURALO_STATE = [
    (REGISTER, 'Registrado'),
    (SEND, 'Enviado'),
    (SUCCESS, 'Aceptado'),
    (OBSERVED, 'Observado'),
    (REJECT, 'Rechazado'),
    (NULL, 'Anulado'),
    (NULLABLE, 'Por anular'),
]


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_pe_sunat_data = fields.Many2one('l10n_pe.datas')
    l10n_pe_facturalo_pdf = fields.Binary(string='PDF', readonly=True, copy=False, help=u'Formato impreso de CPE')
    l10n_pe_facturalo_xml = fields.Binary(string='XML', readonly=True, copy=False, help=u'XML enviado a SUNAT')
    l10n_pe_facturalo_cdr = fields.Binary(string='CDR', readonly=True, copy=False, help=u'Constancia de respuesta SUNAT')
    l10n_pe_facturalo_filename_pdf = fields.Char(copy=False)
    l10n_pe_facturalo_filename_xml = fields.Char(copy=False)
    l10n_pe_facturalo_filename_cdr = fields.Char(copy=False)
    l10n_pe_facturalo_msg = fields.Char(string='Respuesta sunat', readonly=True, copy=False,
                                        help=u'Mensaje de respuesta de SUNAT')
    l10n_pe_facturalo_json = fields.Binary(string='JSON', readonly=True, copy=False)
    l10n_pe_facturalo_filename_json = fields.Char(copy=False)
    l10n_pe_facturalo_external = fields.Char(string='Facturalo external_id', copy=False)
    l10n_pe_facturalo_hash = fields.Char(string='Facturalo código hash', copy=False)
    l10n_pe_facturalo_state = fields.Char(string='Estado CPE', readonly=True, copy=False,
                                          help=u'Estado de CPE según sunat')
    l10n_pe_hide_refund = fields.Boolean(compute='_compute_l10n_pe_hide_refund')
    l10n_pe_facturalo_ticket_voided_document = fields.Char(string='Ticket de anulación', readonly=True, copy=False)
    l10n_pe_facturalo_link_voided_document = fields.Char(string='CDR Anulación', readonly=True, copy=False,
                                                         help=u'Constancia de respuesta de anulación')
    respuestasunat = fields.Char(string='Estado Sunat', compute="_compute_field_obtenerrespuesta")

    @api.depends('l10n_pe_facturalo_msg')
    def _compute_field_obtenerrespuesta(self):
        for x in self:
            salida = ""
            respuesta = x.l10n_pe_facturalo_msg
            respuestados = x.l10n_pe_facturalo_msg
            if respuesta:
                salida = respuesta.index(",") + 9
                x.respuestasunat = respuestados[salida:]
            else:
                x.respuestasunat = ""

    @api.model
    def create(self, vals_list):
        res = super(AccountInvoice, self).create(vals_list)
        res.with_context(no_write_json=True).write_l10n_pe_facturalo_json()
        return res

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if not self.env.context.get('no_write_json'):
            self.with_context(no_write_json=True).mapped(lambda record: record.write_l10n_pe_facturalo_json())
        return res

    @api.depends('journal_id', 'type', 'state', 'l10n_pe_facturalo_state')
    def _compute_l10n_pe_hide_refund(self):
        self.mapped(lambda record: record.update({
            'l10n_pe_hide_refund': record.journal_id.l10n_pe_document_type_id.code in ['07', '08'] or record.type in 'out_refund' or
                record.state not in ('open', 'paid') or record.l10n_pe_facturalo_state in ('Por anular', 'Anulado')
        }))

    @api.multi
    def write_l10n_pe_facturalo_json(self):
        data = self.data_json()
        html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        if self.state in ['draft']:
            number = self.journal_id.sequence_id.get_next_char(self.journal_id.sequence_number_next) or '#'
            self.update({
                'l10n_pe_facturalo_json': base64.encodebytes(html_json.encode('utf-8')),
                'l10n_pe_facturalo_filename_json': '{}.json'.format(number),
            })
        else:
            self.update({
                'l10n_pe_facturalo_json': base64.encodebytes(html_json.encode('utf-8')),
            })

    @api.multi
    def action_invoice_open(self):
        for record in self.filtered('journal_id.l10n_pe_send_sunat'):
            record._check_l10n_pe_invoice()
            record.mapped('invoice_line_ids')._validate_l10n_pe_invoice_line()
            record.send_api_facturalo_document()
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def data_json(self):
        def compute_amount(line, code=''):
            if code:
                invoice_line_tax_ids = line.invoice_line_tax_ids.filtered(
                    lambda tax: tax.l10n_pe_tax_type_id.code == code)
            else:
                invoice_line_tax_ids = line.invoice_line_tax_ids

            price_unit = line.quantity * line.price_unit * (1 - line.discount / 100.0)
            return invoice_line_tax_ids.compute_all(
                price_unit, currency=line.invoice_id.currency_id, quantity=line.quantity
            )

        def get_line_data(line):
            line_icbper = sum(line.invoice_line_tax_ids.filtered(
                    lambda r: r.l10n_pe_tax_type_id.code == '7152').mapped('amount'))
            tax = compute_amount(line)
            # if line.invoice_line_tax_ids.filtered(lambda t: t.l10n_pe_tax_type_id.code == '7152'):
            #     tax = compute_amount(line, '7152')
            #     line_icbper = round(tax['total_included'] - tax['total_excluded'], 2)
            # else:
            #     tax = compute_amount(line)

            amount_tax = sum(line.invoice_line_tax_ids.mapped('amount')) - line_icbper
            if 1 > amount_tax:
                amount_tax = 18

            total_igv = (line.price_subtotal * (amount_tax / 100)) - line_icbper

            for l in line.invoice_line_tax_ids:
                codigo_tipo_afectacion_igv = l.filtered(lambda t: t.l10n_pe_tax_type_id.code != '7152')

                baseimponible = l.include_base_amount
                priceinclude = l.price_include
                item_line = {}
                monto_descuento = 0
                if line.discount:
                    monto_descuento = line.quantity * line.price_unit * line.discount / 100.0
                    item_line.update({
                        "descuentos": [{
                                 "codigo": "00",
                                 "descripcion": "Descuento Lineal",
                                 "factor": line.discount / 100.0,
                                 "monto": round(monto_descuento, 2),
                                 "base": line.quantity * line.price_unit
                        }]
                     })

                # total_igv = line.quantity * line.price_unit - monto_descuento

                if l.name == 'Exonerado':
                    total_igv = 0
                    amount_tax = 0

                if l.name != 'Gratuito':
                    item_line.update({
                        'cantidad': line.quantity,
                        'codigo_interno': line.product_id.default_code or '',
                        'codigo_producto_sunat': line.product_id.l10n_pe_product_sunat_code_id.code or '',
                        'codigo_tipo_afectacion_igv': codigo_tipo_afectacion_igv.l10n_pe_code_affectation_id.code or '10',
                        'codigo_tipo_precio': '01',
                        'descripcion': line.name,
                        'porcentaje_igv': amount_tax,
                        # "precio_unitario": round(line.price_unit + (total_igv / (line.quantity or 1)), 2) - round(line_icbper / (line.quantity or 1), 2),
                        "precio_unitario": round(line.price_unit + (total_igv / (line.quantity or 1)) - (line.discount / (line.quantity or 1)), 2),
                        'total_base_igv': line.price_subtotal,
                        'total_igv': round(total_igv, 2),
                        'total_impuestos': round(total_igv, 2),
                        'total_impuestos_bolsa_plastica': sum(line.invoice_line_tax_ids.filtered(
                            lambda r: r.l10n_pe_tax_type_id.code == '7152').mapped('amount')),
                        'total_item': round((line.price_subtotal + total_igv) - line_icbper, 2),
                        'total_valor_item': line.price_subtotal - line_icbper,
                        'unidad_de_medida': line.uom_id.l10n_pe_sunat_code_id.code or '',
                        # 'valor_unitario': line.price_unit * (1 / (line.quantity or 1)) + monto_descuento, ###

                    })
                    if not baseimponible and not priceinclude:
                        item_line.update({
                            # 'valor_unitario': (tax['base'] / (line.quantity or 1)) + monto_descuento,
                            # 'valor_unitario': (round(tax['total_included'] / (line.quantity or 1), 2) - round(line_icbper / (line.quantity or 1), 2)) - round(total_igv / (line.quantity or 1), 2) - line.discount,
                            'valor_unitario': round(line.price_unit, 2)
                        })
                    else:
                        item_line.update({
                            # 'total_valor_item': tax['base'] - (total_igv / line.quantity or 1),
                            # 'valor_unitario': (tax['base'] / (line.quantity or 1)) - (total_igv / line.quantity or 1) + monto_descuento ,
                            'valor_unitario': round(line.price_unit - (total_igv / (line.quantity or 1)) - (line.discount / (line.quantity or 1)), 2),
                            "precio_unitario": round(line.price_unit - (line.discount / (line.quantity or 1)), 2)
                        })
                else:
                    item_line.update({
                        'codigo_interno': line.product_id.default_code or '',
                        'descripcion': line.name,
                        'codigo_producto_sunat': line.product_id.l10n_pe_product_sunat_code_id.code or '',
                        'unidad_de_medida': line.uom_id.l10n_pe_sunat_code_id.code or '',
                        'cantidad': line.quantity,
                        'valor_unitario':  line.price_unit + monto_descuento,
                        'codigo_tipo_precio': '02',
                        "precio_unitario": (round(tax['total_included'] / (line.quantity or 1), 2) -
                                            round(line_icbper / (line.quantity or 1), 2)),
                        'codigo_tipo_afectacion_igv': codigo_tipo_afectacion_igv.l10n_pe_code_affectation_id.code or '10',
                        'total_base_igv': (line.quantity * line.price_unit) - total_igv,
                        'porcentaje_igv': amount_tax,
                        'total_igv': round(tax['base'] * 0.18, 2),
                        'total_impuestos': total_igv,
                        'total_valor_item': 0.0,
                        'total_item':  0.0,
                        'total_impuestos_bolsa_plastica': sum(line.invoice_line_tax_ids.filtered(
                            lambda r: r.l10n_pe_tax_type_id.code == '7152').mapped('amount'))
                    })

                # if l.name == 'Exonerado':
                #     item_line.update({
                #         'total_igv': 0,
                #         'total_impuestos': 0,
                #     })

                return item_line

        param = self.env['ir.config_parameter'].sudo().get_param
        send_xml = param('api_send_xml_signed', False)

        exp = grav = ina = exo = grat = icbper = disc = 0

        def get_by_tax(l, code):
            tax = l.invoice_line_tax_ids.filtered(lambda t: t.l10n_pe_tax_type_id.code == code)
            price_unit = l.quantity * l.price_unit * (1 - l.discount / 100.0)
            return tax.compute_all(
                price_unit, currency=line.invoice_id.currency_id, quantity=l.quantity
            )['total_excluded'] if tax else 0

        def get_by_tax_i(l, code='7152'):
            return sum(l.invoice_line_tax_ids.filtered(
                    lambda r: r.l10n_pe_tax_type_id.code == code).mapped('amount'))

        number = self.journal_id.sequence_id.get_next_char(self.journal_id.sequence_number_next) or '#'
        series, correlative = number and '-' in number and tuple(number.split('-')) or ('', '')
        leyendas = ""

        codigos = self.l10n_pe_sunat_data.code
        contador = 0
        for line in self.invoice_line_ids:

            icbper += get_by_tax_i(line)
            disc += line.quantity * line.price_unit * line.discount / 100.0

            for l in line.invoice_line_tax_ids:
                if l.name =='Gratuito':
                    grat += get_by_tax(line, '9996')
                    leyendas = {
                        'codigo': '1002',
                        'valor': 'TRANSFERENCIA GRATUITA'
                    }
                else:
                    leyendas = ""
                    contador = 1
                if l.name == 'Exonerado':
                    exo += get_by_tax(line, '9997')
                if l.name == 'IGV 18% Venta':
                    # grav += get_by_tax(line, '1000')
                    line_icbper = sum(line.invoice_line_tax_ids.filtered(
                    lambda r: r.l10n_pe_tax_type_id.code == '7152').mapped('amount'))
                    grav += line.price_subtotal - line_icbper
                if l.name == 'Inafecto':
                    ina += get_by_tax(line, '9998')
                if l.name == 'Exportación':
                    exp += get_by_tax(line, '9995')


        l10n_pe_code = self.picking_ids.mapped('picking_type_id.warehouse_id.l10n_pe_code')
        items = self.invoice_line_ids.mapped(lambda line: get_line_data(line))
        data = {
            'serie_documento': series or self.journal_id.code,
            'numero_documento': correlative and int(correlative) or '#',
            'fecha_de_emision': str(self.date_invoice),
            'hora_de_emision': fields.Datetime().now().time().strftime('%H:%M:%S'),
            'codigo_tipo_operacion': self.l10n_pe_type_sale_operation or '',
            'codigo_tipo_documento': self.journal_id.l10n_pe_document_type_id.code or '',
            'codigo_tipo_moneda': self.currency_id.name or '',
            'fecha_de_vencimiento': self.date_due and str(self.date_due) or str(self.date_invoice),
            'numero_orden_de_compra':  re.sub(r'\W+', '', self.origin and self.origin.replace("/", "-") or ''),
            'datos_del_emisor': {
                'codigo_del_domicilio_fiscal': l10n_pe_code and l10n_pe_code[0] or '0000'
            },
            'datos_del_cliente_o_receptor': {
                'codigo_tipo_documento_identidad': self.partner_id.l10n_pe_document_type or '',
                'numero_documento': self.partner_id.l10n_pe_document_number or '',
                'apellidos_y_nombres_o_razon_social': self.partner_id.l10n_pe_legal_name or self.partner_id.name,
                'codigo_pais': self.partner_id.country_id and self.partner_id.country_id.code or 'PE',
                'ubigeo': self.partner_id.zip or '',
                'direccion': self.partner_id.street or '',
                'correo_electronico': self.partner_id.email or '',
                'telefono': self.partner_id.phone or ''
            },
            "totales": {
                "total_descuentos": 0,
                "total_exportacion": exp,
                "total_operaciones_gravadas": grav,
                "total_operaciones_inafectas": ina,
                "total_operaciones_exoneradas": exo,
                "total_operaciones_gratuitas": grat,
                "total_impuestos_bolsa_plastica": icbper,
                "total_igv": self.amount_tax - icbper,
                "total_impuestos": self.amount_tax - icbper,
                "total_valor": sum(item['total_valor_item'] for item in items),
                "total_venta": round(sum(item['total_item'] for item in items) - icbper, 2)
            },
            'items': items,
            'informacion_adicional': self.comment or '',
            'acciones': {
                'enviar_xml_firmado': send_xml
            },
            'guias': self.picking_ids.filtered('l10n_pe_send_sunat').mapped(lambda record: {
                'numero': record.l10n_pe_number,
                'codigo_tipo_documento': '09'
            })
        }
        if self.journal_id.l10n_pe_document_type_id.code in ['07', '08']:
            data.update({
                'codigo_tipo_documento': self.journal_id.l10n_pe_document_type_id.code,
                'codigo_tipo_nota': self.l10n_pe_debit_note_code or self.l10n_pe_credit_note_code,
                'motivo_o_sustento_de_nota': self.name or '',
                'documento_afectado': {
                    'external_id': self.l10n_pe_invoice_origin_id.l10n_pe_facturalo_external
                }
            })
        if contador == 0:
            data.update({
                'leyendas': [leyendas]
            })
        return data

    @api.multi
    def send_api_facturalo_document(self):
        data = self.data_json()
        number = self.journal_id.sequence_id.get_next_char(self.journal_id.sequence_number_next) or '#'
        values = get_response(self, 'documents', number,  data)
        self.write(values)

    @api.multi
    def action_invoice_cancel(self):
        if not self.filtered(lambda record: record.l10n_pe_facturalo_external):
            return super(AccountInvoice, self).action_invoice_cancel()

        res = super(AccountInvoice, self).action_invoice_cancel()

        if not self.filtered(lambda record: record.l10n_pe_reason_voided):
            raise Warning('Ingrese motivo de anulación en pestaña Otra información')

        data = {
            'fecha_de_emision_de_documentos': str(self.date_invoice),
            'documentos': self.mapped(lambda record: {
                'external_id': record.l10n_pe_facturalo_external,
                'motivo_anulacion': record.l10n_pe_reason_voided
            })
        }

        service = 'voided'
        if self.l10n_pe_number[0] == 'B':
            data.update({'codigo_tipo_proceso': '3'})
            service = 'summaries'
        response = send_request(self, service, data)
        if response and response['data']['ticket']:
            self.write({'l10n_pe_facturalo_ticket_voided_document': response['data']['ticket']})
            data = {
                'external_id': response['data']['external_id'],
                'ticket': response['data']['ticket'],
                'l10n_pe_facturalo_state': 'Por anular'
            }
            url = '{}{}'.format(service, '/status')
            response = send_request(self, url, data)
            if response and response['links']['cdr']:
                self.write({
                    'l10n_pe_facturalo_link_voided_document': response['links']['cdr']
                })
            if response and response['response']['is_accepted']:
                self.write({
                    'l10n_pe_facturalo_state': 'Anulado'
                })
        return res

    @api.multi
    def action_json_generate(self):
        data = self.data_json()
        if data:
            self.write_l10n_pe_facturalo_json()

    @api.multi
    def _check_l10n_pe_invoice(self):
        partner_company = self.env.user.company_id.partner_id
        self.journal_id._check_l10n_pe()
        if not self.partner_id:
            raise ValidationError('No ubicado Cliente.')
        if not partner_company.name:
            raise ValidationError(u'Incorrecto, Razón Social o Nombre Comercial')
        if not partner_company.l10n_pe_document_number:
            raise ValidationError('Incorrecto, empresa RUC')
        if not partner_company.l10n_pe_document_type:
            raise ValidationError(u'Incorrecto, Tipo de Documento Compañía')
        if not self.partner_id.l10n_pe_document_type:
            raise ValidationError('Incorrecto, Tipo de Documento de cliente')
        if not self.journal_id.l10n_pe_document_type_id or not self.journal_id.l10n_pe_document_type_id.code:
            raise ValidationError('No ubicado tipo de documento.')
        if not self.date_invoice:
            raise ValidationError('Incorrecto, Fecha de factura.')
        if not self.currency_id:
            raise ValidationError('Incorrecto, Moneda')
        if not self.partner_id.l10n_pe_district_id:
            raise ValidationError('Incorrecto, registre distrito del cliente')
        if not partner_company or not partner_company.l10n_pe_document_type:
            raise ValidationError(u'Incorrecto, tipo de documento de compañía')
        return True

    def get_api_status(self):
        param = self.env['ir.config_parameter'].sudo().get_param
        token = param('host_api_cpe_token', False)
        data = {
            'external_id': self.l10n_pe_facturalo_external,
            'serie_number': self.number
        }

        response = send_request(self, 'documents/status', data)
        values = dict()
        links = response['links']
        data = response.get('data', {})
        self.update({'l10n_pe_facturalo_state': data.get('status', '')})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(token)
        }
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        if not self.l10n_pe_facturalo_pdf and response['links']:
            response_pdf = requests.get(links.get('pdf'), headers=headers, verify=False) if links.get('pdf') else ''
            self.update({'l10n_pe_facturalo_pdf': base64.b64encode(response_pdf.content)}) if response_pdf else None
        if not self.l10n_pe_facturalo_xml and response['links']:
            response_xml = requests.get(links.get('xml'), headers=headers, verify=False) if links.get('xml') else ''
            self.update({'l10n_pe_facturalo_xml': base64.b64encode(response_xml.content)}) if response_xml else None
        if not self.l10n_pe_facturalo_cdr and response['links']['cdr']:
            response_cdr = requests.get(links.get('cdr'), headers=headers, verify=False) if links.get('cdr') else ''
            self.update({'l10n_pe_facturalo_cdr': base64.b64encode(response_cdr.content)}) if response_cdr else None

    @api.multi
    def create_attachment(self):
        attachment_ids = list()

        if self.l10n_pe_facturalo_pdf:
            attach = dict()
            attach['type'] = "binary"
            attach['res_model'] = "mail.compose.message"

            attach['name'] = self.l10n_pe_facturalo_filename_pdf
            attach['datas'] = self.l10n_pe_facturalo_pdf
            attach['datas_fname'] = self.l10n_pe_facturalo_filename_pdf
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids.append(attachment_id.id)

        if self.l10n_pe_facturalo_xml:
            attach = dict()
            attach['type'] = "binary"
            attach['res_model'] = "mail.compose.message"

            attach['name'] = self.l10n_pe_facturalo_filename_xml
            attach['datas'] = self.l10n_pe_facturalo_xml
            attach['datas_fname'] = self.l10n_pe_facturalo_filename_xml
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids.append(attachment_id.id)

        if self.l10n_pe_facturalo_cdr:
            attach = dict()
            attach['type'] = "binary"
            attach['res_model'] = "mail.compose.message"

            attach['name'] = self.l10n_pe_facturalo_filename_cdr
            attach['datas'] = self.l10n_pe_facturalo_cdr
            attach['datas_fname'] = self.l10n_pe_facturalo_filename_cdr
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids.append(attachment_id.id)

        return attachment_ids


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def _validate_l10n_pe_invoice_line(self):
        for record in self:
            if not record.uom_id.l10n_pe_sunat_code_id:
                raise ValidationError('Incorrecto, unidad de medida Sunat')
            if not record.invoice_line_tax_ids:
                raise ValidationError('No existe impuesto asociado para producto {}'.format(record.product_id.name))
            if not record.invoice_line_tax_ids.filtered(lambda w: w.l10n_pe_tax_type_id and w.l10n_pe_type_sale_id):
                raise ValidationError('Configure en Impuesto , sección (configuración peruana)')
            if not record.product_id.l10n_pe_type_operation_sunat:
                raise ValidationError('Consigne tipo de afectación para el producto {}'.format(record.product_id.name))
