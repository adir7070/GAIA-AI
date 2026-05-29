# Gaia AI - Evaluation Report

- Created: 2026-05-29T09:31:34.041062+00:00
- Test size: 18

## Results

| Model | Indist. Acc | 95% CI | Style Sim | Relevance |
|---|---|---|---|---|
| zero_shot | 41.67% | [27.14%, 57.80%] | 0.905 ± 0.012 | 3.39 ± 1.34 |
| few_shot | 52.78% | [37.01%, 68.01%] | 0.902 ± 0.020 | 3.56 ± 1.42 |

## Interpretation

- **Indistinguishability accuracy ≈ 50%** = the LLM judge cannot reliably tell our model's responses from the oracle's; this is the SUCCESS condition (per spec §33 and lecturer feedback).
- **Style similarity** (cosine in a multilingual embedding space) is a complementary metric; higher is stylistically closer to the user.
- **Relevance** ensures the response actually addresses the message (style without content is not useful).