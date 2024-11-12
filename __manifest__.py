# -*- coding: utf-8 -*-
{
    'name': "Yacht Service Management",
    'author': "Kai Brossmann",
    'summary': """Organize and manage of yacht repair. Yacht Repair Request, Yacht Diagnosis, Yacht Repair Work Orders""",
    'website': 'https://www.boatcv.com',
    'version': '16.0.1003',
    'license': 'Other proprietary',
    'category': 'Services',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'mail',
                'sale',
                'hr',
                'website',
                'website_payment'],

# always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/yachtservice_confirmation.xml',
        'reports/report_actions.xml',
        'reports/yacht_repair_request.xml',
        'views/client.xml',
        'views/gen_views.xml',
        'views/website_form.xml',
        'menus/menu.xml',
    ],
    'images': [],
    'application': True,
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 389,
    'currency': 'EUR',
}
