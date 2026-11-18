# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestSeniatAccess(TransactionCase):
    """Operation-level checks for the ir.access rows converted for 20.0."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.readonly = new_test_user(
            cls.env, "seniat_access_ro", groups="account.group_account_readonly"
        )
        cls.invoicing = new_test_user(
            cls.env, "seniat_access_inv", groups="account.group_account_invoice"
        )
        cls.manager = new_test_user(
            cls.env, "seniat_access_mgr", groups="account.group_account_manager"
        )
        cls.basic = new_test_user(cls.env, "seniat_access_basic")

    def _access(self, user, model):
        records = self.env[model].with_user(user)
        return {
            op: records.has_access(op) for op in ("read", "create", "write", "unlink")
        }

    def test_account_book(self):
        self.assertEqual(
            self._access(self.readonly, "account.book"),
            {"read": True, "create": False, "write": False, "unlink": False},
        )
        self.assertEqual(
            self._access(self.invoicing, "account.book"),
            {"read": True, "create": True, "write": True, "unlink": False},
        )
        self.assertEqual(
            self._access(self.manager, "account.book"),
            {"read": True, "create": True, "write": True, "unlink": True},
        )
        self.assertFalse(self._access(self.basic, "account.book")["read"])

    def test_country_parish_is_readable_by_internal_users_only_for_managers_to_edit(
        self,
    ):
        basic = self._access(self.basic, "res.country.parish")
        self.assertTrue(basic["read"])
        self.assertFalse(basic["write"])
        self.assertTrue(self._access(self.manager, "res.country.parish")["write"])

    def test_cancel_reason_is_read_only_for_invoicing(self):
        access = self._access(self.invoicing, "l10n_ve.invoice.cancel.reason")
        self.assertTrue(access["read"])
        self.assertFalse(access["create"])
