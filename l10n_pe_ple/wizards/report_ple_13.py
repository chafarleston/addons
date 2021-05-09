from odoo import api, fields, models


class ReportPle13Wizard(models.TransientModel):
    _name = 'report.ple.13.wizard'
    _inherit = ['report.report_xlsx.abstract']

    store_code = fields.Char(string='Establecimiento', default='9999', required=True)
    l10n_pe_valuation_method_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.TABLA14'])],
                                                  string=u'Método de valoración', required=True)
    l10n_pe_existence_type_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.TABLA05'])],
                                                  string=u'Tipo de existencia', required=True)
    l10n_pe_sunat_code_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.TABLA06'])], string='Unidad de medida',
                                            required=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Producto')
    location_id = fields.Many2one(comodel_name='stock.location', domain=[('usage', 'in', ['internal'])], string=u'Ubicación')
    ple_13_id = fields.Many2one(comodel_name='report.ple.13', default=lambda self: self.env.context.get('active_id'))

    @api.model
    def default_get(self, fields_list):
        res = super(ReportPle13Wizard, self).default_get(fields_list)
        valuation_method_obj = self.env['l10n_pe.datas'].search([('table_code', 'in', ['PE.TABLA14']), ('code', '=', '1')], limit=1)
        existence_type_obj = self.env['l10n_pe.datas'].search([('table_code', 'in', ['PE.TABLA05']), ('code', '=', '01')], limit=1)
        sunat_code_obj = self.env['l10n_pe.datas'].search([('table_code', 'in', ['PE.TABLA06']), ('code', '=', 'NIU')], limit=1)
        res.update({
            'l10n_pe_valuation_method_id': valuation_method_obj and valuation_method_obj.id or False,
            'l10n_pe_existence_type_id': existence_type_obj and existence_type_obj.id or False,
            'l10n_pe_sunat_code_id': sunat_code_obj and sunat_code_obj.id or False,
        })
        return res

    def generate_xlsx_report(self, workbook, data, obj):
        filename = '234_formato131.xls'
        sheet = workbook.add_worksheet('F 13.1 Det.Inv.Per.Val.')
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
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 15)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 15)

        sheet.set_row(11, 30)
        sheet.set_row(12, 30)

        name = u'FORMATO 13.1: "REGISTRO DE INVENTARIO PERMANENTE VALORIZADO - DETALLE DEL INVENTARIO VALORIZADO"'
        # self._build_template_header(sheet, bold_right, name)

        sheet.merge_range('A1:F1', name, bold_right)
        sheet.merge_range('A3:B3', u'EJERCICIO: {}'.format(obj.ple_13_id.range_id.name), bold_right)
        sheet.merge_range('A4:B4', u'RUC: {}'.format(self.env.user.company_id.partner_id.vat), bold_right)
        sheet.merge_range('A5:F5', u'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: {}'.format(self.env.user.company_id.name), bold_right)

        sheet.merge_range('A7:D7', u'ESTABLECIMIENTO: {}'.format(obj.store_code), bold_right)
        sheet.merge_range('A8:D8', u'CÓDIGO DE LA EXISTENCIA: {}'.format(obj.l10n_pe_existence_type_id.code), bold_right)
        sheet.merge_range('A8:D8', u'DESCRIPCIÓN: {}'.format(obj.l10n_pe_existence_type_id.name), bold_right)
        sheet.merge_range('A9:D9', u'CÓDIGO DE LA UNIDAD DE MEDIDA: {}'.format(obj.l10n_pe_sunat_code_id.code), bold_right)
        sheet.merge_range('A10:D10', u'MÉTODO DE VALUACIÓN: {}'.format(obj.l10n_pe_valuation_method_id.name), bold_right)

        sheet.merge_range('A12:D12', u'DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO, \nDOCUMENTO INTERNO O SIMILAR', bold)
        sheet.write('A13', u'FECHA', bold)
        sheet.write('B13', u'TIPO', bold)
        sheet.write('C13', u'SERIE', bold)
        sheet.write('D13', u'NÚMERO', bold)
        sheet.merge_range('E12:E13', u'TIPO DE \nOPERACIÓN ', bold)
        sheet.merge_range('F12:H12', u'ENTRADAS', bold)
        sheet.write('F13', u'CANTIDAD', bold)
        sheet.write('G13', u'COSTO\nUNITARIO', bold)
        sheet.write('H13', u'COSTO TOTAL', bold)
        sheet.merge_range('I12:K12', u'SALIDAS', bold)
        sheet.write('I13', u'CANTIDAD', bold)
        sheet.write('J13', u'COSTO\nUNITARIO', bold)
        sheet.write('K13', u'COSTO TOTAL', bold)
        sheet.merge_range('L12:N12', u'SALDO FINAL', bold)
        sheet.write('L13', u'CANTIDAD', bold)
        sheet.write('M13', u'COSTO\nUNITARIO', bold)
        sheet.write('N13', u'COSTO TOTAL', bold)

        i = 13
        domain = [
            ('product_id.categ_id.l10n_pe_valuation_method_id', '=', obj.l10n_pe_valuation_method_id.id),
            ('product_id.uom_id.l10n_pe_sunat_code_id', '=', obj.l10n_pe_sunat_code_id.id),
            ('product_id.categ_id.l10n_pe_existence_type_id', '=', obj.l10n_pe_existence_type_id.id)
        ]
        lines = obj.ple_13_id._get_data(product_id=obj.product_id, location_id=obj.location_id, extra_domain=domain)
        for line in lines:
            sheet.write(i, 0, line.get('date_emission') or '', normal)
            sheet.write(i, 1, line.get('document_type') or '', normal)
            sheet.write(i, 2, line.get('document_series'), left)
            sheet.write(i, 3, line.get('document_correlative') or '0.00', right)
            sheet.write(i, 4, line.get('operation_type') or '0.00', right)
            sheet.write(i, 5, line.get('qty_in') or '0.00', right)
            sheet.write(i, 6, line.get('price_in') or '0.00', right)
            sheet.write(i, 7, line.get('total_price_in') or '0.00', right)
            sheet.write(i, 8, line.get('qty_out') or '0.00', right)
            sheet.write(i, 9, line.get('price_out') or '0.00', right)
            sheet.write(i, 10, line.get('total_price_iout') or '0.00', right)
            sheet.write(i, 11, line.get('final_total_qty') or '0.00', right)
            sheet.write(i, 12, line.get('final_unit_price') or '0.00', right)
            sheet.write(i, 13, line.get('final_total_price') or '0.00', right)
            i += 1
