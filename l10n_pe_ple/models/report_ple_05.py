from odoo import api, fields, models

import base64


class ReportPle05(models.Model):
    _name = 'report.ple.05'
    _inherit = ['report.ple']
    _description = 'Libro diario'

    file_account_detail = fields.Binary(string='Detalle del plan contable utilizado', readonly=True)
    filename_account_detail = fields.Text(string='Nombre del archivo de detalle del plan contable utilizado')
    filename_simplified = fields.Char(string='Nombre del archivo  simplificado')
    file_simplified_account_detail = fields.Binary(string='Archivo TXT simplificado de plan contable utilizado',

                                                   readonly=True)
    filename_simplified_account_detail = fields.Char(
        string='Nombre del archivo simplificado del plan contable utilizado')

    @api.model
    def create(self, vals):
        res = super(ReportPle05, self).create(vals)
        res.update({'name': self.env['ir.sequence'].next_by_code(self._name)})
        return res

    def get_move_lines(self):
        date_start = self.range_id.date_start
        date_end = self.range_id.date_end
        return self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id),
            ('date', '>=', date_start),
            ('date', '<=', date_end),
            ('move_id.state', 'in', ['posted'])
        ])

    @api.multi
    def action_generate(self):
        prefix = "LE"
        company_vat = self.env.user.company_id.partner_id.vat
        date_start = self.range_id.date_start
        year, month = fields.Date().from_string(date_start).year, fields.Date().from_string(date_start).month
        currency = 2 if self.currency_id.name in ['USD'] else 1
        move_line_obj = self.get_move_lines()
        template = "{}{}{}{}00{}00{}{}{}{}.txt"
        if self.type_report in ['normal']:
            # diary report normal
            filename = template.format(
                prefix, company_vat, year, month, '050100', self.indicator_operation,
                self.indicator_content, currency, 1)
            data = self._get_content(move_line_obj)
            value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}
        elif self.type_report in ['simplified']:
            # diary report simplified
            filename = template.format(
                prefix, company_vat, year, month, '050200', self.indicator_operation,
                self.indicator_content, currency, 1)
            data = self._get_content_simplified(move_line_obj)
            value = {'filename_simplified': filename, 'file_simplified': base64.encodebytes(data.encode('utf-8'))}
        self.action_generate_ple(value)
        if self.period_special:
            if self.type_report in ['normal']:
                # plan account detail normal
                filename = template.format(
                    prefix, company_vat, year, month, '050300', self.indicator_operation,
                    self.indicator_content, currency, 1)
                data = self._get_content_account_detail(move_line_obj)
                value = {
                    'filename_account_detail': filename,
                    'file_account_detail': base64.encodebytes(data.encode('utf-8'))
                }
            elif self.type_report in ['simplified']:
                # plan account detail simplified
                filename = template.format(
                    prefix, company_vat, year, month, '050400', self.indicator_operation,
                    self.indicator_content, currency, 1)
                data = self._get_content_simplified_account_detail(move_line_obj)
                value = {
                    'filename_simplified_account_detail': filename,
                    'file_simplified_account_detail': base64.encodebytes(data.encode('utf-8'))
                }
            self.action_generate_ple(value)

    def _get_content(self, move_line_obj):
        template = '{period}|{cuo}|{move_name}|{account_code}|{unit_operation_code}|' \
                   '{cost_center_code}|{currency}|{document_type}|{document_number}|{payment_type}|' \
                   '{invoice_series}|{invoice_correlative}|{date}|{due_date}|{operation_date}|{operation_gloss}|' \
                   '{reference_gloss}|{debit}|{credit}|{book_code}|{operation_state}|\r\n'
        data = ''

        for x, line in enumerate(move_line_obj, 1):
            name = line.move_id.name.split('-')[1] if '-' in line.move_id.name else line.move_id.name
            data += template.format(
                period=u'{}00'.format(self.get_year_month(line.date)),
                cuo=line.move_id.name,
                move_name=u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, line.id),
                account_code=line.account_id.code,
                unit_operation_code='',
                cost_center_code='',
                currency=line.company_id.currency_id.name if not line.currency_id.name else line.currency_id.name,
                document_type='',
                document_number='',
                payment_type=line.invoice_id.journal_id.l10n_pe_document_type_id.code or '00',
                invoice_series=line.move_id.name.split('-')[0] if '-' in line.move_id.name else '',
                invoice_correlative=name.replace('/', '') if '/' in name else name,
                date='',
                due_date='',
                operation_date=fields.Date().from_string(line.date).strftime("%d/%m/%Y"),
                operation_gloss=line.name or '',
                reference_gloss='',
                debit=round(line.debit, 2) if line.debit else '0.00',
                credit=round(line.credit, 2) if line.credit else '0.00',
                book_code='',
                operation_state=line.move_id.l10n_pe_operation_state_sunat
            )
        return data

    @staticmethod
    def _get_content_account_detail(move_line_obj):
        template = '{period}|{account_code}|{account_name}|{account_plan_code}|{account_plan_name}|' \
                   '{enterprise_account_code}|{enterprise_account_name}|{operation_state}|\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=fields.Date().from_string(line.move_id.date).strftime("%Y%m%d"),
                account_code=line.account_id.code,
                account_name=line.account_id.name,
                account_plan_code=line.company_id.l10n_pe_plan_account_id.code,
                account_plan_name=line.company_id.l10n_pe_plan_account_id.name,
                enterprise_account_code='',
                enterprise_account_name='',
                operation_state=1
            )
        return data

    def _get_content_simplified(self, move_line_obj):
        template = '{period}|{cuo}|{move_name}|{account_code}|{unit_operation_code}|{cost_center_code}|' \
                   '{currency}|{document_type}|{document_number}|{payment_type}|{invoice_series}|' \
                   '{invoice_correlative}|{date}|{due_date}|{operation_date}|{operation_gloss}|{reference_gloss}|' \
                   '{debit}|{credit}|{book_code}|{operation_state}|\r\n'
        data = ''
        for x, line in enumerate(move_line_obj, 1):
            name = line.move_id.name.split('-')[1] if '-' in line.move_id.name else line.move_id.name
            data += template.format(
                period=u'{}00'.format(self.get_year_month(line.date)),
                cuo=line.move_id.name,
                move_name=u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, x),
                account_code=line.account_id.code,
                unit_operation_code='',
                cost_center_code='',
                currency=line.company_id.currency_id.name if not line.currency_id.name else line.currency_id.name,
                document_type='',
                document_number='',
                payment_type=line.invoice_id.serie_id.document_type_id.code or '00',
                invoice_series=line.move_id.name.split('-')[0] if '-' in line.move_id.name else '',
                invoice_correlative=name.replace('/', '') if '/' in name else name,
                date='',
                due_date='',
                operation_date=fields.Date().from_string(line.date).strftime("%d/%m/%Y"),
                operation_gloss=line.name or '',
                reference_gloss='',
                debit=round(line.debit, 2) or '0.00',
                credit=round(line.credit, 2) or '0.00',
                book_code='',
                operation_state=line.move_id.l10n_pe_operation_state_sunat
            )
        return data

    @staticmethod
    def _get_content_simplified_account_detail(move_line_obj):
        template = '{period}|{account_code}|{account_name}|{account_plan_code}|{account_plan_name}|' \
                   '{enterprise_account_code}|{enterprise_account_name}|{operation_state}|\r\n'

        data = ''
        for line in move_line_obj:
            data += template.format(
                period=fields.Date().from_string(line.move_id.date).strftime("%Y%m%d"),
                account_code=line.account_id.code,
                account_name=line.account_id.name,
                account_plan_code=line.company_id.plan_account_id.code,
                account_plan_name=line.company_id.plan_account_id.name,
                enterprise_account_code='',
                enterprise_account_name='',
                operation_state=1
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

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 50)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 50)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)

        sheet.set_row(6, 30)
        sheet.set_row(7, 40)

        sheet.merge_range('A1:B1', u'FORMATO 5.1: "LIBRO DIARIO"', bold_right)
        sheet.merge_range('A3:B3', u'PERIODO: {}'.format(obj.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                          bold_right)

        sheet.merge_range('A7:A8', u'NÚMERO CORRELATIVO \nDEL ASIENTO O \nCÓDIGO ÚNICO DE \nLA OPERACIÓN', bold)
        sheet.merge_range('B7:B8', u'FECHA DE LA \nOPERACIÓN', bold)
        sheet.merge_range('C7:C8', u'GLOSA O \nDESCRIPCIÓN \nDE LA OPERACIÓN', bold)
        sheet.merge_range('D7:F7', u'REFERENCIA DE LA OPERACIÓN', bold)
        sheet.write('D8', u'CÓDIGO DEL LIBRO \nO REGISTRO', bold)
        sheet.write('E8', u'NÚMERO \nCORRELATIVO', bold)
        sheet.write('F8', u'NÚMERO DEL \nDOCUMENTO \n SUSTENTATORIO', bold)
        sheet.merge_range('G7:H7', u'CUENTA CONTABLE ASOCIADA A LA OPERACIÓN', bold)
        sheet.write('G8', u'CÓDIGO', bold)
        sheet.write('H8', u'DENOMINACIÓN', bold)
        sheet.merge_range('I7:J7', u'MOVIMIENTO', bold)
        sheet.write('I8', u'DEBE', bold)
        sheet.write('J8', u'HABER', bold)
        i = 8
        move_line_obj = obj.get_move_lines()
        move_line_obj = move_line_obj.sorted(lambda x: x.account_id.code)
        t_debit = t_credit = 0
        for x, line in enumerate(move_line_obj, 1):
            sheet.write(i, 0, u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, x), normal)
            sheet.write(i, 1, fields.Date().from_string(line.date).strftime("%d/%m/%Y"), normal)
            sheet.write(i, 2, line.name or '/', left)
            sheet.write(i, 3, '050100', normal)
            sheet.write(i, 4, line.move_id.name, left)
            sheet.write(i, 5, '', left)
            sheet.write(i, 6, line.account_id.code, normal)
            sheet.write(i, 7, line.account_id.name, left)
            sheet.write(i, 8, round(line.debit, 2) or '0.00', right)
            sheet.write(i, 9, round(line.credit, 2) or '0.00', right)
            t_credit += round(line.credit, 2)
            t_debit += round(line.debit, 2)
            i += 1

        workbook.add_format({'bold': True})
        sheet.write(i, 7, 'TOTALES', bold)
        sheet.write(i, 8, t_credit, right)
        sheet.write(i, 9, t_debit, right)
