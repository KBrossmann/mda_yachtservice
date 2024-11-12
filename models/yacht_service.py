from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "hr.employee"

    is_mechanic = fields.Boolean(string="Is Technician")
    is_supervisor = fields.Boolean(string="Is Job Manager")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    yacht_service_client_id = fields.Many2one(
        "yacht.service.client", string="Yacht Service Client"
    )
    source_document = fields.Char(string="Source Document")
    description_name = fields.Char(string="Description Name")
    yacht_name = fields.Char(string="Yacht Name")


class Invoices(models.Model):
    _inherit = "account.move"

    yacht_service_client_id = fields.Many2one(
        "yacht.service.client", string="Yacht Service Client"
    )
    source_document = fields.Char(string="Source Document")
    description_name = fields.Char(string="Description Name")
    yacht_name = fields.Char(string="Yacht Name")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    description_name = fields.Char(string="Description Name")
