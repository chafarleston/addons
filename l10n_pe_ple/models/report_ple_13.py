from odoo import api, fields, models
from odoo.tools.float_utils import float_round

import base64


class ReportPle13(models.Model):
    _name = 'report.ple.13'
    _inherit = ['report.ple']
    _description = 'Registro de inventario permanente valorizado'

    @api.model
    def create(self, vals):
        res = super(ReportPle13, self).create(vals)
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
        vals = self._get_data()
        data = self._get_content(vals)
        filename = template.format(
            prefix, company_vat, year, month, '130100', self.indicator_operation, self.indicator_content, currency, 1)
        value = {'filename_txt': filename, 'file_txt': base64.encodebytes(data.encode('utf-8'))}
        self.action_generate_ple(value)

    def _get_initial_balance(self, product_id, date_start, location_id=None):
        domain = [
            '|',
            ('move_id.inventory_id', '!=', False),
            ('move_id.picking_id', '!=', False),
            ('state', '=', 'done'),
            ('date', '<', date_start),
            ('product_id', '=', product_id.id),
            ('move_id.company_id', '=', self.company_id.id)
        ]
        if location_id:
            domain += ['|', ('location_id', '=', location_id.id), ('location_dest_id', '=', location_id.id)]
        lines = self.env['stock.move.line'].search(domain, order='id')
        r_qty = r_price_out = 0
        for line in lines:
            usage = line.location_id.usage
            dest_usage = line.location_dest_id.usage
            condition1 = usage in ['supplier', 'inventory'] and dest_usage in ['internal']
            condition2 = usage in ['internal'] and dest_usage in ['customer', 'inventory']
            condition3 = usage in ['internal'] and dest_usage in ['internal']
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
        return r_qty, r_price_out

    def _get_data(self, product_id=None, location_id=None, date_start=None, date_end=None, extra_domain=None):
        date_start = date_start or self.range_id.date_start
        date_end = date_end or self.range_id.date_end
        domain = [
            '|',
            ('move_id.inventory_id', '!=', False),
            ('move_id.picking_id', '!=', False),
            ('state', '=', 'done'),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ]
        data = list()
        if location_id:
            domain += ['|', ('location_id', '=', location_id.id), ('location_dest_id', '=', location_id.id)]
        if product_id:
            domain.append(('product_id', '=', product_id.id))
        if extra_domain:
            domain += extra_domain

        lines = self.env['stock.move.line'].search(domain, order='id')
        for product in lines.mapped('product_id'):
            r_qty, r_price_init = self._get_initial_balance(product, date_start, location_id)
            for line in lines.filtered(lambda record: record.product_id == product):
                usage = line.location_id.usage
                dest_usage = line.location_dest_id.usage
                condition1 = usage in ['supplier', 'inventory'] and dest_usage in ['internal']
                condition2 = usage in ['internal'] and dest_usage in ['customer', 'inventory']
                condition3 = usage in ['internal'] and dest_usage in ['internal']
                values = dict(
                    period=u'{}00'.format(self.get_year_month(line.date)),
                    cuo=(line.reference or '').replace('/', '').replace('-', ''),
                    move_name=u'{}{}'.format(line.move_id.id, line.id),
                    store_code='99999',
                    catalog_code=self.env.user.company_id.l10n_pe_catalog_id.code or '',
                    existence_code=line.product_id.categ_id.l10n_pe_existence_type or '',
                    product_code=line.product_id.default_code or '',
                    osce_code=line.product_id.l10n_pe_osce_id.code or '',
                    date_emission=fields.Date().from_string(line.date).strftime('%d/%m/%Y') or '',
                    document_type='',
                    document_series='',
                    document_correlative='',
                    operation_type=line.picking_id.l10n_pe_operation_type or '',
                    product_name=line.product_id.name or '',
                    unit_measurement_code=line.product_id.uom_id.l10n_pe_sunat_code_id.code or '',
                    valuation_method=line.product_id.categ_id.l10n_pe_valuation_method or '',
                    operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                )
                if condition1 or condition2:
                    if condition1:
                        qty_in = line.qty_done
                        qty_out = 0
                    else:
                        qty_out = line.qty_done
                        qty_in = 0
                    r_qty += qty_in - qty_out
                    r_price = line.product_id.standard_price * r_qty
                    values.update(dict(
                        qty_in=qty_in,
                        price_in=qty_in and line.product_id.standard_price,
                        total_price_in=line.product_id.standard_price * qty_in,
                        qty_out=qty_out,
                        price_out=qty_out and line.product_id.standard_price,
                        total_price_out=line.product_id.standard_price * qty_out,
                        final_total_qty=r_qty,
                        final_unit_price=line.product_id.standard_price,
                        final_total_price=r_price,
                        operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                    ))
                    data.append(values)
                elif condition3:
                    if location_id:
                        if line.location_dest_id == location_id:
                            qty_in = line.qty_done
                            qty_out = 0
                            r_qty += qty_in - qty_out
                            r_price = line.product_id.standard_price * r_qty
                            values.update(dict(
                                qty_in=qty_in,
                                price_in=qty_in and line.product_id.standard_price,
                                total_price_in=line.product_id.standard_price * qty_in,
                                qty_out=qty_out,
                                price_out=qty_out and line.product_id.standard_price,
                                total_price_out=line.product_id.standard_price * qty_out,
                                final_total_qty=r_qty,
                                final_unit_price=line.product_id.standard_price,
                                final_total_price=r_price,
                                operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                            ))
                            data.append(values)
                        if line.location_id == location_id:
                            qty_out = line.qty_done
                            qty_in = 0
                            r_qty += qty_in - qty_out
                            r_price = line.product_id.standard_price * r_qty
                            values = values.copy()
                            values.update(dict(
                                qty_in=qty_in,
                                price_in=qty_in and line.product_id.standard_price,
                                total_price_in=line.product_id.standard_price * qty_in,
                                qty_out=qty_out,
                                price_out=qty_out and line.product_id.standard_price,
                                total_price_out=line.product_id.standard_price * qty_out,
                                final_total_qty=r_qty,
                                final_unit_price=line.product_id.standard_price,
                                final_total_price=r_price,
                                operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                            ))
                            data.append(values)
                    else:
                        qty_in = line.qty_done
                        qty_out = 0
                        r_qty += qty_in - qty_out
                        r_price = line.product_id.standard_price * r_qty
                        values.update(dict(
                            qty_in=qty_in,
                            price_in=qty_in and line.product_id.standard_price,
                            total_price_in=line.product_id.standard_price * qty_in,
                            qty_out=0,
                            price_out=0,
                            total_price_out=0,
                            final_total_qty=r_qty,
                            final_unit_price=line.product_id.standard_price,
                            final_total_price=r_price,
                            operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                            ))
                        data.append(values)
                        qty_out = line.qty_done
                        qty_in = 0
                        r_qty += qty_in - qty_out
                        r_price = line.product_id.standard_price * r_qty
                        values = values.copy()
                        values.update(dict(
                            qty_in=0,
                            price_in=0,
                            total_price_in=0,
                            qty_out=qty_out,
                            price_out=qty_out and line.product_id.standard_price,
                            total_price_out=line.product_id.standard_price * qty_out,
                            final_total_qty=r_qty,
                            final_unit_price=line.product_id.standard_price,
                            final_total_price=r_price,
                            operation_state='',  # line.move_id.l10n_pe_operation_state_sunat
                            ))
                        data.append(values)
        return data

    @staticmethod
    def _get_content(lines):
        template = '{period}|{cuo}|{move_name}|{store_code}|{catalog_code}|{existence_code}|{product_code}|' \
                   '{osce_code}|{date_emission}|{document_type}|{document_series}|{document_correlative}|' \
                   '{operation_type}|{product_name}|{unit_measurement_code}|{valuation_method}|{qty_in}|{price_in}|' \
                   '{total_price_in}|{qty_out}|{price_out}|{total_price_out}|{final_total_qty}|{final_unit_price}|' \
                   '{final_total_price}|{operation_state}|\r\n'
        data = ''
        for line in lines:
            data += template.format(
                period=line.get('period', ''),
                cuo=line.get('cuo', ''),
                move_name=line.get('move_name', ''),
                store_code=line.get('store_code', ''),
                catalog_code=line.get('catalog_code', ''),
                existence_code=line.get('existence_code', ''),
                product_code=line.get('product_code', ''),
                osce_code=line.get('osce_code', ''),
                date_emission=line.get('date_emission', ''),
                document_type=line.get('document_type', ''),
                document_series=line.get('document_series', ''),
                document_correlative=line.get('document_correlative', ''),
                operation_type=line.get('operation_type', ''),
                product_name=line.get('product_name', ''),
                unit_measurement_code=line.get('unit_measurement_code', ''),
                valuation_method=line.get('valuation_method', ''),
                qty_in=line.get('qty_in', ''),
                price_in=line.get('price_in', ''),
                total_price_in=line.get('total_price_in', ''),
                qty_out=line.get('qty_out', ''),
                price_out=line.get('price_out', ''),
                total_price_out=line.get('total_price_out', ''),
                final_total_qty=line.get('final_total_qty', ''),
                final_unit_price=line.get('final_unit_price', ''),
                final_total_price=line.get('final_total_price', ''),
                operation_state=line.get('operation_state', '')
            )
        return data

