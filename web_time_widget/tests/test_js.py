import odoo.tests


class TestJS(odoo.tests.HttpCase):

    post_install = True
    at_install = False

    def test_01_js(self):
        self.phantom_js(
            '/web/tests?module=web_time_widget',
            "", "", login='admin', timeout=1800)
