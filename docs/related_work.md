# Gaia AI — Previous Work / Related Work

A review of prior scientific work most relevant to Gaia AI, organized into the four
pillars our project combines: **(1) parameter-efficient fine-tuning**, **(2) synthetic
data generation**, **(3) LLM personalization / persona-conditioned generation**, and
**(4) LLM-as-a-judge evaluation**. All entries are real, peer-reviewed papers; arXiv
IDs are given for verification.

## Comparison table

| # | Paper (year, venue) | Task | Methods | Data | Key results | Relation to Gaia AI |
|---|---|---|---|---|---|---|
| 1 | **LoRA: Low-Rank Adaptation of Large Language Models** — Hu et al., 2022, ICLR (arXiv:2106.09685) | Parameter-efficient adaptation of large pretrained LMs | Freeze base weights; inject trainable low-rank matrices into attention projections | GPT-2/GPT-3, GLUE, E2E NLG | Matches/*beats* full fine-tuning with ~10,000× fewer trainable params; no added inference latency | The adaptation mechanism underneath our fine-tuned model — we add LoRA adapters to `q/k/v/o` of Llama-3-8B |
| 2 | **QLoRA: Efficient Finetuning of Quantized LLMs** — Dettmers et al., 2023, NeurIPS (arXiv:2305.14314) | Memory-efficient fine-tuning of large LMs on a single GPU | 4-bit NormalFloat (NF4) quantization + LoRA + double quantization + paged optimizers | OASST1, Vicuna benchmark | Fine-tunes a 65B model on one 48GB GPU; Guanaco reaches 99.3% of ChatGPT on Vicuna | **Our exact training method** (NF4 4-bit + LoRA r=16, α=32) — lets us fine-tune Llama-3-8B cheaply on synthetic data |
| 3 | **Self-Instruct: Aligning LMs with Self-Generated Instructions** — Wang et al., 2023, ACL (arXiv:2212.10560) | Improving instruction-following without human-labeled data | Bootstrap a seed set; the LM generates new instructions+instances; filter; fine-tune on its own outputs | 52K generated instructions from 175 seeds | +33% on SuperNI over vanilla GPT-3; on par with InstructGPT-001 | Validates our **"no data → generate synthetic training data with an LLM"** strategy; we extend it from generic instructions to *persona-conditioned* triples |
| 4 | **Judging LLM-as-a-Judge with MT-Bench & Chatbot Arena** — Zheng et al., 2023, NeurIPS D&B (arXiv:2306.05685) | Scalable evaluation of open-ended LLM outputs | Use a strong LLM as an automatic judge; study position/verbosity/self-enhancement biases and mitigations | MT-Bench (80 Q, 3K expert votes), Chatbot Arena (30K convos) | GPT-4 judge agrees with humans >80% (≈ human–human agreement); documents and mitigates judge biases | The basis of our **Style-Indistinguishability** metric and its **bias mitigations** (order randomization, separate judge model) |
| 5 | **LaMP: When Large Language Models Meet Personalization** — Salemi et al., 2024, ACL (arXiv:2304.11406) | Benchmark for personalized LM outputs | Retrieval-augmented personalization from user profiles; 7 personalized tasks (classification + generation) | LaMP benchmark (per-user profiles) | Retrieval of user history substantially improves personalized generation/classification | Closest "personalization" framing to ours; we differ by learning style **implicitly via fine-tuning** (not only retrieval) and by an **indistinguishability** metric |
| 6 | **Personalizing Dialogue Agents: "I have a dog, do you have pets too?" (PersonaChat)** — Zhang et al., 2018, ACL (arXiv:1801.07243) | Persona-grounded, consistent chit-chat | Condition dialogue models on explicit profile sentences; collect crowd dialogues | PersonaChat (≈1.1K personas, 160K utterances) | Profile conditioning yields more consistent, engaging, persona-faithful dialogue | Early evidence that persona conditioning works; we move from **explicit profile sentences** to **implicit latent style** learned from a user's own message history |

## How Gaia AI differs (the novelty in one paragraph)

Prior work either (a) personalizes via **explicit** profiles/retrieval (LaMP, PersonaChat),
(b) generates **generic** synthetic instruction data (Self-Instruct), or (c) studies
**efficient fine-tuning** and **LLM judging** as separate tools (LoRA/QLoRA, MT-Bench).
Gaia AI **composes all four**: it generates a large **persona-conditioned** synthetic
corpus where each user has a *hidden* style seed, fine-tunes Llama-3-8B with QLoRA to
learn that style **implicitly** (no style labels at train time), and evaluates success
not with a soft similarity score but with a **Style-Indistinguishability** test where an
LLM judge tries to tell the model's reply from the user's — target accuracy ≈ 50%
(chance). This combination — implicit style learning from synthetic personas, judged by
indistinguishability — is the project's contribution.

## Sources
- LoRA — https://arxiv.org/abs/2106.09685
- QLoRA — https://arxiv.org/abs/2305.14314 · NeurIPS: https://proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87871436031bdc0f2beaa62a049b-Abstract-Conference.html
- Self-Instruct — https://aclanthology.org/2023.acl-long.754/ · https://arxiv.org/abs/2212.10560
- LLM-as-a-Judge (MT-Bench) — https://arxiv.org/abs/2306.05685 · https://papers.nips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html
- LaMP — https://aclanthology.org/2024.acl-long.399/ · https://arxiv.org/abs/2304.11406
- PersonaChat — https://aclanthology.org/P18-1205/ · https://arxiv.org/abs/1801.07243
