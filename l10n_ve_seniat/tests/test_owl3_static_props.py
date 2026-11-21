import re
from pathlib import Path

from odoo.tests import BaseCase, tagged

ADDONS_ROOT = Path(__file__).resolve().parents[2]

# Modules of this repository that are NOT yet ported to Odoo 20.0 and still
# carry Owl 2 code. Remove each entry as soon as the module is ported
# (Track R / TP.4-TP.5) so that the guard starts covering it.
NOT_YET_PORTED = {
    "l10n_ve_reports",
    "l10n_ve_reports_stock",
    "l10n_ve_reports_seniat",
    "l10n_ve_fiscal_serial_pos",
    "l10n_ve_loyalty_pos",
    "l10n_ve_pos_igtf",
    "l10n_ve_pos_credit_currency",
}

LEGACY_PROPS = (
    re.compile(r"^\s*static\s+(?:props|defaultProps)\b", re.MULTILINE),
    re.compile(r"\bstatic\s+get\s+(?:props|defaultProps)\b"),
)


@tagged("post_install", "-at_install")
class TestOwl3StaticProps(BaseCase):
    """Owl 3 ignores ``static props``/``static defaultProps`` and breaks the web client.

    Scans ``static/src/**/*.js`` of every module of this repository (siblings of
    ``l10n_ve_seniat``) except the ones listed in ``NOT_YET_PORTED``.
    """

    def test_no_legacy_static_props(self):
        offenders = []
        for module_dir in sorted(ADDONS_ROOT.iterdir()):
            src = module_dir / "static" / "src"
            if module_dir.name in NOT_YET_PORTED or not src.is_dir():
                continue
            for path in sorted(src.rglob("*.js")):
                text = path.read_text(encoding="utf-8")
                for pattern in LEGACY_PROPS:
                    for match in pattern.finditer(text):
                        line = text.count("\n", 0, match.start()) + 1
                        offenders.append(f"{path.relative_to(ADDONS_ROOT)}:{line}")
        self.assertFalse(
            offenders,
            "Declare props with useProps() instead of static props: %s" % offenders,
        )
