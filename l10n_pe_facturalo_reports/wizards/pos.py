
from odoo import api, fields, models


class ReportL10nPos(models.TransientModel):
    _name = 'report.l10n_pe.pos'
    _inherit = 'report.report_xlsx.abstract'
    _rec_name = 'config_id'

    company_id = fields.Many2one(comodel_name='res.company', string=u'Companía', default=lambda self: self.env.user.company_id,
                                 required=True)
    config_id = fields.Many2one(comodel_name='pos.config', string='Punto de venta', required=True)
    date_start = fields.Datetime(string='Fecha de inicio', required=True,
                             default=lambda self: str(fields.Date().from_string(fields.Date().context_today(self)).replace(day=1)))
    date_end = fields.Datetime(string='Fecha de fin', required=True, default=lambda self: str(fields.Date().context_today(self)))
    user_id = fields.Many2one(comodel_name='res.users', string='Vendedor')
    line_ids = fields.One2many(comodel_name='report.l10n_pe.pos.line', inverse_name='l10n_pe_pos_id', string='Detalle',
                               readonly=True)

    def generate_detail(self):
        if not self.date_end or not self.date_start or not self.config_id:
            return
        lines = self.get_datas()
        self.update({'line_ids': [(0, 0, line) for line in lines]})

    def get_datas(self):
        orders = self.get_orders()
        return [dict(invoice_id=order.get('invoice_id'), table_id=order.get('table_id')) for order in orders]

    def get_orders(self):
        domain = [
            ('invoice_id.date_invoice', '>=', self.date_start),
            ('invoice_id.date_invoice', '<=', self.date_end),
            ('session_id.config_id', '=', self.config_id.id),
            ('invoice_id.company_id', '=', self.company_id.id)
        ]
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        orders = self.env['pos.order'].search(domain)
        return orders.mapped(lambda order: {
            'invoice_id': order.invoice_id.id,
            'invoice_number': order.invoice_id.number,
            'date_invoice': order.invoice_id.date_invoice,
            'partner_name': order.partner_id.name,
            'floor_name': order.table_id.floor_id.name,
            'table_name': order.table_id.name,
            'table_id': order.table_id.id,
            'user_name': order.user_id.name,
            'amount_total': order.invoice_id.amount_total
        })

    def generate_xlsx_report(self, wb, data, obj):
        sheet = wb.add_worksheet('Reporte por tienda')
        align_center_wrap_format = wb.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'size': 10,
            'font_color': 'white',
            'bold': True
        })
        align_center_wrap_format.set_bg_color('#875a7b')
        align_center_wrap_format2 = wb.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'size': 10
        })
        align_center_wrap_format3 = wb.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'size': 10
        })

        format_content_table = wb.add_format({'size': 10, 'bold': True})
        format_qty = wb.add_format({'size': 10, 'border': 1, 'align': 'right'})
        align_center_wrap_format.set_text_wrap()

        i, j, x, y = 2, 4, 4, 6

        date_start = fields.Date().from_string(obj.date_start).strftime('%d/%m/%Y')
        date_end = fields.Date().from_string(obj.date_end).strftime('%d/%m/%Y')

        text_fecha = 'FECHA: (DESDE: ' + str(date_start) + ' - HASTA: ' + str(date_end) + ')'

        sheet.write('A1:D1', 'EMPRESA: {}'.format(self.env.user.company_id.name), format_content_table)
        sheet.write('A2:B2', 'TIENDA: {}'.format(obj.config_id.name), format_content_table)
        sheet.merge_range('D2:F2', text_fecha, format_content_table)
        sheet.merge_range('A{}:A{}'.format(x, y), u'FECHA', align_center_wrap_format)
        sheet.merge_range('B{}:B{}'.format(x, y), u'COMPROBANTE', align_center_wrap_format)
        sheet.merge_range('C{}:C{}'.format(x, y), u'CLIENTE', align_center_wrap_format)
        sheet.merge_range('D{}:D{}'.format(x, y), u'VENDEDOR', align_center_wrap_format)
        sheet.merge_range('E{}:E{}'.format(x, y), u'PISO', align_center_wrap_format)
        sheet.merge_range('F{}:F{}'.format(x, y), u'MESA', align_center_wrap_format)
        sheet.merge_range('G{}:G{}'.format(x, y), u'MONTO', align_center_wrap_format)

        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 40)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 5)
        sheet.set_column('F:F', 5)
        sheet.set_column('G:G', 10)

        orders = obj.get_orders()
        if not orders:
            return
        row = 5
        amount_total = 0
        for order in orders:
            sheet.write(row + 1, 0, order.get('date_invoice'), align_center_wrap_format2)
            sheet.write(row + 1, 1, order.get('invoice_number'), align_center_wrap_format2)
            sheet.write(row + 1, 2, order.get('partner_name'), align_center_wrap_format3)
            sheet.write(row + 1, 3, order.get('user_name'), align_center_wrap_format3)
            sheet.write(row + 1, 4, order.get('floor_name') or '', format_qty)
            sheet.write(row + 1, 5, order.get('table_name') or '', format_qty)
            sheet.write(row + 1, 6, '%.2f' % order.get('amount_total'), format_qty)
            row += 1
            amount_total += order.get('amount_total')
        sheet.write(row + 1, 6, '%.2f' % amount_total, format_qty)


class ReportL10nPosLine(models.TransientModel):
    _name = 'report.l10n_pe.pos.line'

    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Comprobante')
    invoice_number = fields.Char(related='invoice_id.number', string='Comprobante')
    date_invoice = fields.Date(string='Fecha', related='invoice_id.date_invoice')
    user_id = fields.Many2one(related='invoice_id.user_id', string='Vendedor')
    partner_id = fields.Many2one(related='invoice_id.partner_id', string='Cliente')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    amount_total = fields.Monetary(related='invoice_id.amount_total')
    floor_id = fields.Many2one(related='table_id.floor_id', string='Piso')
    table_id = fields.Many2one(comodel_name='restaurant.table', string='Mesa')
    l10n_pe_pos_id = fields.Many2one(comodel_name='report.l10n_pe.pos', string='Reporte')
