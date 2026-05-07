from odoo import api, models, fields


class TrainingCourse(models.Model):
    _name = "training.student"
    _description = "Training Student"
   
    name = fields.Char(string="Name")
    phone = fields.Char(string = "Code")
    email= fields.Char(string="Email")
    address = fields.Text(string= "Address")
    course_ids=fields.Onetomany("training.course","student_id",string="Courses")
    enroll_ids= fields.Onetomany("training.enrollment", "student_id",string="Enrollments")
    total_enrolled=fields.Integer(string="Total Enrolled",compute="_compute_enrollment_count" ,)

    def _compute_enrollment_count(self):
        for rec in self:
            rec.total_enrolled=len(rec.enroll_ids)

    def action_open_enrollments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Enrollments",
            "res_model": "training.enrollment",
            "view_mode": "tree, form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }



