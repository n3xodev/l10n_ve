# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestL10nVeFiscalSerialIrAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_internal = new_test_user(
            cls.env,
            login="ve_fs_internal",
            groups="base.group_user",
        )
        cls.user_seniat = new_test_user(
            cls.env,
            login="ve_fs_seniat",
            groups="base.group_user,l10n_ve_seniat.group_seniat",
        )
        cls.user_portal = new_test_user(
            cls.env,
            login="ve_fs_portal",
            groups="base.group_portal",
        )
        cls.machine = cls.env["l10n.ve.fiscal.machine"].sudo().create(
            {
                "name": "HKA Access Test",
                "company_id": cls.env.company.id,
                "registered_serial": "ACC1234567",
            }
        )

    def test_fiscal_machine_access(self):
        model_internal = self.env["l10n.ve.fiscal.machine"].with_user(self.user_internal)
        self.assertEqual(model_internal.browse(self.machine.id).name, "HKA Access Test")
        model_internal.browse(self.machine.id).write({"name": "HKA Updated"})
        with self.assertRaises(AccessError):
            model_internal.create({"name": "Forbidden", "company_id": self.env.company.id})
        with self.assertRaises(AccessError):
            model_internal.browse(self.machine.id).unlink()

        model_seniat = self.env["l10n.ve.fiscal.machine"].with_user(self.user_seniat)
        created = model_seniat.create(
            {"name": "Seniat Machine", "company_id": self.env.company.id}
        )
        created.write({"name": "Seniat Machine 2"})
        created.unlink()

        with self.assertRaises(AccessError):
            self.env["l10n.ve.fiscal.machine"].with_user(self.user_portal).search([])

    def test_setup_wizard_access(self):
        with self.assertRaises(AccessError):
            self.env["l10n.ve.fiscal.machine.setup.wizard"].with_user(
                self.user_internal
            ).create({"company_id": self.env.company.id})

        wizard = self.env["l10n.ve.fiscal.machine.setup.wizard"].with_user(
            self.user_seniat
        ).create({"company_id": self.env.company.id})
        wizard.write({"name": "Wizard Updated"})
        wizard.unlink()

    def test_fiscal_serial_audit_access(self):
        audit_internal = self.env["l10n.ve.fiscal.serial.audit"].with_user(
            self.user_internal
        ).create({"event_type": "command", "source": "debug_console"})
        self.assertEqual(audit_internal.source, "debug_console")
        with self.assertRaises(AccessError):
            audit_internal.write({"source": "report"})
        with self.assertRaises(AccessError):
            audit_internal.unlink()

        audit_seniat = self.env["l10n.ve.fiscal.serial.audit"].with_user(
            self.user_seniat
        ).create({"event_type": "command", "source": "report"})
        with self.assertRaises(AccessError):
            audit_seniat.write({"source": "other"})
        with self.assertRaises(AccessError):
            audit_seniat.unlink()

        with self.assertRaises(AccessError):
            self.env["l10n.ve.fiscal.serial.audit"].with_user(self.user_portal).search([])

    def test_fiscal_payment_method_access(self):
        self.env["l10n.ve.fiscal.payment.method"].sudo().search(
            [("company_id", "=", self.env.company.id), ("code", "=", "24")]
        ).unlink()

        pm_seniat = self.env["l10n.ve.fiscal.payment.method"].with_user(
            self.user_seniat
        ).create({"company_id": self.env.company.id, "code": "24", "name": "TEST PM"})
        pm_seniat.write({"name": "TEST PM 2"})
        with self.assertRaises(AccessError):
            pm_seniat.unlink()

        pm_internal = self.env["l10n.ve.fiscal.payment.method"].with_user(
            self.user_internal
        )
        self.assertEqual(pm_internal.browse(pm_seniat.id).name, "TEST PM 2")
        with self.assertRaises(AccessError):
            pm_internal.browse(pm_seniat.id).write({"name": "DENIED"})
        with self.assertRaises(AccessError):
            pm_internal.create({"company_id": self.env.company.id, "code": "23", "name": "NO"})
        with self.assertRaises(AccessError):
            pm_internal.browse(pm_seniat.id).unlink()

        with self.assertRaises(AccessError):
            self.env["l10n.ve.fiscal.payment.method"].with_user(self.user_portal).search([])
