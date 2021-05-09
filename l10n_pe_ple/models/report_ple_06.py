from odoo import api, fields, models
from .report_ple import _STATES_READONLY
import base64

OPENING = 'A'
MOVING = 'M'
CLOSING = 'C'

OPERATION_TYPE_SUNAT_SELECTION = [
    (OPENING, 'Apertura del ejercicio'),
    (MOVING, 'Movimiento del mes'),
    (CLOSING, 'Cierre del ejercicio')
]


class PleReport06(models.Model):
    _name = 'report.ple.06'
    _inherit = ['report.ple']
    _description = 'Libro mayor'

    line_ids = fields.One2many(comodel_name='report.ple.06.line', inverse_name='ple_id', readonly=True,
                               string='Detalle del libro mayor')
    operation_type_sunat = fields.Selection(selection=OPERATION_TYPE_SUNAT_SELECTION, string='Tipo de operación sunat',
                                            default=MOVING, states=_STATES_READONLY)

    @api.model
    def create(self, vals):
        res = super(PleReport06, self).create(vals)
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
        filename = template.format(
            prefix, company_vat, year, month, '060100', self.indicator_operation, self.indicator_content, currency, 1)
        self.create_lines(date_start, date_end)
        data = self._get_content(self.line_ids)
        value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}
        self.action_generate_ple(value)

    @api.multi
    def create_lines(self, date_start, date_end):
        self.line_ids.unlink()
        self._cr.execute("""
            SELECT aml.account_id as account_id, COALESCE(SUM(aml.credit), 0) as credit,
             COALESCE(SUM(aml.debit), 0) as debit 
            FROM account_move_line aml
            INNER JOIN account_move am ON am.id = aml.move_id 
            WHERE aml.company_id = {} AND am.date >= '{}'::date AND am.date <= '{}'::date
            GROUP BY aml.account_id;
        """.format(self.company_id.id, date_start, date_end))
        values = self._cr.dictfetchall()
        if values:
            for val in values:
                val.update({'ple_id': self.id})
                if val.get('credit'):
                    val2 = val.copy()
                    val2.update({'debit': 0.0})
                    self.env['report.ple.06.line'].create(val2)
                if val.get('debit'):
                    val.update({'credit': 0.0})
                    self.env['report.ple.06.line'].create(val)

    @api.multi
    def _get_content(self, move_line_obj):
        template = '{period}|{cuo}|{move_name}|{account_code}|{unit_operation_code}|{cost_center_code}|{currency}|' \
                   '{document_type}|{document_number}|{payment_type}|{invoice_series}|{invoice_correlative}|{date}|' \
                   '{due_date}|{operation_date}|{operation_gloss}|{reference_gloss}|{debit}|{credit}|{book_code}|' \
                   '{operation_state}|\r\n'

        data = ''
        date_start = self.range_id.date_start
        year, month = fields.Date().from_string(date_start).year, fields.Date().from_string(date_start).month
        for line in move_line_obj:
            data += template.format(
                period=u'{}{}00'.format(year, month),
                cuo=line.ple_id.name,
                move_name=u'{}{}'.format(line.ple_id.operation_type_sunat, line.id),
                account_code=line.account_id.code,
                unit_operation_code='',
                cost_center_code='',
                currency=(line.ple_id.company_id.currency_id.name
                          if not line.account_id.currency_id.name else line.account_id.currency_id.name),
                document_type='',
                document_number='',
                payment_type='00',
                invoice_series='',
                invoice_correlative='-',
                date='',
                due_date='',
                operation_date=fields.Date().from_string(self.range_id.date_end).strftime("%d/%m/%Y"),
                operation_gloss="Mayorización cuenta {}".format(line.account_id.code),
                reference_gloss='',
                debit=round(line.debit, 2) if line.debit else '0.00',
                credit=round(line.credit, 2) if line.credit else '0.00',
                book_code='',
                operation_state='1'
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

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 50)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 50)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)

        sheet.set_row(6, 25)
        sheet.set_row(7, 25)

        sheet.merge_range('A1:B1', u'FORMATO 6.1: "LIBRO MAYOR"', bold_right)
        sheet.merge_range('A3:B3', u'PERIODO: {}'.format(obj.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                          bold_right)

        sheet.merge_range('A7:A8', u'FECHA DE LA \nOPERACIÓN', bold)
        sheet.merge_range('B7:B8', u'NÚMERO \nCORRELATIVO \nDEL LIBRO', bold)
        sheet.merge_range('C7:C8', u'DESCRIPCIÓN O GLOSA\nDE LA OPERACIÓN', bold)
        sheet.merge_range('D7:E7', u'CUENTA CONTABLE ASOCIADA A LA OPERACIÓN', bold)
        sheet.write('D8', u'CÓDIGO', bold)
        sheet.write('E8', u'DENOMINACIÓN', bold)
        sheet.merge_range('F7:G7', u'SALDOS Y MOVIMIENTO', bold)
        sheet.write('F8', u'DEUDOR', bold)
        sheet.write('G8', u'ACREDOR', bold)
        i = 8

        t_debit = t_credit = 0
        for line in obj.line_ids:
            sheet.write(i, 0, fields.Date().from_string(fields.Date().today()).strftime("%d/%m/%Y"), normal)
            sheet.write(i, 1, '/', normal)
            sheet.write(i, 2, ' Mayorización cuenta {}'.format(line.account_id.code), left)
            sheet.write(i, 3, line.account_id.code, normal)
            sheet.write(i, 4, line.account_id.name, left)
            sheet.write(i, 5, round(line.debit, 2) or '0.00', right)
            sheet.write(i, 6, round(line.credit, 2) or '0.00', right)
            t_credit += round(line.credit, 2)
            t_debit += round(line.debit, 2)
            i += 1

        sheet.write(i, 4, 'TOTALES', bold)
        sheet.write(i, 5, t_credit, right)
        sheet.write(i, 6, t_debit, right)


class ReportPle06Line(models.Model):
    _name = 'report.ple.06.line'
    _order = 'code'
    _description = 'Detalle de libro mayor'

    account_id = fields.Many2one(comodel_name='account.account', string='Cuenta Contable')
    code = fields.Char(related='account_id.code', store=True)
    debit = fields.Float(string='Débito')
    credit = fields.Float(string='Crédito')
    ple_id = fields.Many2one(comodel_name='report.ple.06', string='Libro mayor')
