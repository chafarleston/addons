from odoo import api, fields, models
from .report_ple import _STATES_READONLY
from .account import LOSS_GAIN, BALANCE

import base64

OP_01 = '01'
OP_02 = '02'
OP_03 = '03'
OP_04 = '04'
OP_05 = '05'
OP_06 = '06'
OP_07 = '07'

OPORTUNITY_CODE_SELECTION = [
    (OP_01, 'Al 31 de diciembre'),
    (OP_02, 'Al 31 de enero, por modificación del porcentaje'),
    (OP_03, 'Al 30 de junio, por modificación del coeficiente o porcentaje'),
    (OP_04, 'Al último día del mes que sustentará la suspensión o modificación del coeficiente'
            ' (distinto al 31 de enero o 30 de junio'),
    (OP_05, 'Al día anterior a la entrada en vigencia de la fusión, escisión y demás formas de'
            ' reorganización de sociedades o empresas o extinción de la persona jurídica'),
    (OP_06, 'A la fecha del balance de liquidación, cierre o cese definitivo del deudor tributario'),
    (OP_07, 'A la fecha de presentación para libre propósito'),
]


class PleReport317(models.Model):
    _name = 'report.ple.317'
    _inherit = ['report.ple']
    _description = 'Libro Balance de comprobacion'

    ple_06_id = fields.Many2one(comodel_name='report.ple.06', string='Libro mayor', required=True,
                                domain="[('range_id', '=', range_id), ('state', 'in', ['validated', 'declared'])]")
    line_ids = fields.One2many(comodel_name='report.ple.317.line', inverse_name='ple_id',
                               string='Detalle', readonly=True)

    opportunity_code = fields.Selection(selection=OPORTUNITY_CODE_SELECTION,
                                        string='Código de oportunidad de presentación del EEFF',
                                        default=OP_07, states=_STATES_READONLY)

    @api.model
    def create(self, vals):
        res = super(PleReport317, self).create(vals)
        res.update({'name': self.env['ir.sequence'].next_by_code(self._name)})
        return res

    @api.multi
    def action_generate(self):
        prefix = "LE"
        company_vat = self.env.user.company_id.partner_id.vat
        date = fields.Date().from_string(self.range_id.date_end).strftime("%Y%m%d")
        currency = 2 if self.currency_id.name in ['USD'] else 1
        template = "{}{}{}{}{}{}{}{}{}.txt"
        filename = template.format(
            prefix, company_vat, date, '031700', self.opportunity_code, self.indicator_operation,
            self.indicator_content, currency, 1
        )
        self.create_lines()
        data = self._get_content(self.line_ids)
        value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}
        self.action_generate_ple(value)

    @api.multi
    def create_lines(self):
        self.line_ids.unlink()
        self._cr.execute("""
            SELECT l.account_id as account_id, COALESCE(SUM(l.credit), 0) as credit, COALESCE(SUM(l.debit), 0) as debit 
            FROM report_ple_06_line l 
            WHERE ple_id = %s
            GROUP BY l.account_id;
        """ % self.ple_06_id.id)
        values = self._cr.dictfetchall()
        domain = [('date_end', '<', self.range_id.date_start)]
        range_obj = self.env['date.range'].search(domain, order='date_end DESC', limit=1)
        obj = self.search([('range_id', '=', range_obj.id)]) if range_obj else False
        initial_debit = initial_credit = 0
        for val in values:
            if obj:
                line_ids = obj.line_ids.filtered(lambda x: x.account_id.id == val.get('account_id'))
                initial_debit = sum(line_ids.mapped('balance_debit'))
                initial_credit = sum(line_ids.mapped('balance_credit'))
            self.env['report.ple.317.line'].create({
                'period': fields.Date().from_string(self.range_id.date_end).strftime("%Y%m%d"),
                'account_id': val.get('account_id'),
                'initial_debit':  initial_debit,
                'initial_credit': initial_credit,
                'period_debit': val.get('debit'),
                'period_credit': val.get('credit'),
                'ple_id': self.id
            })

    @staticmethod
    def _get_content(move_line_obj):
        template = '{period}|{account_code}|{initial_debit}|{initial_credit}|{period_debit}|' \
                   '{period_credit}|{major_debit}|{major_credit}|{balance_debit}|{balance_credit}|{transfer_debit}|' \
                   '{transfer_credit}|{balance_active}|{balance_passive}|{result_loss}|{result_gain}|{addition}|' \
                   '{deduction}|{operation_state}|\r\n'
        data = ''
        for line in move_line_obj:
            data += template.format(
                period=line.period,
                account_code=line.account_id.code,
                initial_debit=line.initial_debit or '0.00',
                initial_credit=line.initial_credit or '0.00',
                period_debit=line.period_debit or '0.00',
                period_credit=line.period_credit or '0.00',
                major_debit=line.major_debit or '0.00',
                major_credit=line.major_credit or '0.00',
                balance_debit=0 or '0.00',
                balance_credit=0 or '0.00',
                transfer_debit=0 or '0.00',
                transfer_credit=0 or '0.00',
                balance_active=0 or '0.00',
                balance_passive=0 or '0.00',
                result_loss=0 or '0.00',
                result_gain=0 or '0.00',
                addition=0 or '0.00',
                deduction=0 or '0.00',
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

        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 20)
        sheet.set_column('L:L', 20)

        sheet.set_row(6, 35)
        sheet.set_row(7, 30)

        sheet.merge_range('A1:F1', u'FORMATO 3.17: "LIBRO DE INVENTARIOS Y BALANCES - BALANCE DE COMPROBACIÓN"',
                          bold_right)
        sheet.merge_range('A3:B3', u'PERIODO: {}'.format(obj.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(obj.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(obj.company_id.name),
                          bold_right)

        sheet.merge_range('A7:B7', u'CUENTA', bold)
        sheet.write('A8', u'CÓDIGO', bold)
        sheet.write('B8', u'DENOMICACIÓN', bold)
        sheet.merge_range('C7:D7', u'SALDOS INICIALES', bold)
        sheet.write('C8', u'DEUDOR', bold)
        sheet.write('D8', u'ACREDOR', bold)
        sheet.merge_range('E7:F7', u'MOVIMIENTOS', bold)
        sheet.write('E8', u'DEBE', bold)
        sheet.write('F8', u'HABER', bold)
        sheet.merge_range('G7:H7', u'SALDOS FINALES', bold)
        sheet.write('G8', u'DEUDOR', bold)
        sheet.write('H8', u'ACREDOR', bold)
        sheet.merge_range('I7:J7', u'SALDOS FINALES DEL \nBALANCE GENERAL', bold)
        sheet.write('I8', u'ACTIVO', bold)
        sheet.write('J8', u'PASIVO Y \nPATRIMONIO', bold)
        sheet.merge_range('K7:L7', u'SALDOS FINALES DEL ESTADO DE \nPÉRDIDAS Y GANANCIAS POR FUNCIÓN', bold)
        sheet.write('K8', u'PÉRDIDAS', bold)
        sheet.write('L8', u'GANANCIAS', bold)
        i = 8
        t_initial_debit = t_initial_credit = t_period_debit = t_period_credit = t_balance_debit = t_balance_credit = 0
        t_result_gain = t_result_loss = t_balance_active = t_balance_passive = 0
        for line in obj.line_ids.sorted(lambda x: x.code):
            sheet.write(i, 0, line.account_id.code, normal)
            sheet.write(i, 1, line.account_id.name, left)
            sheet.write(i, 2, line.initial_debit or '0.00', right)
            sheet.write(i, 3, line.initial_credit or '0.00', right)
            sheet.write(i, 4, line.period_debit or '0.00',  right)
            sheet.write(i, 5, line.period_credit or '0.00', right)
            sheet.write(i, 6, line.balance_debit or '0.00', right)
            sheet.write(i, 7, line.balance_credit or '0.00', right)
            sheet.write(i, 8, line.balance_active or '0.00', right)
            sheet.write(i, 9, line.balance_passive or '0.00', right)
            sheet.write(i, 10, line.result_loss or '0.00', right)
            sheet.write(i, 11, line.result_gain or '0.00', right)
            t_initial_credit += round(line.initial_credit, 2)
            t_initial_debit += round(line.initial_debit, 2)
            t_period_credit += round(line.period_credit, 2)
            t_period_debit += round(line.period_debit, 2)
            t_balance_credit += round(line.balance_credit, 2)
            t_balance_debit += round(line.balance_debit, 2)
            t_result_gain += round(line.result_gain, 2)
            t_result_loss += round(line.result_loss, 2)
            t_balance_active += round(line.balance_active, 2)
            t_balance_passive += round(line.balance_passive, 2)
            i += 1

        sheet.write(i, 0, 'TOTALES', bold)
        sheet.write(i, 2, float(t_initial_debit) or '0.00', right)
        sheet.write(i, 3, float(t_initial_credit) or '0.00', right)
        sheet.write(i, 4, float(t_period_debit) or '0.00', right)
        sheet.write(i, 5, float(t_period_credit) or '0.00', right)
        sheet.write(i, 6, float(t_balance_debit) or '0.00', right)
        sheet.write(i, 7, float(t_balance_credit) or '0.00', right)
        sheet.write(i, 8, float(t_balance_active) or '0.00', right)
        sheet.write(i, 9, float(t_balance_passive) or '0.00', right)
        sheet.write(i, 10, float(t_result_loss) or '0.00', right)
        sheet.write(i, 11, float(t_result_gain) or '0.00', right)


class ReportPle317Line(models.Model):
    _name = 'report.ple.317.line'
    _order = 'code'
    _description = 'Detalle de libro balance'

    period = fields.Char(string='Periodo')
    account_id = fields.Many2one(comodel_name='account.account', string='Cuenta')
    code = fields.Char(related='account_id.code', store=True)
    initial_debit = fields.Float(string='Saldo inicial débito')
    initial_credit = fields.Float(string='Sadlo inicial crédito')
    period_debit = fields.Float(string='Débito')
    period_credit = fields.Float(string='Crédito')
    balance_debit = fields.Float(string='Saldo débito', compute='_compute_balance')
    balance_credit = fields.Float(string='Saldo crédito', compute='_compute_balance')
    major_debit = fields.Float(string='Mayor débito')
    major_credit = fields.Float(string='Mayor crédito')
    transfer_debit = fields.Float(string='Transferenciq débito')
    transfer_credit = fields.Float(string='Transferencia crédito')
    balance_active = fields.Float(string='Activo')
    balance_passive = fields.Float(string='Pasivo')
    result_loss = fields.Float(string='Pérdida')
    result_gain = fields.Float(string='Ganancia')
    addition = fields.Float(string='Adiciones')
    deduction = fields.Float(string='Deducciones')
    operation_state = fields.Float(string='Operación')
    ple_id = fields.Many2one(comodel_name='report.ple.317', string='Balance de comprobación', required=True)

    @api.multi
    @api.depends('account_id')
    def _compute_balance(self):
        self.mapped(lambda x: x.update({
            'major_debit': x.initial_debit + x.period_debit,
            'major_credit': x.initial_credit + x.period_credit,
            'balance_active': abs(x.period_credit - x.period_debit)
            if x.period_credit < x.period_debit and x.account_id.user_type_id.l10n_pe_type_plan == BALANCE else 0,
            'balance_passive':  abs(x.period_debit - x.period_credit)
            if x.period_credit > x.period_debit and x.account_id.user_type_id.l10n_pe_type_plan == BALANCE else 0,
            'result_loss': abs(x.period_credit - x.period_debit)
            if x.period_credit < x.period_debit and x.account_id.user_type_id.l10n_pe_type_plan == LOSS_GAIN else 0,
            'result_gain':  abs(x.period_debit - x.period_credit)
            if x.period_credit > x.period_debit and x.account_id.user_type_id.l10n_pe_type_plan == LOSS_GAIN else 0,
            'balance_debit': abs(x.period_credit - x.period_debit) if x.period_credit < x.period_debit else 0,
            'balance_credit': abs(x.period_debit - x.period_credit) if x.period_credit > x.period_debit else 0,
        }))
