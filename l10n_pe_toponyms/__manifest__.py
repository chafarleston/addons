# -*- coding: utf-8 -*-
{
    'name': "Toponyms",
    'summary': "Localización geográfica de Perú",
    'version': '1.0',
    'author': "",
    'website': "",
    'category': 'Localization/Toponyms',
    'license': 'AGPL-3',
    'depends': [
        'base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pe_country_data.xml',
        'data/res_country_data.xml',
        'views/res_country.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
    ],
    'installable': True,
}
