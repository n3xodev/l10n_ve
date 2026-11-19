from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestIgtfAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.basic = new_test_user(cls.env, "igtf_basic_user")
        cls.invoicing = new_test_user(
            cls.env, "igtf_invoicing_user", groups="account.group_account_invoice"
        )

    def _access(self, user, model):
        records = self.env[model].with_user(user)
        return {
            op: records.has_access(op) for op in ("read", "write", "create", "unlink")
        }

    def test_unreconcile_wizard_is_open_to_invoicing_users_without_unlink(self):
        self.assertEqual(
            self._access(self.invoicing, "l10n_ve_igtf.unreconcile.payment.wizard"),
            {"read": True, "write": True, "create": True, "unlink": False},
        )

    def test_unreconcile_wizard_is_closed_to_internal_users(self):
        self.assertFalse(
            self._access(self.basic, "l10n_ve_igtf.unreconcile.payment.wizard")["read"]
        )
