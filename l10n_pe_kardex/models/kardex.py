# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models


class ReportKardex(models.Model):
    _name = 'report.report_xlsx.kardex'
    _inherit = 'report.report_xlsx.abstract'
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.product', string='Producto', required=False)
    category_id = fields.Many2one(comodel_name='product.category', string=u'Categoría', domain=[('parent_id', '!=', False)])
    location_id = fields.Many2one(comodel_name='stock.location', string='Almacen', required=False, domain=[('usage', 'in', ['internal'])])
    date_start = fields.Date(string='Desde', required=True,
                             default=lambda self: str(fields.Date().from_string(fields.Date().context_today(self)).replace(day=1)))
    date_end = fields.Date(string='Hasta', required=True, default=lambda self: str(fields.Date().context_today(self)))
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Lote')
    company_id = fields.Many2one(comodel_name='res.company', required=True, string=u'Compañía')

    def generate_xlsx_report(self, wb, data, kardex_obj):
        self._report_by_unit(wb, kardex_obj)

    def _report_by_unit(self, wb, kardex_obj):
        sheet = wb.add_worksheet('Kardex')
        align_center_wrap_format = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'size': 10,
                                                  'font_color': 'white', 'bold': True})
        align_center_wrap_format.set_bg_color('#875a7b')
        align_center_wrap_format2 = wb.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'size': 10})
        align_center_wrap_format3 = wb.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1, 'size': 10})
        align_right_wrap_format = wb.add_format({'align': 'right', 'valign': 'vcenter', 'border': 1, 'size': 10, 'bold': True})

        format_content_table = wb.add_format({'size': 10, 'bold': True})
        format_qty = wb.add_format({'size': 10, 'border': 1})
        align_center_wrap_format.set_text_wrap()

        i, j, x, y = 2, 4, 4, 6

        date_start = fields.Date().from_string(kardex_obj.date_start).strftime('%d/%m/%Y')
        date_end = fields.Date().from_string(kardex_obj.date_end).strftime('%d/%m/%Y')

        text_fecha = 'FECHA: (DESDE: ' + str(date_start) + ' - HASTA: ' + str(date_end) + ')'
        name = kardex_obj.location_id.location_id.name or ''

        def get_name(_name):
            if _name and '/' in _name:
                return _name.split('/') and len(_name.split('/')) > 1 and _name.split('/')[1]
            return _name

        name = get_name(name)
        sheet.write('A1:D1', 'EMPRESA: {}'.format(self.env.user.company_id.name), format_content_table)
        sheet.write('A2:D2', 'ALMACEN: '.format(name), format_content_table)
        sheet.write('F1:F1', 'PRODUCTO: '.format(kardex_obj.product_id.name), format_content_table)
        sheet.write('F2:F2', text_fecha, format_content_table)
        sheet.merge_range('A{}:A{}'.format(x, y), u'FECHA', align_center_wrap_format)
        sheet.merge_range('B{}:B{}'.format(x, y), u'Nº DE DOCUMENTO', align_center_wrap_format)
        sheet.merge_range('C{}:C{}'.format(x, y), u'NRO. DE OPERACIÓN', align_center_wrap_format)
        sheet.merge_range('D{}:D{}'.format(x, y), u'NOMBRE', align_center_wrap_format)  # nombre
        sheet.merge_range('E{}:E{}'.format(x, y), u'TIPO DE OPERACIÓN', align_center_wrap_format)
        sheet.merge_range('F{}:F{}'.format(x, y), u'CÓDIGO DE BARRAS', align_center_wrap_format)
        sheet.merge_range('G{}:G{}'.format(x, y), u'LOTE', align_center_wrap_format)
        sheet.merge_range('H{}:H{}'.format(x, y), u'FECHA DE VENCIMIENTO', align_center_wrap_format)
        sheet.merge_range('I{}:I{}'.format(x, y), u'INGRESO', align_center_wrap_format)
        sheet.merge_range('J{}:J{}'.format(x, y), u'SALIDA', align_center_wrap_format)
        sheet.merge_range('K{}:K{}'.format(x, y), u'SALDO', align_center_wrap_format)
        sheet.merge_range('L{}:L{}'.format(x, y), u'DOC. DE ORIGEN', align_center_wrap_format)

        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 30)

        sheet.set_column('D:D', 65)
        sheet.set_column('E:E', 50)
        sheet.set_column('F:F', 15)

        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 10)
        sheet.set_column('J:J', 10)
        sheet.set_column('K:K', 10)
        sheet.set_column('L:L', 30)

        datas = self._get_data(kardex_obj.product_id, kardex_obj.location_id, date_start, date_end, kardex_obj.lot_id, kardex_obj.category_id)

        if not datas:
            return
        sheet.merge_range('A7:L7', 'Cantidadidad de Producto al %s: %s' % (datas[0].get('date_operation'), int(datas[0].get('r_qty'))), align_right_wrap_format)
        row = 6
        for data in datas:
            invoice_number = ''
            if type(data.get('invoice_number', '')) is list:
                for inv_n in data.get('invoice_number', ''):
                    invoice_number += inv_n[1]+'\n'
            else:
                invoice_number = data.get('invoice_number', '')

            sheet.write(row + 1, 0, data.get('date_operation', ''), align_center_wrap_format2)
            sheet.write(row + 1, 1, invoice_number, align_center_wrap_format3)
            sheet.write(row + 1, 2, data.get('obj_number', ''), align_center_wrap_format3)
            sheet.write(row + 1, 3, data.get('partner', ''), align_center_wrap_format3)
            sheet.write(row + 1, 4, data.get('op', ''), format_qty)
            sheet.write(row + 1, 5, data.get('barcode', ''), format_qty)
            sheet.write(row + 1, 6, data.get('lot_name', ''), align_center_wrap_format3)
            sheet.write(row + 1, 7, data.get('life_date', ''), align_center_wrap_format2)
            sheet.write(row + 1, 8, data.get('qty_in', ''), format_qty)
            sheet.write(row + 1, 9, data.get('qty_out', ''), format_qty)
            sheet.write(row + 1, 10, data.get('total_qty', ''), format_qty)
            sheet.write(row + 1, 11, data.get('doc_origin', ''), format_qty)
            row += 1

    def _get_initial_balance(self, product_id, date_start, location_id=False, company_id=False):
        domain = ['|', ('move_id.inventory_id', '!=', False), ('move_id.picking_id', '!=', False), ('state', '=', 'done'),
                  ('date', '<', date_start), ('product_id', '=', product_id.id)]
        if location_id:
            domain += ['|', ('location_id', '=', location_id.id), ('location_dest_id', '=', location_id.id)]
        if company_id:
            domain.append(('move_id.company_id', '=', company_id))
        lines = self.env['stock.move.line'].search(domain, order='id')
        r_qty = 0
        for line in lines:
            condition1 = line.location_id.usage in ['customer', 'supplier', 'inventory'] and line.location_dest_id.usage in ['internal']
            condition2 = line.location_id.usage in ['internal'] and line.location_dest_id.usage in ['customer', 'inventory']
            condition3 = line.location_id.usage in ['internal'] and line.location_dest_id.usage in ['internal']
            if condition1 or condition2:
                if condition1:
                    qty_in = line.qty_done
                    qty_out = 0
                else:
                    qty_out = line.qty_done
                    qty_in = 0
                r_qty += qty_in - qty_out
            elif condition3:
                if location_id:
                    if line.location_dest_id == location_id:
                        qty_in = line.qty_done
                        qty_out = 0
                        r_qty += qty_in - qty_out
                    if line.location_id == location_id:
                        qty_out = line.qty_done
                        qty_in = 0
                        r_qty += qty_in - qty_out
                else:
                    qty_in = line.qty_done
                    qty_out = 0
                    r_qty += qty_in - qty_out
                    qty_out = line.qty_done
                    qty_in = 0
                    r_qty += qty_in - qty_out
        return r_qty

    def _get_data(self, product_id=None, location_id=None, date_start=None, date_end=None, lot_id=None, category_id=False,
                  company_id=False):
        def check_date(date, flag):
            if date and isinstance(date, str) and '/' in date:
                if len(date) == 10:
                    if flag:
                        d = datetime.strptime(date, '%d/%m/%Y')
                        res = datetime(year=d.year, month=d.month, day=d.day) + timedelta(hours=29)
                        return res.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        return datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')
                else:
                    return datetime.strptime(date, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            return date

        date_start = check_date(date_start, 0)
        date_end = check_date(date_end, 1)

        domain = ['|', ('move_id.inventory_id', '!=', False), ('move_id.picking_id', '!=', False), ('state', '=', 'done'),
                  ('date', '>=', date_start), ('date', '<=', date_end)]
        data = list()
        if location_id:
            domain += ['|', ('location_id', '=', location_id.id), ('location_dest_id', '=', location_id.id)]
        if product_id:
            domain.append(('product_id', '=', product_id.id))
        if lot_id:
            domain.append(('lot_id', '=', lot_id.id))
        if category_id:
            domain.append(('product_id.categ_id', '=', category_id.id))
        if company_id:
            domain.append(('move_id.company_id', '=', company_id))
        ctx = self.env.context.copy()
        ctx.update({'lang': 'es_PE', 'tz': 'America/Lima', 'uid': 1, 'commit_assetsbundle': True, 'debug': False})
        lines = self.with_context(ctx).env['stock.move.line'].search(domain, order='id')
        for product in lines.mapped('product_id'):
            r_qty = self._get_initial_balance(product, date_start, location_id, company_id)
            for line in lines.filtered(lambda record: record.product_id == product):
                condition1 = line.location_id.usage in ['customer', 'supplier', 'inventory'] and line.location_dest_id.usage in ['internal']
                condition2 = line.location_id.usage in ['internal'] and line.location_dest_id.usage in ['customer', 'inventory']
                condition3 = line.location_id.usage in ['internal'] and line.location_dest_id.usage in ['internal']
                invoice_id = False
                if not(line.location_id.usage in ['inventory'] or line.location_dest_id.usage in ['inventory']):
                    invoice_id = self.env['pos.order'].search([('picking_id', '=', line.move_id.picking_id.id)], limit=1).invoice_id or \
                             line.move_id.invoice_line_id.invoice_id
                line_date = fields.Datetime().from_string(line.date) - timedelta(hours=5)
                values = {
                    'date_operation':  line_date.strftime('%d-%m-%Y'),
                    'invoice_number': invoice_id and invoice_id.number or '',
                    'invoice_id': invoice_id and invoice_id.id or 0,
                    'invoice_type': invoice_id and invoice_id.type or 0,
                    'obj_number': line.move_id.picking_id.name or line.move_id.inventory_id.name or '',
                    'obj_id': line.picking_id.id,
                    'partner': invoice_id and invoice_id.partner_id.name or line.move_id.picking_id.partner_id.name or '',
                    'partner_id': invoice_id and invoice_id.partner_id.id or line.move_id.picking_id.partner_id.id or 0,
                    'r_qty': r_qty,
                    'list_price': line.product_id.list_price,
                    'op': line.location_id.display_name + ' -> ' + line.location_dest_id.display_name,
                    'barcode': line.product_id.barcode or line.product_id.default_code or '',
                    'product_id': line.product_id.id,
                    'lot_name': line.lot_id.name or '',
                    'lot_id': line.lot_id.id,
                    'life_date': line.lot_id.life_date or '',
                    'doc_origin': line.move_id.picking_id.origin or ''
                }
                if condition1 or condition2:
                    if condition1:
                        qty_in = line.qty_done
                        qty_out = 0
                    else:
                        qty_out = line.qty_done
                        qty_in = 0
                    r_qty += qty_in - qty_out
                    values.update(dict(
                        qty_in=qty_in,
                        qty_out=qty_out,
                        total_qty=r_qty,
                    ))
                    data.append(values)
                elif condition3:
                    if location_id:
                        if line.location_dest_id == location_id:
                            qty_in = line.qty_done
                            qty_out = 0
                            r_qty += qty_in - qty_out
                            values.update(dict(
                                qty_in=qty_in,
                                qty_out=qty_out,
                                total_qty=r_qty,
                            ))
                            data.append(values)
                        if line.location_id == location_id:
                            qty_out = line.qty_done
                            qty_in = 0
                            r_qty += qty_in - qty_out
                            values = values.copy()
                            values.update(dict(
                                qty_in=qty_in,
                                qty_out=qty_out,
                                total_qty=r_qty,
                            ))
                            data.append(values)
                    else:
                        qty_in = line.qty_done
                        qty_out = 0
                        r_qty += qty_in - qty_out
                        values.update(dict(
                            qty_in=qty_in,
                            qty_out=0,
                            total_qty=r_qty,
                            ))
                        data.append(values)
                        qty_out = line.qty_done
                        qty_in = 0
                        r_qty += qty_in - qty_out
                        values = values.copy()
                        values.update(dict(
                            qty_in=0,
                            qty_out=qty_out,
                            total_qty=r_qty,
                            ))
                        data.append(values)
        return data

    @api.model
    def get_products(self, product_id=False, location_id=False, date_start=False, date_end=False, lot_id=False, category_id=False, company_id=False):
        if product_id:
            product_id = self.env['product.product'].browse(product_id)
        if location_id:
            location_id = self.env['stock.location'].browse(location_id)
        if category_id:
            category_id = self.env['product.category'].browse(category_id)
        return self.sudo()._get_data(product_id, location_id, date_start, date_end, lot_id, category_id, company_id) if date_end and date_start else []

    @api.model
    def action_view(self, number, model, res_id, invoice_type):
        context = dict(self.env.context, active_ids=self.ids)
        data = {
            'type': 'ir.actions.act_window',
            'name': 'Comprobante',
            'res_model': model,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
            'flags': {'mode': 'readonly'}
        }
        if model in ['account.invoice']:
            if 'I' == number[0]:
                data.update(self.action_view_model(number, 'stock.inventory', 'stock.view_inventory_form', 'name'))
            elif 'B' in number or 'F' in number:
                invoice_form = 'invoice_form' if invoice_type in ('out_invoice', 'out_refund') else 'invoice_supplier_form'
                if res_id:
                    data.update(self.action_view_model(number, model, 'account.%s' % invoice_form, 'number', res_id))
                else:
                    data.update(self.action_view_model(number, model, 'account.%s' % invoice_form, 'number'))
            else:
                if res_id:
                    data.update(self.action_view_model(number, 'stock.picking', 'stock.view_picking_form', 'name', res_id))
                else:
                    data.update(self.action_view_model(number, 'stock.picking', 'stock.view_picking_form', 'name'))
        elif model in ['stock.picking']:
            if 'I' == number[0]:
                data.update(self.action_view_model(number, 'stock.inventory', 'stock.view_inventory_form', 'name'))
            else:
                data.update(self.action_view_model(number, model, 'stock.view_picking_form', 'name', res_id))
        elif model in ['res.partner']:
            if 'I' == number[0]:
                data.update(self.action_view_model(number, 'stock.inventory', 'stock.view_inventory_form', 'name', res_id))
            else:
                if res_id:
                    data.update(self.action_view_model(number, model, 'base.view_partner_form', 'name', res_id))
                else:
                    data.update(self.action_view_model(number, model, 'base.view_partner_form', 'name'))
        elif model in ['product.template']:
            if res_id:
                data.update(self.action_view_model(number, model, 'product.product_template_only_form_view', 'default_code', res_id))
            else:
                data.update(self.action_view_model(number, model, 'product.product_template_only_form_view', 'default_code'))
        elif model in ['stock.production.lot']:
            if res_id:
                data.update(self.action_view_model(number, model, 'stock.view_production_lot_form', 'name', res_id))
            else:
                data.update(self.action_view_model(number, model, 'stock.view_production_lot_form', 'name'))
        return data

    @api.model
    def action_view_model(self, number, model, form_name, op, res_id=False):
        form = self.env.ref(form_name, False)
        obj = self.env[model].browse(res_id) if res_id else self.env[model].search([(op, '=', number)], limit=1)
        print(form, obj)
        if form and obj:
            return {
                'views': [(form.id, 'form')],
                'view_id': form.id,
                'res_id': obj and obj.id or False,
            }
