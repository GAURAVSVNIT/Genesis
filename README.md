<div align="center">

# ✦ Genesis

### A Full-Stack, Agentic AI Content Generation Platform

*Powered by Google Gemini · Vertex AI · LangGraph · Next.js 16*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.124+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## 📖 Overview

**Genesis** (formerly Verbix AI) is a production-grade, multi-tenant AI content generation platform. It combines a **LangGraph multi-agent orchestration graph** with a rich suite of intelligence tools — trend analysis, SEO optimization, image generation, and social publishing — delivered through a modern Next.js frontend and a FastAPI backend.

Users can chat naturally with the AI to produce blog posts, social media content, and images in real time. The system automatically classifies intent, routes to the right AI agent, fetches live trend data, applies guardrails, and streams the result back to the user — all in one unified workflow.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| 🧠 **Multi-Agent Graph** | LangGraph-powered orchestration with specialized agents for planning, execution, review, and safety |
| 💬 **Intent Classification** | Automatically routes requests to the correct agent (Blog, Image, Social, etc.) |
| 📝 **Blog Generation** | SEO-optimized, long-form articles with readability scoring and keyword analysis |
| 🖼️ **Image Generation** | Vertex AI Imagen + DALL-E 3 fallback via a structured prompt pipeline |
| 📈 **Trend Intelligence** | Real-time data from Google (Serper), Twitter/X, and Reddit with Redis caching |
| 🎨 **Tone Engine** | 5 configurable tones (Analytical, Opinionated, Critical, Investigative, Contrarian) |
| 🔒 **Guardrails** | Multi-layer content safety (bias detection, harm filtering, factual grounding) |
| 🗂️ **Context & Memory** | Conversation history, RAG with pgvector embeddings, and checkpoint restoration |
| 🌐 **Social Publisher** | OAuth-connected publishing to LinkedIn and Twitter/X |
| 🔑 **Developer Portal** | API key management, usage analytics, and interactive documentation |
| 👤 **Guest Mode** | Full functionality for unauthenticated users with session-based storage |
| 💾 **Multi-Tier Caching** | Upstash Redis (L1) + PostgreSQL prompt cache (L2) with automatic invalidation |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                            │
│              Next.js 16 + React 19 + Tailwind CSS v4                │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  ┌─────────────┐    │
│  │  /home   │  │  / chat  │  │  /auth  (SSR)  │  │ /developer  │   │
│  │ Landing  │  │Interface │  │ Login/Signup   │  │   Portal    │  │
│  └──────────┘  └──────────┘  └────────────────┘  └─────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / REST
┌────────────────────────────▼────────────────────────────────────────┐
│                      FastAPI Backend (Python)                        │
│                     host: localhost:8000 / GCP                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    API Layer  (api/v1/*)                        │ │
│  │  /content  /blog  /agent  /classifier  /context  /trends       │ │
│  │  /social  /guardrails  /embeddings  /guest  /advanced          │ │
│  └───────────────────────────┬────────────────────────────────────┘ │
│                              │                                       │
│  ┌───────────────────────────▼────────────────────────────────────┐ │
│  │               LangGraph Agent Orchestration (graph/)           │ │
│  │                                                                │ │
│  │   ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │ │
│  │   │ Planner │→ │Coordinator│→ │ Executor │→ │  Reviewer   │  │ │
│  │   └─────────┘  └──────────┘  └──────────┘  └──────┬──────┘  │ │
│  │                                                     │         │ │
│  │   ┌─────────────────────────────────────────────────▼──────┐  │ │
│  │   │  Safety Agent  (bias check · harm filter · grounding)  │  │ │
│  │   └────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────┬────────────────────────────────────┘ │
│                              │                                       │
│  ┌───────────────────────────▼────────────────────────────────────┐ │
│  │                  Intelligence Modules                          │ │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────────┐   │ │
│  │  │  Trend     │  │ Tone Enhancer│  │  SEO Suite          │   │ │
│  │  │  Analyzer  │  │ (5 modes)    │  │  keyword·meta·read  │   │ │
│  │  └────────────┘  └──────────────┘  └─────────────────────┘   │ │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────────┐   │ │
│  │  │  Image     │  │   Social     │  │    RAG / Vector      │   │ │
│  │  │  Prompter  │  │  Publisher   │  │    Embeddings        │   │ │
│  │  └────────────┘  └──────────────┘  └─────────────────────┘   │ │
│  └───────────────────────────┬────────────────────────────────────┘ │
│                              │                                       │
│  ┌───────────────────────────▼────────────────────────────────────┐ │
│  │                    Core Services (core/)                       │ │
│  │  Rate Limiter · Response Cache · Guardrails · LLM Factory      │ │
│  │  Token Counter · Logging · Supabase Client · Upstash Redis     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────┬──────────────────────────┬─────────────────────┘
                     │                          │
         ┌───────────▼───────────┐   ┌──────────▼──────────┐
         │  Supabase (PostgreSQL) │   │   Upstash (Redis)   │
         │  + pgvector extension  │   │   L1 Response Cache │
         │  Users · Sessions      │   │   Trend Data Cache  │
         │  Conversations · Cache │   │   Rate Limit State  │
         │  Embeddings · Metrics  │   └─────────────────────┘
         └────────────────────────┘
```

---

## 📂 Project Structure

```
Genesis/                          # Monorepo root (pnpm workspaces + Turborepo)
├── apps/
│   ├── frontend/                 # Next.js 16 application
│   │   ├── app/
│   │   │   ├── page.tsx          # Root → redirects to /chat
│   │   │   ├── home/             # Public landing page
│   │   │   ├── chat/             # Main chat interface
│   │   │   ├── auth/             # Login / signup / callback pages
│   │   │   ├── developer/        # API key mgmt + docs portal
│   │   │   ├── settings/         # User preferences
│   │   │   └── api/              # Next.js API routes (proxies)
│   │   ├── components/           # Reusable UI components
│   │   │   ├── chat-interface.tsx
│   │   │   ├── sidebar-editor.tsx  # CKEditor 5 rich-text editor
│   │   │   ├── message-bubble.tsx
│   │   │   ├── tone-selector.tsx
│   │   │   └── ...
│   │   └── lib/                  # Utilities, hooks, API client
│   │       ├── api-client.ts
│   │       ├── supabase/         # Supabase SSR helpers
│   │       └── tone-options.ts
│   │
│   └── backend/                  # FastAPI application
│       ├── main.py               # App entry point, CORS, router registration
│       ├── api/
│       │   └── v1/               # All REST endpoints
│       │       ├── content.py    # Primary content generation endpoint
│       │       ├── blog.py       # Dedicated blog generation
│       │       ├── agent.py      # Agent graph invocation
│       │       ├── classifier.py # Intent classification
│       │       ├── context.py    # Conversation context & checkpoints
│       │       ├── guest.py      # Guest session management
│       │       ├── social.py     # Social media OAuth + posting
│       │       ├── guardrails.py # Content safety checks
│       │       ├── embeddings.py # Vector embedding endpoints
│       │       └── advanced.py   # Power-user generation features
│       ├── agents/               # LangGraph node implementations
│       │   ├── orchestrator.py   # Graph assembly & routing
│       │   ├── planner.py        # Task decomposition
│       │   ├── coordinator.py    # Agent coordination logic
│       │   ├── executor.py       # LLM call execution
│       │   ├── reviewer.py       # Output quality review
│       │   ├── blog_writer.py    # Blog-specific writer agent
│       │   └── safety.py         # Safety/guardrail agent
│       ├── graph/                # LangGraph state & pipeline
│       ├── intelligence/         # AI intelligence modules
│       │   ├── trend_collector.py   # Multi-source trend fetching
│       │   ├── trend_analyzer.py    # Scoring & insight engine
│       │   ├── tone_enhancer.py     # Prompt tone injection
│       │   ├── image_prompter.py    # Image prompt builder
│       │   ├── image_collector.py   # Image artifact storage
│       │   ├── social_publisher.py  # LinkedIn/Twitter publisher
│       │   └── seo/                 # Full SEO optimization suite
│       │       ├── optimizer.py
│       │       ├── keyword_analyzer.py
│       │       ├── readability_analyzer.py
│       │       ├── metadata_generator.py
│       │       ├── hashtag_optimizer.py
│       │       └── suggestions.py
│       ├── core/                 # Shared services
│       │   ├── config.py         # Pydantic settings (env vars)
│       │   ├── guardrails.py     # Multi-layer content safety
│       │   ├── embeddings.py     # Sentence-transformer embeddings
│       │   ├── rag_service.py    # Retrieval-augmented generation
│       │   ├── rate_limiter.py   # Per-user/guest rate limiting
│       │   ├── response_cache.py # Response caching logic
│       │   ├── llm_factory.py    # Model selection (Gemini/GPT/Groq)
│       │   ├── token_counter.py  # Token usage tracking
│       │   ├── chatgpt_cache.py  # Prompt-level cache (L2)
│       │   ├── vertex_ai.py      # Vertex AI client wrapper
│       │   └── upstash_redis.py  # Redis client singleton
│       └── database/             # DB models & migrations (Alembic)
│
├── packages/                     # Shared packages (Turborepo)
├── turbo.json                    # Turborepo pipeline config
├── pnpm-workspace.yaml
└── package.json
```

---

## 🔄 Request Lifecycle

```
User types a message in the chat interface
            │
            ▼
 ┌───────── Frontend ─────────────────────────────┐
 │  1. Captures prompt + conversation history     │
 │  2. Attaches tone, format, and safety options  │
 │  3. POSTs to /v1/content (or /v1/agent)        │
 └───────────────────────────────────────────────-┘
            │
            ▼
 ┌───────── Backend: API Layer ────────────────────┐
 │  1. Rate limit check (per user/guest/IP)        │
 │  2. Hash prompt → check L1 Redis cache          │
 │     ├── HIT  → return cached response           │
 │     └── MISS → continue                         │
 │  3. Check L2 PostgreSQL prompt cache            │
 └─────────────────────────────────────────────────┘
            │
            ▼
 ┌───────── Intent Classifier ─────────────────────┐
 │  Classifies intent into one of:                 │
 │  blog | image | social | general | research     │
 │  Extracts: topic, refined_query                 │
 └─────────────────────────────────────────────────┘
            │
            ▼
 ┌───────── Agent Graph (LangGraph) ───────────────┐
 │  Planner  →  Coordinator  →  Executor           │
 │    ↑              │               │             │
 │    │         Intelligence    LLM Factory        │
 │    │         - Trend Data    (Gemini/GPT/Groq)  │
 │    │         - Tone Prompt                      │
 │    │         - SEO Context                      │
 │    └────────── Reviewer ◄──────────────────     │
 │                   │                             │
 │               Safety Agent                      │
 │         (bias check · harm filter)              │
 └─────────────────────────────────────────────────┘
            │
            ▼
 ┌───────── Post-Processing ───────────────────────┐
 │  1. Calculate metadata (word count, sections)   │
 │  2. Compute uniqueness score (embedding diff)   │
 │  3. Store response to DB + update cache         │
 │  4. Log token usage & metrics                   │
 └─────────────────────────────────────────────────┘
            │
            ▼
      Response streamed to frontend
      with content + metadata badges
```

---

## 🧠 Agent Architecture

The backend uses **LangGraph** to assemble a directed graph of specialized agents. Each node handles a distinct phase of content creation:

| Agent | File | Responsibility |
|---|---|---|
| **Planner** | `agents/planner.py` | Decomposes user intent into sub-tasks |
| **Coordinator** | `agents/coordinator.py` | Routes sub-tasks to appropriate executors |
| **Executor** | `agents/executor.py` | Performs the actual LLM generation call |
| **Blog Writer** | `agents/blog_writer.py` | Specialized node for long-form blog drafts |
| **Reviewer** | `agents/reviewer.py` | Scores output quality; triggers re-generation if below threshold |
| **Safety** | `agents/safety.py` | Applies guardrails; blocks or modifies harmful output |
| **Orchestrator** | `agents/orchestrator.py` | Assembles the graph and manages state transitions |

---

## 📡 API Reference

All endpoints are prefixed with the base URL of the backend server.

### Content Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/content/generate` | Primary generation endpoint (text, tones, formats) |
| `POST` | `/v1/blog/generate` | Dedicated long-form blog generation |
| `POST` | `/v1/agent/invoke` | Direct LangGraph agent graph invocation |
| `POST` | `/v1/advanced/generate` | Advanced generation with fine-grained parameters |

### Intelligence

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/trends/analyze` | Analyze keywords across Google, Twitter, Reddit |
| `POST` | `/v1/trends/generate-context` | Generate trend context for the AI writer |
| `GET` | `/v1/trends/top` | Fetch current top trending topics |
| `POST` | `/v1/classifier/classify` | Classify prompt intent and extract topic |

### Context & Memory

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/context/save` | Save conversation checkpoint |
| `GET` | `/v1/context/restore/{session_id}` | Restore context from a checkpoint |
| `GET` | `/v1/context/history` | Retrieve paginated conversation history |
| `POST` | `/v1/embeddings/store` | Store content as a vector embedding |
| `POST` | `/v1/embeddings/search` | Semantic search over stored embeddings |

### Social & Publishing

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/social/auth/linkedin` | OAuth flow for LinkedIn |
| `GET` | `/v1/social/auth/twitter` | OAuth flow for Twitter/X |
| `POST` | `/v1/social/publish/linkedin` | Publish content to LinkedIn |
| `POST` | `/v1/social/publish/twitter` | Post a tweet or thread |

### Safety & Guardrails

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/guardrails/check` | Run multi-layer safety analysis on content |

### Guest & User Sessions

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/guest/session` | Create a guest session |
| `GET` | `/v1/guest/history/{guest_id}` | Fetch guest conversation history |
| `POST` | `/v1/guest/migrate` | Migrate guest data to authenticated user |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Basic liveness check |
| `GET` | `/v1/health/redis` | Redis connectivity check |

---

## 🎨 Tone Engine

The **Tone Enhancer** injects personality into every generation. Five tones are available:

| Tone | System Persona | Best For |
|---|---|---|
| `analytical` | Thoughtful analyst & critic | Deep dives, technical research |
| `opinionated` | Bold commentator with strong views | Opinion pieces, editorials |
| `critical` | Discerning critic | Reviews, evaluations |
| `investigative` | Investigative journalist | Exposés, investigative pieces |
| `contrarian` | Thoughtful contrarian | Counter-narratives, debate prep |

Each tone can be augmented with optional enrichment sections: **Critical Analysis**, **Alternative Perspectives**, **Real-World Implications**, and **Questions to Consider**.

---

## 📈 Trend Intelligence Pipeline

```
User Prompt
    │
    ▼
Keyword Extraction
    │
    ├──► Google (Serper API) ──┐
    ├──► Twitter/X API ────────┤──► Aggregator ──► Redis Cache (30 min TTL)
    └──► Reddit API ───────────┘         │
                                         ▼
                                  Trend Analyzer
                                  ┌─────────────────────────────────────┐
                                  │  Scoring (0–100):                   │
                                  │  • Keyword Match      40%           │
                                  │  • Source Credibility  20%          │
                                  │  • Engagement (log)   20%           │
                                  │  • Recency            10%           │
                                  │  • Content Quality    10%           │
                                  └─────────────────────────────────────┘
                                         │
                                         ▼
                                  AI Content Context
                                  (target audience · trending angles · keywords)
```

---

## 🔍 SEO Suite

The `intelligence/seo/` module provides a complete pipeline for content optimization:

- **`keyword_analyzer.py`** — Extracts primary and secondary keywords, scores density
- **`readability_analyzer.py`** — Flesch-Kincaid, sentence length, complexity metrics
- **`metadata_generator.py`** — Auto-generates title tags, meta descriptions, Open Graph data
- **`hashtag_optimizer.py`** — Suggests platform-specific hashtags for social posts
- **`suggestions.py`** — End-to-end improvement recommendations
- **`optimizer.py`** — Orchestrates the full SEO pass over generated content

---

## 🔒 Content Guardrails

Every piece of generated content passes through a multi-layer safety pipeline:

1. **Bias Detection** — Scans for demographic, political, and factual biases
2. **Harm Filtering** — Blocks NSFW, violent, or dangerous content
3. **Factual Grounding** — Cross-references claims with trusted sources where possible
4. **Rate Limiting** — Per-user and per-IP limits enforced via Redis

---

## 💾 Caching Architecture

| Layer | Technology | TTL | Scope |
|---|---|---|---|
| **L1** | Upstash Redis | 30 min (trends) / configurable | Trend data, rate limit counters |
| **L2** | PostgreSQL (prompt_cache table) | Persistent | Identical prompt responses |
| **Embeddings** | pgvector | Persistent | Semantic search index |

Cache keys are generated from sorted keyword lists and prompt hashes to maximize hit rates across similar queries.

---

## ⚙️ Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Node.js | 18+ |
| pnpm | 8+ |
| Python | 3.10+ |
| Supabase project | — |
| Google Cloud project (GCP) | For Vertex AI |

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/genesis.git
cd genesis
```

### 2. Backend Setup

```bash
cd apps/backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your keys (see Environment Variables section below)

# Start the development server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd apps/frontend

# Install dependencies
pnpm install

# Configure environment variables
cp .env.example .env.local
# Add your Supabase URL and Anon Key

# Start the development server
pnpm dev
```

Frontend runs on **<http://localhost:3000>** · Backend runs on **<http://localhost:8000>**

### 4. Run the Full Monorepo (Turborepo)

```bash
# From the project root
pnpm install
pnpm dev          # Starts both frontend and backend concurrently
```

---

## 🔑 Environment Variables

### Backend (`apps/backend/.env`)

```env
# ── AI Models ───────────────────────────────────────────────
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# ── Google Cloud / Vertex AI ────────────────────────────────
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=./your-service-account.json

# ── Supabase ────────────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# ── Upstash Redis ───────────────────────────────────────────
UPSTASH_REDIS_REST_URL=https://xxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxx...

# ── Trend Intelligence ──────────────────────────────────────
SERPER_API_KEY=your_serper_key          # Google Trends via Serper.dev
TWITTER_BEARER_TOKEN=AAAA...            # Twitter API v2
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=Genesis/1.0

# ── Social Publishing ───────────────────────────────────────
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
TWITTER_CLIENT_ID=...
TWITTER_CLIENT_SECRET=...

# ── CORS ────────────────────────────────────────────────────
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

### Frontend (`apps/frontend/.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧱 Technology Stack

### Frontend

| Library | Version | Purpose |
|---|---|---|
| Next.js | 16 | React framework (App Router + RSC) |
| React | 19 | UI rendering |
| Tailwind CSS | v4 | Utility-first styling |
| Shadcn/UI + Radix UI | latest | Accessible component library |
| CKEditor 5 | 47 | Rich-text sidebar editor |
| Supabase JS | 2 | Auth + realtime DB client |
| react-markdown | 10 | Markdown rendering in chat |
| Sonner | 2 | Toast notifications |
| Lucide React | latest | Icon system |

### Backend

| Library | Version | Purpose |
|---|---|---|
| FastAPI | 0.124+ | Async REST API framework |
| LangChain | 0.3+ | LLM abstraction layer |
| LangGraph | 0.2+ | Multi-agent orchestration graph |
| Google Generative AI | latest | Gemini model access |
| Vertex AI | 1.35+ | Imagen image generation |
| LangChain OpenAI | 0.1+ | GPT-4o integration |
| LangChain Groq | 0.1+ | Llama 3.3 via Groq |
| SQLAlchemy + Alembic | 2.0+ | ORM and DB migrations |
| pgvector | 0.2+ | Vector similarity search |
| Supabase Python | 2.4+ | Supabase DB/Auth client |
| sentence-transformers | 3.0+ | Local text embeddings |
| Upstash Redis | latest | Serverless Redis caching |
| PRAW | 7.7+ | Reddit API wrapper |
| Tweepy | 4.14+ | Twitter API client |
| textstat | 0.7+ | Readability scoring |
| httpx | 0.27+ | Async HTTP for trend fetching |
| BeautifulSoup4 | 4.12+ | Web scraping |

---

## 🚢 Deployment

### Vercel (Frontend)

The frontend is configured for zero-config Vercel deployment via `vercel.json`.

```bash
vercel --prod
```

### Google Cloud Platform (Backend)

A `Dockerfile` and `deploy_gcp.ps1` script are included for Cloud Run deployment.

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/genesis-backend

# Deploy to Cloud Run
gcloud run deploy genesis-backend \
  --image gcr.io/YOUR_PROJECT_ID/genesis-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

See [`apps/backend/DEPLOYMENT.md`](apps/backend/DEPLOYMENT.md) for detailed GCP instructions.

---

## 🤝 Contributing

1. Fork the Project
2. Create a Feature Branch: `git checkout -b feature/YourFeature`
3. Commit your Changes: `git commit -m 'feat: Add YourFeature'`
4. Push to the Branch: `git push origin feature/YourFeature`
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
  Built with ❤️ · Genesis AI Platform
</div>
