from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    l10n_pe_existence_type = fields.Selection(selection='_get_l10n_pe_existence_type',
                                                string='Tipo de existencia')
    l10n_pe_valuation_method = fields.Selection(selection='_get_l10n_pe_valuation_method',
                                                string='Método de valuación de existencia')

    @api.model
    def _get_l10n_pe_existence_type(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG13')

    @api.model
    def _get_l10n_pe_valuation_method(self):
        return self.env['l10n_pe.datas'].get_selection('PE.CPE.CATALOG20')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    l10n_pe_osce_id = fields.Many2one(comodel_name='l10n_pe.datas',
                                      domain=[('table_code', '=', 'PE.CPE.CATALOG25')],
                                      string='Código OSCE')