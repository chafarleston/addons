# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    l10n_pe_province_id = fields.Many2one(comodel_name='l10n_pe.res.country.province', string='Province')
    l10n_pe_district_id = fields.Many2one(comodel_name='l10n_pe.res.country.district', string='District')
    zip = fields.Char(compute='_compute_zip', store=True)

    @api.depends('l10n_pe_district_id')
    def _compute_zip(self):
        self.mapped(lambda record: record.update({
            'zip': record.l10n_pe_district_id and record.l10n_pe_district_id.code and record.l10n_pe_district_id.code[2:]
        }))

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            if not self.country_id:
                self.country_id = self.state_id.country_id.id
            return {'domain': {'l10n_pe_province_id': [('state_id', '=', self.state_id.id)]}}
        else:
            return {'domain': {'l10n_pe_province_id': []}}

    @api.onchange('l10n_pe_province_id')
    def _onchange_l10n_pe_province_id(self):
        if self.l10n_pe_province_id:
            if not self.state_id:
                self.state_id = self.province_id.state_id.id
            return {'domain': {'l10n_pe_district_id': [('province_id', '=', self.l10n_pe_province_id.id)]}}
        else:
            return {'domain': {'l10n_pe_district_id': []}}
        
    @api.onchange('l10n_pe_district_id')
    def _onchange_l10n_pe_district_id(self):
        if self.l10n_pe_district_id:
            if not self.l10n_pe_province_id:
                self.l10n_pe_province_id = self.l10n_pe_district_id.province_id.id
        self.zip = self.l10n_pe_district_id.code and len(self.l10n_pe_district_id.code) >= 2 and self.l10n_pe_district_id.code[2:] or False
        self.city = self.l10n_pe_district_id.name
