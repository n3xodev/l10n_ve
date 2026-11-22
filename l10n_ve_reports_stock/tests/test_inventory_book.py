# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInventoryBook(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.retiros_location = cls.env["stock.location"].create(
            {"name": "Retiros", "usage": "internal"}
        )
        cls.autoconsumos_location = cls.env["stock.location"].create(
            {"name": "Autoconsumos", "usage": "internal"}
        )
        cls.warehouse.write(
            {
                "l10n_ve_location_retiros_id": cls.retiros_location.id,
                "l10n_ve_location_autoconsumos_id": cls.autoconsumos_location.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Inventory book product",
                "is_storable": True,
                "standard_price": 10.0,
            }
        )
        cls.report = cls.env.ref("l10n_ve_reports_stock.inventory_book_report")
        cls.handler = cls.env["stock.inventory.book.report.handler.oca"]
        cls.date_from = fields.Date.from_string("2024-02-01")
        cls.date_to = fields.Date.from_string("2024-02-29")

        # Before the period: 10 units received -> opening inventory
        cls._move(cls.supplier_location, cls.stock_location, 10, "2024-01-10")
        # During the period
        cls._move(cls.supplier_location, cls.stock_location, 5, "2024-02-05")
        cls._move(cls.stock_location, cls.customer_location, 3, "2024-02-10")
        cls._move(cls.stock_location, cls.retiros_location, 2, "2024-02-12")
        cls._move(cls.stock_location, cls.autoconsumos_location, 1, "2024-02-15")
        # After the period: must be ignored
        cls._move(cls.supplier_location, cls.stock_location, 7, "2024-03-05")

    @classmethod
    def _move(cls, source, destination, quantity, date):
        move = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": quantity,
                "uom_id": cls.product.uom_id.id,
                "location_id": source.id,
                "location_dest_id": destination.id,
            }
        )
        move._action_confirm()
        move.quantity = quantity
        move.picked = True
        move._action_done()
        move.date = f"{date} 12:00:00"
        return move

    def test_report_and_menus_are_registered(self):
        self.assertEqual(
            self.report.custom_handler_model_name,
            "stock.inventory.book.report.handler.oca",
        )
        action = self.env.ref("l10n_ve_reports_stock.action_inventory_book_report")
        self.assertEqual(action.tag, "account_report_oca")
        for xml_id in (
            "l10n_ve_reports_stock.menu_seniat_report_inventory_book",
            "l10n_ve_reports_stock.menu_stock_report_inventory_book",
        ):
            self.assertTrue(self.env.ref(xml_id, raise_if_not_found=False), xml_id)

    def test_product_data_for_the_period(self):
        data = self.handler._get_product_data(
            self.warehouse,
            self.date_from,
            self.date_to,
            self.company.currency_id,
        )[self.product.id]
        self.assertEqual(data["inv_initial_qty"], 10.0)
        self.assertEqual(data["inv_initial_val"], 100.0)
        self.assertEqual(data["entradas_qty"], 5.0)
        self.assertEqual(data["entradas_val"], 50.0)
        self.assertEqual(data["salidas_qty"], 3.0)
        self.assertEqual(data["retiros_qty"], 2.0)
        self.assertEqual(data["autoconsumos_qty"], 1.0)
        self.assertEqual(data["inv_final_qty"], 9.0)
        self.assertEqual(data["inv_final_val"], 90.0)
        self.assertEqual(data["cost"], 10.0)

    def test_report_lines(self):
        options = self.report.get_options(
            {
                "date": {
                    "mode": "range",
                    "filter": "custom",
                    "date_from": "2024-02-01",
                    "date_to": "2024-02-29",
                },
            }
        )
        self.assertEqual(options["warehouse_ids"], [])
        lines = self.report._get_lines(options)
        product_lines = [
            line for line in lines if line["name"] == self.product.display_name
        ]
        self.assertEqual(len(product_lines), 1, "the stored product must be listed once")
        values = {
            column["expression_label"]: product_lines[0]["columns"][index].get(
                "no_format"
            )
            for index, column in enumerate(options["columns"])
        }
        self.assertEqual(values["inv_initial_qty"], 10.0)
        self.assertEqual(values["entradas_qty"], 5.0)
        self.assertEqual(values["salidas_qty"], 3.0)
        self.assertEqual(values["retiros_qty"], 2.0)
        self.assertEqual(values["autoconsumos_qty"], 1.0)
        self.assertEqual(values["inv_final_qty"], 9.0)

    def test_warehouse_filter_excludes_other_warehouses(self):
        other_warehouse = self.env["stock.warehouse"].create(
            {"name": "Other warehouse", "code": "OTH"}
        )
        options = {"warehouse_ids": [other_warehouse.id]}
        self.assertEqual(self.handler._get_warehouses(options), other_warehouse)
        data = self.handler._get_product_data(
            other_warehouse,
            self.date_from,
            self.date_to,
            self.company.currency_id,
        )
        self.assertFalse(data.get(self.product.id, {}).get("entradas_qty"))
