from odoo import fields, models, api, _, exceptions
from odoo.exceptions import ValidationError


class PartOrderLine(models.Model):
    _name = 'part.order.line'
    _description = 'Part Order Line'

    service_client_id = fields.Many2one('yacht.service.client', string='Yacht Service Client')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('detailed_type', 'in', ['product', 'consu'])]")
    quantity = fields.Float(string='Quantity', default="1")
    related_price_unit = fields.Float(related='product_id.lst_price', string='Related Price Unit', store=True)

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_("Quantities can't be zero."))
