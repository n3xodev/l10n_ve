from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestLoyaltyAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.basic = new_test_user(cls.env, "loyalty_basic_user")
        cls.readonly = new_test_user(
            cls.env, "loyalty_readonly_user", groups="account.group_account_readonly"
        )
        cls.invoicing = new_test_user(
            cls.env, "loyalty_invoicing_user", groups="account.group_account_invoice"
        )
        cls.manager = new_test_user(
            cls.env, "loyalty_manager_user", groups="account.group_account_manager"
        )

    def _access(self, user, model):
        records = self.env[model].with_user(user)
        return {
            op: records.has_access(op) for op in ("read", "write", "create", "unlink")
        }

    def test_discount_reason_access_by_group(self):
        model = "l10n.ve.discount.reason"
        read_only = {"read": True, "write": False, "create": False, "unlink": False}
        self.assertEqual(self._access(self.readonly, model), read_only)
        self.assertEqual(self._access(self.invoicing, model), read_only)
        self.assertEqual(
            self._access(self.manager, model),
            {"read": True, "write": True, "create": True, "unlink": True},
        )
        self.assertFalse(self._access(self.basic, model)["read"])

    def test_move_discount_requires_invoicing_group(self):
        model = "l10n.ve.account.move.discount"
        self.assertEqual(
            self._access(self.invoicing, model),
            {"read": True, "write": True, "create": True, "unlink": True},
        )
        self.assertFalse(self._access(self.basic, model)["read"])
        self.assertFalse(self._access(self.readonly, model)["write"])
