from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Trainer(models.Model):
    _name= "training.trainer"
    _description="Training trainer"

    name= fields.Char(string="Trainer Name", required=True)
    email = fields.Char(string="Email")
    phone= fields.Char(string = 'Phone')
    expertise= fields.Char(string="Expertise")
    active= fields.Boolean(string ="active", default=True)

    course_ids=fields.One2many("training.course","trainer_id", string="courses")
    course_count=fields.Integer(string="Course Count", compute="_compute_course_count")

    def _compute_course_count(self):
        for rec in self:
            rec.course_count=len(rec.course_ids)
    
    def action_open_courses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Trainer Courses",
            "res_model": "training.course",
            "view_mode": "tree,form",
            "domain": [("trainer_id", "=", self.id)],
            "context": {"default_trainer_id": self.id},
        }
