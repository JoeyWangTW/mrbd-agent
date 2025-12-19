import hmac
import hashlib
import os
from fastapi import FastAPI, Request, Query, Response, HTTPException
from fastapi.responses import PlainTextResponse

app = FastAPI()

VERIFY_TOKEN = "joeywang"
APP_SECRET = os.getenv("APP_SECRET", "")


def verify_request_signature(payload: bytes, signature: str) -> bool:
    """Verify that the callback came from Facebook."""
    if not signature:
        print("Couldn't find 'x-hub-signature-256' in headers.")
        return False

    elements = signature.split("=")
    if len(elements) != 2:
        return False

    signature_hash = elements[1]
    expected_hash = hmac.new(
        APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature_hash, expected_hash)


def handle_status(phone_number_id: str, status: dict):
    """Handle message status updates."""
    print(f"Status update for {phone_number_id}: {status}")


def handle_message(phone_number_id: str, message: dict):
    """Handle incoming messages."""
    print(f"Message received for {phone_number_id}: {message}")


@app.get("/")
async def health_check():
    """Default route for health check."""
    return {
        "message": "WhatsApp Webhook Server is running",
        "endpoints": ["POST /webhook - WhatsApp webhook endpoint"],
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Handle webhook verification handshake."""
    if hub_mode != "subscribe" or hub_verify_token != VERIFY_TOKEN:
        return Response(status_code=403)

    return PlainTextResponse(content=hub_challenge)


@app.post("/webhook")
async def receive_message(request: Request):
    """Handle incoming messages."""
    payload = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")

    if APP_SECRET and not verify_request_signature(payload, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    body = await request.json()
    print(body)

    if body.get("object") == "whatsapp_business_account":
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value")
                if value:
                    phone_number_id = value.get("metadata", {}).get("phone_number_id")

                    if value.get("statuses"):
                        for status in value["statuses"]:
                            handle_status(phone_number_id, status)

                    if value.get("messages"):
                        for message in value["messages"]:
                            handle_message(phone_number_id, message)

    return PlainTextResponse(content="EVENT_RECEIVED", status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
