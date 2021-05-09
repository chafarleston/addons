from odoo import api,models

class GuideReport(models.AbstractModel):
    _name = "report.l10n_pe_stock_reports.report_stock_blank"

    @api.model
    def get_report_values(self,docids,data=None):

        records = self.env[objectname].browse(docids)
        return {
            "doc_ids":docids,
            "docs":records,
            "data":data,
        }
