from odoo import api, fields, models
from odoo.addons.l10n_pe_sunat_data.models.constants import CODE_TABLE_13, CODE_TABLE_17


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_pe_plan_account_id = fields.Many2one(comodel_name='l10n_pe.datas',
                                              domain=[('table_code', '=', CODE_TABLE_17)],
                                              string='Plan de cuentas contables')
    l10n_pe_catalog_id = fields.Many2one(comodel_name='l10n_pe.datas',
                                         domain=[('table_code', '=', CODE_TABLE_13)],
                                         string='Código de catálogo')

    @api.model
    def default_get(self, fields_list):
        res = super(ResCompany, self).default_get(fields_list)
        domain = [
            ('table_code', '=', CODE_TABLE_17),
            ('code', 'in', ['01'])
        ]
        plan_account = self.env['l10n_pe.datas'].search(domain, limit=1)
        res.update({
            'l10n_pe_plan_account_id': plan_account and plan_account.id or False
        })

        return res
