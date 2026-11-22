# pylint: disable=C0326

from freezegun import freeze_time

import odoo.tests
from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.l10n_ve_reports.models.account_report import PARENT_ACCOUNT_MARKUP

from .common import TestAccountReportsCommon


@tagged("post_install", "-at_install")
class TestGeneralLedgerReport(TestAccountReportsCommon, odoo.tests.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Give codes in company_1 to the accounts in company_2.
        context = {
            "allowed_company_ids": [
                cls.company_data["company"].id,
                cls.company_data_2["company"].id,
            ]
        }
        cls.company_data_2["default_account_payable"].with_context(
            context
        ).code = "211010"
        cls.company_data_2["default_account_revenue"].with_context(
            context
        ).code = "400010"
        cls.company_data_2["default_account_expense"].with_context(
            context
        ).code = "600010"
        cls.env["account.account"].search(
            [
                ("company_ids", "=", cls.company_data_2["company"].id),
                ("account_type", "=", "equity_unaffected"),
            ]
        ).with_context(context).code = "999989"

        # Entries in 2016 for company_1 to test the initial balance.
        cls.move_2016_1 = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2016-01-01"),
                "journal_id": cls.company_data["default_journal_misc"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "name": "2016_1_1",
                            "account_id": cls.company_data[
                                "default_account_payable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 200.0,
                            "credit": 0.0,
                            "name": "2016_1_2",
                            "account_id": cls.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 300.0,
                            "name": "2016_1_3",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        cls.move_2016_1.action_post()

        # Entries in 2016 for company_2 to test the initial balance in multi-companies/multi-currencies.
        cls.move_2016_2 = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2016-06-01"),
                "journal_id": cls.company_data_2["default_journal_misc"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "name": "2016_2_1",
                            "account_id": cls.company_data_2[
                                "default_account_payable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 100.0,
                            "name": "2016_2_2",
                            "account_id": cls.company_data_2[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        cls.move_2016_2.action_post()

        # Entry in 2017 for company_1 to test the report at current date.
        cls.move_2017_1 = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2017-01-01"),
                "journal_id": cls.company_data["default_journal_sale"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 1000.0,
                            "credit": 0.0,
                            "name": "2017_1_1",
                            "account_id": cls.company_data[
                                "default_account_receivable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 2000.0,
                            "credit": 0.0,
                            "name": "2017_1_2",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 3000.0,
                            "credit": 0.0,
                            "name": "2017_1_3",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 4000.0,
                            "credit": 0.0,
                            "name": "2017_1_4",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 5000.0,
                            "credit": 0.0,
                            "name": "2017_1_5",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 6000.0,
                            "credit": 0.0,
                            "name": "2017_1_6",
                            "account_id": cls.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 6000.0,
                            "name": "2017_1_7",
                            "account_id": cls.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 7000.0,
                            "name": "2017_1_8",
                            "account_id": cls.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 8000.0,
                            "name": "2017_1_9",
                            "account_id": cls.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                ],
            }
        )
        cls.move_2017_1.action_post()

        # Entry in 2017 for company_2 to test the current period in multi-companies/multi-currencies.
        cls.move_2017_2 = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2017-06-01"),
                "journal_id": cls.company_data_2["default_journal_bank"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 400.0,
                            "credit": 0.0,
                            "name": "2017_2_1",
                            "account_id": cls.company_data_2[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 400.0,
                            "name": "2017_2_2",
                            "account_id": cls.company_data_2[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        cls.move_2017_2.action_post()

        # Archive 'default_journal_bank' to ensure archived entries are not filtered out.
        cls.company_data_2["default_journal_bank"].active = False

        # Deactive all currencies to ensure group_multi_currency is disabled.
        cls.env["res.currency"].search([("name", "!=", "USD")]).with_context(
            force_deactivate=True
        ).active = False

        cls.report = cls.env.ref("l10n_ve_reports.general_ledger_report")

    # -------------------------------------------------------------------------
    # TESTS: General Ledger
    # -------------------------------------------------------------------------
    def test_general_ledger_unaffected_earnings_current_fiscal_year(self):
        def invoice_move(date):
            return self.env["account.move"].create(
                {
                    "move_type": "entry",
                    "date": fields.Date.from_string(date),
                    "journal_id": self.company_data["default_journal_misc"].id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "debit": 1000.0,
                                "credit": 0.0,
                                "name": "payable",
                                "account_id": self.company_data[
                                    "default_account_payable"
                                ].id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "debit": 2000.0,
                                "credit": 0.0,
                                "name": "expense",
                                "account_id": self.company_data[
                                    "default_account_expense"
                                ].id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "debit": 0.0,
                                "credit": 3000.0,
                                "name": "revenue",
                                "account_id": self.company_data[
                                    "default_account_revenue"
                                ].id,
                            },
                        ),
                    ],
                }
            )

        move_2009_12 = invoice_move("2009-12-31")
        move_2009_12.action_post()

        move_2010_01 = invoice_move("2010-01-31")
        move_2010_01.action_post()

        move_2010_02 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2010-02-01"),
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "name": "payable",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 200.0,
                            "credit": 0.0,
                            "name": "expense",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 300.0,
                            "name": "revenue",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        move_2010_02.action_post()

        move_2010_03 = invoice_move("2010-03-01")
        move_2010_03.action_post()

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2010-02-01"),
            fields.Date.from_string("2010-02-28"),
        )

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("211000 Account Payable", 2100.0, 0.0, 2100.0),
                ("400000 Product Sales", 0.0, 3300.0, -3300.0),
                ("600000 Expenses", 2200.0, 0.0, 2200.0),
                ("999999 Undistributed Profits/Losses", 2000.0, 3000.0, -1000.0),
                ("Total", 6300.0, 6300.0, 0.0),
            ],
            options,
        )

    def test_general_ledger_unaffected_earnings_previous_fiscal_year(self):
        def invoice_move(date):
            return self.env["account.move"].create(
                {
                    "move_type": "entry",
                    "date": fields.Date.from_string(date),
                    "journal_id": self.company_data["default_journal_misc"].id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "debit": 1000.0,
                                "credit": 0.0,
                                "name": "payable",
                                "account_id": self.company_data[
                                    "default_account_payable"
                                ].id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "debit": 2000.0,
                                "credit": 0.0,
                                "name": "expense",
                                "account_id": self.company_data[
                                    "default_account_expense"
                                ].id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "debit": 0.0,
                                "credit": 3000.0,
                                "name": "revenue",
                                "account_id": self.company_data[
                                    "default_account_revenue"
                                ].id,
                            },
                        ),
                    ],
                }
            )

        move_2009_12 = invoice_move("2009-12-31")
        move_2009_12.action_post()

        move_2010_01 = invoice_move("2010-01-31")
        move_2010_01.action_post()

        move_2010_02 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2010-02-01"),
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "name": "payable",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 200.0,
                            "credit": 0.0,
                            "name": "expense",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 300.0,
                            "name": "revenue",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        move_2010_02.action_post()

        move_2010_03 = invoice_move("2010-03-01")
        move_2010_03.action_post()

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2010-01-01"),
            fields.Date.from_string("2010-02-28"),
        )

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("211000 Account Payable", 2100.0, 0.0, 2100.0),
                ("400000 Product Sales", 0.0, 3300.0, -3300.0),
                ("600000 Expenses", 2200.0, 0.0, 2200.0),
                ("999999 Undistributed Profits/Losses", 2000.0, 3000.0, -1000.0),
                ("Total", 6300.0, 6300.0, 0.0),
            ],
            options,
        )

    def test_general_ledger_branch_unaffected_earnings(self):
        """A branch company with its own equity-unaffected account must not
        raise 'Expected singleton' when the General Ledger aggregates
        unaffected earnings across a root company and its branch: each
        company's prior-year result must land on its own account.
        """
        root_company = self.company_data["company"]
        root_company.write({"child_ids": [Command.create({"name": "Branch A"})]})
        self.cr.precommit.run()  # load the CoA on the branch
        branch = root_company.child_ids
        self.env.user.company_ids |= branch

        branch_unaffected_account = self.env["account.account"].create(
            {
                "name": "Branch Undistributed Profits/Losses",
                "code": "888888",
                "account_type": "equity_unaffected",
                "company_ids": [Command.set(branch.ids)],
            }
        )
        # The shared test fixture already carries more than one
        # 'equity_unaffected' account for the root company alone (this is
        # exactly the pre-existing ambiguity the singleton bug was built on) ;
        # any of them is an acceptable resting place for the root's own
        # earnings, as long as it is not merged onto the branch's account.
        root_unaffected_accounts = self.env["account.account"].search(
            [
                ("company_ids", "=", root_company.id),
                ("account_type", "=", "equity_unaffected"),
            ]
        )

        def prior_year_move(company):
            return self.env["account.move"].create(
                {
                    "move_type": "entry",
                    "company_id": company.id,
                    "date": fields.Date.from_string("2016-01-01"),
                    "journal_id": self.company_data["default_journal_misc"].id,
                    "line_ids": [
                        Command.create(
                            {
                                "debit": 1000.0,
                                "credit": 0.0,
                                "name": "expense",
                                "account_id": self.company_data[
                                    "default_account_expense"
                                ].id,
                            }
                        ),
                        Command.create(
                            {
                                "debit": 0.0,
                                "credit": 1000.0,
                                "name": "revenue",
                                "account_id": self.company_data[
                                    "default_account_revenue"
                                ].id,
                            }
                        ),
                    ],
                }
            )

        root_move = prior_year_move(root_company)
        root_move.action_post()

        branch_move = prior_year_move(branch)
        branch_move.action_post()

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )

        # Must not raise `ValueError: Expected singleton`.
        lines = self.report._get_lines(options)

        line_names = {line["name"] for line in lines}
        self.assertTrue(
            line_names & set(root_unaffected_accounts.mapped("display_name")),
            "the root company's own unaffected earnings must still be "
            "aggregated onto one of its own accounts",
        )
        self.assertIn(
            branch_unaffected_account.display_name,
            line_names,
            "the branch's own unaffected earnings account must be "
            "aggregated under its own account, not merged onto the root "
            "company's",
        )

    def test_general_ledger_unaffected_earnings_account_selection_order(self):
        """The generic Odoo 19 CoA seeds *two* 'equity_unaffected' accounts
        for a single company: 'Profit or Loss Appropriation' (999999) and
        'Accumulated Retained Earnings' (999998). The prior-year result must
        land on the account fetched first by creation order (matching the
        code's own "first fetched account" intent), not on whichever account
        happens to sort first by its code string (999998 < 999999).
        """
        root_company = self.company_data["company"]
        profit_or_loss_account = self.env["account.account"].search(
            [
                ("company_ids", "=", root_company.id),
                ("account_type", "=", "equity_unaffected"),
                ("code", "=", "999999"),
            ]
        )
        self.assertTrue(
            profit_or_loss_account,
            "the generic CoA must seed the 'Profit or Loss Appropriation' "
            "account with code 999999",
        )

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2016-01-01"),
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 1000.0,
                            "credit": 0.0,
                            "name": "expense",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 1000.0,
                            "name": "revenue",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )
        lines = self.report._get_lines(options)

        line_names = {line["name"] for line in lines}
        self.assertIn(
            profit_or_loss_account.display_name,
            line_names,
            "the prior-year result must be aggregated onto the account "
            "fetched first by creation order (999999), not by code-string "
            "order (999998)",
        )

    def test_general_ledger_fold_unfold_multicompany_multicurrency(self):
        """Test unfolding a line when rendering the whole report."""
        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("211000 Account Payable", 100.0, 0.0, 100.0),
                ("211010 Account Payable", 33.33, 0.0, 33.33),
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", 0.0, 200.0, -200.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("600010 Expenses", 200.0, 0.0, 200.0),
                ("999989 Undistributed Profits/Losses", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", 200.0, 300.0, -100.0),
                ("Total", 21533.33, 21550.0, -16.67),
            ],
            options,
        )

        options["unfold_all"] = True

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("INV/2017/00001", 1000.0, 0.0, 1000.0),
                ("Total 121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("211000 Account Payable", 100.0, 0.0, 100.0),
                ("211010 Account Payable", 33.33, 0.0, 33.33),
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("INV/2017/00001", 2000.0, 0.0, 2000.0),
                ("INV/2017/00001", 3000.0, 0.0, 5000.0),
                ("INV/2017/00001", 4000.0, 0.0, 9000.0),
                ("INV/2017/00001", 5000.0, 0.0, 14000.0),
                ("INV/2017/00001", 6000.0, 0.0, 20000.0),
                ("Total 400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", 0.0, 200.0, -200.0),
                ("BNK1/2017/00001", 0.0, 200.0, -200.0),
                ("Total 400010 Product Sales", 0.0, 200.0, -200.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("INV/2017/00001", 0.0, 6000.0, -6000.0),
                ("INV/2017/00001", 0.0, 7000.0, -13000.0),
                ("INV/2017/00001", 0.0, 8000.0, -21000.0),
                ("Total 600000 Expenses", 0.0, 21000.0, -21000.0),
                ("600010 Expenses", 200.0, 0.0, 200.0),
                ("BNK1/2017/00001", 200.0, 0.0, 200.0),
                ("Total 600010 Expenses", 200.0, 0.0, 200.0),
                ("999989 Undistributed Profits/Losses", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", 200.0, 300.0, -100.0),
                ("Total", 21533.33, 21550.0, -16.67),
            ],
            options,
        )

    def test_general_ledger_multiple_years_initial_balance(self):
        # Entries in 2015 for company_1 to test the initial balance.
        move_2015_1 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2015-01-01"),
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 100.0,
                            "credit": 0.0,
                            "name": "2015_1_1",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 200.0,
                            "credit": 0.0,
                            "name": "2015_1_2",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 300.0,
                            "name": "2015_1_3",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        move_2015_1.action_post()

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("211000 Account Payable", 200.0, 0.0, 200.0),
                ("211010 Account Payable", 33.33, 0.0, 33.33),
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", 0.0, 200.0, -200.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("600010 Expenses", 200.0, 0.0, 200.0),
                ("999989 Undistributed Profits/Losses", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", 400.0, 600.0, -200.0),
                ("Total", 21833.33, 21850.0, -16.67),
            ],
            options,
        )

        options["unfold_all"] = True

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("INV/2017/00001", 1000.0, 0.0, 1000.0),
                ("Total 121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("211000 Account Payable", 200.0, 0.0, 200.0),
                ("211010 Account Payable", 33.33, 0.0, 33.33),
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("INV/2017/00001", 2000.0, 0.0, 2000.0),
                ("INV/2017/00001", 3000.0, 0.0, 5000.0),
                ("INV/2017/00001", 4000.0, 0.0, 9000.0),
                ("INV/2017/00001", 5000.0, 0.0, 14000.0),
                ("INV/2017/00001", 6000.0, 0.0, 20000.0),
                ("Total 400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", 0.0, 200.0, -200.0),
                ("BNK1/2017/00001", 0.0, 200.0, -200.0),
                ("Total 400010 Product Sales", 0.0, 200.0, -200.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("INV/2017/00001", 0.0, 6000.0, -6000.0),
                ("INV/2017/00001", 0.0, 7000.0, -13000.0),
                ("INV/2017/00001", 0.0, 8000.0, -21000.0),
                ("Total 600000 Expenses", 0.0, 21000.0, -21000.0),
                ("600010 Expenses", 200.0, 0.0, 200.0),
                ("BNK1/2017/00001", 200.0, 0.0, 200.0),
                ("Total 600010 Expenses", 200.0, 0.0, 200.0),
                ("999989 Undistributed Profits/Losses", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", 400.0, 600.0, -200.0),
                ("Total", 21833.33, 21850.0, -16.67),
            ],
            options,
        )

    def test_general_ledger_load_more(self):
        """Test unfolding a line to use the load more."""
        self.env.companies = self.env.company
        self.report.load_more_limit = 2

        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )
        options["unfolded_lines"] = [
            self.report._get_generic_line_id(
                "account.account", self.company_data["default_account_revenue"].id
            )
        ]

        report_lines = self.report._get_lines(options)

        self.assertLinesValues(
            report_lines,
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 1000.0, 0.0, 1000.0),
                ("211000 Account Payable", 100.0, 0.0, 100.0),
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("INV/2017/00001", 2000.0, 0.0, 2000.0),
                ("INV/2017/00001", 3000.0, 0.0, 5000.0),
                ("Load more...", "", "", ""),
                ("Total 400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("999999 Undistributed Profits/Losses", 200.0, 300.0, -100.0),
                ("Total", 21300.0, 21300.0, 0.0),
            ],
            options,
        )

        load_more_1 = self.report.get_expanded_lines(
            options,
            report_lines[3]["id"],
            report_lines[6]["groupby"],
            "_report_expand_unfoldable_line_general_ledger",
            report_lines[6]["progress"],
            report_lines[6]["offset"],
            None,
        )

        self.assertLinesValues(
            load_more_1,
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("INV/2017/00001", 4000.0, 0.0, 9000.0),
                ("INV/2017/00001", 5000.0, 0.0, 14000.0),
                ("Load more...", "", "", ""),
            ],
            options,
        )

        load_more_2 = self.report.get_expanded_lines(
            options,
            report_lines[3]["id"],
            load_more_1[2]["groupby"],
            "_report_expand_unfoldable_line_general_ledger",
            load_more_1[2]["progress"],
            load_more_1[2]["offset"],
            None,
        )

        self.assertLinesValues(
            load_more_2,
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("INV/2017/00001", 6000.0, 0.0, 20000.0),
            ],
            options,
        )

    def test_general_ledger_foreign_currency_account(self):
        """Ensure the total in foreign currency of an account is displayed only if all journal items are sharing the
        same currency.
        """
        self.env.user.group_ids |= self.env.ref("base.group_multi_currency")

        foreign_curr_account = self.env["account.account"].create(
            {
                "name": "foreign_curr_account",
                "code": "test",
                "account_type": "liability_current",
                "currency_id": self.other_currency.id,
            }
        )

        move_2016 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2016-01-01",
                "journal_id": self.company_data["default_journal_sale"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "curr_1",
                            "debit": 100.0,
                            "credit": 0.0,
                            "amount_currency": 100.0,
                            "currency_id": self.company_data["currency"].id,
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "curr_2",
                            "debit": 0.0,
                            "credit": 100.0,
                            "amount_currency": -300.0,
                            "currency_id": self.other_currency.id,
                            "account_id": foreign_curr_account.id,
                        },
                    ),
                ],
            }
        )
        move_2016.action_post()

        move_2017 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2017-01-01",
                "journal_id": self.company_data["default_journal_sale"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "curr_1",
                            "debit": 1000.0,
                            "credit": 0.0,
                            "amount_currency": 1000.0,
                            "currency_id": self.company_data["currency"].id,
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "curr_2",
                            "debit": 0.0,
                            "credit": 1000.0,
                            "amount_currency": -2000.0,
                            "currency_id": self.other_currency.id,
                            "account_id": foreign_curr_account.id,
                        },
                    ),
                ],
            }
        )
        move_2017.action_post()
        move_2017.line_ids.flush_recordset()

        # Init options.
        options = self._generate_options(
            self.report,
            fields.Date.from_string("2017-01-01"),
            fields.Date.from_string("2017-12-31"),
        )
        options["unfolded_lines"] = [
            self.report._get_generic_line_id("account.account", foreign_curr_account.id)
        ]

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Amount_currency Debit           Credit          Balance
            [0, 4, 5, 6, 7],
            [
                ("121000 Account Receivable", "", 2100.0, 0.0, 2100.0),
                ("211000 Account Payable", "", 100.0, 0.0, 100.0),
                ("211010 Account Payable", "", 33.33, 0.0, 33.33),
                ("400000 Product Sales", "", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", "", 0.0, 200.0, -200.0),
                ("600000 Expenses", "", 0.0, 21000.0, -21000.0),
                ("600010 Expenses", "", 200.0, 0.0, 200.0),
                ("999989 Undistributed Profits/Losses", "", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", "", 200.0, 300.0, -100.0),
                ("test foreign_curr_account", -2300.0, 0.0, 1100.0, -1100.0),
                ("Initial Balance", -300.0, 0.0, 100.0, -100.0),
                ("INV/2017/00002", -2000.0, 0.0, 1000.0, -1100.0),
                ("Total test foreign_curr_account", -2300.0, 0.0, 1100.0, -1100.0),
                ("Total", "", 22633.33, 22650.0, -16.67),
            ],
            options,
            currency_map={4: {"currency": self.other_currency}},
        )

    def test_general_ledger_filter_search_bar_print(self):
        """Test the lines generated when a user filters on the search bar and prints the report"""
        options = self._generate_options(
            self.report,
            "2017-01-01",
            "2017-12-31",
            default_options={"export_mode": "print"},
        )
        options["filter_search_bar"] = "400"
        options["unfold_all"] = True

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("INV/2017/00001", 2000.0, 0.0, 2000.0),
                ("INV/2017/00001", 3000.0, 0.0, 5000.0),
                ("INV/2017/00001", 4000.0, 0.0, 9000.0),
                ("INV/2017/00001", 5000.0, 0.0, 14000.0),
                ("INV/2017/00001", 6000.0, 0.0, 20000.0),
                ("Total 400000 Product Sales", 20000.0, 0.0, 20000.0),
                ("400010 Product Sales", 0.0, 200.0, -200.0),
                ("BNK1/2017/00001", 0.0, 200.0, -200.0),
                ("Total 400010 Product Sales", 0.0, 200.0, -200.0),
                ("Total", 20000.0, 200.0, 19800.0),
            ],
            options,
        )

        options["filter_search_bar"] = "999"

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                          Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("999989 Undistributed Profits/Losses", 0.0, 50.0, -50.0),
                ("999999 Undistributed Profits/Losses", 200.0, 300.0, -100.0),
                ("Total", 200.0, 350.0, -150.0),
            ],
            options,
        )

    def test_general_ledger_communication(self):
        invoice_1 = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2010-01-01",
                "payment_reference": "payment_ref1",
                "ref": "ref1",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "test1",
                            "tax_ids": [],
                            "quantity": 1,
                            "price_unit": 1,
                        },
                    )
                ],
            }
        )
        invoice_1.action_post()

        invoice_2 = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2010-01-01",
                "payment_reference": "payment_ref2",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "test2",
                            "tax_ids": [],
                            "quantity": 1,
                            "price_unit": 2,
                        },
                    )
                ],
            }
        )
        invoice_2.action_post()

        options = self._generate_options(
            self.report,
            "2010-01-01",
            "2010-01-01",
            default_options={"unfold_all": True},
        )
        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Communication
            [0, 2],
            [
                ("121000 Account Receivable", ""),
                (invoice_1.name, "ref1 - payment_ref1"),
                (invoice_2.name, "payment_ref2"),
                ("400000 Product Sales", ""),
                (invoice_1.name, "ref1 - test1"),
                (invoice_2.name, "test2"),
                ("Total", ""),
            ],
            options,
        )

    def test_general_ledger_income_expense_initial_balance(self):
        """Test that when the report period does not start at the beginning of the FY,
        any AMLs prior to the report period but after the beginning of the FY are
        displayed in the initial balance for Income and Expense accounts."""

        self.env.companies = self.env.company

        move_2017 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2017-02-01"),
                "journal_id": self.company_data["default_journal_sale"].id,
                "line_ids": [
                    Command.create(
                        {
                            "debit": 1000.0,
                            "credit": 0.0,
                            "name": "2017_3_1",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                        }
                    ),
                    Command.create(
                        {
                            "debit": 0.0,
                            "credit": 1000.0,
                            "name": "2017_3_2",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        }
                    ),
                ],
            }
        )
        move_2017.action_post()

        # Init options.
        options = self._generate_options(self.report, "2017-02-01", "2017-03-01")
        options["unfolded_lines"] = [
            self.report._get_generic_line_id(
                "account.account", self.company_data["default_account_revenue"].id
            )
        ]

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                                    Debit           Credit          Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 2000.0, 0.0, 2000.0),
                ("211000 Account Payable", 100.0, 0.0, 100.0),
                ("400000 Product Sales", 20000.0, 1000.0, 19000.0),
                ("Initial Balance", 20000.0, 0.0, 20000.0),
                ("INV/2017/00002", 0.0, 1000.0, 19000.0),
                ("Total 400000 Product Sales", 20000.0, 1000.0, 19000.0),
                ("600000 Expenses", 0.0, 21000.0, -21000.0),
                ("999999 Undistributed Profits/Losses", 200.0, 300.0, -100.0),
                ("Total", 22300.0, 22300.0, 0.0),
            ],
            options,
        )

    @freeze_time("2017-07-11")
    def test_tour_account_reports_search(self):
        move_07_2017 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2017-07-10"),
                "journal_id": self.company_data["default_journal_sale"].id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": 1000.0,
                            "credit": 0.0,
                            "name": "2017_1_1",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": 0.0,
                            "credit": 1000.0,
                            "name": "2017_1_2",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                        },
                    ),
                ],
            }
        )
        move_07_2017.action_post()

        self.start_tour("/odoo", "account_reports_search", login=self.env.user.login)

    def test_general_ledger_hierarchy_non_numerical_column_value(self):
        """
        This test will check the value of the different (non-numerical) columns of the general ledger in case the
        hierarchy options is enabled
        """
        parent_account = self._create_parent_account("1", "Parent")
        receivable = self.company_data["default_account_receivable"]
        revenue = self.company_data["default_account_revenue"]
        (receivable + revenue).parent_id = parent_account
        self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2017-06-01",
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {"debit": 100.0, "credit": 0.0, "account_id": receivable.id}
                    ),
                    Command.create(
                        {"debit": 0.0, "credit": 100.0, "account_id": revenue.id}
                    ),
                ],
            }
        ).action_post()

        options = self._generate_options(self.report, "2017-01-01", "2017-12-31")
        options["hierarchy"] = True

        # String and Date figure type should be empty on the parent account line when using hierarchy.
        lines = self.report._get_lines(options)
        parent_lines = [
            line
            for line in lines
            if self.report._parse_line_id(line["id"], markup_as_string=True)[-1][0]
            == PARENT_ACCOUNT_MARKUP
        ]
        self.assertEqual([line["name"] for line in parent_lines], ["1 Parent"])
        # Columns: Date, Communication, Partner, then the numerical ones
        self.assertEqual(
            [column["name"] for column in parent_lines[0]["columns"][:3]], ["", "", ""]
        )

    def test_general_ledger_same_date_ordering(self):
        self.env.company.account_sale_tax_id = None
        report = self.env.ref("l10n_ve_reports.general_ledger_report")
        options = self._generate_options(
            report,
            fields.Date.from_string("2010-01-01"),
            fields.Date.from_string("2010-01-01"),
            default_options={"unfold_all": True},
        )

        move_1 = self.init_invoice(
            "out_invoice", invoice_date="2010-01-01", amounts=[100]
        )
        move_2 = self.init_invoice(
            "out_invoice", invoice_date="2010-01-01", amounts=[200]
        )

        # Make sure no sequence is set on them by default, so that move_2 can receive a lower sequence when posting
        (move_1 + move_2).write({"name": ""})

        # Post the moves in reverse order than the one they were created in, so that their line ids' respective order does not match their sequences'
        move_2.action_post()
        move_1.action_post()

        self.assertLinesValues(
            report._get_lines(options),
            #   Name                                      Debit       Credit      Balance
            [0, 4, 5, 6],
            [
                ("121000 Account Receivable", 300.0, 0.0, 300.0),
                (move_2.name, 200.0, 0.0, 200.0),
                (move_1.name, 100.0, 0.0, 300.0),
                ("400000 Product Sales", 0.0, 300.0, -300.0),
                (move_2.name, 0.0, 200.0, -200.0),
                (move_1.name, 0.0, 100.0, -300.0),
                ("Total", 300.0, 300.0, 0.0),
            ],
            options,
        )

    def test_caret_option_audit_tax(self):
        """The General Ledger's audit-tax caret option must resolve the generic
        tax report handler (models/account_general_ledger.py:910) and redirect
        to the move lines affected by the audited tax.
        """
        invoice = self.init_invoice(
            "out_invoice",
            invoice_date="2019-01-01",
            amounts=[1000],
            taxes=self.tax_sale_a,
            post=True,
        )
        base_line = invoice.line_ids.filtered(
            lambda line: self.tax_sale_a in line.tax_ids
            and not line.tax_repartition_line_id
        )
        tax_line = invoice.line_ids.filtered(
            lambda line: line.tax_line_id == self.tax_sale_a
        )
        expected_lines = base_line + tax_line
        self.assertEqual(
            len(expected_lines),
            2,
            "the invoice must carry one base line and one tax line for the audited tax",
        )

        report = self.env.ref("l10n_ve_reports.general_ledger_report")
        options = self._generate_options(
            report,
            fields.Date.from_string("2019-01-01"),
            fields.Date.from_string("2019-01-01"),
        )
        params = {
            "line_id": report._get_generic_line_id(
                "account.tax", self.tax_sale_a.id
            )
        }

        action = self.env[
            "account.general.ledger.report.handler.oca"
        ].caret_option_audit_tax(options, params)

        audited_lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(
            set(audited_lines.ids),
            set(expected_lines.ids),
            "the caret option must redirect to exactly the move lines tied "
            "to the audited tax",
        )
