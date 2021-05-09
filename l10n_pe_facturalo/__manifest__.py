# -*- coding: utf-8 -*-
{
    'name': "FacturaloPeru - Facturación",
    'summary': "Sincronización con la API de Facturador Electrónico",
    'version': '1.0',
    'author': "FacturaloPeru",
    'website': "",
    'category': 'Account',
    'license': 'AGPL-3',
    'depends': [
        'l10n_pe_account',
        'l10n_pe_stock',
        'stock_picking_invoice_link',
        'report_xlsx',
        'base',
        'account',
        'l10n_pe_sunat_data',
    ],
    'data': [
        'views/account.xml',
        'views/stock.xml',
        'data/config_params.xml',
        'views/invoice_report_template.xml',
        'views/res.xml'
    ],
    'installable': True,
    'application': True,
}
