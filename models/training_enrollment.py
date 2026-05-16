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
        compute="_compute_payment_amounts",
        store=True,
        tracking=True,
    )

    due_amount = fields.Float(
        string="Due Amount",
        compute="_compute_payment_amounts",
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

    attendance_line_ids = fields.One2many(
        "training.attendance.line",
        "enrollment_id",
        string="Attendance Lines",
    )

    attendance_warning_sent = fields.Boolean(
        string="Attendance Warning Sent",
        copy=False,
    )

    payment_ids = fields.One2many(
        "training.payment",
        "enrollment_id",
        string="Payments",
    )

    payment_count = fields.Integer(
        string="Payment Count",
        compute="_compute_payment_count",
    )

    online_transaction_ids = fields.One2many(
        "training.payment.transaction",
        "enrollment_id",
        string="Online Transactions",
    )

    latest_online_transaction_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        string="Latest Online Payment Status",
        compute="_compute_latest_online_transaction_state",
    )

    @api.depends(
        "attendance_line_ids.status",
        "attendance_line_ids.session_id.state",
        "student_id",
        "course_id",
    )
    def _compute_attendance_percentage(self):
        for rec in self:
            if not rec.student_id or not rec.course_id:
                rec.total_sessions = 0
                rec.present_sessions = 0
                rec.attendance_percentage = 0
                continue

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

    @api.depends("course_fee", "payment_ids.amount", "payment_ids.state")
    def _compute_payment_amounts(self):
        for rec in self:
            paid_amount = sum(
                rec.payment_ids.filtered(
                    lambda payment: payment.state != "cancelled"
                ).mapped("amount")
            )
            rec.paid_amount = paid_amount
            rec.due_amount = rec.course_fee - rec.paid_amount

    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    @api.depends("online_transaction_ids.state")
    def _compute_latest_online_transaction_state(self):
        for rec in self:
            transaction = rec.online_transaction_ids[:1]
            rec.latest_online_transaction_state = transaction.state if transaction else False

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
            rec._send_notification_template(
                "Training_academy_management_system.email_template_enrollment_submitted"
            )

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
            rec._send_notification_template(
                "Training_academy_management_system.email_template_enrollment_approved"
            )

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
            rec._send_notification_template(
                "Training_academy_management_system.email_template_certificate_generated"
            )

    def _finalize_paid_enrollment_if_ready(self):
        for rec in self:
            if rec.state != "confirmed" or rec.paid_amount < rec.course_fee:
                continue

            rec.state = "paid"
            rec.completion_date = fields.Date.today()

            if (
                not rec.certificate_number
                and (rec.total_sessions == 0 or rec.attendance_percentage >= 80)
            ):
                rec.certificate_number = self.env["ir.sequence"].next_by_code(
                    "training.certificate"
                )
                rec._send_notification_template(
                    "Training_academy_management_system.email_template_certificate_generated"
                )

            rec.message_post(
                body=f"""
                    Online payment completed.<br/>
                    Paid amount: <b>{rec.paid_amount}</b>
                """
            )

    def action_create_stripe_checkout(self):
        self.ensure_one()

        if self.state != "confirmed":
            raise ValidationError("Only confirmed enrollments can be paid online.")

        if self.due_amount <= 0:
            raise ValidationError("This enrollment has no due amount.")

        transaction = self.env["training.payment.transaction"].create({
            "enrollment_id": self.id,
            "amount": self.due_amount,
        })
        checkout_url = transaction.action_create_stripe_checkout_session()

        return {
            "type": "ir.actions.act_url",
            "url": checkout_url,
            "target": "self",
        }

    def action_open_payments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Payments",
            "res_model": "training.payment",
            "view_mode": "tree,form",
            "domain": [("enrollment_id", "=", self.id)],
            "context": {
                "default_enrollment_id": self.id,
                "default_amount": self.due_amount if self.due_amount > 0 else 0,
            },
        }

    def action_add_payment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Add Payment",
            "res_model": "training.payment",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_enrollment_id": self.id,
                "default_amount": self.due_amount if self.due_amount > 0 else 0,
            },
        }

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

    def _send_notification_template(self, template_xmlid):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if not template:
            return

        for rec in self:
            if not rec.student_id.email:
                continue

            rec.with_context(force_send=True).message_post_with_source(
                template,
                email_layout_xmlid="mail.mail_notification_light",
                subtype_xmlid="mail.mt_comment",
            )

    def _send_attendance_warning_if_needed(self):
        for rec in self:
            if rec.total_sessions <= 0 or rec.state not in ("confirmed", "paid"):
                continue

            if rec.attendance_percentage < 80:
                if rec.attendance_warning_sent:
                    continue

                rec._send_notification_template(
                    "Training_academy_management_system.email_template_attendance_warning"
                )
                rec.attendance_warning_sent = True
            elif rec.attendance_warning_sent:
                rec.attendance_warning_sent = False
