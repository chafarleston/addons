# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class UomUom(models.Model):
    _inherit = 'uom.uom'

    l10n_pe_sunat_code_id = fields.Many2one(comodel_name='l10n_pe.datas', domain=[('table_code', 'in', ['PE.TABLA06'])],
                                            string='Código SUNAT', help=u'Según tabla sunat N° 06')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_product_sunat_code_id = fields.Many2one(comodel_name='l10n_pe.datas', string=u'Código sunat',
                                                    domain=[('table_code', 'in', ['PE.CPE.CATALOG25'])],
                                                    help=u'Según catálogo sunat N° 25')
    l10n_pe_type_operation_sunat = fields.Selection(selection="_get_l10n_pe_reason_code", string="Tipo de afectacion",
                                                    default="10", required=True, help=u'Según catálogo sunat N° 07')

    @api.model
    def _get_l10n_pe_reason_code(self):
        return self.env['l10n_pe.datas'].get_selection("PE.CPE.CATALOG7")
