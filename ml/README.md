# Gaia ML

Synthetic data generation, fine-tuning (QLoRA on Llama 3 8B), and evaluation
(Style Indistinguishability + relevance + similarity) for the Gaia AI project.

## Pipeline

```
1. synthetic/generate_personas.py     → data/synthetic/personas.jsonl
2. synthetic/generate_histories.py    → data/synthetic/histories.jsonl
3. synthetic/generate_pairs.py        → data/synthetic/pairs.jsonl
4. dataset/build_jsonl.py             → data/synthetic/{train,val,test}.jsonl
5. train/train_qlora.py               → checkpoints/gaia-lora-v1/
6. eval/run_all.py                    → results/eval_report.{json,md}
```

## Quickstart

```bash
# generate small set first to smoke-test
python -m synthetic.generate_personas --n 5
python -m synthetic.generate_histories
python -m synthetic.generate_pairs
python -m dataset.build_jsonl
python -m eval.run_all   # baselines only (no fine-tune yet)
```

## Scaling to 1000 users

```bash
python -m synthetic.generate_personas --n 1000 --concurrency 8
python -m synthetic.generate_histories --concurrency 8
python -m synthetic.generate_pairs --pairs-per-user 50 --concurrency 8
python -m dataset.build_jsonl
```

## Cloud GPU training (Modal)

See `train/modal_app.py`. Run `modal run train/modal_app.py::main` after configuring HF + W&B tokens.

## Cloud GPU training (RunPod)

See `train/runpod_command.sh`. Spin up an A100/H100 pod with the deep-learning template, sync this repo, and run the script.
