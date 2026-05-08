# Gaia AI - Deployment Notes

## Local (recommended for course work)

```bash
cp .env.example .env
make up
make migrate
open http://localhost:3000
```

Everything runs in Docker. Hot-reload mounts are configured for backend and
frontend; rebuild only when dependencies change.

## Production sketch (NOT in scope for course)

The local stack maps cleanly onto a small managed deployment:

| Component          | Suggested host                                                              |
|--------------------|------------------------------------------------------------------------------|
| frontend           | Vercel                                                                       |
| backend (+worker)  | Railway / Fly.io / AWS ECS Fargate                                           |
| whatsapp-bridge    | Same as backend, but **dedicated process** with persistent volume for `.wwebjs_auth` |
| postgres           | Supabase / Neon / RDS                                                        |
| mongo              | MongoDB Atlas                                                                |
| qdrant             | Qdrant Cloud / self-hosted                                                   |
| redis              | Upstash / Elasticache                                                        |
| LLM serving (LoRA) | RunPod (vLLM with adapter), Modal, or Lambda Labs                            |

## Running the WhatsApp bridge in production

- **Persistent disk** for `.wwebjs_auth/` per user (or a TURN-style central
  store, e.g. S3, mounted via `LocalAuth({ dataPath })`).
- **Single-process per session**: do not horizontally scale a single user's
  bridge - LocalAuth files are mutable.
- **Watch RAM**: each Chromium-backed Client is ~250-400MB. 100 simultaneous
  sessions ≈ 25-40GB RAM.
- **WhatsApp ToS**: unofficial automation can trigger bans. Keep send rates
  low and never auto-send without user approval.

## Serving the fine-tuned LoRA in production

Recommended: vLLM with `--enable-lora` and `--lora-modules gaia=path/to/adapter`.

```bash
vllm serve meta-llama/Meta-Llama-3-8B-Instruct \
  --enable-lora --lora-modules gaia=./gaia-lora-v1 \
  --port 8001
```

Then route `LLM_PROVIDER=vllm` (would require adding a `vllm` branch in
`backend/app/services/llm_provider.py` — a small extension point).

## Secrets

- **Never** commit `.env`.
- Rotate `JWT_SECRET` and `AES_KEY` at least once.
- For multi-tenant deployments, derive per-user encryption keys from `AES_KEY`
  + `user_id` so a single key compromise has bounded blast radius.

## Backups

- Postgres: nightly `pg_dump` to encrypted S3.
- Mongo: nightly mongodump.
- Qdrant: snapshot to disk (built-in API) + sync to S3.
- LoRA checkpoints: pushed to HuggingFace Hub or saved as artifacts in W&B.

## Monitoring

- Backend / worker: stdout structured logs (JSON) to your log service.
- Bridge: same.
- Surfaces to watch: `ws_clients`, `suggestions/min`, `judge_p_oracle_first`,
  cost per generated suggestion.
