from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TrainingEnrollment(models.Model):
    _name = "training.enrollment"
    _description = "Training Enrollment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "enrollment_date desc"

    student_id = fields.Many2one(
        "training.student",
        string="Student",
        required=True,
        ondelete="restrict",
        tracking=True,
    )

    course_id = fields.Many2one(
        "training.course",
        string="Course",
        required=True,
        ondelete="restrict",
        tracking=True,
    )

    enrollment_date = fields.Date(
        string="Enrollment Date",
        default=fields.Date.today,
        tracking=True,
    )

    course_fee = fields.Float(
        string="Course Fee",
        related="course_id.final_fee",
        store=True,
        readonly=True,
    )

    paid_amount = fields.Float(
        string="Paid Amount",
        tracking=True,
    )

    due_amount = fields.Float(
        string="Due Amount",
        compute="_compute_due_amount",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting_approval", "Waiting Approval"),
            ("confirmed", "Confirmed"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    certificate_number = fields.Char(
        string="Certificate Number",
        readonly=True,
        copy=False,
    )

    completion_date = fields.Date(
        string="Completion Date",
    )
    attendance_percentage = fields.Float(
        string="Attendance %",
        compute="_compute_attendance_percentage",
        store=True,
    )

    total_sessions = fields.Integer(
        string="Total Sessions",
        compute="_compute_attendance_percentage",
        store=True,
    )

    present_sessions = fields.Integer(
        string="Present Sessions",
        compute="_compute_attendance_percentage",
        store=True,
    )

    @api.depends("student_id", "course_id")
    def _compute_attendance_percentage(self):
        for rec in self:
            lines = self.env["training.attendance.line"].search([
                ("student_id", "=", rec.student_id.id),
                ("course_id", "=", rec.course_id.id),
                ("session_id.state", "=", "confirmed"),
            ])

            total = len(lines)
            present = len(lines.filtered(lambda line: line.status == "present"))

            rec.total_sessions = total
            rec.present_sessions = present

            if total:
                rec.attendance_percentage = (present / total) * 100
            else:
                rec.attendance_percentage = 0

    @api.depends("course_fee", "paid_amount")
    def _compute_due_amount(self):
        for rec in self:
            rec.due_amount = rec.course_fee - rec.paid_amount

    @api.constrains("paid_amount")
    def _check_paid_amount(self):
        for rec in self:
            if rec.paid_amount < 0:
                raise ValidationError("Paid amount cannot be negative.")

            if rec.course_fee and rec.paid_amount > rec.course_fee:
                raise ValidationError("Paid amount cannot be greater than course fee.")

    def action_submit_for_approval(self):
        for rec in self:
            if not rec.student_id:
                raise ValidationError("Please select a student.")

            if not rec.course_id:
                raise ValidationError("Please select a course.")

            if rec.course_id.available_seats <= 0:
                raise ValidationError("No available seats for this course.")

            rec.state = "waiting_approval"

            rec.message_post(
                body=f"""
                    Enrollment submitted for approval.<br/>
                    Student: <b>{rec.student_id.name}</b><br/>
                    Course: <b>{rec.course_id.name}</b>
                """
            )

            rec._create_approval_activity()

    def action_approve(self):
        for rec in self:
            if not self.env.user.has_group("Training_academy_management_system.group_training_manager"):
                raise UserError("Only Training Managers can approve enrollments.")

            if rec.state != "waiting_approval":
                raise ValidationError("Only waiting approval enrollments can be approved.")

            if rec.course_id.available_seats <= 0:
                raise ValidationError("No available seats for this course.")

            rec.state = "confirmed"
            rec.course_id.enrolled_students += 1

            rec.message_post(
                body=f"""
                    Enrollment approved by <b>{self.env.user.name}</b>.<br/>
                    Student: <b>{rec.student_id.name}</b><br/>
                    Course: <b>{rec.course_id.name}</b>
                """
            )

            rec._mark_approval_activities_done()

    def action_mark_paid(self):
        for rec in self:

            if rec.state != "confirmed":
                raise ValidationError(
                    "Only confirmed enrollments can be marked as paid."
                )

            if rec.paid_amount < rec.course_fee:
                raise ValidationError("Paid amount is less than course fee.")

            if rec.attendance_percentage < 80:
                raise ValidationError(
                    "Certificate cannot be generated because attendance is below 80%."
                )

            rec.state = "paid"
            rec.completion_date = fields.Date.today()

            if not rec.certificate_number:
                rec.certificate_number = self.env[
                    "ir.sequence"
                ].next_by_code(
                    "training.certificate"
                )

            rec.message_post(
                body=f"""
                    Payment completed.<br/>
                    Certificate generated:
                    <b>{rec.certificate_number}</b>
                """
            )

    def action_cancel(self):
        for rec in self:
            if rec.state in ("confirmed", "paid"):
                rec.course_id.enrolled_students -= 1

            rec.state = "cancelled"

            rec.message_post(
                body="Enrollment has been cancelled."
            )

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ("cancelled", "waiting_approval"):
                raise ValidationError("Only cancelled or waiting approval records can be reset.")

            rec.state = "draft"

            rec.message_post(
                body="Enrollment reset to draft."
            )

    def _create_approval_activity(self):
        activity_type = self.env.ref("mail.mail_activity_data_todo")

        manager_group = self.env.ref(
            "Training_academy_management_system.group_training_manager",
            raise_if_not_found=False,
        )

        managers = manager_group.users if manager_group else self.env.user

        for rec in self:
            for manager in managers:
                self.env["mail.activity"].create({
                    "activity_type_id": activity_type.id,
                    "summary": "Enrollment Approval Required",
                    "note": f"Please approve enrollment for {rec.student_id.name}.",
                    "user_id": manager.id,
                    "res_id": rec.id,
                    "res_model_id": self.env["ir.model"]._get_id("training.enrollment"),
                    "date_deadline": fields.Date.today(),
                })

    def _mark_approval_activities_done(self):
        for rec in self:
            activities = self.env["mail.activity"].search([
                ("res_model", "=", "training.enrollment"),
                ("res_id", "=", rec.id),
                ("summary", "=", "Enrollment Approval Required"),
            ])
            activities.action_done()

    def _cron_followup_due_payments(self):
        enrollments = self.search([
            ("state", "=", "confirmed"),
            ("due_amount", ">", 0),
        ])

        activity_type = self.env.ref("mail.mail_activity_data_todo")

        for enrollment in enrollments:
            existing_activity = self.env["mail.activity"].search([
                ("res_model", "=", "training.enrollment"),
                ("res_id", "=", enrollment.id),
                ("summary", "=", "Payment Follow-up Required"),
            ], limit=1)

            if existing_activity:
                continue

            self.env["mail.activity"].create({
                "activity_type_id": activity_type.id,
                "summary": "Payment Follow-up Required",
                "note": f"Follow up payment for {enrollment.student_id.name}.",
                "user_id": self.env.user.id,
                "res_id": enrollment.id,
                "res_model_id": self.env["ir.model"]._get_id("training.enrollment"),
                "date_deadline": fields.Date.today(),
            })
