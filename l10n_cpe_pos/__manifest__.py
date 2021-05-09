# -*- coding: utf-8 -*-
{
    'name': 'FacturaloPeru - POS',
    'summary': "Complemento de facturación electrónica para el punto de venta",
    'version': '1.0',
    'author': "FacturaloPeru",
    'website': '',
    'category': 'Point of Sale',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale',
        'l10n_pe_vat',
        'l10n_pe_account'
    ],
    "data": [
        "views/pos_templates.xml",
        "views/pos_config_views.xml"
    ],
    'qweb': [
        'static/src/xml/pos_ticket_view.xml',
        'static/src/xml/pos_client_view.xml',
        'static/src/xml/pos_numpad_view.xml'
    ],
    "installable": True,
}
