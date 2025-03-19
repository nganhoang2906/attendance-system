# -*- coding: utf-8 -*-
{
    'name': "cham_cong_demo",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'nhan_su'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dot_dang_ky_ca_lam.xml',
        'views/ca_lam.xml',
        'views/lich_nghi_le.xml',
        'views/ngay_phep.xml',
        'views/dang_ky_ca_lam.xml',
        'views/don_xin_nghi.xml',
        'views/don_xin_di_muon_ve_som.xml',
        'views/don_dang_ky_lam_them_gio.xml',
        'views/cham_cong_chi_tiet.xml',
        'views/tong_hop_cham_cong.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

}
