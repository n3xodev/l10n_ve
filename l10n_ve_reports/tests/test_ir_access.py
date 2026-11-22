# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user

FULL = {"read": True, "write": True, "create": True, "unlink": True}
READ = {"read": True, "write": False, "create": False, "unlink": False}
CRU = {"read": True, "write": True, "create": True, "unlink": False}
NONE = {"read": False, "write": False, "create": False, "unlink": False}


@tagged("post_install", "-at_install")
class TestReportsIrAccess(TransactionCase):
    """Access of the models of the reports engine, per accounting group.

    In Odoo 20 the accounting groups of a privilege do not imply each other the way
    they did in 19 (the Administrator group only implies Billing), so every group that
    needs a permission must be granted by an ir.access row.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = {
            "basic": new_test_user(cls.env, "reports_basic_user"),
            "invoice": new_test_user(
                cls.env, "reports_invoice_user", groups="account.group_account_invoice"
            ),
            "readonly": new_test_user(
                cls.env,
                "reports_readonly_user",
                groups="account.group_account_readonly",
            ),
            "user": new_test_user(
                cls.env, "reports_account_user", groups="account.group_account_user"
            ),
            "manager": new_test_user(
                cls.env,
                "reports_manager_user",
                groups="account.group_account_manager",
            ),
        }

    def _access(self, user_key, model):
        records = self.env[model].with_user(self.users[user_key])
        return {
            operation: records.has_access(operation)
            for operation in ("read", "write", "create", "unlink")
        }

    def _assert_access(self, model, expected):
        for user_key, expected_access in expected.items():
            self.assertEqual(
                self._access(user_key, model),
                expected_access,
                f"{model} for the {user_key} user",
            )

    def test_annotation(self):
        self._assert_access(
            "account.report.annotation.oca",
            {
                "basic": NONE,
                "invoice": READ,
                "readonly": READ,
                "user": FULL,
                "manager": FULL,
            },
        )

    def test_export_wizards(self):
        for model in (
            "account_reports.export.wizard",
            "account_reports.export.wizard.format",
            "account.report.file.download.error.wizard",
        ):
            self._assert_access(
                model,
                {
                    "basic": NONE,
                    "invoice": NONE,
                    "readonly": NONE,
                    "user": CRU,
                    "manager": CRU,
                },
            )

    def test_configuration_models_are_managed_by_administrators(self):
        for model in (
            "account.tax.unit",
            "account.report.horizontal.group.oca",
            "account.report.horizontal.group.rule.oca",
            "account.report.budget.oca",
            "account.report.budget.item.oca",
        ):
            self._assert_access(
                model,
                {
                    "basic": NONE,
                    "invoice": NONE,
                    "readonly": READ,
                    "user": READ,
                    "manager": FULL,
                },
            )

    def test_report_send_wizard(self):
        self._assert_access(
            "account.report.send",
            {
                "basic": NONE,
                "invoice": FULL,
                "readonly": NONE,
                "user": FULL,
                "manager": FULL,
            },
        )
