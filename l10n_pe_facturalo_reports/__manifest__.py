# -*- coding: utf-8 -*-
{
    'name': "Facturalo reportes Perú",
    'summary': "Reprotes personalizados para Facturalo",
    'version': '1.0',
    'author': "Facturalo Peru",
    'website': "",
    'category': 'Account',
    'license': 'AGPL-3',
    'depends': [
        'pos_restaurant',
        'report_xlsx'
    ],
    'data': [
        'wizards/pos_views.xml',
    ],
    'installable': True,
    'application': True,
}
