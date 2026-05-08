"""QLoRA fine-tuning of Llama 3 8B Instruct on the Gaia synthetic dataset.

Designed to run on a single A100 / H100 (Modal or RunPod).

Inputs (relative to ml/):
  data/synthetic/train.jsonl   — chatml format produced by dataset/build_jsonl.py
  data/synthetic/val.jsonl

Outputs:
  ./checkpoints/gaia-lora-v1/   — adapter + tokenizer
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    args = parser.parse_args()

    # Heavy ML deps imported lazily so the script can be inspected without GPU env.
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from trl import SFTConfig, SFTTrainer

    cfg = yaml.safe_load(Path(args.config).read_text())

    bnb = BitsAndBytesConfig(
        load_in_4bit=cfg.get("load_in_4bit", True),
        bnb_4bit_quant_type=cfg.get("bnb_4bit_quant_type", "nf4"),
        bnb_4bit_use_double_quant=cfg.get("bnb_4bit_use_double_quant", True),
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    print(f"Loading base model: {cfg['base_model']}")
    tokenizer = AutoTokenizer.from_pretrained(cfg["base_model"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        cfg["base_model"],
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    lora = LoraConfig(
        r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"],
        target_modules=cfg["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    train_path = Path(__file__).resolve().parents[1] / cfg["train_file"]
    val_path = Path(__file__).resolve().parents[1] / cfg["val_file"]
    ds = load_dataset(
        "json",
        data_files={"train": str(train_path), "validation": str(val_path)},
    )

    def fmt(example):
        msgs = example["messages"]
        text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    ds = ds.map(fmt, remove_columns=ds["train"].column_names)

    sft_cfg = SFTConfig(
        output_dir=cfg["output_dir"],
        num_train_epochs=cfg["num_train_epochs"],
        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        lr_scheduler_type=cfg["lr_scheduler_type"],
        warmup_ratio=cfg["warmup_ratio"],
        weight_decay=cfg["weight_decay"],
        max_seq_length=cfg["max_seq_length"],
        gradient_checkpointing=cfg["gradient_checkpointing"],
        bf16=cfg["bf16"],
        logging_steps=cfg["logging_steps"],
        eval_strategy="steps",
        eval_steps=cfg["eval_steps"],
        save_steps=cfg["save_steps"],
        save_total_limit=cfg["save_total_limit"],
        report_to=cfg.get("report_to", "none"),
        run_name=cfg.get("run_name", "gaia-lora"),
        dataset_text_field="text",
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=ds["train"],
        eval_dataset=ds["validation"],
        peft_config=lora,
        tokenizer=tokenizer,
    )
    print("Starting training…")
    trainer.train()
    trainer.save_model(cfg["output_dir"])
    tokenizer.save_pretrained(cfg["output_dir"])
    print(f"Saved adapter → {cfg['output_dir']}")


if __name__ == "__main__":
    main()
