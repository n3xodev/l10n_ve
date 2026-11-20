from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.l10n_ve_edi_tfhka.models.client import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    ICP_BASE_URL,
    ICP_TIMEOUT,
)
from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestL10nVeEdiTfhka(L10nVeSeniatCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_id.write({"vat": "J123456789"})
        cls.partner_a.write({"vat": "J987654321"})
        digital_medium = cls.env.ref("l10n_ve_seniat.emission_medium_digital_billing")
        cls.env.company.write(
            {"l10n_ve_emission_medium_ids": [Command.set([digital_medium.id])]}
        )
        cls.digital_journal = cls.env["account.journal"].create(
            {
                "name": "Ventas Digital TFHKA",
                "code": "VTFH",
                "type": "sale",
                "l10n_ve_emission_medium": "digital",
                "l10n_ve_edi_provider": "tfhka",
            }
        )
        cls.account_user = cls.env["res.users"].create(
            {
                "name": "TFHKA Account User",
                "login": "tfhka_account_user",
                "email": "tfhka_account@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set([cls.env.company.id])],
                "group_ids": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("account.group_account_invoice").id,
                        ]
                    )
                ],
            }
        )
        cls.stock_user = cls.env["res.users"].create(
            {
                "name": "TFHKA Stock User",
                "login": "tfhka_stock_user",
                "email": "tfhka_stock@example.com",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set([cls.env.company.id])],
                "group_ids": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("stock.group_stock_user").id,
                        ]
                    )
                ],
            }
        )

    def test_client_icp_and_settings(self):
        icp = self.env["ir.config_parameter"].sudo()
        client = self.env["l10n_ve_edi_tfhka.api.service"]
        icp.set_str(ICP_BASE_URL, "")
        self.assertEqual(client._base_url(), DEFAULT_BASE_URL)
        icp.set_str(ICP_TIMEOUT, "invalid")
        self.assertEqual(client._timeout(), DEFAULT_TIMEOUT)
        icp.set_str(ICP_TIMEOUT, "45")
        self.assertEqual(client._timeout(), 45)

        settings = self.env["res.config.settings"].create(
            {
                "tfhka_api_environment": "production",
                "tfhka_production_url": "https://prod.example.com/",
            }
        )
        settings.set_values()
        self.assertEqual(icp.get_str(ICP_BASE_URL), "https://prod.example.com")
        self.assertEqual(client._base_url(), "https://prod.example.com")

        settings_test = self.env["res.config.settings"].create(
            {"tfhka_api_environment": "test"}
        )
        settings_test.set_values()
        self.assertEqual(icp.get_str(ICP_BASE_URL), DEFAULT_BASE_URL)

    def test_invoice_payload_payment_reference_and_pdf_attachment(self):
        move = (
            self.env["account.move"]
            .with_user(self.account_user)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_a.id,
                    "journal_id": self.digital_journal.id,
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "display_type": "line_note",
                                "name": "Note excluded from items",
                            }
                        ),
                        Command.create(
                            {
                                "name": "TFHKA Service",
                                "quantity": 2.0,
                                "price_unit": 50.0,
                                "account_id": self.company_data["default_account_revenue"].id,
                                "tax_ids": [Command.set([self.company_data["default_tax_sale"].id])],
                            }
                        ),
                    ],
                }
            )
        )
        move.action_post()
        items = move._tfhka_get_line_items()
        self.assertEqual(len(items), 1)
        payload = move._build_payload_to_send()
        self.assertEqual(len(payload["documentoElectronico"]["detallesItems"]), 1)

        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner_a.id,
                "amount": 100.0,
                "journal_id": self.company_data["default_journal_bank"].id,
                "payment_reference": "REF-TFHKA-001",
            }
        )
        fp_line = move._tfhka_build_formas_pago_line(payment, 100.0)
        self.assertEqual(fp_line["descripcion"], "REF-TFHKA-001")

        action = move._tfhka_return_pdf_attachment_download_action(b"%PDF-1.4\n%%EOF")
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(bytes(move.l10n_ve_edi_tfhka_pdf_attachment_id.raw), b"%PDF-1.4\n%%EOF")

    def test_stock_picking_item_detail_uom_and_description_with_user(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        product = self.env["product.product"].create(
            {"name": "TFHKA Item", "type": "consu", "list_price": 25.0}
        )
        picking = (
            self.env["stock.picking"]
            .with_user(self.stock_user)
            .create(
                {
                    "picking_type_id": warehouse.out_type_id.id,
                    "location_id": warehouse.lot_stock_id.id,
                    "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                    "partner_id": self.partner_a.id,
                    "move_ids": [
                        Command.create(
                            {
                                "product_id": product.id,
                                "product_uom_qty": 3.0,
                                "uom_id": product.uom_id.id,
                                "location_id": warehouse.lot_stock_id.id,
                                "location_dest_id": self.env.ref(
                                    "stock.stock_location_customers"
                                ).id,
                            }
                        )
                    ],
                }
            )
        )
        detail = picking._tfhka_build_item_detail(1, picking.move_ids[0])
        self.assertEqual(detail["unidadMedida"], (product.uom_id.name or "UND")[:3])
        self.assertIn("TFHKA Item", detail["descripcion"])

    def test_portal_dispatch_template_xpath_compiles(self):
        base_view = self.env.ref("sale_stock.sale_order_portal_content_inherit_sale_stock")
        combined = base_view._get_combined_arch()
        delivery_nodes = combined.xpath("//div[@name='delivery_details']")
        self.assertTrue(delivery_nodes)
        self.assertIn(
            "l10n_ve_edi_tfhka_get_public_document_url",
            "".join(delivery_nodes[0].itertext())
            + str(combined.xpath("//div[@name='delivery_details']//@t-if")),
        )
