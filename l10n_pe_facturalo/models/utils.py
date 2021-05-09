import base64
import json
import requests
import urllib3

from requests.exceptions import ConnectionError, HTTPError, Timeout
from odoo.exceptions import ValidationError, Warning


def send_request(self, service, data=None):
    param = self.env['ir.config_parameter'].sudo().get_param
    url = self.env.user.company_id.l10n_pe_facturalo_url or param('host_api_cpe_url', False)
    token = self.env.user.company_id.l10n_pe_facturalo_token or param('host_api_cpe_token', False)
    if not token:
        raise ValidationError('Configure token para el envio del documento')

    url = '{}{}'.format(url, service)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    try:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        if data is not None:
            r = requests.post(url, data=json.dumps(data), headers=headers, timeout=30, verify=False)
        else:
            r = requests.get(url, headers=headers, timeout=30, verify=False)
        response = r.json()
    except (ConnectionError, HTTPError) as e:
        raise Warning('Error Http {}'.format(e))
    except (ConnectionError, Timeout) as e:
        raise Warning(
            'El tiempo de envío se ha agotado, el servidor de la Sunat puede encontrarse no disponible temporalemente')

    if not response['success']:
        raise Warning(response['message'])
    return response


def get_response(self, service, number,  data):
    param = self.env['ir.config_parameter'].sudo().get_param
    token = self.env.user.company_id.l10n_pe_facturalo_token or param('host_api_cpe_token', False)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }
    html_json = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
    # number = self.journal_id.sequence_id.get_next_char(self.journal_id.sequence_number_next) or '#'
    values = {}
    values.update({
        'l10n_pe_facturalo_json': base64.encodebytes(html_json.encode('utf-8')),
        'l10n_pe_facturalo_filename_json': '{}.json'.format(number),
        'l10n_pe_facturalo_state': 'Registrado',
        'l10n_pe_number': number
    })
    content = send_request(self, service, data)
    if not content.get('success'):
        return
    data = content.get('data', {})
    links = content.get('links', {})
    response_sunat = content.get('response', {})
    filename = data.get('filename', '')
    external = data.get('external_id', '')
    hash_code = data.get('hash', '')
    state_type_description = data.get('state_type_description', '')
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response_pdf = requests.get(links.get('pdf'), headers=headers, verify=False) if links.get('pdf') else ''
    response_xml = requests.get(links.get('xml'), headers=headers, verify=False) if links.get('xml') else ''
    response_cdr = requests.get(links.get('cdr'), headers=headers, verify=False) if links.get('cdr') else ''

    values.update({'l10n_pe_facturalo_pdf': base64.b64encode(response_pdf.content)}) if response_pdf else None
    values.update({'l10n_pe_facturalo_xml': base64.b64encode(response_xml.content)}) if response_xml else None
    values.update({'l10n_pe_facturalo_cdr': base64.b64encode(response_cdr.content)}) if response_cdr else None
    values.update({'l10n_pe_facturalo_msg': response_sunat.get('description')}) if response_sunat else None
    values.update({
        'l10n_pe_facturalo_filename_pdf': '{}.pdf'.format(filename),
        'l10n_pe_facturalo_filename_xml': '{}.xml'.format(filename),
        'l10n_pe_facturalo_filename_cdr': '{}.zip'.format(filename),
        'l10n_pe_facturalo_external': external,
        'l10n_pe_facturalo_hash': hash_code,
        'l10n_pe_facturalo_state': state_type_description
    })
    return values
