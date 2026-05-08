# Gaia AI - Prompt Library

All prompts live in `backend/app/prompts/` and are imported by both the runtime
generation path and the synthetic-data generation pipeline (so they stay in sync).

## Runtime generation prompt

`backend/app/prompts/runtime.py` — what the model sees in production when an
incoming message arrives.

```
You are mimicking a specific human user's WhatsApp writing style.
You are NOT a chatbot. You write exactly like THIS user does, learning their style from the messages below.

[STYLE HISTORY - past messages by this user, semantically similar to the topic]
{history}        # top-k (default 12) from Qdrant retrieval

[RECENT TURNS WITH THIS CONTACT - most recent first; IN = received, OUT = user's prior reply]
{recent}        # last N (default 8) from Mongo

[NEW INCOMING MESSAGE]
{incoming}

[TASK]
Write the response THIS user would write.
- Match their sentence length, punctuation, emoji habits, slang, level of formality, and rhythm.
- Reply only with the response text. No labels, no quotes, no explanations.
- If you genuinely cannot tell what the user would say, output the single token: __UNSURE__
```

The runtime prompt deliberately **does not describe the user's style explicitly**
(implicit style learning, per spec §7).

## Style Indistinguishability judge prompt

`backend/app/prompts/judge.py` — used by the eval pipeline to compare an oracle
response (LLM that knew the latent style) against our model's response.

```
You are an expert judge of personal writing style on WhatsApp.

You will be given:
1. A user's chat history.
2. A new incoming message addressed to the user.
3. Two candidate responses, A and B. Exactly one was written by the actual user; the other was generated.

Decide which response was MORE LIKELY written by the same user, based on style cues
(length, punctuation, emojis, slang, rhythm, vocabulary, formality, greeting habits).
Ignore which response is "better" or "more correct" - judge ONLY by stylistic resemblance.

[USER'S CHAT HISTORY]
{history}

[INCOMING MESSAGE]
{incoming}

[RESPONSE A]
{response_a}

[RESPONSE B]
{response_b}

Reply with exactly one character: A or B.
```

## Relevance judge prompt

```
Rate how well the response addresses the incoming message on a 1-5 scale.
1 = ignores or contradicts; 3 = partially relevant; 5 = fully addresses.

[INCOMING MESSAGE]
{incoming}

[RESPONSE]
{response}

Reply with a single digit 1-5.
```

## Synthetic persona generator

`backend/app/prompts/synthetic_user.py` — used by `ml/synthetic/generate_personas.py`.

The seed object (sampled from a diversity matrix in
`ml/synthetic/_diversity.py`) is passed into the prompt; the LLM produces a
persona summary + topics. The seed is preserved alongside the persona in
`personas.jsonl` for downstream oracle generation, but **never** ends up in the
training data fed to the fine-tuned model.

## Synthetic history + pair generators

`backend/app/prompts/synthetic_chat.py` — message and target-response generators.
The pair generator's "oracle" prompt receives the full hidden-style seed; this is
what makes the oracle the upper bound (lecturer feedback, gpt.md).

## Bias mitigations (very important for the eval)

1. **Order randomization**: every (oracle, model) pair is judged twice — once
   with oracle as A, once as B. Reported separately + averaged.
2. **Generator ≠ Judge providers**: if both Anthropic and OpenAI keys are
   available, the oracle uses one and the judge uses the other. See
   `ml/eval/indistinguishability.py::_judge_provider()`.
3. **No style leakage**: the judge prompt never sees the persona seed.
4. **Per-user split**: `dataset/build_jsonl.py` splits by user, not by example,
   so test-set users don't appear in train.
