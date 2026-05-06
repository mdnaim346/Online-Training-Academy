from odoo import models, fields, api

class CourseModel(models.Model):
    _name="training.course"
    _description="Training course model"

    name=fields.Char(string="Course Name")
    code = fields.Char(string="Course Code")
    trainer_id= fields.Many2one("res.partner", string ="Trainer")
    start_date = fields.Date(string = "Start Date")
    duration= fields.Selection([
        ("one_month", "One Month"),
        ("two_month", "Two Month"),
        ("three_month", "Three Month"),
        ("six_month", "Six Month"),
        ("twelve_month", "Twelve Month"),

         
    ], default="one_month", string="Duration")
    fee = fields.Float(string = "Fee")
    discount = fields.Float(string= "Discount(%)")
    final_fee= fields.Float( string = "Final Fee", compute="_compute_final_fee")

    state= fields.Selection([
        ("draft", "Draft"),
        ("confirm", "Confirm"),
        ("done", "Done"),
        ("cancel", "Cancel")
    ])

    @api.depends("fee", "discount")
    def _compute_final_fee(self):
        for rec in self:
            rec.final_fee=rec.fee *rec.discount/100
    