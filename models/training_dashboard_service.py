from odoo import api, fields, models


class TrainingDashboardService(models.AbstractModel):
    _name = "training.dashboard.service"
    _description = "Training Dashboard Service"

    @api.model
    def get_dashboard_data(self):
        user = self.env.user
        is_manager = user.has_group(
            "Training_academy_management_system.group_training_manager"
        )
        is_training_user = user.has_group(
            "Training_academy_management_system.group_training_user"
        )
        is_portal = user.has_group("base.group_portal") and not is_training_user

        if is_portal:
            return self._get_portal_dashboard_data()

        data = {
            "is_manager": is_manager,
            "is_portal": False,
            "total_courses": self.env["training.course"].search_count([]),
            "total_students": self.env["training.student"].search_count([]),
            "total_trainers": self.env["training.trainer"].search_count([]),
            "total_enrollments": self.env["training.enrollment"].search_count([]),
            "attendance_sessions": self.env["training.attendance.session"].search_count([]),
            "today_activities": self.env["mail.activity"].search_count([
                ("user_id", "=", user.id),
                ("date_deadline", "<=", fields.Date.today()),
            ]),
            "draft_enrollments": self.env["training.enrollment"].search_count([
                ("state", "=", "draft"),
            ]),
            "waiting_approval": self.env["training.enrollment"].search_count([
                ("state", "=", "waiting_approval"),
            ]),
            "confirmed_enrollments": self.env["training.enrollment"].search_count([
                ("state", "=", "confirmed"),
            ]),
            "paid_enrollments": self.env["training.enrollment"].search_count([
                ("state", "=", "paid"),
            ]),
            "cancelled_enrollments": self.env["training.enrollment"].search_count([
                ("state", "=", "cancelled"),
            ]),
            "latest_enrollments": self._get_latest_enrollments(),
        }

        if is_manager:
            data.update(self._get_manager_metrics())

        return data

    def _get_manager_metrics(self):
        posted_payments = self.env["training.payment"].search([
            ("state", "=", "posted"),
        ])
        due_enrollments = self.env["training.enrollment"].search([
            ("state", "=", "confirmed"),
            ("due_amount", ">", 0),
        ])
        attendance_risk = self.env["training.enrollment"].search([
            ("state", "in", ["confirmed", "paid"]),
            ("total_sessions", ">", 0),
            ("attendance_percentage", "<", 80),
        ])

        return {
            "total_revenue": sum(posted_payments.mapped("amount")),
            "total_due": sum(due_enrollments.mapped("due_amount")),
            "pending_payments": len(due_enrollments),
            "certificates_issued": self.env["training.enrollment"].search_count([
                ("certificate_number", "!=", False),
            ]),
            "attendance_risk_students": len(attendance_risk),
        }

    def _get_latest_enrollments(self):
        enrollments = self.env["training.enrollment"].search([], limit=5, order="id desc")
        return [
            {
                "id": enrollment.id,
                "student": enrollment.student_id.name,
                "course": enrollment.course_id.name,
                "paid_amount": enrollment.paid_amount,
                "due_amount": enrollment.due_amount,
                "state": enrollment.state,
            }
            for enrollment in enrollments
        ]

    def _get_portal_dashboard_data(self):
        student = self.env["training.student"].sudo().search([
            ("partner_id", "=", self.env.user.partner_id.id),
        ], limit=1)
        enrollments = self.env["training.enrollment"].sudo().search([
            ("student_id", "=", student.id),
        ])

        return {
            "is_manager": False,
            "is_portal": True,
            "total_enrollments": len(enrollments),
            "confirmed_enrollments": len(enrollments.filtered(
                lambda enrollment: enrollment.state == "confirmed"
            )),
            "paid_enrollments": len(enrollments.filtered(
                lambda enrollment: enrollment.state == "paid"
            )),
            "latest_enrollments": [
                {
                    "id": enrollment.id,
                    "student": enrollment.student_id.name,
                    "course": enrollment.course_id.name,
                    "paid_amount": enrollment.paid_amount,
                    "due_amount": enrollment.due_amount,
                    "state": enrollment.state,
                }
                for enrollment in enrollments[:5]
            ],
        }
