from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TrainingAttendanceSession(models.Model):
    _name = "training.attendance.session"
    _description = "Training Attendance Session"
    _order = "session_date desc"

    name = fields.Char(
        string="Session Name",
        required=True,
    )

    course_id = fields.Many2one(
        "training.course",
        string="Course",
        required=True,
        ondelete="restrict",
    )

    session_date = fields.Date(
        string="Session Date",
        default=fields.Date.today,
        required=True,
    )

    attendance_line_ids = fields.One2many(
        "training.attendance.line",
        "session_id",
        string="Attendance Lines",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        string="Status",
    )

    def action_generate_students(self):
        for rec in self:
            if not rec.course_id:
                raise ValidationError("Please select a course first.")

            enrollments = self.env["training.enrollment"].search([
                ("course_id", "=", rec.course_id.id),
                ("state", "in", ["confirmed", "paid"]),
            ])

            existing_students = rec.attendance_line_ids.mapped("student_id")

            for enrollment in enrollments:
                if enrollment.student_id not in existing_students:
                    self.env["training.attendance.line"].create({
                        "session_id": rec.id,
                        "student_id": enrollment.student_id.id,
                        "enrollment_id": enrollment.id,
                        "status": "present",
                    })

    def action_confirm(self):
        for rec in self:
            if not rec.attendance_line_ids:
                raise ValidationError("Please generate attendance lines first.")
            rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = "draft"


class TrainingAttendanceLine(models.Model):
    _name = "training.attendance.line"
    _description = "Training Attendance Line"
    _order = "student_id asc"

    session_id = fields.Many2one(
        "training.attendance.session",
        string="Session",
        required=True,
        ondelete="cascade",
    )

    course_id = fields.Many2one(
        related="session_id.course_id",
        string="Course",
        store=True,
        readonly=True,
    )

    session_date = fields.Date(
        related="session_id.session_date",
        string="Session Date",
        store=True,
        readonly=True,
    )

    student_id = fields.Many2one(
        "training.student",
        string="Student",
        required=True,
        ondelete="restrict",
    )

    enrollment_id = fields.Many2one(
        "training.enrollment",
        string="Enrollment",
        ondelete="restrict",
    )

    status = fields.Selection(
        [
            ("present", "Present"),
            ("absent", "Absent"),
        ],
        string="Status",
        default="present",
        required=True,
    )

    note = fields.Char(string="Note")