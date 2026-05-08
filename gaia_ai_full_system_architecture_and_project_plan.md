# Gaia AI
## Full Startup-Level Architecture + LLM Research Project Plan

---

# 1. Project Overview

## Goal
Gaia AI is a personalized conversational AI assistant that learns how a user writes and communicates using historical WhatsApp conversations.

The system analyzes previous chats, extracts implicit communication patterns, and generates context-aware responses that imitate the user's writing style.

The system does NOT automatically send messages at this stage.
Instead, it suggests:
- what the AI would respond
- confidence level
- optional explanations

The user decides whether to send the response.

---

# 2. Main Product Flow

## High-Level User Journey

1. User creates account
2. User connects WhatsApp via QR scan
3. System downloads conversation history
4. AI analyzes user's style
5. User selects allowed contacts/groups
6. Incoming messages are processed
7. AI generates suggested replies
8. User approves or edits
9. User corrections become future learning data

---

# 3. System Architecture

## Main Components

### Frontend
- Next.js
- React
- TailwindCSS
- Zustand or Redux
- Socket.IO client

### Backend API
- Python FastAPI
- REST API
- WebSocket server

### AI Services
- Llama 3 8B Instruct
- LoRA fine-tuning
- Embedding service
- Prompt orchestration layer

### Databases

#### PostgreSQL
Stores:
- users
- sessions
- contacts
- permissions
- settings
- feedback

#### MongoDB
Stores:
- messages
- chat history
- training samples
- AI outputs

#### Vector Database
Recommended:
- Qdrant
or
- Weaviate

Stores:
- semantic embeddings
- style embeddings
- memory retrieval

### Queue System
- Redis
- Celery or BullMQ

Used for:
- training jobs
- background processing
- embedding generation
- response generation

---

# 4. WhatsApp Integration

## Recommended Stack

### Non-Official WhatsApp Web Automation
Use:
- whatsapp-web.js

Alternative:
- Baileys

---

## QR Login Flow

### Backend creates WhatsApp session

```javascript
const { Client } = require('whatsapp-web.js');
const qrcode = require('qrcode');

const client = new Client();

client.on('qr', async (qr) => {
  const qrImage = await qrcode.toDataURL(qr);
  // send QR to frontend
});
```

---

## Frontend displays QR

```tsx
<img src={qrCode} />
```

---

## After successful login

System receives:
- chat list
- messages
- contacts
- groups

---

# 5. WhatsApp Message Pipeline

## Incoming Message Flow

```text
WhatsApp Event
→ Backend Listener
→ Message Queue
→ Context Builder
→ Style Retrieval
→ Prompt Builder
→ LLM
→ Suggested Response
→ Frontend Dashboard
```

---

# 6. Data Collection Pipeline

## Initial Sync

System downloads:
- last 1000 messages
- grouped by contact
- timestamps
- metadata

---

## Preprocessing

### Remove:
- media-only messages
- system messages
- duplicates
- spam

### Normalize:
- emojis
- whitespace
- timestamps
- language detection

---

# 7. Style Learning System

## Goal
Learn implicit user style.

NOT:
- explicit labels
- manual tone categories

YES:
- latent style behavior

---

## What AI learns implicitly

- sentence length
- punctuation patterns
- emoji usage
- slang
- formality
- response structure
- vocabulary
- rhythm
- greeting habits
- conversation pacing

---

# 8. Dataset Design

## Training Example Format

```json
{
  "user_id": "u_001",
  "history": [
    "כן אחי סגור",
    "אני בודק עכשיו",
    "שלח לי שוב"
  ],
  "incoming_message": "מה עם הפרויקט?",
  "target_response": "אני בודק עכשיו ואעדכן אותך"
}
```

---

# 9. Hybrid Dataset Strategy

## Synthetic Dataset

### Purpose
Main training source.

### Scale
- 1000 synthetic users
- 50+ interactions each

### Generation Method
LLM role-playing.

---

## Real Dataset

### Purpose
Evaluation only.

### Requirements
- opt-in consent
- anonymization
- encrypted storage

---

# 10. Synthetic User Generation

## Goal
Generate realistic users with consistent hidden communication styles.

---

## Example Prompt

```text
Create a realistic WhatsApp user.

Generate:
- natural conversations
- recurring communication patterns
- realistic slang
- emotional consistency
- informal human texting

Avoid robotic phrasing.

Generate 50 messages.
```

---

# 11. Training Pipeline

## Recommended Model

### Primary Choice
Llama 3 8B Instruct

Alternative:
- Mistral 7B

---

## Fine-Tuning Method

### QLoRA

Why:
- low GPU memory
- cheap
- fast
- practical

---

# 12. What is Fine-Tuning?

## Simple Explanation

The model already knows language.

You do NOT teach it language from zero.

Instead:
You teach it YOUR specific task.

Example:
- original model knows English
- fine-tuning teaches:
  "how THIS user responds"

---

# 13. What is LoRA?

## Simple Explanation

Normal fine-tuning changes billions of model parameters.

LoRA:
- freezes original model
- adds tiny trainable layers
- trains only those

Result:
- much cheaper
- much faster
- keeps original model knowledge

---

# 14. Understanding Layers

## Simplified Explanation

A neural network is built from layers.

Each layer:
- receives information
- transforms it
- passes it forward

Example:

Layer 1:
Understands words.

Layer 5:
Understands sentence meaning.

Layer 20:
Understands tone and context.

LoRA adds small adjustments to those layers.

---

# 15. Training Infrastructure

## Recommended GPUs

### Minimum
RTX 3090 24GB

