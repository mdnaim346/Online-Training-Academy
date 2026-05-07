from odoo import fields, models
from odoo.exceptions import ValidationError


class TrainingEnrollment(models.Model):
    _name = "training.enrollment"
    _description = "Training Enrollment"
    _order = "enrollment_date desc"

    student_id = fields.Many2one(
        "training.student",
        string="Student",
        required=True,
        ondelete="restrict",
    )

    course_id = fields.Many2one(
        "training.course",
        string="Course",
        required=True,
        ondelete="restrict",
    )

    enrollment_date = fields.Date(
        string="Enrollment Date",
        default=fields.Date.today,
    )

    course_fee = fields.Float(
        string="Course Fee",
        related="course_id.final_fee",
        store=True,
        readonly=True,
    )

    paid_amount = fields.Float(string="Paid Amount")

    due_amount = fields.Float(
        string="Due Amount",
        compute="_compute_due_amount",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
    )

    def _compute_due_amount(self):
        for rec in self:
            rec.due_amount = rec.course_fee - rec.paid_amount

    def action_confirm(self):
        for rec in self:
            if rec.course_id.available_seats <= 0:
                raise ValidationError("No available seats for this course.")

            rec.state = "confirmed"
            rec.course_id.enrolled_students += 1

    def action_mark_paid(self):
        for rec in self:
            if rec.paid_amount < rec.course_fee:
                raise ValidationError("Paid amount is less than course fee.")

            rec.state = "paid"

    def action_cancel(self):
        for rec in self:
            if rec.state in ("confirmed", "paid"):
                rec.course_id.enrolled_students -= 1

            rec.state = "cancelled"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"