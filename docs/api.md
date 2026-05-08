# Gaia AI - API Reference

OpenAPI is auto-generated and served at `http://localhost:8000/docs`. This file is a hand-curated summary.

All authenticated routes require `Authorization: Bearer <jwt>`.

## Auth

```
POST /auth/register
  body: { email, password, display_name? }
  201:  { token, user: { id, email, display_name } }

POST /auth/login
  body: { email, password }
  200:  { token, user }
```

## WhatsApp

```
POST   /whatsapp/connect              # auth - start a session via bridge
GET    /whatsapp/qr                   # auth - { qr_base64, status }
POST   /whatsapp/send                 # auth - { contact_id, text }
DELETE /whatsapp/disconnect           # auth - logout + wipe session

POST   /whatsapp/internal/event       # bridge → backend (HMAC)
       header: X-Bridge-Signature: <hex>
       body:   { user_id, type: "message"|"ready"|"qr"|"disconnected", payload }
```

## Contacts

```
GET   /contacts                       # auth - list contacts (allowed flag)
PATCH /contacts/{id}                  # auth - { allowed?, name? }
```

## Messages

```
GET /messages?contact_id=&limit=&before=
  Returns latest decrypted messages for the user (page-by-cursor on `ts`).
```

## AI

```
POST /ai/generate
  body: { contact_id, incoming_message }
  res:  { suggestion_id, suggestion, confidence, label }
        label ∈ ANSWER_NOW | UNSURE | ASK_USER_FOR_TEACHING

POST /ai/feedback
  body: { suggestion_id, edited_text, decision: approve|edit|skip }
  res:  { ok: true }
```

## Analytics

```
GET /analytics/summary
  res: { window_days, suggestions, feedback, approved, edited, approval_rate }
```

## Privacy / Self-service

```
GET    /me/export       # downloads full user data as JSON file
DELETE /me/data         # wipes data, keeps account
DELETE /me              # wipes data + deletes account
```

## WebSocket

```
ws://<host>/ws?token=<jwt>
  Server-pushed events:
    { event: "new_suggestion", data: { suggestion_id, contact_id, contact_name, incoming, suggestion, confidence, label } }
    { event: "qr_update",      data: { qr_base64 } }
    { event: "session_ready",  data: {} }
```

## Bridge HTTP API

```
POST   /sessions                      # { user_id }
GET    /sessions/:userId/status       # { status }
GET    /sessions/:userId/qr           # { qr_base64, status }
GET    /sessions/:userId/contacts     # { contacts: [{wa_id, name, is_group}] }
GET    /sessions/:userId/history?contact_id=&limit=  # { messages: [...] }
POST   /sessions/:userId/send         # { to, text }
DELETE /sessions/:userId              # logout & destroy
GET    /healthz                       # { status: "ok" }
```
