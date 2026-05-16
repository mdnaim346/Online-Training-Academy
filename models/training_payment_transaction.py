import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TrainingPaymentTransaction(models.Model):
    _name = "training.payment.transaction"
    _description = "Training Payment Transaction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(
        string="Transaction Reference",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    enrollment_id = fields.Many2one(
        "training.enrollment",
        string="Enrollment",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    student_id = fields.Many2one(
        related="enrollment_id.student_id",
        string="Student",
        store=True,
        readonly=True,
    )
    course_id = fields.Many2one(
        related="enrollment_id.course_id",
        string="Course",
        store=True,
        readonly=True,
    )
    payment_id = fields.Many2one(
        "training.payment",
        string="Posted Payment",
        readonly=True,
        copy=False,
    )
    provider = fields.Selection(
        [("stripe", "Stripe")],
        string="Provider",
        default="stripe",
        required=True,
        tracking=True,
    )
    amount = fields.Float(
        string="Amount",
        required=True,
        tracking=True,
    )
    currency = fields.Char(
        string="Currency",
        required=True,
        default="usd",
        tracking=True,
    )
    stripe_session_id = fields.Char(
        string="Stripe Checkout Session",
        readonly=True,
        copy=False,
        index=True,
    )
    stripe_payment_intent_id = fields.Char(
        string="Stripe Payment Intent",
        readonly=True,
        copy=False,
        index=True,
    )
    checkout_url = fields.Char(
        string="Checkout URL",
        readonly=True,
        copy=False,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    raw_payload = fields.Text(
        string="Last Gateway Payload",
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        (
            "stripe_session_id_unique",
            "unique(stripe_session_id)",
            "Stripe checkout session must be unique.",
        ),
    ]

    def _get_stripe_config(self):
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("training_academy.stripe_enabled")
        secret_key = params.get_param("training_academy.stripe_secret_key")
        currency = (
            params.get_param("training_academy.stripe_currency") or "usd"
        ).lower()

        if enabled not in ("True", "1", True):
            raise UserError(_("Stripe payments are not enabled."))

        if not secret_key:
            raise UserError(_("Please configure the Stripe secret key."))

        return secret_key, currency

    def action_create_stripe_checkout_session(self):
        self.ensure_one()

        if self.state not in ("draft", "failed", "cancelled"):
            if self.checkout_url:
                return self.checkout_url
            raise UserError(_("This transaction is already being processed."))

        if self.amount <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))

        secret_key, currency = self._get_stripe_config()
        self.currency = currency

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        success_url = (
            f"{base_url}/my/training/payment/success"
            "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = f"{base_url}/my/training/payment/cancel?transaction_id={self.id}"
        amount_minor = int(round(self.amount * 100))

        payload = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": self.name,
            "customer_email": self.student_id.email or "",
            "line_items[0][quantity]": 1,
            "line_items[0][price_data][currency]": currency,
            "line_items[0][price_data][unit_amount]": amount_minor,
            "line_items[0][price_data][product_data][name]": self.course_id.name,
            "metadata[transaction_id]": self.id,
            "metadata[enrollment_id]": self.enrollment_id.id,
        }
        payload = {key: value for key, value in payload.items() if value}
        request_data = urllib.parse.urlencode(payload).encode("utf-8")
        request_obj = urllib.request.Request(
            "https://api.stripe.com/v1/checkout/sessions",
            data=request_data,
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request_obj, timeout=30) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8")
            _logger.exception("Stripe checkout session creation failed: %s", body)
            raise UserError(_("Stripe rejected the checkout request: %s") % body)
        except (urllib.error.URLError, TimeoutError) as error:
            _logger.exception("Stripe checkout session request failed.")
            raise UserError(_("Could not connect to Stripe: %s") % error)

        self.write({
            "stripe_session_id": response_data.get("id"),
            "checkout_url": response_data.get("url"),
            "state": "pending",
            "raw_payload": json.dumps(response_data, indent=2),
        })

        if not self.checkout_url:
            raise UserError(_("Stripe did not return a checkout URL."))

        return self.checkout_url

    def action_mark_cancelled(self):
        for rec in self.filtered(lambda transaction: transaction.state == "pending"):
            rec.state = "cancelled"

    def _retrieve_stripe_session(self, session_id):
        secret_key, _currency = self._get_stripe_config()
        request_obj = urllib.request.Request(
            f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
            headers={"Authorization": f"Bearer {secret_key}"},
            method="GET",
        )

        try:
            with urllib.request.urlopen(request_obj, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8")
            _logger.exception("Stripe checkout session retrieve failed: %s", body)
            raise UserError(_("Stripe rejected the session lookup: %s") % body)
        except (urllib.error.URLError, TimeoutError) as error:
            _logger.exception("Stripe checkout session lookup failed.")
            raise UserError(_("Could not connect to Stripe: %s") % error)

    def _mark_success_from_stripe_session(self, session):
        self.ensure_one()

        if self.state == "success":
            return self.payment_id

        payment_status = session.get("payment_status")
        if payment_status != "paid":
            self.write({
                "state": "failed",
                "raw_payload": json.dumps(session, indent=2),
            })
            return False

        payment = False
        amount_to_post = min(self.amount, max(self.enrollment_id.due_amount, 0))
        if amount_to_post > 0:
            payment = self.env["training.payment"].sudo().create({
                "enrollment_id": self.enrollment_id.id,
                "amount": amount_to_post,
                "payment_method": "card",
                "reference": session.get("payment_intent") or session.get("id"),
                "note": _("Stripe Checkout payment received."),
            })
        self.write({
            "state": "success",
            "payment_id": payment.id if payment else False,
            "stripe_payment_intent_id": session.get("payment_intent"),
            "raw_payload": json.dumps(session, indent=2),
        })
        self.enrollment_id.sudo()._finalize_paid_enrollment_if_ready()
        return payment

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "training.payment.transaction"
                ) or "New"
        return super().create(vals_list)
