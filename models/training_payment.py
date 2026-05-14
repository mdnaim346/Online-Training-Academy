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

    payment_notification_sent = fields.Boolean(
        string="Payment Notification Sent",
        copy=False,
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
        payments.filtered(lambda payment: payment.state == "posted")._send_payment_confirmed_email()
        return payments

    def write(self, vals):
        result = super().write(vals)
        self._check_enrollment_overpayment()
        if vals.get("state") == "posted":
            self._send_payment_confirmed_email()
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

    def _send_payment_confirmed_email(self):
        template = self.env.ref(
            "Training_academy_management_system.email_template_payment_confirmed",
            raise_if_not_found=False,
        )
        if not template:
            return

        for rec in self:
            if rec.payment_notification_sent or not rec.student_id.email:
                continue

            rec.with_context(force_send=True).message_post_with_source(
                template,
                email_layout_xmlid="mail.mail_notification_light",
                subtype_xmlid="mail.mt_comment",
            )
            rec.payment_notification_sent = True
