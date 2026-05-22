from odoo import http
from odoo.http import request


class WebsiteTraining(http.Controller):

    def _get_current_portal_students(self):
        if request.env.user._is_public():
            return request.env["training.student"].sudo().browse()

        partner = request.env.user.partner_id
        emails = [email for email in {partner.email, request.env.user.login} if email]
        domain = [("partner_id", "=", partner.id)]
        if emails:
            domain = ["|", ("partner_id", "=", partner.id), ("email", "in", emails)]
        return request.env["training.student"].sudo().search(domain)

    def _get_current_course_enrollment(self, course):
        students = self._get_current_portal_students()
        if not students:
            return request.env["training.enrollment"].sudo().browse()

        return request.env["training.enrollment"].sudo().search([
            ("student_id", "in", students.ids),
            ("course_id", "=", course.id),
            ("state", "!=", "cancelled"),
        ], order="id desc", limit=1)

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
                "course_enrollment": self._get_current_course_enrollment(course),
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

        existing_enrollment = self._get_current_course_enrollment(course)
        if existing_enrollment:
            if not request.env.user._is_public():
                return request.redirect(
                    "/my/training/enrollment/%s" % existing_enrollment.id
                )
            return request.render(
                "Training_academy_management_system.website_training_enroll_form",
                {
                    "course": course,
                    "error": "You already have an enrollment for this course.",
                }
            )

        if request.env.user._is_public():
            partner = request.env["res.partner"].sudo().create({
                "name": name,
                "email": email,
                "phone": phone,
            })
        else:
            partner = request.env.user.partner_id
            partner.sudo().write({
                "name": partner.name or name,
                "email": partner.email or email,
                "phone": partner.phone or phone,
            })

        student = request.env["training.student"].sudo().search([
            ("partner_id", "=", partner.id),
        ], limit=1)

        if not student and email:
            student = request.env["training.student"].sudo().search([
                ("email", "=", email),
            ], limit=1)

        student_values = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "partner_id": partner.id,
        }
        if student:
            student.write(student_values)
        else:
            student = request.env["training.student"].sudo().create(student_values)

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
