# Data

This project's task is **data-free by design** — no public dataset of "a person's
WhatsApp style" exists, so we **generate synthetic data** (course requirement:
*task with no data → generate synthetic training and test data*).

## Where the data lives
- **Full generated dataset:** [`../ml/data/synthetic/`](../ml/data/synthetic/) (JSONL, committed — it is synthetic, no privacy concern).
- **Curated sample:** [`sample_pairs.jsonl`](sample_pairs.jsonl) — a small human-readable excerpt for quick inspection.
- **Real data (optional, evaluation only):** `../ml/data/real/` — opt-in, AES-256-GCM encrypted, **gitignored**. Never committed.

## Files (in `ml/data/synthetic/`)
| File | What it is |
|---|---|
| `personas.jsonl` | One synthetic user per line: `user_id`, `language`, `persona_summary`, `topics`, and the **hidden** `hidden_style` seed (style axes). |
| `histories.jsonl` | Per user: a list of ~20–50 outgoing messages in that user's style (style reference). |
| `pairs.jsonl` | Training/eval triples: `{user_id, history[], incoming_message, target_response}` (target written by an oracle that saw the seed). |
| `train/val/test.jsonl` | Chat-formatted SFT splits (per-user 80/10/10). |
| `*_raw.jsonl` | The raw triples for each split (used by evaluation). |

## Schema example (`pairs.jsonl`)
```json
{
  "user_id": "u_0007",
  "history": ["כן אחי סגור", "אני בודק עכשיו 👍", "שלח לי שוב"],
  "incoming_message": "מה עם הפרויקט?",
  "target_response": "בודק עכשיו ואחזור אליך 🙏"
}
```

## Regenerate
```bash
# from repo root, with API key in .env (LLM_PROVIDER + key)
cd ml
python -m synthetic.generate_personas  --n 30
python -m synthetic.generate_histories --n-messages 20
python -m synthetic.generate_pairs     --pairs-per-user 8
python -m dataset.build_jsonl
python -m eda.run_eda            # EDA figures + ../results/eda_stats.json
```

> **Scale note.** This run was generated on the **Groq free tier** (1,000 req/day on
> 70B; 14,400/day on 8B; ~6–12k tokens/min). The pipeline is scale-agnostic — to reach
> hundreds/thousands of users, raise `--n`/`--pairs-per-user` on a paid tier or run
> across days. See the repo README for details.
