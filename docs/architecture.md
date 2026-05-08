# Gaia AI - System Architecture

## High-Level Diagram

```
                ┌──────────────┐
                │  Frontend    │  Next.js 14 + Tailwind + Zustand
                │  (port 3000) │  WebSocket client for live suggestions
                └──────┬───────┘
                       │ REST + WS (JWT)
                ┌──────▼───────┐
                │  Backend API │  FastAPI + Celery
                │  (port 8000) │
                └─┬───────┬────┘
        ┌────────┘       └─────────┐
        │                          │
┌───────▼────────┐         ┌───────▼────────┐
│ WhatsApp Bridge│         │   ML Service   │
│ Node + WWeb.js │         │  Python infer  │
│  (port 4000)   │         │   (vLLM/HF)    │
└───────┬────────┘         └────────────────┘
        │ QR / events                  ▲
        ▼                              │
   WhatsApp Web                  ml/ training pipeline
                                  (offline, on cloud GPU)

Storage:
  Postgres 16  (users, sessions, contacts, permissions, feedback)  :5432
  MongoDB 7    (raw messages, training samples, AI outputs)         :27017
  Qdrant       (style/semantic embeddings, memory retrieval)        :6333
  Redis 7      (Celery queue + cache + WS pub/sub)                  :6379
```

## Process Topology (Docker Compose)

| Service          | Image / Build                  | Notes                                  |
|------------------|--------------------------------|----------------------------------------|
| postgres         | postgres:16-alpine             | Schema managed by Alembic              |
| mongo            | mongo:7                        | Indexes ensured at backend startup     |
| qdrant           | qdrant/qdrant:1.11             | One collection per user                |
| redis            | redis:7-alpine                 | Broker + result backend + WS pubsub    |
| backend          | ./backend                      | FastAPI uvicorn :8000                  |
| worker           | ./backend (same image)         | Celery worker on `gaia` queue          |
| whatsapp-bridge  | ./whatsapp-bridge              | Node 20 + chromium + whatsapp-web.js   |
| frontend         | ./frontend                     | Next.js dev (build for prod)           |

## Data Flow

### Initial onboarding
1. `POST /auth/register` → JWT.
2. `POST /whatsapp/connect` → backend asks bridge to start a Client.
3. Bridge emits `qr` event → backend webhook → WS push → frontend renders QR.
4. User scans → bridge `ready` event → backend marks session ready.
5. Frontend redirects to `/dashboard`.
6. (Background) Celery `import_history` pulls last ~1000 messages per allowed contact, stores in Mongo, embeds outgoing messages in Qdrant.

### Incoming message
1. Bridge `message` event → POST `/whatsapp/internal/event` (HMAC-signed).
2. Backend persists to Mongo, dispatches `handle_incoming_message` Celery task.
3. Task: retrieve top-k similar history from Qdrant + recent N turns from Mongo → build prompt → call LLM → score confidence.
4. Persist `ai_output` in Mongo + push `new_suggestion` over WS.
5. Frontend `<SuggestionCard>` renders with Approve/Edit/Skip.
6. Approve → `POST /whatsapp/send` → bridge sends. Edit → `POST /ai/feedback` → Postgres.

## Module Map

```
backend/app/
  api/              REST + WS routers (auth, whatsapp, ai, contacts, messages, analytics, me, ws)
  core/             config, security (JWT/AES/HMAC), DI deps
  db/               Postgres engine, Mongo client, Qdrant client, Redis client, ORM models
  services/         llm_provider, embeddings, style_memory, prompt_builder, confidence
  prompts/          runtime, judge, synthetic_user, synthetic_chat
  workers/          Celery app + tasks (import_history, embed_messages, handle_incoming_message)
  schemas/          Pydantic request/response

whatsapp-bridge/src/
  index.js          Express bootstrap
  session.js        Per-user WhatsApp Client lifecycle
  routes.js         HTTP routes
  events.js         HMAC-signed webhook to backend

frontend/src/
  app/              Next.js App Router pages (login, register, connect, dashboard, learn, analytics, settings, permissions)
  components/       SuggestionCard, ConfidenceBadge, ContactToggle
  hooks/            useSocket
  services/         api, socket
  store/            authStore, suggestionsStore (Zustand)

ml/
  synthetic/        generate_personas, generate_histories, generate_pairs
  dataset/          build_jsonl
  train/            train_qlora, modal_app, runpod_command, config.yaml
  inference/        generate, _loaded
  eval/             indistinguishability, style_similarity, relevance, run_all
```

## Cross-Service Contracts

### Frontend ↔ Backend (REST)
See [api.md](api.md).

### Backend ↔ Bridge (REST + Webhook)
- Bridge:  `POST /sessions`, `GET /sessions/:uid/qr`, `POST /sessions/:uid/send`, `GET /sessions/:uid/history`, `DELETE /sessions/:uid`.
- Webhook (bridge → backend): `POST /whatsapp/internal/event`, header `X-Bridge-Signature: HMAC_SHA256(BRIDGE_SECRET, raw_body)`.

### WebSocket events (Backend → Frontend)
- `new_suggestion`: `{suggestion_id, contact_id, contact_name, incoming, suggestion, confidence, label}`
- `qr_update`: `{qr_base64}`
- `session_ready`: `{}`

## Persistence

### Postgres tables
- `users(id, email, password_hash, display_name, created_at)`
- `sessions(id, user_id, wa_session_id, status, created_at, updated_at)`
- `contacts(id, user_id, wa_id, name, is_group, allowed, created_at)`
- `permissions(id, user_id, contact_id, suggest, auto_send, note, updated_at)`
- `feedback(id, user_id, suggestion_id, contact_id, incoming_message, original, edited, delta_json, decision, created_at)`

### MongoDB collections
- `messages(user_id, contact_id, wa_id, direction, text/text_encrypted, ts, meta)`
- `training_samples(user_id, ...)`
- `ai_outputs(user_id, suggestion_id, contact_id, incoming, suggestion, confidence, label, created_at)`

### Qdrant
- One collection per user: `user_{user_id}_style`, dim=1024 (BGE-large), distance=Cosine.

## Privacy & Security
See [security.md](../README.md#privacy--consent) and `app/core/security.py`. AES-256-GCM at-rest helpers exist for any text we want to encrypt on disk.

## Why each tech?

- **FastAPI**: async-first, OpenAPI for free, easy WS support.
- **Postgres** for relational truth (users, contacts, FK semantics).
- **Mongo** for high-volume semi-structured chat logs.
- **Qdrant** because per-user collections + cosine search at scale, easy local docker.
- **Redis** for Celery + WS pubsub fan-out across worker processes.
- **whatsapp-web.js**: best community-supported unofficial WA Web client; LocalAuth persists sessions across restarts.
- **Next.js App Router**: typed routes, RSC where helpful, easy WS integration via "use client" pages.
