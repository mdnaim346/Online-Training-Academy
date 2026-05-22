from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class TrainingPortal(CustomerPortal):

    def _get_current_portal_students(self):
        partner = request.env.user.partner_id
        emails = [email for email in {partner.email, request.env.user.login} if email]
        domain = [("partner_id", "=", partner.id)]
        if emails:
            domain = ["|", ("partner_id", "=", partner.id), ("email", "in", emails)]
        return request.env["training.student"].sudo().search(domain)

    @http.route(
        ["/my/training"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_training(self, **kwargs):

        students = self._get_current_portal_students()
        student = students[:1]

        enrollments = request.env["training.enrollment"].sudo()
        if students:
            enrollments = enrollments.search([
                ("student_id", "in", students.ids)
            ])
        else:
            enrollments = enrollments.browse()

        available_courses = request.env["training.course"].sudo().search([
            ("state", "=", "confirmed"),
            ("available_seats", ">", 0),
        ])
        enrollments_by_course = {
            enrollment.course_id.id: enrollment
            for enrollment in enrollments
        }

        values = {
            "student": student,
            "enrollments": enrollments,
            "available_courses": available_courses,
            "enrollments_by_course": enrollments_by_course,
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

        students = self._get_current_portal_students()

        enrollment = request.env[
            "training.enrollment"
        ].sudo().browse(enrollment_id)

        if not enrollment.exists():
            return request.not_found()

        if enrollment.student_id not in students:
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
