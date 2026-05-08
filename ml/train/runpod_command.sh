#!/usr/bin/env bash
# Run on a RunPod A100/H100 pod. Assumes you've git-cloned the repo.
set -euo pipefail

cd "$(dirname "$0")/../.."

# Install training deps if missing
pip install -e "ml[train]"

# HF + W&B login (set via env or interactively)
if [[ -n "${HF_TOKEN:-}" ]]; then
  python -c "from huggingface_hub import login; login('$HF_TOKEN', add_to_git_credential=False)"
fi
if [[ -n "${WANDB_API_KEY:-}" ]]; then
  wandb login "$WANDB_API_KEY"
fi

cd ml
python -m train.train_qlora --config train/config.yaml
