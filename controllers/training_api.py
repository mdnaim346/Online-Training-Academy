import json

from odoo import http
from odoo.http import request


class TrainingAcademyAPI(http.Controller):

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data),
            headers=[
                ("Content-Type", "application/json"),
            ],
            status=status,
        )

    @http.route(
        "/training/api/courses",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def get_courses(self, **kwargs):
        courses = request.env["training.course"].sudo().search([])

        result = []

        for course in courses:
            result.append({
                "id": course.id,
                "code": course.code,
                "name": course.name,
                "trainer": course.trainer_id.name if course.trainer_id else "",
                "start_date": str(course.start_date) if course.start_date else "",
                "duration_days": course.duration_days,
                "fee": course.fee,
                "discount": course.discount,
                "final_fee": course.final_fee,
                "max_students": course.max_students,
                "enrolled_students": course.enrolled_students,
                "available_seats": course.available_seats,
                "state": course.state,
            })

        return self._json_response({
            "success": True,
            "count": len(result),
            "courses": result,
        })

    @http.route(
        "/training/api/courses/<int:course_id>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def get_course_detail(self, course_id, **kwargs):
        course = request.env["training.course"].sudo().browse(course_id)

        if not course.exists():
            return self._json_response({
                "success": False,
                "message": "Course not found.",
            }, status=404)

        data = {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "trainer": course.trainer_id.name if course.trainer_id else "",
            "start_date": str(course.start_date) if course.start_date else "",
            "duration_days": course.duration_days,
            "fee": course.fee,
            "discount": course.discount,
            "final_fee": course.final_fee,
            "max_students": course.max_students,
            "enrolled_students": course.enrolled_students,
            "available_seats": course.available_seats,
            "state": course.state,
            "enrollments": [
                {
                    "student": enrollment.student_id.name,
                    "state": enrollment.state,
                    "paid_amount": enrollment.paid_amount,
                    "due_amount": enrollment.due_amount,
                }
                for enrollment in course.enrollment_ids
            ],
        }

        return self._json_response({
            "success": True,
            "course": data,
        })

    @http.route(
        "/training/api/students/create",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def create_student(self, **kwargs):
        data = request.jsonrequest or {}

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        address = data.get("address")

        if not name:
            return {
                "success": False,
                "message": "Student name is required.",
            }

        student = request.env["training.student"].sudo().create({
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
        })

        return {
            "success": True,
            "message": "Student created successfully.",
            "student": {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "phone": student.phone,
            },
        }

    @http.route(
        "/training/api/enrollments/create",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def create_enrollment(self, **kwargs):
        data = request.jsonrequest or {}

        student_id = data.get("student_id")
        course_id = data.get("course_id")

        if not student_id:
            return {
                "success": False,
                "message": "student_id is required.",
            }

        if not course_id:
            return {
                "success": False,
                "message": "course_id is required.",
            }

        student = request.env["training.student"].sudo().browse(student_id)
        course = request.env["training.course"].sudo().browse(course_id)

        if not student.exists():
            return {
                "success": False,
                "message": "Student not found.",
            }

        if not course.exists():
            return {
                "success": False,
                "message": "Course not found.",
            }

        if course.available_seats <= 0:
            return {
                "success": False,
                "message": "No available seats for this course.",
            }

        enrollment = request.env["training.enrollment"].sudo().create({
            "student_id": student.id,
            "course_id": course.id,
        })

        return {
            "success": True,
            "message": "Enrollment created successfully.",
            "enrollment": {
                "id": enrollment.id,
                "student": student.name,
                "course": course.name,
                "state": enrollment.state,
                "course_fee": enrollment.course_fee,
                "due_amount": enrollment.due_amount,
            },
        }