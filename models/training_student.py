from odoo import fields, models


class TrainingStudent(models.Model):
    _name = "training.student"
    _description = "Training Student"
    _order = "name asc"

    name = fields.Char(string="Student Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    address = fields.Text(string="Address")

    enrollment_ids = fields.One2many(
        "training.enrollment",
        "student_id",
        string="Enrollments",
    )

    enrollment_count = fields.Integer(
        string="Enrollment Count",
        compute="_compute_enrollment_count",
    )

    def _compute_enrollment_count(self):
        for rec in self:
            rec.enrollment_count = len(rec.enrollment_ids)

    def action_open_enrollments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Enrollments",
            "res_model": "training.enrollment",
            "view_mode": "tree,form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }