# -*- coding: utf-8 -*-

from odoo import fields, models


class CountryProvince(models.Model):
    _description = "Country Province"
    _name = 'l10n_pe.res.country.province'
    _order = 'code'

    state_id = fields.Many2one(comodel_name='res.country.state', string='States', required=True)
    country_id = fields.Many2one(related='state_id.country_id', store=True)
    name = fields.Char(string='Province Name', required=True)
    code = fields.Char(string='Province Code', help='The province code.', required=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(state_id, code)', 'The code of the province must be unique by country !')
    ]


class CountryDistrict(models.Model):
    _description = "Country District"
    _name = 'l10n_pe.res.country.district'
    _order = 'code'

    province_id = fields.Many2one(comodel_name='l10n_pe.res.country.province', string='Province', required=True)
    country_id = fields.Many2one(related='province_id.country_id', store=True)
    name = fields.Char(string='District Name', required=True)
    code = fields.Char(string='Province Code', help='The province code.', required=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(province_id, code)', 'The code of the district must be unique by country !')
    ]
