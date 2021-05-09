# -*- coding: utf-8 -*-
{
    'name': "Facturaloperu - Base",
    'summary': "Funciones generales de facturación electrónica",
    'version': '1.0',
    'author': "FacturaloPeru",
    'website': "",
    'category': 'Uncategorized',
    'license': 'AGPL-3',
    'depends': [
        'mail',
        'l10n_pe_sunat_data',
        'l10n_pe_toponyms',
        'l10n_pe_vat'
    ],
    'data': [
        'views/res.xml',
        'data/config_params.xml',
        'data/cron.xml'
    ],
    "installable": True,
}
