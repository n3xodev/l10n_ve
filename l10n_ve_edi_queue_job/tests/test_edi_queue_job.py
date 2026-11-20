from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.l10n_ve_seniat.tests.common import L10nVeSeniatCommon
from odoo.addons.queue_job.tests.common import trap_jobs


@tagged("post_install", "-at_install")
class TestL10nVeEdiQueueJob(L10nVeSeniatCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_sale"]
        cls.today = fields.Date.today()
        cls.account_user = cls.env["res.users"].create(
            {
                "name": "EDI Queue Account User",
                "login": "edi_queue_account_user",
                "email": "edi_queue_account@example.com",
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
                "name": "EDI Queue Stock User",
                "login": "edi_queue_stock_user",
                "email": "edi_queue_stock@example.com",
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

    def test_uses_queue_job_flag(self):
        self.assertTrue(self.env["account.move"]._l10n_ve_edi_send_uses_queue_job())
        self.assertTrue(self.env["account.retention"]._l10n_ve_edi_send_uses_queue_job())
        self.assertTrue(self.env["stock.picking"]._l10n_ve_edi_send_uses_queue_job())

    def test_schedule_send_enqueues_invoice_job_with_user(self):
        move = (
            self.env["account.move"]
            .with_user(self.account_user)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_a.id,
                    "journal_id": self.journal.id,
                    "invoice_date": self.today,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Queue EDI Line",
                                "quantity": 1.0,
                                "price_unit": 50.0,
                                "account_id": self.company_data["default_account_revenue"].id,
                            }
                        )
                    ],
                }
            )
        )
        with trap_jobs() as trap:
            move._l10n_ve_edi_schedule_send()
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(
                move._job_l10n_ve_edi_send_invoice,
                args=(move.id,),
                properties={"channel": "root"},
            )

    def test_schedule_send_enqueues_picking_job_with_user(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
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
                }
            )
        )
        with trap_jobs() as trap:
            picking._l10n_ve_edi_schedule_send()
            trap.assert_jobs_count(1)
            trap.assert_enqueued_job(
                picking._job_l10n_ve_edi_send_picking,
                args=(picking.id,),
                properties={"channel": "root"},
            )
