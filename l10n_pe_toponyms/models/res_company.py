# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'
    
    l10n_pe_province_id = fields.Many2one(comodel_name='l10n_pe.res.country.province', compute='_compute_address', inverse='_inverse_province',
                                          string="Provincia")
    l10n_pe_district_id = fields.Many2one(comodel_name='l10n_pe.res.country.district', compute='_compute_address', inverse='_inverse_district',
                                          string="Distrito")
    
    def _inverse_province(self):
        for company in self:
            company.partner_id.l10n_pe_province_id = company.l10n_pe_province_id
    
    def _inverse_district(self):
        for company in self:
            company.partner_id.l10n_pe_district_id = company.l10n_pe_district_id
    
    def _compute_address(self):
        super(Company, self)._compute_address()
        for company in self.filtered(lambda w: w.partner_id):
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact'])
                company.l10n_pe_province_id = partner.l10n_pe_province_id
                company.l10n_pe_district_id = partner.l10n_pe_district_id
    
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
                self.state_id = self.l10n_pe_province_id.state_id.id
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
