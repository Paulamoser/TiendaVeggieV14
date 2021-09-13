# -*- coding: utf-8 -*-
{
    'name': "Veggie Odoo",

    'summary': """
        Modificaciones a Tienda Veggie - Odoo""",

    'description': """
        Modificaciones a Tienda Veggie - Odoo
    """,

    'author': "Codize",
    'website': "https://www.codize.ar",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'stock', 'sale'],

    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/table.xml',
        'views/congelados.xml',
        'views/secos.xml',
        'views/refrigerados.xml',
        'views/mixtos.xml',
        'views/invoices.xml',
    ],
    'demo': [],
}