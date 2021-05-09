from odoo import api, fields, models

import base64


class ReportPle08(models.Model):
    _name = 'report.ple.08'
    _inherit = ['report.ple']
    _description = 'Registro de compras'

    file_non_domiciled = fields.Binary(string='Archivo TXT no domiciliado', readonly=True)
    filename_non_domiciled = fields.Char(string='Nombre del archivo no simplificado')

    file_simplified = fields.Binary(string='Archivo TXT simplificado', readonly=True)
    filename_simplified = fields.Char(string='Nombre del archivo  simplificado')
    line_ids = fields.One2many(comodel_name='report.ple.08.line', inverse_name='ple_id', string='Detalle del libro',
                               readonly=True)

    @api.model
    def create(self, vals):
        res = super(ReportPle08, self).create(vals)
        res.update({'name': self.env['ir.sequence'].next_by_code(self._name)})
        return res

    @api.multi
    def action_generate(self):
        prefix = "LE"
        company_vat = self.env.user.company_id.partner_id.vat
        date_start = self.range_id.date_start
        date_end = self.range_id.date_end
        year, month = fields.Date().from_string(date_start).year, fields.Date().from_string(date_start).month
        currency = 2 if self.currency_id.name in ['USD'] else 1
        template = "{}{}{}{}00{}00{}{}{}{}.txt"
        domain = [
            ('date_invoice', '>=', date_start),
            ('date_invoice', '<=', date_end),
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ['open', 'paid']),
            ('type', 'in', ['in_invoice', 'in_refund'])
        ]
        invoice_obj = self.env['account.invoice'].search(domain, order='create_date')
        self.create_lines(invoice_obj)

        # purchase report normal
        data = self._get_content(self.line_ids)
        filename = template.format(
            prefix, company_vat, year, month, '080100', self.indicator_operation, self.indicator_content, currency, 1)
        value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}

        # purchase report non-domiciled
        data = self._get_content_non_domiciled(self.line_ids)
        filename = template.format(prefix, company_vat, year, month, '080200', self.indicator_operation,
                                   self.indicator_content, currency, 1)
        value.update({
            'filename_non_domiciled': filename,
            'file_non_domiciled': base64.encodebytes(data.encode('utf-8'))
        })

        # purchase report simplified
        filename = template.format(prefix, company_vat, year, month, '080300', self.indicator_operation,
                                   self.indicator_content, currency, 1)
        data = self._get_content_simplified(self.line_ids)
        value.update({'filename_simplified': filename, 'file_simplified': base64.encodebytes(data.encode('utf-8'))})
        self.action_generate_ple(value)

    @api.multi
    def create_lines(self, invoice_obj):
        self.line_ids.unlink()
        for x, line in enumerate(invoice_obj, 1):
            self.env['report.ple.08.line'].create({
                'invoice_id': line.id,
                'ple_id': self.id,
                'move_name': u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, x)
            })

    @staticmethod
    def _get_content(move_line_obj):
        template = '{period}|{cuo}|{move_name}|{date_emission}|{date_due}|{document_payment_type}|' \
                   '{document_payment_series}|{date_dua}|{document_payment_number}|{no_fiscal_credit}|' \
                   '{supplier_document_type}|{supplier_document_number}|{supplier_name}|{amount_untaxed1}|' \
                   '{amount_tax_igv1}|{amount_untaxed2}|{amount_tax_igv2}|{amount_untaxed3}|{amount_tax_igv3}|' \
                   '{amount_exo}|{amount_tax_isc}|{amount_tax_other}|{amount_total}|{currency}|{exchange_currency}|' \
                   '{date_emission_update}|{document_payment_type_update}|{document_payment_series_update}|' \
                   '{dua_code}|{document_payment_correlative_update}|{date_detraction}|{number_detraction}|' \
                   '{retention_mark}|{goods_services_classification}|{contract_ident}|{type_error_1}|{type_error_2}|' \
                   '{type_error_3}|{type_error_4}|{method_payment}|{state_opportunity}|\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                cuo=line.cuo,
                move_name=line.move_name,
                date_emission=line.date_emission,
                date_due=line.date_due,
                document_payment_type=line.document_payment_type,
                document_payment_series=line.document_payment_series,
                date_dua=line.date_dua or '',
                document_payment_number=line.document_payment_number,
                no_fiscal_credit=line.no_fiscal_credit or '',
                supplier_document_type=line.supplier_document_type,
                supplier_document_number=line.supplier_document_number,
                supplier_name=line.supplier_name,
                amount_untaxed1=round(line.amount_untaxed1, 2) or '0.00',
                amount_tax_igv1=round(line.amount_tax_igv1, 2) or '0.00',
                amount_untaxed2=round(line.amount_untaxed2, 2) or '0.00',
                amount_tax_igv2=round(line.amount_tax_igv2, 2) or '0.00',
                amount_untaxed3=round(line.amount_untaxed3, 2) or '0.00',
                amount_tax_igv3=round(line.amount_tax_igv3, 2) or '0.00',
                amount_exo=round(line.amount_exo, 2) or '0.00',
                amount_tax_isc=round(line.amount_tax_isc, 2) or '0.00',
                amount_tax_other=round(line.amount_tax_other, 2) or '0.00',
                amount_total=round(line.amount_total, 2) or '0.00',
                currency=line.currency or '',
                exchange_currency=line.exchange_currency or '',
                date_emission_update=line.date_emission_update or '',
                document_payment_type_update=line.document_payment_type_update or '',
                document_payment_series_update=line.document_payment_series_update or '',
                dua_code=line.dua_code or '',
                document_payment_correlative_update=line.document_payment_correlative_update or '',
                date_detraction=line.date_detraction or '',
                number_detraction=line.number_detraction or '',
                retention_mark=line.retention_mark or '',
                goods_services_classification=line.goods_services_classification or '',
                contract_ident=line.contract_ident or '',
                type_error_1=line.type_error_1 or '',
                type_error_2=line.type_error_2 or '',
                type_error_3=line.type_error_3 or '',
                type_error_4=line.type_error_4 or '',
                method_payment=line.method_payment or '',
                state_opportunity=line.state_opportunity or ''
            )
        return data

    @staticmethod
    def _get_content_simplified(move_line_obj):
        template = '''{period}|{cuo}|{move_name}|{date_emission}|{date_due}|{document_payment_type}|
        {document_payment_series}|{document_payment_number}|{no_fiscal_credit}|{supplier_document_type}|{supplier_document_number}|
        {supplier_name}|{amount_untaxed1}|{amount_tax_igv1}|{amount_tax_other}|{amount_total}|{currency}|{exchange_currency}|
        {date_emission_update}|{document_payment_type_update}|{document_payment_series_update}|{document_payment_correlative_update}|
        {date_detraction}|{number_detraction}|{retention_mark}|{goods_services_classification}|{type_error_1}|{type_error_2}|
        {type_error_3}|{method_payment}|{state_opportunity}|\r\n'''
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                cuo=line.cuo,
                move_name=line.move_name,
                date_emission=line.date_emission,
                date_due=line.date_due,
                document_payment_type=line.document_payment_type,
                document_payment_series=line.document_payment_series,
                document_payment_number=line.document_payment_number,
                no_fiscal_credit=line.no_fiscal_credit or '',
                supplier_document_type=line.supplier_document_type,
                supplier_document_number=line.supplier_document_number,
                supplier_name=line.supplier_name,
                amount_untaxed1=round(line.amount_untaxed1, 2) or '0.00',
                amount_tax_igv1=round(line.amount_tax_igv1, 2) or '0.00',
                amount_tax_other=round(line.amount_tax_other, 2) or '0.00',
                amount_total=round(line.amount_total, 2) or '0.00',
                currency=line.currency or '',
                exchange_currency=line.exchange_currency or '',
                date_emission_update=line.date_emission_update or '',
                document_payment_type_update=line.document_payment_type_update or '',
                document_payment_series_update=line.document_payment_series_update or '',
                document_payment_correlative_update=line.document_payment_correlative_update or '',
                date_detraction=line.date_detraction or '',
                number_detraction=line.number_detraction or '',
                retention_mark=line.retention_mark or '',
                goods_services_classification=line.goods_services_classification or '',
                type_error_1=line.type_error_1 or '',
                type_error_2=line.type_error_2 or '',
                type_error_3=line.type_error_3 or '',
                method_payment=line.method_payment or '',
                state_opportunity=line.state_opportunity or ''
            )
        return data
    
    @staticmethod
    def _get_content_non_domiciled(move_line_obj):
        template = '{period}|{cuo}|{move_name}|{date_emission}|{nd_payment_type}|{nd_payment_series}|' \
                   '{nd_payment_number}|{amount_untaxed}|{amount_other}|{amount_total}|{document_payment_type}|' \
                   '{document_payment_series}|{dua_year}|{document_payment_number}|{amount_retention_igv}|' \
                   '{currency}|{exchange_currency}|{supplier_country}|{supplier_name}|{supplier_address}|' \
                   '{supplier_document_number}|{beneficiary_number}|{beneficiary_name}|{beneficiary_country}|' \
                   '{linkage}|{income_gross}|{deduction}|{income_net}|{retention_rate}|{retention_tax}|' \
                   '{agreements_tax}|{exemption_applied}|{income_type}|{service_modality}|{art_76}|' \
                   '{opportunity_state}\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                cuo=line.cuo,
                move_name=line.move_name,
                date_emission=line.date_emission,
                nd_payment_type='',
                nd_payment_series='',
                nd_payment_number='',
                amount_untaxed='',
                amount_other='',
                amount_total='',
                document_payment_type=line.document_payment_type,
                document_payment_series=line.document_payment_series,
                dua_year='',
                document_payment_number=line.document_payment_number,
                amount_retention_igv='',
                currency=line.currency,
                exchange_currency=line.exchange_currency,
                supplier_country='',
                supplier_name=line.supplier_name,
                supplier_address='',
                supplier_document_number='',
                beneficiary_number='',
                beneficiary_name='',
                beneficiary_country='',
                linkage='',
                income_gross='',
                deduction='',
                income_net='',
                retention_rate='',
                retention_tax='',
                agreements_tax='',
                exemption_applied='',
                income_type='',
                service_modality='',
                art_76='',
                opportunity_state=''
            )
        return data

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('{}.xlsx'.format(obj.filename_txt))
        bold_right = workbook.add_format({'bold': True, 'font_color': 'black'})
        bold = workbook.add_format({'bold': True, 'font_color': 'black'})
        normal = workbook.add_format({'font_color': 'black'})
        right = workbook.add_format({'font_color': 'black'})
        left = workbook.add_format({'font_color': 'black'})

        bold.set_align('center')
        normal.set_align('center')
        left.set_align('left')
        right.set_align('right')

        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 5)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 50)
        sheet.set_column('H:H', 5)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 50)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)
        sheet.set_column('Q:Q', 20)
        sheet.set_column('R:R', 10)
        sheet.set_column('S:S', 10)
        sheet.set_column('T:T', 10)
        sheet.set_column('U:U', 25)
        sheet.set_column('V:V', 15)
        sheet.set_column('W:W', 10)
        sheet.set_column('X:X', 10)
        sheet.set_column('Y:Y', 10)
        sheet.set_column('Z:Z', 5)
        sheet.set_column('AA:AA', 15)
        sheet.set_column('AB:AB', 20)

        sheet.set_row(6, 30)
        sheet.set_row(7, 30)
        sheet.set_row(8, 30)

        sheet.merge_range('A1:B1', u'FORMATO 8.1: "REGISTRO DE COMPRAS"', bold_right)
        sheet.merge_range('A3:B3', u'PERIODO: {}'.format(obj.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                          bold_right)

        sheet.merge_range('A7:A9', u'NÚMERO \nCORRELATIVO \nDEL ASIENTO O \nCÓDIGO ÚNICO DE \nLA OPERACIÓN', bold)
        sheet.merge_range('B7:B9', u'FECHA DE \nEMISION DEL \nCOMPROBANTE DE \nPAGO O DOCUMENT0', bold)
        sheet.merge_range('C7:C9', u'FECHA DE \nVENCIMIENTO\n O FECHA', bold)
        sheet.merge_range('D7:F7', u'COMPROBANTE DE PAGO O DOCUMENTO', bold)
        sheet.merge_range('D8:D9', u'TIPO', bold)
        sheet.merge_range('E8:E9', u'SERIE O CODIGO DE LA \nDEPENDENCIA ADUANERA', bold)
        sheet.merge_range('F8:F9', u'AÑO DE EMISION DE \nLA DUA O DSI', bold)
        sheet.merge_range('G7:G9', u'''Nº DEL COMPROBANTE DE PAGO, DOCUMENTO, \nNº DE ORDEN DEL FORMULARIO FISICO O 
        VIRTUAL,\nNº DE DUA, DSI O \nLIQUIDACION DE COBRANZA \nU OTROS DOCUMENTOS\n EMITIDOS POR SUNAT PARA ACREDITAR\n 
        EL CREDITO FISCAL EN LA IMPORTACION''', bold)
        sheet.merge_range('H7:J7', u'INFORMACION DEL PROVEDOOR', bold)
        sheet.merge_range('H8:I8', u'DOCUMENTO \nDE IDENTIDAD', bold)
        sheet.write('H9', u'TIPO', bold)
        sheet.write('I9', u'NUMERO', bold)
        sheet.merge_range('J8:J9', u'APELLIDOS Y NOMBRES,\nDENOMINACION O \nRAZON SOCIAL', bold)

        sheet.merge_range('K7:L8', u'ADQUISICIONES GRAVADAS \nDESTINADAS A OPERACIONES \nGRAVADAS Y/O EXPORTACIONES',
                          bold)
        sheet.write('K9', u'BASE \nIMPONIBLE', bold)
        sheet.write('L9', u'IGV', bold)

        sheet.merge_range('M7:N8', u'ADQUISICIONES GRAVADAS \nDESTINADAS A OPERACIONES '
                                   u'\nGRAVADAS Y/O EXPORTACION Y \nA OPERACIONES NO GRAVADAS', bold)
        sheet.write('M9', u'BASE \nIMPONIBLE', bold)
        sheet.write('N9', u'IGV', bold)

        sheet.merge_range('O7:P8', u'ADQUISICION GRAVADAS \nDESTINADAS A OPERACIONES \nNO GRAVADAS', bold)
        sheet.write('O9', u'BASE \nIMPONIBLE', bold)
        sheet.write('P9', u'IGV', bold)

        sheet.merge_range('Q7:Q9', u'VALOR DE LAS \nADQUISICIONES \nNO GRAVADAS', bold)
        sheet.merge_range('R7:R9', u'ISC', bold)
        sheet.merge_range('S7:S9', u'OTROS \nTRIBUTOS \nY CARGOS', bold)
        sheet.merge_range('T7:T9', u'IMPORTE\nTOTAL', bold)
        sheet.merge_range('U7:U9', u'Nº DE COMPROBANTE \nDE PAGO EMITIDO \nPOR SUJETO \nNO DOMICILIADO', bold)

        sheet.merge_range('V7:W7', u'CONSTANCIA DE DEPOSITO \nDE DETRACCION', bold)
        sheet.merge_range('V8:V9', u'NUMERO', bold)
        sheet.merge_range('W8:W9', u'FECHA DE \nEMISION', bold)

        sheet.merge_range('X7:X9', u'TIPO DE \nCAMBIO', bold)

        sheet.merge_range('Y7:AB7', u'REFERENCIA DEL COMPROBANTE DE PAGO O \nDOCUMENTO ORIGINAL QUE SE MODIFICA', bold)
        sheet.merge_range('Y8:Y9', u'FECHA', bold)
        sheet.merge_range('Z8:Z9', u'TIPO', bold)
        sheet.merge_range('AA8:AA9', u'SERIE', bold)
        sheet.merge_range('AB8:AB9', u'Nº DEL \nCOMPROBANTE \nDE PAGO O \nDOCUMENTO', bold)

        i = 9
        for line in obj.line_ids:
            sheet.write(i, 0, line.move_name, normal)
            sheet.write(i, 1, line.date_emission, normal)
            sheet.write(i, 2, line.date_due, normal)
            sheet.write(i, 3, line.document_payment_type, normal)
            sheet.write(i, 4, line.document_payment_series, normal)
            sheet.write(i, 5, line.date_dua, normal)
            sheet.write(i, 6, line.document_payment_number, normal)
            sheet.write(i, 7, line.supplier_document_type, normal)
            sheet.write(i, 8, line.supplier_document_number, normal)
            sheet.write(i, 9, line.supplier_name, normal)
            sheet.write(i, 10, round(line.amount_untaxed1, 2) or '0.00', normal)
            sheet.write(i, 11, round(line.amount_tax_igv1, 2)or '0.00', normal)
            sheet.write(i, 12, round(line.amount_untaxed2, 2) or '0.00', normal)
            sheet.write(i, 13, round(line.amount_tax_igv2, 2) or '0.00', normal)
            sheet.write(i, 14, round(line.amount_untaxed3, 2) or '0.00', normal)
            sheet.write(i, 15, round(line.amount_tax_igv3, 2) or '0.00', normal)
            sheet.write(i, 16, round(line.amount_exo, 2) or '0.00', normal)
            sheet.write(i, 17, round(line.amount_tax_isc, 2) or '0.00', normal)
            sheet.write(i, 18, round(line.amount_tax_other, 2) or '0.00', normal)
            sheet.write(i, 19, round(line.amount_total, 2) or '0.00', normal)
            sheet.write(i, 20, "", normal)
            sheet.write(i, 21, line.number_detraction, normal)
            sheet.write(i, 22, line.date_detraction, normal)
            sheet.write(i, 23, line.exchange_currency, normal)
            sheet.write(i, 24, line.date_emission_update, normal)
            sheet.write(i, 25, line.document_payment_type_update, normal)
            sheet.write(i, 26, line.document_payment_series_update, normal)
            sheet.write(i, 27, line.document_payment_correlative_update, normal)
            i += 1


class ReportPle08Line(models.Model):
    _name = 'report.ple.08.line'
    _order = 'date_emission,supplier_document_number,amount_total'
    _description = 'Detalle de registro de compras'

    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Factura')
    statefacturas = fields.Char(string='Estado de Facturas')
    
    period = fields.Char(string='Periodo', compute='_compute_data')
    cuo = fields.Char(string='CUO', compute='_compute_data')
    move_name = fields.Char(string='Asiento')
    date_emission = fields.Char(string='Fecha de emision', compute='_compute_data')
    date_due = fields.Char(string='Fecha de vencimiento', compute='_compute_data')
    document_payment_type = fields.Char(string='Tipo', compute='_compute_data')
    document_payment_series = fields.Char(string='Serie', compute='_compute_data')
    date_dua = fields.Integer(string='Año de emision de la DUA', compute='_compute_data')
    document_payment_number = fields.Char(string='Nº del comprobante', compute='_compute_data')
    no_fiscal_credit = fields.Float(string='Operaciones sin derecho fiscal')
    supplier_document_type = fields.Char(string='Tipo de DC', compute='_compute_data')
    supplier_document_number = fields.Char(string='Numero de DC', compute='_compute_data')
    supplier_name = fields.Char(string='Proveedor', compute='_compute_data')
    amount_untaxed1 = fields.Float(string='OG', compute='_compute_amount', digits=(10, 2))
    amount_tax_igv1 = fields.Float(string='IGV OG', compute='_compute_amount', digits=(10, 2))
    amount_untaxed2 = fields.Float(string='ONG', compute='_compute_amount', digits=(10, 2))
    amount_tax_igv2 = fields.Float(string='IGV ONG', compute='_compute_amount', digits=(10, 2))
    amount_untaxed3 = fields.Float(string='ANG', compute='_compute_amount', digits=(10, 2))
    amount_tax_igv3 = fields.Float(string='IGV ANG', compute='_compute_amount', digits=(10, 2))
    amount_exo = fields.Float(string='Exonerado', compute='_compute_amount', digits=(10, 2))
    amount_tax_isc = fields.Float(string='ISC', compute='_compute_amount', digits=(10, 2))
    amount_tax_other = fields.Float(string='Otros conceptos', compute='_compute_amount', digits=(10, 2))
    amount_total = fields.Float(string='Total', compute='_compute_amount', digits=(10, 2))
    currency = fields.Char(string='Moneda', compute='_compute_data')
    exchange_currency = fields.Float(string='Tipo de cambio', compute='_compute_data')
    date_emission_update = fields.Char(string='Fecha emision de CR', compute='_compute_data')
    document_payment_type_update = fields.Char(string='Tipo de CR', compute='_compute_data')
    document_payment_series_update = fields.Char(string='Serie de CR', compute='_compute_data')
    dua_code = fields.Char(string='Codigo dua')
    document_payment_correlative_update = fields.Char(string='Nº de CR')
    date_detraction = fields.Date(string='Fecha de detraccion')
    number_detraction = fields.Char(string='Constancia de deposito de detraccion')
    retention_mark = fields.Char(string='Pago sujeto a retencion')
    goods_services_classification = fields.Char(string='Clasificacion de los bienes y servicios')
    contract_ident = fields.Char(string='Identificacion del contrato')
    type_error_1 = fields.Char(string='Error tipo 1')
    type_error_2 = fields.Char(string='Error tipo 2')
    type_error_3 = fields.Char(string='Error tipo 3')
    type_error_4 = fields.Char(string='Error tipo 4')
    method_payment = fields.Boolean(string='Método de pago', compute='_compute_data')
    state_opportunity = fields.Char(string='Estado')
    ple_id = fields.Many2one(comodel_name='report.ple.08')

    @api.multi
    @api.depends('invoice_id')
    def _compute_data(self):
        def get_series_correlative(name):
            return (name.split('-')[0], name.split('-')[1]) if name and '-' in name else ('', '')

        def format_date(date):
            return date and fields.Date().from_string(date).strftime("%d/%m/%Y") or ''

        def get_year_month(date):
            return '{}{}'.format(fields.Date().from_string(date).year, fields.Date().from_string(date).month)

        self.mapped(lambda x: x.update({
            'period': '{}00'.format(get_year_month(x.invoice_id.date_invoice)),
            'cuo': x.invoice_id.move_id.name,
            'date_emission': fields.Date().from_string(x.invoice_id.date_invoice).strftime("%d/%m/%Y"),
            'date_due': fields.Date().from_string(x.invoice_id.date_due).strftime("%d/%m/%Y"),
            'document_payment_type': str(x.invoice_id.journal_id.l10n_pe_document_type_id.code or ''),
            'document_payment_series': get_series_correlative(x.invoice_id.reference)[0],
            'date_dua': fields.Date().from_string(x.invoice_id.date_invoice).year,
            'document_payment_number': get_series_correlative(x.invoice_id.reference)[1],
            'supplier_document_type': x.invoice_id.partner_id.l10n_pe_document_type or '',
            'supplier_document_number': x.invoice_id.partner_id.vat or '',
            'supplier_name': x.invoice_id.partner_id.name or '',
            'date_emission_update': format_date(x.invoice_id.l10n_pe_invoice_origin_id.date_invoice),
            'document_payment_type_update': x.invoice_id.l10n_pe_invoice_origin_id.journal_id.l10n_pe_document_type_id.code,
            'document_payment_series_update': get_series_correlative(x.invoice_id.l10n_pe_invoice_origin_id.number)[0],
            'document_payment_correlative_update': get_series_correlative(
                x.invoice_id.l10n_pe_invoice_origin_id.number)[1],
            'currency': x.invoice_id.currency_id != x.invoice_id.company_id.currency_id and
            x.invoice_id.currency_id.name or '',
            'exchange_currency':  x.invoice_id.l10n_pe_exchange_rate,
        }))

    @api.multi
    @api.depends('invoice_id')
    def _compute_amount(self):
        def get_amount_tax(lines):
            def compute_tax(p, t, x):
                res = t.compute_all(
                    p,
                    x.invoice_id.currency_id,
                    x.quantity,
                    product=x.product_id,
                    partner=x.invoice_id.partner_id
                )
                return res['total_included'] - res['total_excluded']

            igv = inaf = exo = rice = isc = other = 0
            for line in lines:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for tax in line.invoice_line_tax_ids:
                    if tax.l10n_pe_tax_type_id.code in ['1000']:
                        igv += compute_tax(price, tax, line)
                    if tax.l10n_pe_tax_type_id.code in ['2000']:
                        isc += compute_tax(price, tax, line)
                    if tax.l10n_pe_tax_type_id.code in ['9997']:
                        exo += compute_tax(price, tax, line)
                    if tax.l10n_pe_tax_type_id.code in ['9998']:
                        inaf += compute_tax(price, tax, line)
                    if tax.l10n_pe_tax_type_id.code in ['1016']:
                        rice += compute_tax(price, tax, line)
                    if tax.l10n_pe_tax_type_id.code in ['9999']:
                        other += compute_tax(price, tax, line)
            return exo, inaf, isc, igv, other

        self.mapped(lambda w: w.update({
            'amount_untaxed1': w.invoice_id.amount_untaxed,
            'amount_tax_igv1': get_amount_tax(w.invoice_id.invoice_line_ids)[3],
            'amount_tax_igv2': get_amount_tax(w.invoice_id.invoice_line_ids)[1],
            'amount_exo': get_amount_tax(w.invoice_id.invoice_line_ids)[0],
            'amount_tax_isc': get_amount_tax(w.invoice_id.invoice_line_ids)[2],
            'amount_tax_other': get_amount_tax(w.invoice_id.invoice_line_ids)[4],
            'amount_total': w.invoice_id.amount_total
        }))
