from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TimeSheetLine(models.Model):
    _name = 'time.sheet.line'
    _description = 'Time Sheet Line'

    service_client_id = fields.Many2one('yacht.service.client', string='Yacht Service Client')
    mechanic_id = fields.Many2one('hr.employee', string='Technician')
    product_id = fields.Many2one('product.product', string='Fees', domain="[('detailed_type', '=', 'service')]")
    name = fields.Char(string='Description', required=False)
    time = fields.Float(string='Time', default=1)
    related_price_unit = fields.Float(related='product_id.lst_price', string='Related Price Unit', store=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    def float_time_convert(self):
        factor = self.time < 0 and -1 or 1
        val = abs(self.time)
        time = (factor * int(math.floor(val)), int(round((val % 1) * 60)))
        str1 = str(time)
        removestr1 = str1.strip("(")
        removestr2 = removestr1.strip(")")
        removestr3 = removestr2.replace(",", ":")
        return removestr3