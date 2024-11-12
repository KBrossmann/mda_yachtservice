from odoo import fields, models, api, _
# from odoo.exceptions import UserError#
import random, string


class YachtServiceClient(models.Model):
    _name = "yacht.service.client"
    _rec_name = "yacht_name"
    _inherit = "mail.thread"
    _description = "Yacht Service Records"

    active = fields.Boolean("Active?", default=True)
    quotation_create = fields.Boolean("Quotation Created", default=False)
    work_order_create = fields.Boolean("Workorder Created", default=False)
    has_related_sale_order = fields.Boolean(compute='_compute_has_related_sale_order', store=True)
    under_process = fields.Boolean("Under Process")
    yacht_name = fields.Char(string="Boat Name", required=True, tracking=True)
    related_payment_state = fields.Selection(
        selection=[
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
        ],
        string="Invoice Payment Status",
        compute="_compute_related_payment_state",
    )
    yacht_brand = fields.Char(
        string="Boat Brand", help="Monohull, Cat, Motorboat, etc."
    )
    yacht_type = fields.Selection(
        [("3", "Monohull"), ("2", "Multihull"), ("1", "Motor Yacht"), ("0", "Other")],
        "Boat Type",
        default="3",
        tracking=True,
    )
    type_txt = fields.Char("Other type")
    customer = fields.Many2one("res.partner", "Customer", required=True, tracking=True)
    ref = fields.Char(string="Reference", default=lambda self: _("New"))
    has_cc = fields.Boolean(
        string="Has CC",
    )
    description = fields.Text(string="Description", tracking=True)
    parts_requested = fields.Text(string="Parts Requested", tracking=True)
    attachment_field = fields.One2many(
        "ir.attachment",
        "res_id",
        string="Attachments",
        domain=[("res_model", "=", _name)],
        copy=False,
        tracking=True,
    )
    issue = fields.Text(string="Reason for Repair")
    company_id = fields.Many2one("res.company", string="Company")

    no_credit_card = fields.Boolean("No Credit Card", default=False)
    arc = fields.Boolean("Regatta", default=False, tracking=True)
    arc_number = fields.Char("Regatta Number", size=5)
    location = fields.Selection(
        [
            ("8", "A Pontoon"),
            ("7", "B Pontoon"),
            ("6", "C Pontoon"),
            ("5", "D Pontoon"),
            ("4", "E Pontoon"),
            ("3", "F Pontoon"),
            ("2", "Anchored"),
            ("1", "Other"),
            ("0", "Underway"),
        ],
        "Location",
        default="0",
        tracking=True,
    )
    location_txt = fields.Char("Location Text")
    eta = fields.Char(string="ETA")
    manager_id = fields.Many2one(
        "hr.employee",
        string="Job Manager",
        domain=[("is_supervisor", "=", True)],
    )
    mechanic_id = fields.Many2many(
        "hr.employee",
        "yacht_service_client_technician_rel",
        "service_client_id",
        "employee_id",
        string="Job Team",
        domain=[("is_mechanic", "=", True)],
    )
    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Normal"),
            ("2", " High"),
            ("3", "Higher"),
            ("4", "Highest"),
        ],
        compute="_compute_priority",
        store=True,
        default="1",
        tracking=True,
    )
    order_line_ids = fields.One2many(
        "part.order.line", "service_client_id", string="Order Lines"
    )
    time_line_ids = fields.One2many(
        "time.sheet.line", "service_client_id", string="Time Sheet"
    )
    # required fields for the sale_order_line
    customer_lead = fields.Float(
        string="Customer Lead Time"
    )  # Define the customer_lead field
    name = fields.Text(string="Description")
    order_id = fields.Many2one("sale.order", string="Sale Order")
    invoice_ids = fields.Many2one(
        "account.invoice", string="Related Invoice", readonly=True
    )
    price_unit = fields.Float(string="Unit Price")

    # fields for the email confirmation
    # confirmation_token = fields.Char("Confirmation Token", readonly=True)
    # invoice_paid = fields.Boolean(string='Invoice Paid', default=False)

    def set_under_process(self):
        if self.location == "0":  # Check if the location is 'Underway'
            warning_msg = "The boat is still underway! You cannot activate the Job!"
            raise UserError(warning_msg)
        else:
            self.write({"under_process": True})
            report = self.env.ref(
                "mda_yachtservice.print_support_request_yacht"
            )  # Fetching the report action
            if report:
                return report.report_action(
                    self
                )  # This will trigger the report generation
            else:
                return False

    @api.depends('ref')
    def _compute_related_payment_state(self):
        for record in self:
            if not record.ref:
                record.related_payment_state = 'not_paid'
                continue

            sale_order = self.env['sale.order'].search([('name', '=', record.ref)], limit=1)
            if sale_order:
                invoice = self.env['account.move'].search([
                    ('invoice_origin', '=', sale_order.name),
                    ('move_type', '=', 'out_invoice')
                ], order="invoice_date desc", limit=1)

                if invoice:
                    # The `payment_state` might include 'not_paid', 'in_payment', 'paid', 'partial'
                    record.related_payment_state = invoice.payment_state

                    # Set the `active` field to False if the payment state is 'paid'
                    if record.related_payment_state == 'paid':
                        record.active = False

                else:
                    record.related_payment_state = 'not_paid'
            else:
                record.related_payment_state = 'not_paid'

    @api.model_create_multi  # creates the sequence e.g. WO#12345
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("yacht.repair")
        return super(YachtServiceClient, self).create(vals_list)

    def create_quotation(self):
        SaleOrder = self.env["sale.order"]

        # Get the next number from the custom sequence
        next_sequence = self.env["ir.sequence"].next_by_code("sale.order.sequence")
        # Update the "quotation sent" field to True
        self.write({"quotation_create": True})

        sale_order = SaleOrder.create(
            {
                "partner_id": self.customer.id,  # Set the customer from your model
                "name": next_sequence,  # Set the sale order's name using the custom sequence
                "yacht_name": self.yacht_name,
            }
        )
        # Additional code to update the 'ref' field in your model with the 'name' value of the created sale order
        self.ref = sale_order.name
        # Create sale order lines based on your order_line_ids
        SaleOrderLine = self.env["sale.order.line"]
        TimeSheetLine = self.env["time.sheet.line"]

        # Create a quotation
        quotation = SaleOrder.create(
            {
                "partner_id": self.customer.id,  # Set the customer from your model
            }
        )

        # Create quotation lines based on PartOrderLine
        for order_line in self.order_line_ids:
            sale_order_line = SaleOrderLine.create(
                {
                    "order_id": sale_order.id,
                    "product_id": order_line.product_id.id,
                    "product_uom_qty": order_line.quantity,
                    "name": order_line.product_id.name
                            or "",  # Set the Description field
                    # Add other fields specific to your quotation lines
                }
            )

        # Create quotation lines based on TimeSheetLine
        for time_line in self.time_line_ids:
            SaleOrderLine.create(
                {
                    "order_id": sale_order.id,
                    "product_id": time_line.product_id.id,
                    "product_uom_qty": time_line.time,
                    "name": time_line.name
                            or "",  # Use the new "name" field for the description
                    # Add other fields specific to your quotation lines
                }
            )

        return {
            "name": _("Quotation Created"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order",
            "res_id": sale_order.id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "default_ref": self.ref  # Pass the updated 'ref' value to the quotation form
            },
        }

    def create_sale_order(self):
        SaleOrder = self.env["sale.order"]

        # Get the next number from the custom sequence
        next_sequence = self.env["ir.sequence"].next_by_code("sale.order.sequence")
        self.write({"work_order_create": True})

        sale_order = SaleOrder.create(
            {
                "partner_id": self.customer.id,  # Set the customer from your model
                "name": next_sequence,  # Set the sale order's name using the custom sequence
                "state": "sale",
                "yacht_name": self.yacht_name,
                # Add other fields specific to your sale order
            }
        )

        # Additional code to update the 'ref' field in your model with the 'name' value of the created sale order
        self.ref = sale_order.name
        # Create sale order lines based on your order_line_ids
        SaleOrderLine = self.env["sale.order.line"]
        TimeSheetLine = self.env["time.sheet.line"]

        for order_line in self.order_line_ids:
            sale_order_line = SaleOrderLine.create(
                {
                    "order_id": sale_order.id,
                    "product_id": order_line.product_id.id,
                    "product_uom_qty": order_line.quantity,
                    "name": order_line.product_id.name
                            or "",  # Set the Description field
                    # Add other fields specific to your sale order lines
                }
            )

        for time_line in self.time_line_ids:
            SaleOrderLine.create(
                {
                    "order_id": sale_order.id,
                    "product_id": time_line.product_id.id,
                    "product_uom_qty": time_line.time,
                    "name": time_line.name or "",  # Set the Description field
                    # Add other fields specific to your sale order lines
                }
            )

        return {
            "name": _("Sale Order Created"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order",
            "res_id": sale_order.id,
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "default_ref": self.ref  # Pass the updated 'ref' value to the quotation form
            },
        }

    @api.depends("has_cc", "arc", "location")
    def _compute_priority(self):
        try:
            for record in self:
                if record.has_cc and record.arc and record.location >= "3":
                    record["priority"] = "4"
                elif record.has_cc and record.location >= "3":
                    record["priority"] = "3"
                elif record.arc and record.location >= "3":
                    record["priority"] = "3"
                elif not record.has_cc and record.location >= "3":
                    record["priority"] = "2"
                elif record.location == "2" or record.location == "1":
                    record["priority"] = "1"
                else:
                    record["priority"] = "0"
        except:
            ValueError

    @api.depends("arc_number")
    def _compute_arc(self):
        for record in self:
            if record.arc_number:
                record.arc = True
            else:
                record.arc = False

    def action_open_related_sale_order(self):
        self.ensure_one()
        sale_order = self.env["sale.order"].search([("name", "=", self.ref)], limit=1)
        if sale_order:
            return {
                "name": _("Sale Order"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "sale.order",
                "res_id": sale_order.id,
                "target": "current",
            }
        else:
            raise UserError(_("No related sale order found."))

    @api.depends('ref')
    def _compute_has_related_sale_order(self):
        for record in self:
            sale_order = self.env['sale.order'].search([('name', '=', record.ref)], limit=1)
            record.has_related_sale_order = bool(sale_order)
