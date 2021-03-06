# Copyright 2019 Anvar Kildebekov <https://www.it-projects.info/team/fedoranvar>
# Copyright 2019 Ilmir Karamov <https://www.it-projects.info/team/ilmir-k>
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": """Product Sets for POS""",
    "summary": """Add own set of products per each POS""",
    "category": "Point Of Sale",
    "images": ["images/pos_menu_main.jpg"],
    "version": "12.0.1.0.0",
    "application": False,
    "author": "IT-Projects LLC, Dinar Gabbasov",
    "support": "apps@itpp.dev",
    "website": "https://github.com/itpp-labs/pos-addons#readme",
    "license": "Other OSI approved licence",  # MIT
    "depends": ["point_of_sale"],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        "security/ir.model.access.csv",
        "views/product_view.xml",
        "views/pos_config_view.xml",
        "views/pos_menu_view.xml",
        "views/pos_menu_template.xml",
    ],
    "qweb": [],
    "demo": ["demo/product_set_demo.xml"],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
}
