import hmac
import hashlib
import os
import logging
from fastapi import FastAPI, Request, Query, Response, HTTPException
from fastapi.responses import PlainTextResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "joeywang")
APP_SECRET = os.getenv("APP_SECRET", "")


def verify_request_signature(payload: bytes, signature: str) -> bool:
    """Verify that the callback came from Facebook."""
    if not signature:
        logger.warning("Couldn't find 'x-hub-signature-256' in headers.")
        return False

    elements = signature.split("=")
    if len(elements) != 2:
        logger.warning(f"Invalid signature format: {signature}")
        return False

    signature_hash = elements[1]
    expected_hash = hmac.new(
        APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(signature_hash, expected_hash)
    if not is_valid:
        logger.warning("Signature verification failed")
    return is_valid


def handle_status(phone_number_id: str, status: dict):
    """Handle message status updates."""
    logger.info(f"Status update for {phone_number_id}: {status}")


def handle_message(phone_number_id: str, message: dict):
    """Handle incoming messages."""
    logger.info(f"Message received for {phone_number_id}: {message}")


@app.get("/")
async def health_check():
    """Default route for health check."""
    return {
        "status": "healthy",
        "message": "WhatsApp Webhook Server is running",
        "endpoints": {
            "GET /webhook": "Webhook verification (with hub.mode, hub.verify_token, hub.challenge)",
            "POST /webhook": "Receive WhatsApp events",
        },
        "config": {
            "verify_token_set": bool(VERIFY_TOKEN),
            "app_secret_set": bool(APP_SECRET),
        }
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Handle webhook verification handshake from Meta."""
    logger.info(f"Webhook verification request: mode={hub_mode}, token_provided={bool(hub_verify_token)}, challenge={hub_challenge}")

    # Validate required parameters
    if not hub_mode or not hub_verify_token or not hub_challenge:
        logger.warning(f"Missing required parameters: mode={bool(hub_mode)}, token={bool(hub_verify_token)}, challenge={bool(hub_challenge)}")
        return Response(status_code=400)

    # Verify the token and mode
    if hub_mode != "subscribe":
        logger.warning(f"Invalid hub.mode: expected 'subscribe', got '{hub_mode}'")
        return Response(status_code=403)

    if hub_verify_token != VERIFY_TOKEN:
        logger.warning("Verify token mismatch")
        return Response(status_code=403)

    logger.info("Webhook verification successful")
    # Return challenge as integer (Meta expects this format)
    return int(hub_challenge)


@app.post("/webhook")
async def receive_message(request: Request):
    """Handle incoming webhook events from WhatsApp."""
    logger.info("Received webhook POST request")

    payload = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")

    # Verify signature if APP_SECRET is configured
    if APP_SECRET and not verify_request_signature(payload, signature):
        logger.error("Webhook signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.debug(f"Webhook body: {body}")

    # Handle WhatsApp Business Account events
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
    else:
        logger.warning(f"Unknown webhook object type: {body.get('object')}")

    # Always return 200 quickly to acknowledge receipt
    return PlainTextResponse(content="EVENT_RECEIVED", status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
