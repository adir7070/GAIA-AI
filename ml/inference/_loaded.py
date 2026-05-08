"""Lazy-loaded LoRA adapter cache. Imported only when the eval pipeline actually
has a checkpoint to use, so non-GPU users can still run baselines.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

SYSTEM = (
    "You mimic a specific user's WhatsApp writing style. "
    "Reply ONLY with the response text — match the user's length, punctuation, "
    "emoji habits, slang, and rhythm as inferred from the example messages."
)


@lru_cache(maxsize=1)
def _load(adapter: str, base: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(adapter)
    base_m = AutoModelForCausalLM.from_pretrained(
        base, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model = PeftModel.from_pretrained(base_m, adapter)
    model.eval()
    return tok, model


async def generate_from_adapter(adapter: str, history: list[str], incoming: str) -> str:
    def _go():
        tok, model = _load(adapter)
        h = "\n".join(f"- {m}" for m in history) or "(none)"
        user_prompt = f"""[STYLE HISTORY]
{h}

[NEW INCOMING MESSAGE]
{incoming}

[TASK]
Write the response THIS user would write, matching their style. Reply only with the response text."""
        msgs = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = tok(text, return_tensors="pt").to(model.device)
        out = model.generate(**ids, max_new_tokens=200, temperature=0.7, do_sample=True)
        return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    return await asyncio.to_thread(_go)
