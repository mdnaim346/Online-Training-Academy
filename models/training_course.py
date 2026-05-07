from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TrainingCourse(models.Model):
    _name = "training.course"
    _description = "Training Course"
    _order = "start_date desc, name asc"

    name = fields.Char(string="Course Name", required=True)
    code = fields.Char(string="Course Code", readonly=True, copy=False)

    trainer_name = fields.Char(string="Trainer Name")
    start_date = fields.Date(string="Start Date")
    duration_days = fields.Integer(string="Duration Days", default=1)

    fee = fields.Float(string="Course Fee")
    discount = fields.Float(string="Discount")
    final_fee = fields.Float(
        string="Final Fee",
        compute="_compute_final_fee",
        store=True,
    )

    max_students = fields.Integer(string="Maximum Students")
    enrolled_students = fields.Integer(string="Enrolled Students")
    available_seats = fields.Integer(
        string="Available Seats",
        compute="_compute_available_seats",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
    )
    enrollment_ids = fields.One2many(
        "training.enrollment",
        "course_id",
        string="Enrollments",
    )

    enrollment_count = fields.Integer(
        string="Enrollments",
        compute="_compute_enrollment_count",
    )

    def _compute_enrollment_count(self):
     for rec in self:
        rec.enrollment_count = len(rec.enrollment_ids)

    def action_open_enrollments(self):
     self.ensure_one()
     return {
            "type": "ir.actions.act_window",
            "name": "Course Enrollments",
            "res_model": "training.enrollment",
            "view_mode": "tree,form",
            "domain": [("course_id", "=", self.id)],
            "context": {"default_course_id": self.id},
        }
    @api.depends("fee", "discount")
    def _compute_final_fee(self):
        for rec in self:
            rec.final_fee = rec.fee - rec.discount

    @api.depends("max_students", "enrolled_students")
    def _compute_available_seats(self):
        for rec in self:
            rec.available_seats = rec.max_students - rec.enrolled_students

    @api.constrains("fee", "discount", "duration_days", "max_students", "enrolled_students")
    def _check_course_values(self):
        for rec in self:
            if rec.fee < 0:
                raise ValidationError("Course fee cannot be negative.")

            if rec.discount < 0:
                raise ValidationError("Discount cannot be negative.")

            if rec.discount > rec.fee:
                raise ValidationError("Discount cannot be greater than fee.")

            if rec.duration_days <= 0:
                raise ValidationError("Duration must be greater than zero.")

            if rec.max_students < 0:
                raise ValidationError("Maximum students cannot be negative.")

            if rec.enrolled_students < 0:
                raise ValidationError("Enrolled students cannot be negative.")

            if rec.enrolled_students > rec.max_students:
                raise ValidationError("Enrolled students cannot exceed maximum students.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self.env["ir.sequence"].next_by_code(
                    "training.course"
                ) or "NEW"

        return super().create(vals_list)

    def write(self, vals):
        if "fee" in vals and vals["fee"] < 0:
            raise ValidationError("Course fee cannot be negative.")

        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == "confirmed":
                raise ValidationError("You cannot delete a confirmed course.")

        return super().unlink()

    def action_confirm(self):
        for rec in self:
            rec.state = "confirmed"

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"