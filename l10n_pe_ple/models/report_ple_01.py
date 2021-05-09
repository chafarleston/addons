from odoo import api, fields, models
from .account import CASH, CURRENT_ACCOUNT
import base64


class ReportPle01(models.Model):
    _name = 'report.ple.01'
    _inherit = ['report.ple']
    _description = 'Libro caja y bancos'

    file_current_account = fields.Binary(string='Cuenta corriente TXT', readonly=True)
    filename_current_account = fields.Char(string='Nombre del archivo de cuenta corriente')

    @api.model
    def create(self, vals):
        res = super(ReportPle01, self).create(vals)
        res.update({'name': self.env['ir.sequence'].next_by_code(self._name)})
        return res

    def get_move_lines(self, type_box):
        date_start = self.range_id.date_start
        date_end = self.range_id.date_end
        return self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id),
            ('date', '>=', date_start),
            ('date', '<=', date_end),
            ('move_id.state', 'in', ['posted']),
            ('account_id.user_type_id.l10n_pe_type_box', '=', type_box)
        ], order='date')

    @api.multi
    def action_generate(self):
        prefix = "LE"
        company_vat = self.env.user.company_id.partner_id.vat
        date_start = self.range_id.date_start
        year, month = fields.Date().from_string(date_start).year, fields.Date().from_string(date_start).month
        currency = 2 if self.currency_id.name in ['USD'] else 1
        template = "{}{}{}{}00{}00{}{}{}{}.txt"

        # efectivo
        filename = template.format(
            prefix, company_vat, year, month, '010100', self.indicator_operation,
            self.indicator_content, currency, 1)
        move_lines = self.get_move_lines(CASH)
        data = self._get_content_cash(move_lines)
        value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}

        # cuenta corriente
        filename = template.format(
            prefix, company_vat, year, month, '010200', self.indicator_operation,
            self.indicator_content, currency, 1)
        move_lines = self.get_move_lines(CURRENT_ACCOUNT)
        data = self._get_content_current_account(move_lines)
        value.update({'filename_current_account': filename, 'file_current_account': base64.encodebytes(data.encode('utf-8'))})
        self.action_generate_ple(value)

    def _get_content_cash(self, move_lines):
        template = '{period}|{cuo}|{move_name}|{account_code}|{unit_operation_code}|{cost_center_code}|{currency}|' \
                   '{document_type}|{invoice_series}|{invoice_correlative}|{date}|{due_date}|{operation_date}|' \
                   '{operation_gloss}|{reference_gloss}|{debit}|{credit}|{relate_code}|{operation_state}|\r\n'
        data = ''
        for x, line in enumerate(move_lines, 1):
            name = line.move_id.name.split('-')[1] if '-' in line.move_id.name else line.move_id.name
            data += template.format(
                period=u'{}00'.format(self.get_year_month(line.date)),
                cuo=line.move_id.name,
                move_name=u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, line.id),
                account_code=line.account_id.code,
                unit_operation_code='',
                cost_center_code='',
                currency=line.company_id.currency_id.name if not line.currency_id.name else line.currency_id.name,
                document_type=line.move_id.journal_id.l10n_pe_document_type_id.code,
                invoice_series=line.move_id.name.split('-')[0] if '-' in line.move_id.name else '',
                invoice_correlative=name.replace('/', '') if '/' in name else name,
                date=fields.Date().from_string(line.date).strftime("%d/%m/%Y"),
                due_date=fields.Date().from_string(line.date_maturity).strftime("%d/%m/%Y"),
                operation_date=fields.Date().from_string(line.date).strftime("%d/%m/%Y"),
                operation_gloss=line.name or '',
                reference_gloss='',
                debit=round(line.debit, 2) if line.debit else '0.00',
                credit=round(line.credit, 2) if line.credit else '0.00',
                relate_code='',
                operation_state=line.move_id.l10n_pe_operation_state_sunat
            )
        return data

    def _get_content_current_account(self, move_lines):
        template = '{period}|{cuo}|{move_name}|{entity_code}|{account_code}|{date_operation}|{payment_method}|' \
                   '{operation_description}|{document_type}|{document_number}|{name}|{transaction_number}|{debit}|' \
                   '{credit}|{operation_state}|\r\n'
        data = ''
        for x, line in enumerate(move_lines, 1):
            data += template.format(
                period=u'{}00'.format(self.get_year_month(line.date)),
                cuo=line.move_id.name,
                move_name=u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, line.id),
                entity_code=line.move_id.journal_id.bank_id.bic,
                account_code=line.move_id.journal_id.bank_acc_number,
                date_operation=fields.Date().from_string(line.date).strftime("%d/%m/%Y"),
                payment_method='',
                operation_description=line.name,
                document_type=line.move_id.journal_id.company_partner_id.l10n_pe_document_type,
                document_number=line.move_id.journal_id.company_partner_id.l10n_pe_document_number,
                name=line.move_id.journal_id.company_partner_id.name,
                transaction_number='',
                debit=round(line.debit, 2) if line.debit else '0.00',
                credit=round(line.credit, 2) if line.credit else '0.00',
                operation_state=line.move_id.l10n_pe_operation_state_sunat
            )
        return data

    def generate_xlsx_report(self, workbook, data, obj):
        self._build_file_content1_1(workbook, obj)
        self._build_file_content1_2(workbook, obj)

    def _build_file_content1_1(self, workbook, obj):
            sheet = workbook.add_worksheet('F1.1 Detalle mov efectivo')
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
            sheet.set_column('C:C', 40)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:E', 40)
            sheet.set_column('F:F', 15)
            sheet.set_column('G:G', 15)

            sheet.set_row(8, 30)
            sheet.set_row(9, 40)

            name = u'FORMATO 1.1: "LIBRO CAJA Y BANCOS - DETALLE DE LOS MOVIMIENTOS DEL EFECTIVO"'
            sheet.merge_range('A1:F1', name, bold_right)
            sheet.merge_range('A3:B3', u'PERÍODO: {}'.format(obj.range_id.name), bold_right)
            sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.l10n_pe_document_number), bold_right)
            sheet.merge_range('A5:F5',
                              u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                              bold_right)

            sheet.merge_range('A9:A10', u'NÚMERO CORRELATIVO \nDEL REGISTRO O \nCÓDIGO ÚNICO DE \nLA OPERACIÓN', bold)
            sheet.merge_range('B9:B10', u'FECHA DE LA \nOPERACIÓN', bold)
            sheet.merge_range('C9:C10', u'DESCRIPCIÓN DE \nLA OPERACIÓN', bold)

            sheet.merge_range('D9:E9', u'CUENTA CONTABLE ASOCIADA', bold)
            sheet.write('D10', u'CÓDIGO', bold)
            sheet.write('E10', u'DENOMINACIÓN', bold)

            sheet.merge_range('F9:G9', u'SALDOS Y MOVIMIENTO', bold)
            sheet.write('F10', u'DEUDOR', bold)
            sheet.write('G10', u'ACREEDOR', bold)

            move_lines = obj.get_move_lines(CASH)
            i = 10
            t_debit = t_credit = 0
            for x, line in enumerate(move_lines, 1):
                sheet.write(i, 0, u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, line.id), normal)
                sheet.write(i, 1, fields.Date().from_string(line.date).strftime("%d/%m/%Y"), normal)
                sheet.write(i, 2, line.name, normal)
                sheet.write(i, 3, line.account_id.code, normal)
                sheet.write(i, 4, line.account_id.name, normal)
                sheet.write(i, 5, line.debit, right)
                sheet.write(i, 6, line.credit, right)
                i += 1
                t_debit += line.debit
                t_credit += line.credit

            sheet.write(i, 4, 'TOTAL', bold)
            sheet.write(i, 5, t_debit, right)
            sheet.write(i, 6, t_credit, right)

    def _build_file_content1_2(self, workbook, obj):
            sheet = workbook.add_worksheet('F1.2 Detalle mov cta cte')
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
            sheet.set_column('C:C', 20)
            sheet.set_column('D:D', 20)
            sheet.set_column('E:E', 40)
            sheet.set_column('F:F', 40)
            sheet.set_column('G:G', 15)
            sheet.set_column('H:H', 20)
            sheet.set_column('I:I', 15)
            sheet.set_column('J:J', 15)

            sheet.set_row(8, 30)
            sheet.set_row(9, 40)

            name = u'FORMATO 1.2: "LIBRO CAJA Y BANCOS - DETALLE DE LOS MOVIMIENTOS DE LA CUENTA CORRIENTE"'
            sheet.merge_range('A1:F1', name, bold_right)
            sheet.merge_range('A3:B3', u'PERÍODO: {}'.format(obj.range_id.name), bold_right)
            sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.l10n_pe_document_number), bold_right)
            sheet.merge_range('A5:F5',
                              u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                              bold_right)

            sheet.merge_range('A6:C6', u'ENTIDAD FINANCIERA: {}'.format(''), bold_right)
            sheet.merge_range('A7:C7', u'CÓDIGO DE LA CUENTA CORRIENTE: {}'.format(''), bold_right)

            sheet.merge_range('A9:A10', u'NÚMERO CORRELATIVO \nDEL REGISTRO O \nCÓDIGO ÚNICO DE \nLA OPERACIÓN', bold)
            sheet.merge_range('B9:B10', u'FECHA DE LA \nOPERACIÓN', bold)

            sheet.merge_range('C9:F9', u'OPERACIONES BANCARIAS', bold)
            sheet.write('C10', u'MEDIO DE PAGO', bold)
            sheet.write('D10', u'DESCRIPCIÓN DE \nLA OPERACIÓN', bold)
            sheet.write('E10', u'APELLIDOS Y NOMBRES,\nDENOMINACIÓN O RAZÓN SOCIAL', bold)
            sheet.write('F10',
                        u'NÚMERO DE TRANSACCIÓN BANCARIA,\nDE DOCUMENTO SUSTENTATORIO O DE \nCONTROL INTERNO DE LA OPERACIÓN',
                        bold)

            sheet.merge_range('G9:H9', u'CUENTA CONTABLE ASOCIADA', bold)
            sheet.write('G10', u'CÓDIGO', bold)
            sheet.write('H10', u'DENOMINACIÓN', bold)

            sheet.merge_range('I9:J9', u'SALDOS Y MOVIMIENTO', bold)
            sheet.write('I10', u'DEUDOR', bold)
            sheet.write('J10', u'ACREEDOR', bold)

            move_lines = obj.get_move_lines(CURRENT_ACCOUNT)
            i = 10
            t_debit = t_credit = 0
            for x, line in enumerate(move_lines, 1):
                sheet.write(i, 0, u'{}{}'.format(line.move_id.l10n_pe_operation_type_sunat, line.id), normal)
                sheet.write(i, 1, fields.Date().from_string(line.date).strftime("%d/%m/%Y"), normal)
                sheet.write(i, 2, '', normal)
                sheet.write(i, 3, line.name, normal)
                sheet.write(i, 4, line.partner_id.name, normal)
                sheet.write(i, 5, line.id, normal)
                sheet.write(i, 6, line.account_id.code, normal)
                sheet.write(i, 7, line.account_id.name, normal)
                sheet.write(i, 8, line.debit, right)
                sheet.write(i, 9, line.credit, right)
                i += 1
                t_debit += line.debit
                t_credit += line.credit

            sheet.write(i, 7, 'TOTAL', bold)
            sheet.write(i, 8, t_debit, right)
            sheet.write(i, 9, t_credit, right)
