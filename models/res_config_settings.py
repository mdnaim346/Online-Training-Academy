from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    training_stripe_enabled = fields.Boolean(
        string="Enable Stripe Payments",
        config_parameter="training_academy.stripe_enabled",
    )
    training_stripe_secret_key = fields.Char(
        string="Stripe Secret Key",
        config_parameter="training_academy.stripe_secret_key",
    )
    training_stripe_webhook_secret = fields.Char(
        string="Stripe Webhook Secret",
        config_parameter="training_academy.stripe_webhook_secret",
    )
    training_stripe_currency = fields.Char(
        string="Stripe Currency",
        default="usd",
        config_parameter="training_academy.stripe_currency",
    )
