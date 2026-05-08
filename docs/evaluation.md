# Gaia AI - Research Evaluation Methodology

This document describes the experimental setup the project uses to evaluate
whether a fine-tuned LLM can mimic a user's WhatsApp writing style well enough
to be **stylistically indistinguishable** from the user themselves.

## Research question

> Can a Llama 3 8B model, fine-tuned with QLoRA on a synthetic dataset of 1000
> users with diverse hidden writing styles, generate WhatsApp responses that
> are stylistically indistinguishable from the actual user's responses?

This formulation came directly from feedback by Vlada Savitski (course
lecturer): instead of measuring "similarity", measure **indistinguishability**
via an LLM judge. Random-chance accuracy ≈ 50% means success.

## Hypothesis

H1: A fine-tuned model trained on diverse synthetic personas achieves
indistinguishability accuracy closer to 50% than baseline zero-shot or
few-shot prompting.

H0: Baseline prompting matches or exceeds the fine-tuned model.

## Dataset

### Synthetic (primary - training)
- **1000 personas** with hidden style seeds sampled from a diversity matrix
  (length × emoji × slang × formality × rhythm × punctuation × greetings ×
  occupation × age bucket × language). See `ml/synthetic/_diversity.py`.
- For each persona: ~50 outgoing WhatsApp messages (style reference) +
  ~50 (history, incoming, target_response) triples. Targets are produced by
  an "oracle" LLM that *does* see the hidden seed — this is the upper bound.
- Total: ~50,000 training pairs.

### Real (secondary - generalization test)
- 10–50 opt-in users.
- AES-256-GCM encrypted at rest, gitignored, used for evaluation only.

### Splits
Per-user split (no user appears in both train and test), 80/10/10.

## Models compared

| Model            | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| zero_shot        | API LLM (Claude/GPT) prompted with the user's history and asked to reply    |
| few_shot         | Same, but with 5–8 in-context history examples                              |
| **fine_tuned**   | Llama 3 8B + QLoRA (r=16, α=32, target=qkvo), trained on 50k synthetic pairs |
| oracle (upper)   | LLM that saw the latent style seed at generation time                       |

## Metrics

### 1. Style Indistinguishability (headline)

For each test sample with `(history, incoming, oracle_response, model_response)`:
1. Randomize A/B order.
2. Show judge: history, incoming, A, B.
3. Judge picks A or B.

We report:
- **Accuracy** = % of trials the judge picks the oracle.
- **95% Wilson CI**.
- Separate accuracies for "oracle was A" vs "oracle was B" (order-bias check).
- Per-baseline.

**Target**: accuracy ∈ [45%, 55%] for `fine_tuned`. Baselines should sit higher
(judge can spot the model).

### 2. Style Similarity

Cosine similarity in BGE-large embedding space between the model's response and
the mean embedding of the user's history. Reported as mean ± std.

### 3. Relevance (sanity)

LLM judge 1–5: does the response address the incoming message? A model could
score great on style by parroting greetings — relevance ensures content is real.

## Bias mitigations

1. **Order randomization** (above).
2. **Generator ≠ Judge** providers (Claude generates, GPT-4o judges, or vice
   versa). See `ml/eval/indistinguishability.py::_judge_provider()`.
3. **No style leakage in prompts**: the judge never sees the persona seed.
4. **Per-user split**.
5. **Per-trial concurrency cap** to avoid rate-limit-induced biases.

## Expected results table

| Model      | Indist. acc | 95% CI       | Style sim     | Relevance |
|------------|-------------|--------------|---------------|-----------|
| zero_shot  | ~70-80%     | [..]         | 0.55-0.70     | 4.0-4.5   |
| few_shot   | ~60-70%     | [..]         | 0.65-0.75     | 4.0-4.5   |
| fine_tuned | ~50-58%     | [..]         | 0.75-0.85     | 4.0-4.5   |

(Numbers are illustrative; the actual experiment fills these in.)

## Reproducing the experiment

```bash
# 1. Generate synthetic dataset (set ANTHROPIC_API_KEY or OPENAI_API_KEY)
make seed-synthetic n=1000

# 2. Build splits
make build-dataset

# 3. (Optional) Fine-tune on a cloud GPU
modal run ml/train/modal_app.py::main         # or runpod_command.sh

# 4. Run evaluation (limit=50 for quick smoke; remove for full)
make eval                                     # or python -m eval.run_all --limit 50

# 5. Read the report
cat ml/results/eval_report.md
```

## Limitations

- The "oracle" is an LLM, not the user themselves. It is not literally ground
  truth — it is the strongest available approximation given the synthetic
  setting. For the small real-data test set, the user's actual response *is*
  ground truth.
- LLM judges have known order/format biases; we report separately to surface
  them rather than hide them.
- Style metrics tend to over-credit length/punctuation matching; embedding
  similarity helps balance this.
