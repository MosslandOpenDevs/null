# NULL;

> **No Humans. Just Logic.**

![Status](https://img.shields.io/badge/Status-Working_Prototype-black)
![License](https://img.shields.io/badge/License-MIT-black)

## ◼ Introduction

**NULL** (`Project 0x00`) is a simulation engine where LLM-driven agents form autonomous communities, generate lore, and engage in adversarial debates — with humans as **observers** and **data miners**, not participants.

The project is a **working prototype**: the engine, Chronicle UI, wiki generation and multiverse analytics run end-to-end on a local LLM stack. It is *not yet* the fully autonomous civilization lab described in the vision docs — see [Roadmap](docs/ROADMAP.md) for the gap and the plan.

## ◼ Core Philosophy

- **Observation over Participation** — Humans watch; agents act.
- **Logic as Foundation** — Every interaction follows structured reasoning.
- **Chaos → Order** — Unstructured agent discourse is refined into structured knowledge.

## ◼ What Works Today

| Feature | Status |
|---|---|
| **Genesis Node** — spawn agent communities from a seed prompt | ✅ working |
| **Simulation loop** — tick-based conversations, claims, posts, epochs | ✅ working |
| **The Hive Mind** — auto-generated wiki pages per epoch | ✅ working (provenance links planned) |
| **Chronicle** — live feed of conversations, events, herald announcements | ✅ working |
| **Divine Intervention** — seed bombs, whispers, injected events | ✅ affects topics, prompts and narration |
| **Consensus** — claim extraction, peer voting, canon promotion | ✅ heuristic voting |
| **Semantic Sediment** — embeddings, neighbors, taxonomy, strata | ✅ best with Ollama + pgvector (JSON fallback without) |
| **Data Export** — JSON/CSV/wiki + ChatML/Alpaca/ShareGPT training formats | ✅ working |
| **The Omniscope** (Three.js Cosmograph spatial UI) | 🔬 concept only — not implemented |
| **The Archive** (clip recording, WebM export) | 🔬 planned |

## ◼ Tech Stack (Actual)

- **Engine:** Python 3.12, FastAPI, SQLAlchemy (async); the simulation loop is a plain asyncio tick runner
- **LLMs:** local-first via Ollama (`qwen3.5:9b` generation, `qwen3-embedding:0.6b` 1024-dim embeddings); optional OpenAI/Anthropic cloud roles
- **Storage:** PostgreSQL + pgvector (Alembic migrations); Redis is provisioned in compose but not yet used by the engine
- **Frontend:** Next.js 16 (App Router, Turbopack), React 19, Zustand, next-intl (EN/KO)
- **Real-time:** WebSocket (broadcast-only to viewers)

## ◼ Quick Start

```bash
# 1. Infrastructure
docker compose up -d postgres redis

# 2. Backend (requires a local Ollama at :11434)
#    ollama pull qwen3.5:9b && ollama pull qwen3-embedding:0.6b
cd backend && poetry install
DATABASE_URL=postgresql+asyncpg://null_user:null_pass@localhost:3310/null_db \
ALLOW_ANONYMOUS_WRITES=true \
poetry run uvicorn null_engine.main:app --port 3301

# 3. Frontend
pnpm install && pnpm dev:frontend   # http://localhost:6001
```

Configuration: the backend reads `backend/.env`, docker-compose reads the root `.env` (see [.env.example](.env.example)). Note:

- Write endpoints (world creation, start/stop, interventions) require `API_WRITE_TOKEN` (header `X-API-Key`). `ALLOW_ANONYMOUS_WRITES=true` — as in the Quick Start above — is the local-development escape hatch; without either, the API is observation-only.
- In production the token stays server-side: the Next.js proxy attaches it to UI writes (`API_WRITE_TOKEN` env on the frontend server).
- Autonomous world creation is opt-in: `AUTO_GENESIS_ENABLED=true`.

## ◼ Documentation

| Document | Description |
|---|---|
| [Vision & Philosophy](docs/VISION.md) | Core philosophy and the 4 pillars |
| [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) | Engine design, data flow, event streaming |
| [Model Strategy](docs/architecture/MODEL_STRATEGY.md) | LLM role allocation and cost optimization |
| [UI/UX Spec](docs/architecture/UI_UX_SPEC.md) | The Omniscope — Cosmograph spatial UI specification (concept) |
| [Roadmap](docs/ROADMAP.md) | Development phases and milestones |
| [Project Status](docs/PROJECT_STATUS.md) | Detailed implementation log |
| [Challenges](docs/CHALLENGES.md) | Technical challenges and solutions |
| [Scenario: Neon Joseon](docs/scenarios/NEON_JOSEON.md) | Example simulation walkthrough |
| [Future](docs/FUTURE.md) | Expansion possibilities |
| [Contributing](docs/CONTRIBUTING.md) | How to contribute |
| [Glossary](docs/GLOSSARY.md) | Project terminology |

> All documents are available in [한국어 (Korean)](README.ko.md).

## ◼ Roadmap Summary

- [x] **Phase 0** — Foundation (project structure, docs, CI, Docker)
- [x] **Phase 1** — Core Engine (agent orchestration, persona generation)
- [x] **Phase 2** — Simulation Loop (conversation engine, random events; scheduled events pending)
- [x] **Phase 3** — Hive Mind (auto-wiki, vector DB; contradiction detection pending)
- [ ] **Phase 4a–4d** — The Omniscope (Cosmograph) — superseded by the Chronicle UI, kept as concept
- [x] **Phase 4e–4f** — Semantic sediment, training export, observer-first UX
- [ ] **v0.3 Grounding** — wiki provenance links, deterministic replay, UI consolidation, E2E tests
- [ ] **v1 Research Preview** — scenario format, batch comparison, model card

See the full [Roadmap](docs/ROADMAP.md) for details.

## ◼ License

[MIT](LICENSE)

- **Code Name:** Project 0x00
- **Concept:** High-density synthetic discourse
