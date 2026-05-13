from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TrainingPayment(models.Model):
    _name = "training.payment"
    _description = "Training Payment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "payment_date desc, id desc"

    name = fields.Char(
        string="Receipt Number",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )

    enrollment_id = fields.Many2one(
        "training.enrollment",
        string="Enrollment",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    student_id = fields.Many2one(
        related="enrollment_id.student_id",
        string="Student",
        store=True,
        readonly=True,
    )

    course_id = fields.Many2one(
        related="enrollment_id.course_id",
        string="Course",
        store=True,
        readonly=True,
    )

    payment_date = fields.Date(
        string="Payment Date",
        default=fields.Date.today,
        required=True,
        tracking=True,
    )

    amount = fields.Float(
        string="Amount",
        required=True,
        tracking=True,
    )

    payment_method = fields.Selection(
        [
            ("cash", "Cash"),
            ("bank", "Bank Transfer"),
            ("card", "Card"),
            ("mobile", "Mobile Banking"),
            ("other", "Other"),
        ],
        string="Payment Method",
        default="cash",
        required=True,
        tracking=True,
    )

    reference = fields.Char(
        string="Reference",
        tracking=True,
    )

    note = fields.Text(string="Note")

    state = fields.Selection(
        [
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="posted",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "training.payment"
                ) or "New"

        payments = super().create(vals_list)
        payments._check_enrollment_overpayment()
        return payments

    def write(self, vals):
        result = super().write(vals)
        self._check_enrollment_overpayment()
        return result

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Payment amount must be greater than zero.")

    def _check_enrollment_overpayment(self):
        for enrollment in self.mapped("enrollment_id"):
            if enrollment.course_fee and enrollment.paid_amount > enrollment.course_fee:
                raise ValidationError(
                    "Total payment cannot be greater than the course fee."
                )

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_set_posted(self):
        for rec in self:
            rec.state = "posted"
