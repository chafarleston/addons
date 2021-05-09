
from odoo import api, fields, models
from .utils import send_request
import requests


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_facturalo_pro(self, document_type, document_number):
        document_type = 'dni' if document_type == '1' else 'ruc' if document_type == '6' else ''
        register_url = u'services/{}/{}'.format(document_type, document_number)
        response = send_request(self, register_url)
        if not response.get('success'):
            return {}
        data = response.get('data', {})
        ubigeo = u'{}{}'.format('PE', data.get('district_id'))
        district = self.env['l10n_pe.res.country.district'].search([('code', '=', ubigeo)], limit=1)
        res = {
            'name': data.get('name'),
            'l10n_pe_legal_name': data.get('name'),
            'l10n_pe_tradename': data.get('trade_name'),
            'street': data.get('address'),
            'l10n_pe_district_id': district and district.id or False,
            'l10n_pe_province_id': district and district.province_id and district.province_id.id or False,
            'state_id': district and district.province_id.state_id and district.province_id.state_id.id or False,
            'zip': data.get('district_id', ''),
            'is_company': True,
            'company_type': 'company',
            'image': self._get_default_image('company', 1, False)
        }
        if document_type == 'dni':
            res.update({
                'company_type': 'person',
                'image': self._get_default_image('person', 0, False)
            })
        return res

    @api.model
    def get_apiperu_data(self, document_type, document_number):
        if not document_type:
            return {}

        param = self.env['ir.config_parameter'].sudo().get_param
        url = param('host_apiperu_url', False)
        token = param('host_apiperu_token', False)
        document_type = 'dni' if document_type == '1' else 'ruc' if document_type == '6' else ''

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(token),
        }
        register_url = u'{}{}/{}'.format(url, document_type, document_number)

        response = requests.get(register_url, headers=headers)
        if response.status_code != 200:
            return {}
        response = response.json()
        if not response.get('success'):
            return {}
        data = response.get('data', {})
        if document_type == 'dni':
            res = {
                'name': data.get('nombre_completo'),
                'company_type': 'person',
                'image': self._get_default_image('person', 0, False)
            }
        else:
            if len(data.get('ubigeo', [])) == 3:
                ubigeo = u'{}{}'.format('PE', data.get('ubigeo', '')[2])
            else:
                ubigeo = u'{}{}'.format('PE', data.get('ubigeo', ''))
            district = self.env['l10n_pe.res.country.district'].search([('code', '=', ubigeo)], limit=1)
            res = {
                'name': data.get('nombre_o_razon_social'),
                'l10n_pe_legal_name': data.get('nombre_o_razon_social'),
                'l10n_pe_tradename': data.get('nombre_o_razon_social'),
                'street': data.get('direccion_completa'),
                'l10n_pe_district_id': district and district.id or False,
                'l10n_pe_province_id': district and district.province_id and district.province_id.id or False,
                'state_id': district and district.province_id.state_id and district.province_id.state_id.id or False,
                'zip': data.get('ubigeo', ''),
                'is_company': True,
                'company_type': 'company',
                'image': self._get_default_image('company', 1, False)
            }
        return res

    def get_pydevs_data(self, document_type, document_number):
        param = self.env['ir.config_parameter'].sudo().get_param
        url = param('host_pydevs_url', False)
        username = param('host_pydevs_username', False)
        password = param('host_pydevs_password', False)
        document_type = 'dni' if document_type == '1' else 'ruc' if document_type == '6' else ''

        url = '%s%s/%s' % (url, document_type, document_number)
        res = {}
        try:
            response = requests.post(url, auth=(username, password))
        except requests.exceptions.ConnectionError as e:
            return res

        if response.status_code == 200:
            d = response.json()
            if document_type == 'ruc':
                ubigeo = u'{}{}'.format('PE', d.get('ubigeo', ''))
                district = self.env['l10n_pe.res.country.district'].search([('code', '=', ubigeo)], limit=1)
                res = {
                    'name': d['nombre_comercial'] != '-' and d['nombre_comercial'] or d['nombre'],
                    'l10n_pe_legal_name': d['nombre'],
                    'l10n_pe_tradename': d['nombre'],
                    'street': d['domicilio_fiscal'],
                    'l10n_pe_district_id': district and district.id or False,
                    'l10n_pe_province_id': district and district.province_id and district.province_id.id or False,
                    'state_id': district and district.province_id.state_id and district.province_id.state_id.id or False,
                    'zip': d['ubigeo'],
                    'company_type': 'company',
                    'image': self._get_default_image('company', 1, False)
                }
            else:
                res = {
                    'name': '{} {} {}'.format(d['nombres'], d['ape_paterno'], d['ape_materno']),
                    'company_type': 'person',
                    'image': self._get_default_image('person', 0, False)
                }

        return res

    @api.model
    def l10n_pe_get_data(self, document_type, document_number):
        res = super(ResPartner, self).l10n_pe_get_data(document_type, document_number)
        pydevs = self.get_pydevs_data(document_type, document_number)
        res.update(pydevs)
        if not pydevs.get('name', False):
            apiperu = self.get_apiperu_data(document_type, document_number)
            res.update(apiperu)
            if not apiperu.get('name', False):
                facturalo_pro = self.get_facturalo_pro(document_type, document_number)
                res.update(facturalo_pro)
        return res


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_pe_facturalo_url = fields.Char(string='URL')
    l10n_pe_facturalo_token = fields.Char(string='Token')
