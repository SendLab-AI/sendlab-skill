import os
import uuid

from flask import Flask, request
from twilio.rest import Client
from twilio.request_validator import RequestValidator

app = Flask(__name__)
client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
STATUS_URL = "https://app.example.com/twilio/status"


def notify(phone: str, text: str, appointment_id: int) -> str:
    """Send an appointment notification. Returns the provider message id."""
    for attempt in range(3):
        try:
            msg = client.messages.create(
                messaging_service_sid=os.environ["TWILIO_MESSAGING_SERVICE_SID"],
                to=phone,
                body=text,
                status_callback=STATUS_URL,
            )
            save_message(appointment_id, msg.sid, "queued", str(uuid.uuid4()))
            return msg.sid
        except Exception:
            if attempt == 2:
                raise


@app.post("/twilio/status")
def twilio_status():
    validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])
    if not validator.validate(request.url, request.form, request.headers.get("X-Twilio-Signature", "")):
        return "", 403
    status = request.form["MessageStatus"]
    update_status(request.form["MessageSid"], status)
    if status in ("failed", "undelivered"):
        flag_bad_number(request.form["To"])
    return "", 204


def save_message(appointment_id, sid, status, attempt_id): ...
def update_status(sid, status): ...
def flag_bad_number(phone): ...
