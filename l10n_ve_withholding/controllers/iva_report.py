from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class GenerateTxt(http.Controller):
    @http.route("/web/binary/download_retention_iva_txt", type="http", auth="user")
    def download_retention_iva_txt(self, date_start, date_end, company_id, **kw):
        try:
            company_id = int(company_id)
        except (TypeError, ValueError) as exc:
            raise BadRequest("Invalid company_id") from exc
        if company_id not in request.env.user.company_ids.ids:
            raise AccessError("You do not have access to this company.")

        wizard_model = request.env["wizard.retention.iva"]
        domain = wizard_model._get_retention_domain(date_start, date_end, company_id)
        retentions = request.env["account.retention"].search(
            domain, order="date_accounting asc, id asc"
        )
        content = wizard_model._build_txt_content(retentions)
        return request.make_response(
            content,
            [
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Disposition", "attachment; filename=retenciones_iva.txt"),
            ],
        )
