from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestPartnerListEnterTour(TestPointOfSaleHttpCommon):
    """Pressing Enter in the POS partner search must not throw (needs --workers=0)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Partner = cls.env["res.partner"]
        # The POS preloads the first N partners (by order count, then name): the
        # "far" one is sorted last, behind the fillers, so it needs the server.
        cls.env["ir.config_parameter"].set_param("point_of_sale.limited_customer_count", 10)
        Partner.create([{"name": f"AAB Filler {i:02d}"} for i in range(10)])
        cls.unique = Partner.create({"name": "AAA Zxq Unico Cliente"})
        cls.local = cls.unique | Partner.create(
            [{"name": "AAA Zxq Doble Uno"}, {"name": "AAA Zxq Doble Dos"}]
        )
        cls.far = Partner.create({"name": "ZZZ Zxq Lejano"})

    def test_fixture_preload_boundary(self):
        """Guard: the local partners are preloaded, the far one is not."""
        preloaded = {row[0] for row in self.main_pos_config.get_limited_partners_loading()}
        self.assertLessEqual(set(self.local.ids), preloaded)
        self.assertNotIn(self.far.id, preloaded)

    def test_enter_with_local_matches(self):
        self.start_pos_tour("L10nVePartnerListEnterLocalTour")

    def test_enter_searches_the_server(self):
        self.start_pos_tour("L10nVePartnerListEnterServerTour")
