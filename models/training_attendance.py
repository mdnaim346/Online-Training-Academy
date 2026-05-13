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
            rec.attendance_line_ids.mapped("enrollment_id")._compute_attendance_percentage()

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

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_enrollment()
        lines.mapped("enrollment_id")._compute_attendance_percentage()
        return lines

    def write(self, vals):
        enrollments = self.mapped("enrollment_id")
        result = super().write(vals)
        if not self.env.context.get("skip_attendance_enrollment_sync"):
            self._sync_enrollment()
        (enrollments | self.mapped("enrollment_id"))._compute_attendance_percentage()
        return result

    def unlink(self):
        enrollments = self.mapped("enrollment_id")
        result = super().unlink()
        enrollments._compute_attendance_percentage()
        return result

    def _sync_enrollment(self):
        for line in self:
            if not line.student_id or not line.course_id:
                continue

            enrollment = self.env["training.enrollment"].search([
                ("student_id", "=", line.student_id.id),
                ("course_id", "=", line.course_id.id),
                ("state", "in", ["confirmed", "paid"]),
            ], limit=1)

            if line.enrollment_id != enrollment:
                line.with_context(skip_attendance_enrollment_sync=True).enrollment_id = enrollment
