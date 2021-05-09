# -*- coding: utf-8 -*-
{
    'name': "Localización contable",
    'summary': "Complemento de facturación electrónica para contabilidad",
    'version': '1.0',
    'author': "FacturaloPeru",
    'website': "",
    'category': 'Account',
    'license': 'AGPL-3',
    'depends': [
        'l10n_pe_base',
        'sale',
        'account_cancel',
        'account',
        'web',

    ],
    'data': [
        'wizard/invoice_refund.xml',
        'views/account.xml',
        'views/sale.xml',
        'views/reporte_facturalo.xml',
        'views/reporte_facturalo_views.xml',
        'views/product.xml',
        'data/ir.sequence.csv',
        'data/account.journal.csv',
        'data/account.tax.csv',
        'data/uom.uom.csv',
    ],
    "installable": True,
}
