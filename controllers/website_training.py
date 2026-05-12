from odoo import http
from odoo.http import request


class WebsiteTraining(http.Controller):

    @http.route("/training/courses", type="http", auth="public", website=True)
    def website_courses(self, **kwargs):
        courses = request.env["training.course"].sudo().search([
            ("state", "=", "confirmed"),
            ("available_seats", ">", 0),
        ])

        return request.render(
            "Training_academy_management_system.website_training_courses",
            {
                "courses": courses,
            }
        )

    @http.route("/training/course/<int:course_id>", type="http", auth="public", website=True)
    def website_course_detail(self, course_id, **kwargs):
        course = request.env["training.course"].sudo().browse(course_id)

        if not course.exists():
            return request.not_found()

        return request.render(
            "Training_academy_management_system.website_training_course_detail",
            {
                "course": course,
            }
        )

    @http.route("/training/course/<int:course_id>/enroll", type="http", auth="public", website=True)
    def website_course_enroll_form(self, course_id, **kwargs):
        course = request.env["training.course"].sudo().browse(course_id)

        if not course.exists():
            return request.not_found()

        return request.render(
            "Training_academy_management_system.website_training_enroll_form",
            {
                "course": course,
                "error": False,
            }
        )

    @http.route(
        "/training/course/<int:course_id>/enroll/submit",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def website_course_enroll_submit(self, course_id, **post):
        course = request.env["training.course"].sudo().browse(course_id)

        if not course.exists():
            return request.not_found()

        name = post.get("name")
        email = post.get("email")
        phone = post.get("phone")
        address = post.get("address")

        if not name:
            return request.render(
                "Training_academy_management_system.website_training_enroll_form",
                {
                    "course": course,
                    "error": "Student name is required.",
                }
            )

        if course.available_seats <= 0:
            return request.render(
                "Training_academy_management_system.website_training_enroll_form",
                {
                    "course": course,
                    "error": "No available seats for this course.",
                }
            )

        partner = request.env["res.partner"].sudo().create({
            "name": name,
            "email": email,
            "phone": phone,
        })

        student = request.env["training.student"].sudo().create({
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "partner_id": partner.id,
        })

        enrollment = request.env["training.enrollment"].sudo().create({
            "student_id": student.id,
            "course_id": course.id,
        })

        enrollment.action_submit_for_approval()

        return request.render(
            "Training_academy_management_system.website_training_enroll_success",
            {
                "student": student,
                "course": course,
                "enrollment": enrollment,
            }
        )
