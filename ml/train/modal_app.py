"""Run train_qlora.py on Modal with an A100.

Setup once:
  pip install modal
  modal token new
  modal secret create huggingface HF_TOKEN=xxx
  modal secret create wandb WANDB_API_KEY=xxx

Run:
  modal run ml/train/modal_app.py::main
"""
from __future__ import annotations

import modal

stub = modal.App("gaia-train")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "torch>=2.4",
        "transformers>=4.45",
        "peft>=0.13",
        "trl>=0.11",
        "accelerate>=0.34",
        "bitsandbytes>=0.43",
        "datasets>=3.0",
        "wandb>=0.18",
        "pyyaml>=6.0",
    )
)

volume = modal.Volume.from_name("gaia-checkpoints", create_if_missing=True)


@stub.function(
    image=image,
    gpu="A100-80GB",
    timeout=60 * 60 * 8,
    volumes={"/checkpoints": volume},
    secrets=[
        modal.Secret.from_name("huggingface"),
        modal.Secret.from_name("wandb"),
    ],
    mounts=[modal.Mount.from_local_dir(".", remote_path="/workspace")],
)
def train():
    import os
    import subprocess
    os.chdir("/workspace/ml")
    # redirect output_dir to mounted volume
    cfg = "train/config.yaml"
    subprocess.check_call(["python", "-m", "train.train_qlora", "--config", cfg])
    subprocess.check_call(["cp", "-r", "checkpoints/gaia-lora-v1", "/checkpoints/"])


@stub.local_entrypoint()
def main():
    train.remote()
