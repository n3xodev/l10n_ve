# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import L10nVeSeniatCommon


@tagged("post_install", "-at_install")
class TestChartTemplateVe(L10nVeSeniatCommon):
    def test_ve_seniat_template_data(self):
        tpl = self.env["account.chart.template"]
        funcs = tpl._template_register[False]["ve_seniat"]["template_data"]
        self.assertTrue(funcs)
        data = funcs[0](tpl)
        self.assertEqual(data.get("code_digits"), "7")

    def test_ve_seniat_basic_res_company_template(self):
        tpl = self.env["account.chart.template"]
        funcs = tpl._template_register[False]["ve_seniat_basic"]["res.company"]
        self.assertTrue(funcs)
        data = funcs[0](tpl)
        self.assertIn(self.env.company.id, data)
        row = data[self.env.company.id]
        self.assertEqual(row["account_fiscal_country_id"], "base.ve")
        self.assertEqual(row["receivable_account_id"], "account_account_1106001")
        self.assertEqual(row["payable_account_id"], "account_account_2101002")
        self.assertEqual(row["income_account_id"], "account_account_4101001")
        self.assertEqual(row["expense_account_id"], "account_account_5101001")

    def test_ve_seniat_empty_res_company_template(self):
        tpl = self.env["account.chart.template"]
        funcs = tpl._template_register[False]["ve_seniat_empty"]["res.company"]
        self.assertTrue(funcs)
        data = funcs[0](tpl)
        row = data[self.env.company.id]
        self.assertEqual(row["account_fiscal_country_id"], "base.ve")
        self.assertNotIn("cash_account_code_prefix", row)
        self.assertEqual(row["account_sale_tax_id"], "tax1sale")

    def test_ve_seniat_empty_has_no_coa_in_template_data(self):
        tpl = self.env["account.chart.template"]
        funcs = tpl._template_register[False]["ve_seniat_empty"]["template_data"]
        data = funcs[0](tpl)
        self.assertNotIn("code_digits", data)
        self.assertNotIn("income_account_id", data)
