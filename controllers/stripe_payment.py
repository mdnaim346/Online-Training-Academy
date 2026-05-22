import hashlib
import hmac
import json
import logging
import time

from odoo import http
from odoo.http import request
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


class TrainingStripePayment(http.Controller):

    @http.route(
        "/my/training/enrollment/<int:enrollment_id>/pay",
        type="http",
        auth="user",
        website=True,
    )
    def start_stripe_payment(self, enrollment_id, **kwargs):
        enrollment = request.env["training.enrollment"].sudo().browse(enrollment_id)
        if not enrollment.exists() or not self._is_portal_enrollment(enrollment):
            return request.not_found()

        try:
            action = enrollment.action_create_stripe_checkout()
        except Exception as error:
            return request.render(
                "Training_academy_management_system.portal_training_enrollment_detail",
                {
                    "enrollment": enrollment,
                    "page_name": "training_detail",
                    "payment_success": False,
                    "payment_error": str(error),
                },
            )

        return request.redirect(action["url"], local=False)

    @http.route(
        "/my/training/payment/success",
        type="http",
        auth="user",
        website=True,
    )
    def stripe_payment_success(self, session_id=None, **kwargs):
        if not session_id:
            return request.redirect("/my/training")

        transaction = request.env["training.payment.transaction"].sudo().search([
            ("stripe_session_id", "=", session_id),
        ], limit=1)
        if not transaction.exists() or not self._is_portal_enrollment(transaction.enrollment_id):
            return request.not_found()

        try:
            session = transaction._retrieve_stripe_session(session_id)
            transaction._mark_success_from_stripe_session(session)
            message = "Payment received successfully."
        except Exception as error:
            _logger.exception("Stripe success verification failed.")
            message = f"Payment is being verified. {error}"

        return request.render(
            "Training_academy_management_system.portal_training_enrollment_detail",
            {
                "enrollment": transaction.enrollment_id,
                "page_name": "training_detail",
                "payment_success": message,
                "payment_error": False,
            },
        )

    @http.route(
        "/my/training/payment/cancel",
        type="http",
        auth="user",
        website=True,
    )
    def stripe_payment_cancel(self, transaction_id=None, **kwargs):
        transaction = request.env["training.payment.transaction"].sudo().browse(
            int(transaction_id or 0)
        )
        if not transaction.exists() or not self._is_portal_enrollment(transaction.enrollment_id):
            return request.not_found()

        transaction.action_mark_cancelled()
        return request.render(
            "Training_academy_management_system.portal_training_enrollment_detail",
            {
                "enrollment": transaction.enrollment_id,
                "page_name": "training_detail",
                "payment_success": False,
                "payment_error": "Payment was cancelled.",
            },
        )

    @http.route(
        "/payment/stripe/webhook",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def stripe_webhook(self, **kwargs):
        payload = request.httprequest.get_data()
        signature = request.httprequest.headers.get("Stripe-Signature", "")
        webhook_secret = request.env["ir.config_parameter"].sudo().get_param(
            "training_academy.stripe_webhook_secret"
        )

        if not webhook_secret or not self._verify_stripe_signature(
            payload,
            signature,
            webhook_secret,
        ):
            return Response("Invalid signature", status=400)

        try:
            event = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            return Response("Invalid payload", status=400)

        if event.get("type") == "checkout.session.completed":
            session = event.get("data", {}).get("object", {})
            session_id = session.get("id")
            transaction = request.env["training.payment.transaction"].sudo().search([
                ("stripe_session_id", "=", session_id),
            ], limit=1)

            if transaction:
                transaction._mark_success_from_stripe_session(session)

        return Response("OK", status=200)

    def _is_portal_enrollment(self, enrollment):
        partner = request.env.user.partner_id
        emails = [email for email in {partner.email, request.env.user.login} if email]
        domain = [("partner_id", "=", partner.id)]
        if emails:
            domain = ["|", ("partner_id", "=", partner.id), ("email", "in", emails)]
        students = request.env["training.student"].sudo().search(domain)
        return enrollment.student_id in students

    def _verify_stripe_signature(self, payload, signature, webhook_secret):
        timestamp = None
        signatures = []
        for item in signature.split(","):
            key, _, value = item.partition("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)

        if not timestamp or not signatures:
            return False

        try:
            timestamp_int = int(timestamp)
        except ValueError:
            return False

        if abs(time.time() - timestamp_int) > 300:
            return False

        signed_payload = timestamp.encode("utf-8") + b"." + payload
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in signatures)
