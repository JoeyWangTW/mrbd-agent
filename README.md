# MRBD Agent

WhatsApp webhook server for receiving chatbot messages.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /webhook` - WhatsApp verification endpoint
- `POST /webhook` - Receive messages, returns `{"message": "get the message"}`

## Test

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```
