from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class TrainingPortal(CustomerPortal):

    @http.route(
        ["/my/training"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_training(self, **kwargs):

        partner = request.env.user.partner_id

        student = request.env["training.student"].sudo().search([
            ("partner_id", "=", partner.id)
        ], limit=1)

        enrollments = request.env["training.enrollment"].sudo()
        if student:
            enrollments = enrollments.search([
                ("student_id", "=", student.id)
            ])
        else:
            enrollments = enrollments.browse()

        available_courses = request.env["training.course"].sudo().search([
            ("state", "=", "confirmed"),
            ("available_seats", ">", 0),
        ])

        values = {
            "student": student,
            "enrollments": enrollments,
            "available_courses": available_courses,
            "page_name": "training",
        }

        return request.render(
            "Training_academy_management_system.portal_my_training",
            values
        )

    @http.route(
        ["/my/training/enrollment/<int:enrollment_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_training_enrollment_detail(
        self,
        enrollment_id,
        **kwargs
    ):

        partner = request.env.user.partner_id

        student = request.env[
            "training.student"
        ].sudo().search([
            ("partner_id", "=", partner.id)
        ], limit=1)

        enrollment = request.env[
            "training.enrollment"
        ].sudo().browse(enrollment_id)

        if not enrollment.exists():
            return request.not_found()

        if enrollment.student_id.id != student.id:
            return request.not_found()

        values = {
            "enrollment": enrollment,
            "page_name": "training_detail",
            "payment_success": False,
            "payment_error": False,
        }

        return request.render(
            "Training_academy_management_system.portal_training_enrollment_detail",
            values
        )
