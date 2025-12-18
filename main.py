from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/webhook")
async def verify_webhook(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):
    """WhatsApp webhook verification endpoint."""
    # For webhook verification, return the challenge
    if hub_challenge:
        return int(hub_challenge)
    return {"status": "ok"}


@app.post("/webhook")
async def receive_message(request: Request):
    """Receive WhatsApp webhook messages."""
    body = await request.json()
    print(f"Received message: {body}")
    return {"message": "get the message"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
