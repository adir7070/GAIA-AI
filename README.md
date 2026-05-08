# Gaia AI

> Personalized conversational AI assistant that learns a user's WhatsApp writing style and suggests responses in that style — with human approval before sending.

This is a **course project + startup-grade architecture**. It combines:
- **Research**: implicit user-style learning via QLoRA fine-tuning on a synthetic dataset of 1000 users + a "Style Indistinguishability" evaluation (LLM judge ≈ 50% accuracy = success).
- **Product**: full stack (FastAPI + Next.js + Node WhatsApp bridge + Postgres/Mongo/Qdrant/Redis).

The system **never auto-sends**. It only *suggests*; the human decides.

---

## Quickstart

```bash
# 1. Copy env template
cp .env.example .env
# (edit .env: at minimum fill JWT_SECRET, AES_KEY, BRIDGE_SECRET, ANTHROPIC_API_KEY or OPENAI_API_KEY)

# 2. Bring up all services
make up

# 3. Run database migrations
make migrate

# 4. Open the app
open http://localhost:3000           # frontend
open http://localhost:8000/docs      # backend OpenAPI
```

### What's running

| Service          | Port  | Purpose                                        |
|------------------|-------|------------------------------------------------|
| frontend         | 3000  | Next.js 14 dashboard (RTL, Hebrew/English)     |
| backend          | 8000  | FastAPI (REST + WebSocket)                     |
| whatsapp-bridge  | 4000  | Node.js whatsapp-web.js bridge                 |
| postgres         | 5432  | Users, sessions, contacts, feedback            |
| mongo            | 27017 | Raw messages, training samples, AI outputs     |
| qdrant           | 6333  | Style/semantic embeddings                      |
| redis            | 6379  | Celery queue + cache                           |

---

## Repository Layout

```
backend/             FastAPI service + Celery workers
whatsapp-bridge/     Node.js whatsapp-web.js bridge
frontend/            Next.js 14 app (App Router, Tailwind)
ml/                  Synthetic data, training, evaluation
infra/               Postgres init.sql, Qdrant config
docs/                Architecture, API, prompts, evaluation, deployment
```

---

## End-to-End User Flow (MVP)

1. User registers → logs in.
2. Visits `/connect` → sees WhatsApp QR → scans with their phone.
3. Backend pulls last ~1000 messages, embeds them into Qdrant, builds style memory.
4. User picks which contacts/groups the assistant is allowed to suggest replies for (`/permissions`).
5. New incoming message → backend pulls top-k similar history → builds prompt → LLM suggests a response.
6. Frontend dashboard shows the suggestion with a confidence badge.
7. User clicks **Approve / Edit / Skip**. Edits become future training signal.

---

## Research Pipeline

```bash
# 1. Generate 1000 synthetic users with hidden styles
make seed-synthetic n=1000

# 2. Build train/val/test jsonl
make build-dataset

# 3. Fine-tune (run on RunPod / Modal — script is GPU-aware)
make train

# 4. Run evaluation: zero-shot vs few-shot vs fine-tuned
#    Output: results/eval_report.json + results/eval_report.md
make eval
```

The headline metric is **Style Indistinguishability**:

> An LLM judge sees the user's history + an incoming message + two responses (one from the oracle, one from our model) and must guess which one is "real". Target accuracy: ~50% (random) — meaning the model successfully imitates the user's style.

See [docs/evaluation.md](docs/evaluation.md) for the full methodology.

---

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2 (async), Motor, qdrant-client, Celery, anthropic + openai SDK.
- **Frontend**: Next.js 14 (App Router), TypeScript, TailwindCSS, Zustand, socket.io-client.
- **Bridge**: Node.js 20, whatsapp-web.js, Express, Socket.IO, qrcode.
- **ML**: transformers, peft, trl, bitsandbytes, accelerate, sentence-transformers.
- **Infra**: Docker Compose for local; Postgres 16, MongoDB 7, Qdrant, Redis 7.

---

## Privacy & Consent

- Real WhatsApp data is **only** used with explicit per-user opt-in (see `/permissions` page and the consent terms shown at first connect).
- Messages are encrypted at rest with AES-256-GCM (`AES_KEY` in `.env`).
- Real-data folders (`ml/data/real/`) are gitignored.
- Users can export (`GET /me/export`) or delete (`DELETE /me/data`) at any time.

For research purposes the **primary** dataset is synthetic (1000 users); real data is used **only for evaluation/generalization**.

---

## Development

See `make help` for all commands.

Common workflows:

```bash
make dev-backend       # Run FastAPI with hot reload (outside docker)
make dev-frontend      # Run Next.js with hot reload
make dev-bridge        # Run WhatsApp bridge with nodemon

make test              # Run backend tests
make lint              # Lint backend + frontend
make migrate           # Apply DB migrations
make revision m="msg"  # Create new migration
```

---

## Documentation

- [docs/architecture.md](docs/architecture.md) — System architecture
- [docs/api.md](docs/api.md) — API contracts
- [docs/prompts.md](docs/prompts.md) — All LLM prompts
- [docs/evaluation.md](docs/evaluation.md) — Research methodology
- [docs/deployment.md](docs/deployment.md) — Production deployment notes
- [docs/proposal.md](docs/proposal.md) — Course project proposal (EN + HE)

---

## License

Educational / research use. WhatsApp Web automation is unofficial — review the WhatsApp ToS before any production deployment.
