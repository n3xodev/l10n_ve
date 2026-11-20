# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestWithholdingAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.basic = new_test_user(cls.env, "wh_basic_user")
        cls.invoicing = new_test_user(
            cls.env, "wh_invoicing_user", groups="account.group_account_invoice"
        )
        cls.readonly = new_test_user(
            cls.env, "wh_readonly_user", groups="account.group_account_readonly"
        )
        cls.manager = new_test_user(
            cls.env, "wh_manager_user", groups="account.group_account_manager"
        )
        cls.fiscal_support = new_test_user(
            cls.env,
            "wh_fiscal_support_user",
            groups="l10n_ve_seniat.group_fiscal_config_support",
        )

    def _access(self, user, model):
        records = self.env[model].with_user(user)
        return {
            op: records.has_access(op) for op in ("read", "write", "create", "unlink")
        }

    def test_retention_invoicing_user_has_full_access(self):
        self.assertEqual(
            self._access(self.invoicing, "account.retention"),
            {"read": True, "write": True, "create": True, "unlink": True},
        )

    def test_retention_readonly_user_only_reads(self):
        self.assertEqual(
            self._access(self.readonly, "account.retention"),
            {"read": True, "write": False, "create": False, "unlink": False},
        )

    def test_retention_internal_user_has_no_access(self):
        self.assertFalse(self._access(self.basic, "account.retention")["read"])

    def test_payment_concept_invoicing_user_only_reads(self):
        for model in ("payment.concept", "payment.concept.line"):
            self.assertEqual(
                self._access(self.invoicing, model),
                {"read": True, "write": False, "create": False, "unlink": False},
                model,
            )

    def test_payment_concept_fiscal_support_cannot_unlink(self):
        for model in ("payment.concept", "payment.concept.line"):
            self.assertEqual(
                self._access(self.fiscal_support, model),
                {"read": True, "write": True, "create": True, "unlink": False},
                model,
            )

    def test_payment_concept_internal_user_has_no_access(self):
        for model in ("payment.concept", "payment.concept.line"):
            self.assertFalse(self._access(self.basic, model)["read"], model)

    def test_core_overrides_keep_manager_from_unlinking(self):
        # The module narrows the core rows to operation "cru" for account managers.
        for model in ("account.journal.group", "account.tax"):
            self.assertEqual(
                self._access(self.manager, model),
                {"read": True, "write": True, "create": True, "unlink": False},
                model,
            )

    def test_core_overrides_keep_other_users_restricted(self):
        self.assertFalse(self._access(self.basic, "account.journal.group")["read"])
        tax = self._access(self.basic, "account.tax")
        self.assertEqual(
            tax, {"read": True, "write": False, "create": False, "unlink": False}
        )
        self.assertTrue(self._access(self.invoicing, "account.journal.group")["read"])
        self.assertFalse(self._access(self.invoicing, "account.journal.group")["write"])
