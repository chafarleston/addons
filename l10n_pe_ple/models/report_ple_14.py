from odoo import api, fields, models

import base64


class ReportPle14(models.Model):
    _name = 'report.ple.14'
    _inherit = ['report.ple']
    _description = 'Registro de ventas'

    file_simplified = fields.Binary(string='Archivo TXT simplificado', readonly=True)
    filename_simplified = fields.Char(string='Nombre del archivo  simplificado')
    line_ids = fields.One2many(comodel_name='report.ple.14.line', inverse_name='ple_id',
                               string='Detalle del libro', readonly=True)

    @api.model
    def create(self, vals):
        res = super(ReportPle14, self).create(vals)
        res.update({'name': self.env['ir.sequence'].next_by_code(self._name)})
        return res

    @api.multi
    def action_generate(self):
        prefix = "LE"
        company_vat = self.env.user.company_id.partner_id.vat or ''
        date_start = self.range_id.date_start
        date_end = self.range_id.date_end
        year, month = fields.Date().from_string(date_start).year, fields.Date().from_string(date_start).month
        currency = 2 if self.currency_id.name in ['USD'] else 1
        template = "{}{}{}{}00{}00{}{}{}{}.txt"
        domain = [
            ('date_invoice', '>=', date_start),
            ('date_invoice', '<=', date_end),
            ('state', 'in', ['open', 'paid', 'cancel']),
            ('company_id', '=', self.company_id.id),
            ('type', 'in', ['out_invoice', 'out_refund'])
        ]
        invoice_obj = self.env['account.invoice'].search(domain, order='create_date')
        self.create_lines(invoice_obj)
        if self.type_report in ['normal']:
            # sale report normal
            data = self._get_content(self.line_ids)
            filename = template.format(
                prefix, company_vat, year, month, '140100', self.indicator_operation,
                self.indicator_content, currency, 1)
            value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}
        elif self.type_report in ['simplified']:
            # sale report simplified
            filename = template.format(
                prefix, company_vat, year, month, '140200', self.indicator_operation,
                self.indicator_content, currency, 1)
            data = self._get_content_simplified(self.line_ids)
            value = {
                'filename_simplified': filename,
                'file_simplified': base64.encodebytes(data.encode('utf-8'))
            }
        self.action_generate_ple(value)

    @api.multi
    def create_lines(self, invoice_obj):
        self.line_ids.unlink()
        for x, line in enumerate(invoice_obj, 1):
            self.env['report.ple.14.line'].create({
                'invoice_id': line.id,
                'ple_id': self.id,
                'move_name': u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, x),
                'state_opportunity': '2' if line.state in ['cancel'] or line.state in ['open', 'paid'] else '1'
            })

    @staticmethod
    def _get_content(move_line_obj):
        template = '{period}|{cuo}|{move_name}|{date_emission}|{date_due}|{document_payment_type}|' \
                   '{document_payment_series}|{document_payment_number}|{ticket_fiscal_credit}|' \
                   '{customer_document_type}|{customer_document_number}|{customer_name}|{amount_export}|' \
                   '{amount_untaxed}|{amount_discount_untaxed}|{amount_tax_igv}|{amount_discount_tax_igv}|' \
                   '{amount_tax_ina}|{amount_tax_isc}|{amount_rice}|{amount_tax_rice}|{amount_tax_other}|' \
                   '{amount_total}|{currency}|{exchange_currency}|{date_emission_update}|' \
                   '{document_payment_type_update}|{document_payment_series_update}|' \
                   '{document_payment_correlative_update}|{contract_ident}|{type_error_1}|{method_payment}|' \
                   '{state_opportunity}|\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                cuo=line.cuo,
                move_name=line.move_name,
                date_emission=line.date_emission,
                date_due=line.date_due or '',
                document_payment_type=line.document_payment_type or '',
                document_payment_series=line.document_payment_series or '',
                document_payment_number=line.document_payment_number or '',
                ticket_fiscal_credit=line.ticket_fiscal_credit or '',
                customer_document_type=line.customer_document_type or '',
                customer_document_number=line.customer_document_number or '',
                customer_name=line.customer_name or '',
                amount_export=round(line.amount_export, 2) or '0.00',
                amount_untaxed=round(line.amount_untaxed, 2) or '0.00',
                amount_discount_untaxed=round(line.amount_discount_untaxed, 2) or '0.00',
                amount_tax_igv=round(line.amount_tax_igv, 2) or '0.00',
                amount_discount_tax_igv=round(0, 2) or '0.00',
                amount_tax_exo=round(line.amount_tax_exo, 2) or '0.00',
                amount_tax_ina=round(line.amount_tax_ina, 2) or '0.00',
                amount_tax_isc=round(line.amount_tax_isc, 2) or '0.00',
                amount_rice=round(line.amount_rice, 2) or '0.00',
                amount_tax_rice=round(line.amount_tax_rice, 2) or '0.00',
                amount_tax_other=round(line.amount_tax_other, 2) or '0.00',
                amount_total=round(line.amount_total, 2) or '0.00',
                currency=line.currency or '',
                exchange_currency=line.exchange_currency or '',
                date_emission_update=line.date_emission_update or '',
                document_payment_type_update=line.document_payment_type_update or '',
                document_payment_series_update=line.document_payment_series_update or '',
                document_payment_correlative_update=line.document_payment_correlative_update or '',
                contract_ident=line.contract_ident or '',
                type_error_1=line.type_error_1 or '',
                method_payment=line.method_payment and '1' or '',
                state_opportunity=line.state_opportunity or ''
            )
        return data

    @staticmethod
    def _get_content_simplified(move_line_obj):
        template = '{period}|{cuo}|{move_name}|{date_emission}|{date_due}|{document_payment_type}|' \
                   '{document_payment_series}|{document_payment_number}|{ticket_fiscal_credit}|' \
                   '{customer_document_type}|{customer_document_number}|{customer_name}|{amount_untaxed}|' \
                   '{amount_tax_igv}|{amount_tax_other}|{amount_total}|{currency}|{exchange_currency}|' \
                   '{date_emission_update}|{document_payment_type_update}|{document_payment_series_update}|' \
                   '{document_payment_correlative_update}|{type_error_1}|{method_payment}|{state_opportunity}|\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                cuo=line.cuo,
                move_name=line.move_name,
                date_emission=line.date_emission,
                date_due=line.date_due or '',
                document_payment_type=line.document_payment_type or '',
                document_payment_series=line.document_payment_series or '',
                document_payment_number=line.document_payment_number or '',
                ticket_fiscal_credit=line.ticket_fiscal_credit or '',
                customer_document_type=line.customer_document_type or '',
                customer_document_number=line.customer_document_number or '',
                customer_name=line.customer_name or '',
                amount_untaxed=round(line.amount_untaxed, 2) or '0.00',
                amount_tax_igv=round(line.amount_tax_igv, 2) or '0.00',
                amount_tax_other=round(line.amount_tax_other, 2) or '0.00',
                amount_total=round(line.amount_total, 2) or '0.00',
                currency=line.currency or '',
                exchange_currency=line.exchange_currency or '',
                date_emission_update=line.date_emission_update or '',
                document_payment_type_update=line.document_payment_type_update or '',
                document_payment_series_update=line.document_payment_series_update or '',
                document_payment_correlative_update=line.document_payment_correlative_update or '',
                type_error_1=line.type_error_1 or '',
                method_payment=line.method_payment and '1' or '',
                state_opportunity=line.state_opportunity or ''
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
        sheet.set_column('E:E', 10)
        sheet.set_column('F:F', 10)
        sheet.set_column('G:G', 5)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 35)
        sheet.set_column('J:J', 20)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P', 15)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 10)
        sheet.set_column('S:S', 10)
        sheet.set_column('T:T', 10)
        sheet.set_column('U:U', 20)
        sheet.set_column('V:V', 15)

        sheet.set_row(6, 30)
        sheet.set_row(7, 25)
        sheet.set_row(8, 30)

        sheet.merge_range('A1:D1', u'FORMATO 14.1: REGISTRO DE VENTAS E INGRESOS', bold_right)
        sheet.merge_range('A3:B3', u'PERIODO: {}'.format(obj.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                          bold_right)

        sheet.merge_range('A7:A9', u'NÚMERO \nCORRELATIVO \nDEL REGISTRO O \nCÓDIGO ÚNICO DE \nLA OPERACIÓN', bold)
        sheet.merge_range('B7:B9', u'FECHA DE \nEMISION DEL \nCOMPROBANTE DE \nPAGO O DOCUMENT0', bold)
        sheet.merge_range('C7:C9', u'FECHA DE \nVENCIMIENTO\n Y/O PAGO', bold)
        sheet.merge_range('D7:F7', u'COMPROBANTE DE PAGO \nO DOCUMENTO', bold)
        sheet.merge_range('D8:D9', u'TIPO', bold)
        sheet.merge_range('E8:E9', u'Nº SERIE', bold)
        sheet.merge_range('F8:F9', u'NÚMERO', bold)
        sheet.merge_range('G7:I7', u'INFORMACION DEL CLIENTE', bold)
        sheet.merge_range('G8:H8', u'DOCUMENTO DE IDENTIDAD', bold)
        sheet.write('G9', u'TIPO', bold)
        sheet.write('H9', u'NUMERO', bold)
        sheet.merge_range('I8:I9', u'APELLIDOS Y NOMBRES,\nDENOMINACION \nO RAZON SOCIAL', bold)

        sheet.merge_range('J7:J9', u'VALOR \nFACTURADO \nDE LA \nEXPORTACIÓN', bold)
        sheet.merge_range('K7:K9', u'BASE \nIMPONIBLE \nDE LA \nOPERACIÓN \nGRAVADA', bold)

        sheet.merge_range('L7:M8', u'IMPORTE TOTAL \nDE LA OEPRACIÓN \nEXONERADA O INAFECTA', bold)
        sheet.write('L9', u'EXONERADA', bold)
        sheet.write('M9', u'INAFECTA', bold)

        sheet.merge_range('N7:N9', u'ISC', bold)
        sheet.merge_range('O7:O9', u'IGV Y/O IPM', bold)
        sheet.merge_range('P7:P9', u'OTROS \nTRIBUTOS \nY CARGOS', bold)
        sheet.merge_range('Q7:Q9', u'IMPORTE\nTOTAL DEL \nCOMPROBANTE \nDE PAGO', bold)

        sheet.merge_range('R7:R9', u'TIPO DE \nCAMBIO', bold)

        sheet.merge_range('S7:V7', u'REFERENCIA DEL COMPROBANTE DE PAGO O \nDOCUMENTO ORIGINAL QUE SE MODIFICA', bold)
        sheet.merge_range('S8:S9', u'FECHA', bold)
        sheet.merge_range('T8:T9', u'TIPO', bold)
        sheet.merge_range('U8:U9', u'SERIE', bold)
        sheet.merge_range('V8:V9', u'Nº DEL \nCOMPROBANTE \nDE PAGO O \nDOCUMENTO', bold)
        sheet.merge_range('W8:W9', u'ESTADO', bold)

        i = 9
        for line in obj.line_ids:
            sheet.write(i, 0, line.move_name, normal)
            sheet.write(i, 1, line.date_emission, normal)
            sheet.write(i, 2, line.date_due, normal)
            sheet.write(i, 3, line.document_payment_type, normal)
            sheet.write(i, 4, line.document_payment_series or '', normal)
            sheet.write(i, 5, line.document_payment_number or '', normal)
            sheet.write(i, 6, line.customer_document_type or '', normal)
            sheet.write(i, 7, line.customer_document_number or '', normal)
            sheet.write(i, 8, line.customer_name, left)
            sheet.write(i, 9, line.amount_export or '0.00', right)
            sheet.write(i, 10, line.amount_untaxed or '0.00', right)
            sheet.write(i, 11, line.amount_tax_exo or '0.00', right)
            sheet.write(i, 12, line.amount_tax_ina or '0.00', right)
            sheet.write(i, 13, line.amount_tax_isc or '0.00', right)
            sheet.write(i, 14, line.amount_tax_igv or '0.00', right)
            sheet.write(i, 15, line.amount_tax_other or '0.00', right)
            sheet.write(i, 16, line.amount_total or '0.00', right)
            sheet.write(i, 17, line.exchange_currency, right)
            sheet.write(i, 18, line.date_emission_update, normal)
            sheet.write(i, 19, line.document_payment_type_update, normal)
            sheet.write(i, 20, line.document_payment_series_update, normal)
            sheet.write(i, 21, line.document_payment_correlative_update, normal)
            sheet.write(i, 22, line.state_opportunity, normal)
            i += 1


class PleReport14Line(models.Model):
    _name = 'report.ple.14.line'
    _order = 'date_emission,document_payment_series,document_payment_number'
    _description = 'Detalle de registro de ventas'

    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Factura')

    period = fields.Char(string='Periodo', compute='_compute_data')
    cuo = fields.Char(string='CUO', compute='_compute_data')
    move_name = fields.Char(string='Asiento')
    date_emission = fields.Char(string='Fecha de emisión', compute='_compute_data')
    date_due = fields.Char(string='Fecha de vencimiento', compute='_compute_data')
    document_payment_type = fields.Char(string='Tipo', compute='_compute_data')
    document_payment_series = fields.Char(string='Serie', compute='_compute_data')
    document_payment_number = fields.Char(string='Nª del comprobante', compute='_compute_data')
    ticket_fiscal_credit = fields.Float(string='Operaciones sin derecho fiscal')
    customer_document_type = fields.Char(string='Tipo de DC', compute='_compute_data')
    customer_document_number = fields.Char(string='Número de DC')
    customer_name = fields.Char(string='Cliente', related='invoice_id.partner_id.name')
    amount_export = fields.Float(string='Valor facturado de la exportación', compute='_compute_amount', digits=(10, 2))
    amount_untaxed = fields.Float(string='Base imponible', compute='_compute_amount', digits=(10, 2))
    amount_discount_untaxed = fields.Float(string='Op. No Gravadas', compute='_compute_amount', digits=(10, 2))
    amount_tax_igv = fields.Float(string='IGV y/o IPM', compute='_compute_amount', digits=(10, 2))
    amount_tax_ina = fields.Float(string='Inafecta', compute='_compute_amount', digits=(10, 2))
    amount_tax_exo = fields.Float(string='Exonerada', compute='_compute_amount', digits=(10, 2))
    amount_tax_isc = fields.Float(string='ISC', compute='_compute_amount', digits=(10, 2))
    amount_rice = fields.Float(string='IVP', compute='_compute_amount', digits=(10, 2))
    amount_tax_rice = fields.Float(string='', compute='_compute_amount', digits=(10, 2))
    amount_tax_other = fields.Float(string='Otros conceptos', compute='_compute_amount', digits=(10, 2))
    amount_total = fields.Float(string='Imp. total', compute='_compute_amount', digits=(10, 2))
    currency = fields.Char(string='Moneda', compute='_compute_data')
    exchange_currency = fields.Float(string='Tipo de cambio', compute='_compute_data', digits=(10, 2), store=True)
    date_emission_update = fields.Char(string='Fecha emision de CR', compute='_compute_data')
    document_payment_type_update = fields.Char(string='Tipo de CR', compute='_compute_data')
    document_payment_series_update = fields.Char(string='Serie de CR', compute='_compute_data')
    document_payment_correlative_update = fields.Char(string='Correlativo de CR', compute='_compute_data')
    contract_ident = fields.Char(string='Identificación del contrato')
    type_error_1 = fields.Char(string='Error tipo 1')
    method_payment = fields.Boolean(string='Método de pago', compute='_compute_data')
    state_opportunity = fields.Char(string='Estado')
    ple_id = fields.Many2one(comodel_name='report.ple.14')


    @api.multi
    @api.depends('invoice_id')
    def _compute_statefacturas(self):
        for x in self:
            x.estatefacturas = x.invoice_id.state


    @api.multi
    @api.depends('invoice_id')
    def _compute_data(self):

        def get_series_correlative(name):
            return (name.split('-')[0], name.split('-')[1].rjust(8, '0')) if name and '-' in name else ('', '')

        def format_date(date):
            return date and fields.Date().from_string(date).strftime("%d/%m/%Y") or ''

        def get_year_month(date):
            return '{}{}'.format(fields.Date().from_string(date).year, fields.Date().from_string(date).month)
        self.mapped(lambda x: x.update({
            'period': '{}00'.format(get_year_month(x.invoice_id.date_invoice)),
            'cuo': x.invoice_id.move_id.name,
            'date_emission': format_date(x.invoice_id.date_invoice),
            'date_due': format_date(x.invoice_id.date_due),
            'document_payment_type': x.invoice_id.journal_id.l10n_pe_document_type_id.code or '',
            'document_payment_series': get_series_correlative(x.invoice_id.number)[0],
            'document_payment_number': get_series_correlative(x.invoice_id.number)[1],
            'customer_document_type': x.invoice_id.partner_id.l10n_pe_document_type or '',
            'customer_document_number': x.invoice_id.partner_id.vat or '',
            'date_emission_update': format_date(x.invoice_id.l10n_pe_invoice_origin_id.date_invoice),
            'document_payment_type_update':
                x.invoice_id.l10n_pe_invoice_origin_id.journal_id.l10n_pe_document_type_id.code,
            'document_payment_series_update': get_series_correlative(x.invoice_id.l10n_pe_invoice_origin_id.number)[0],
            'document_payment_correlative_update': get_series_correlative(
                x.invoice_id.l10n_pe_invoice_origin_id.number)[1],
            'currency':
                x.invoice_id.currency_id != x.invoice_id.company_id.currency_id and x.invoice_id.currency_id.name or '',
            'exchange_currency': x.invoice_id.l10n_pe_exchange_rate,
            'method_payment': x.invoice_id.state in ['paid'] or False
        }))

    @api.depends('invoice_id', 'exchange_currency')
    def _compute_amount(self):
        def get_amount_tax(lines):
            def compute_tax(p, t, x):
                res = t.compute_all(p, x.invoice_id.currency_id, x.quantity, product=x.product_id, partner=x.invoice_id.partner_id)
                return res['total_included'] - res['total_excluded'] if res['total_included'] != res['total_excluded'] else res['total_included']

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
            'amount_export': 0,
            'amount_untaxed': w.invoice_id.amount_untaxed * (w.exchange_currency or 1),
            'amount_discount_untaxed': 0,
            'amount_tax_igv': 0.0 if(w.invoice_id.state == "cancel") else get_amount_tax(w.invoice_id.invoice_line_ids)[3] * (w.exchange_currency or 1),
            'amount_tax_ina': 0.0 if(w.invoice_id.state == "cancel") else get_amount_tax(w.invoice_id.invoice_line_ids)[1] * (w.exchange_currency or 1),
            'amount_tax_exo': 0.0 if(w.invoice_id.state == "cancel") else get_amount_tax(w.invoice_id.invoice_line_ids)[0] * (w.exchange_currency or 1),
            'amount_tax_isc': 0.0 if(w.invoice_id.state == "cancel") else get_amount_tax(w.invoice_id.invoice_line_ids)[2] * (w.exchange_currency or 1),
            'amount_tax_other': 0.0 if(w.invoice_id.state == "cancel") else get_amount_tax(w.invoice_id.invoice_line_ids)[4] * (w.exchange_currency or 1),
            'amount_total': 0.0 if(w.invoice_id.state == "cancel") else  w.invoice_id.amount_total * (w.exchange_currency or 1)
        }))