### Better
A100
H100

---

## Training Libraries

### Python Stack

```python
transformers
trl
peft
accelerate
bitsandbytes
```

---

# 16. Example Fine-Tuning Code

```python
from transformers import AutoModelForCausalLM
from peft import LoraConfig

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B-Instruct"
)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"]
)
```

---

# 17. Prompt Construction System

## Final Runtime Prompt

```text
[CHAT HISTORY]
כן אחי סגור
אני אבדוק ואחזיר לך תשובה

[NEW MESSAGE]
מה קורה עם זה?

[TASK]
Generate a response in the same writing style.
```

---

# 18. Style Memory System

## Why Needed
Long-term user personality consistency.

---

## Stored Memory

Examples:
- preferred greetings
- recurring phrases
- vocabulary
- writing habits
- emoji behavior

---

# 19. Embedding System

## Purpose
Semantic retrieval.

---

## Embedding Models

Recommended:
- BGE-large
- e5-large
- Instructor-XL

---

# 20. Vector Search Flow

```text
Incoming Message
→ Create Embedding
→ Search Similar Conversations
→ Retrieve Relevant History
→ Build Prompt
→ Generate Response
```

---

# 21. Confidence System

## Goal
Determine whether AI should answer.

---

## Output

```json
{
  "confidence": 0.92,
  "should_reply": true
}
```

---

# 22. User Feedback Learning

## If User Edits Response

Store:
- original suggestion
- edited version
- correction delta

Use later for:
- reinforcement learning
- retraining

---

# 23. Frontend Dashboard

## Main Screens

### Login
### QR Scan
### Chat Dashboard
### AI Suggestions
### Learning Center
### Analytics
### Settings
### Permissions

---

# 24. Suggested Frontend Structure

```text
/src
  /app
  /components
  /hooks
  /services
  /store
  /styles
```

---

# 25. Example React Component

```tsx
export default function SuggestionCard() {
  return (
    <div>
      <h2>Suggested Reply</h2>
      <p>כן בטח אני בודק עכשיו</p>
    </div>
  )
}
```

---

# 26. Backend Structure

```text
/backend
  /api
  /services
  /workers
  /training
  /prompts
  /db
```

---

# 27. API Design

## Example Routes

### Auth

```http
POST /auth/login
POST /auth/register
```

### WhatsApp

```http
GET /whatsapp/qr
POST /whatsapp/connect
```

### AI

```http
POST /ai/generate
POST /ai/feedback
```

---

# 28. Security Requirements

## Critical

### Encrypt:
- messages
- chat history
- tokens
- sessions

---

## Recommended

- AES-256 encryption
- HTTPS only
- JWT authentication
- role-based access

---

# 29. Privacy Design

## Important

Users must:
- explicitly opt-in
- select allowed chats
- control stored data
- delete data anytime

---

# 30. Evaluation System

## Main Research Contribution

### Style Indistinguishability Test

---

## Goal
Check whether AI-generated responses are distinguishable from authentic user responses.

---

# 31. Evaluation Flow

```text
History + Message
→ Generate Ground Truth Response
→ Generate Model Response
→ Ask LLM Judge
→ Measure Accuracy
```

---

# 32. Judge Prompt

```text
You are given:
- a user's chat history
- a new incoming message
- two candidate responses

Determine which response better matches the user's authentic communication style.
```

---

# 33. Success Metric

## Ideal Outcome

Judge accuracy ≈ 50%

Meaning:
AI responses are indistinguishable from real user style.

---

# 34. Deployment Architecture

## Recommended Production Stack

### Frontend
- Vercel

### Backend
- Railway
or
- AWS ECS

### AI Serving
- RunPod
- Modal
- Lambda Labs

---

# 35. Production AI Serving

## Recommended

### vLLM
or
### Text Generation Inference (TGI)

Benefits:
- batching
- low latency
- scalable inference

---

# 36. Scaling Challenges

## Problems

- GPU costs
- WhatsApp reliability
- session persistence
- large context windows
- memory retrieval speed

---

# 37. Recommended MVP Scope

## MVP Features

- QR login
- history sync
- style learning
- response suggestions
- approval flow

NOT:
- autonomous sending
- voice support
- multi-agent orchestration

---

# 38. Recommended Future Features

## Future Ideas

- voice cloning
- autonomous workflows
- calendar integration
- CRM integration
- memory timelines
- multi-personality switching

---

# 39. Suggested Development Order

## Phase 1
WhatsApp connection.

## Phase 2
Message storage.

## Phase 3
Style dataset generation.

## Phase 4
Fine-tuning.

## Phase 5
Suggestion dashboard.

## Phase 6
Evaluation experiments.

## Phase 7
Optimization and deployment.

---

# 40. Final Research Framing

## Academic Positioning

This project investigates whether large-scale synthetic conversational datasets can enable personalized response generation that generalizes to real-world user communication.

The project combines:
- synthetic data generation
- implicit style learning
- LLM fine-tuning
- human-style indistinguishability evaluation

---

# 41. Final Notes

## Important Reality Check

This is a VERY ambitious project.

For the course:
- focus on the AI + evaluation
- keep production scope controlled

For startup production:
- reliability
- privacy
- scaling
- legal considerations
become major engineering challenges.

---

# 42. Recommended Immediate Next Steps

1. Build WhatsApp QR prototype
2. Save messages to database
3. Create synthetic users generator
4. Generate first 10k training samples
5. Fine-tune small model
6. Build evaluation pipeline
7. Build dashboard UI
8. Run experiments
9. Prepare presentation

---

# END

