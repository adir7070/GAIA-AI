"""Inference helper for the fine-tuned LoRA adapter.

Usage:
  python -m inference.generate --adapter ./checkpoints/gaia-lora-v1
"""
from __future__ import annotations

import argparse
from pathlib import Path

SYSTEM = (
    "You mimic a specific user's WhatsApp writing style. "
    "Reply ONLY with the response text — match the user's length, punctuation, "
    "emoji habits, slang, and rhythm as inferred from the example messages."
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", required=True)
    p.add_argument("--base", default="meta-llama/Meta-Llama-3-8B-Instruct")
    p.add_argument("--history", nargs="*", default=[])
    p.add_argument("--incoming", required=True)
    p.add_argument("--max-new-tokens", type=int, default=200)
    args = p.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.adapter)
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model = PeftModel.from_pretrained(base, args.adapter)
    model.eval()

    history_block = "\n".join(f"- {h}" for h in args.history) or "(none)"
    user_prompt = f"""[STYLE HISTORY]
{history_block}

[NEW INCOMING MESSAGE]
{args.incoming}

[TASK]
Write the response THIS user would write, matching their style. Reply only with the response text."""
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = tok(text, return_tensors="pt").to(model.device)
    out = model.generate(**ids, max_new_tokens=args.max_new_tokens, temperature=0.7, do_sample=True)
    print(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))


if __name__ == "__main__":
    main()
