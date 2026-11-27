# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.account_reports.utils.report_data_objects import (
    AccountReportLineData,
)


@tagged("post_install", "-at_install")
class TestInventoryBookEnterprise(TransactionCase):
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
            {"name": "Retiros EE", "usage": "internal"}
        )
        cls.autoconsumos_location = cls.env["stock.location"].create(
            {"name": "Autoconsumos EE", "usage": "internal"}
        )
        cls.warehouse.write(
            {
                "l10n_ve_location_retiros_id": cls.retiros_location.id,
                "l10n_ve_location_autoconsumos_id": cls.autoconsumos_location.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Inventory book EE product",
                "is_storable": True,
                "standard_price": 10.0,
            }
        )
        cls.report = cls.env.ref(
            "l10n_ve_reports_stock_enterprise.inventory_book_report"
        )
        cls.handler = cls.env["l10n_ve.inventory.book.report.handler"]
        cls.date_from = fields.Date.from_string("2024-02-01")
        cls.date_to = fields.Date.from_string("2024-02-29")

        # Opening: 10 units
        cls._move(cls.supplier_location, cls.stock_location, 10, "2024-01-10")
        # Period movements: +5 in, -3 out, -2 retiros, -1 autoconsumos -> 9 final
        cls._move(cls.supplier_location, cls.stock_location, 5, "2024-02-05")
        cls._move(cls.stock_location, cls.customer_location, 3, "2024-02-10")
        cls._move(cls.stock_location, cls.retiros_location, 2, "2024-02-12")
        cls._move(cls.stock_location, cls.autoconsumos_location, 1, "2024-02-15")
        # After period: ignored
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

    def test_report_action_and_menus_registered(self):
        self.assertEqual(
            self.report.custom_handler_model_name,
            "l10n_ve.inventory.book.report.handler",
        )
        action = self.env.ref(
            "l10n_ve_reports_stock_enterprise.action_inventory_book_report"
        )
        self.assertEqual(action.tag, "account_report")
        for xml_id in (
            "l10n_ve_reports_stock_enterprise.menu_seniat_report_inventory_book",
            "l10n_ve_reports_stock_enterprise.menu_stock_report_inventory_book",
        ):
            self.assertTrue(self.env.ref(xml_id, raise_if_not_found=False), xml_id)
        self.assertEqual(
            self.handler._get_custom_display_config()["components"][
                "AccountReportFilters"
            ],
            "InventoryBookReportFilters",
        )

    def test_product_data_math(self):
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

    def test_report_lines_and_xlsx_export(self):
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
        self.assertTrue(all(isinstance(line, AccountReportLineData) for line in lines))

        product_lines = [
            line for line in lines if line.name == self.product.display_name
        ]
        self.assertEqual(len(product_lines), 1)
        values = {
            column["expression_label"]: product_lines[0].columns[idx].no_format
            for idx, column in enumerate(options["columns"])
        }
        self.assertEqual(values["inv_initial_qty"], 10.0)
        self.assertEqual(values["entradas_qty"], 5.0)
        self.assertEqual(values["salidas_qty"], 3.0)
        self.assertEqual(values["retiros_qty"], 2.0)
        self.assertEqual(values["autoconsumos_qty"], 1.0)
        self.assertEqual(values["inv_final_qty"], 9.0)

        exported = self.report.export_to_xlsx(options)
        self.assertEqual(exported["file_type"], "xlsx")
        self.assertTrue(exported["file_content"].startswith(b"PK"))

    def test_warehouse_filter_isolation(self):
        other_warehouse = self.env["stock.warehouse"].create(
            {"name": "Other EE warehouse", "code": "OEE"}
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
