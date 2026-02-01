# System Architecture

## Overview

NULL operates through four core engines working in sequence: **Genesis → Simulation → Documentation → Storage**, with a real-time presentation layer (the Omniscope) streaming simulation state to observers.

## Core Engines

### 1. Genesis Node
The world-building engine. Takes a seed prompt and generates an entire simulation environment.

**Responsibilities:**
- Parse seed prompt into world parameters (era, tech level, social structure)
- Generate initial agent personas with backgrounds, beliefs, and motivations
- Establish starting conditions (resources, power dynamics, information asymmetry)
- Define simulation rules and constraints

**Input:** Seed prompt (e.g., "Cyberpunk Joseon Dynasty, 2145 AD")
**Output:** World config + N agent personas + initial state

### 2. Hive Mind Engine
The collective intelligence layer. Agents collaboratively maintain a living wiki that documents their civilization.

**Responsibilities:**
- Real-time wiki page creation and editing by agents
- Consensus-driven fact establishment (Canon vs. Legends)
- Knowledge graph construction from agent interactions
- Contradiction detection and resolution protocols

**Storage:** PostgreSQL + pgvector for semantic search across wiki entries.

### 3. External Reality Injection
Bridges the simulation with the real world by injecting external data.

**Responsibilities:**
- Fetch real-time news, research, and data via search APIs (Tavily/Perplexity)
- Transform external events into in-world events
- Maintain injection frequency controls to prevent information overload
- Track how external data propagates through the agent network

### 4. Time Dilation Engine
Controls the temporal flow of the simulation.

**Responsibilities:**
- Accelerate or decelerate simulation time (1 real hour = N simulated years)
- Trigger epoch transitions (technological revolutions, societal shifts)
- Schedule generational events (leadership changes, cultural movements)
- Manage time-based decay and evolution of agent beliefs

## 5. WebSocket Event Streaming

Real-time bridge between the simulation backend and the Omniscope frontend.

**Event Types:**
- `agent.state` — Agent status changes (active, debating, idle, conspiring)
- `agent.message` — New conversation messages between agents
- `relation.update` — Alliance formed, broken, or shifted
- `epoch.transition` — Epoch boundary crossed, new era begins
- `event.triggered` — Random or injected event fired
- `wiki.edit` — Wiki page created or modified
- `consensus.reached` — Canon/Legends status changed

**Protocol:**
- WebSocket for bidirectional communication (Divine Intervention commands upstream)
- EventSource (SSE) fallback for read-only observers
- Message format: JSON with `{ type, timestamp, epoch, payload }` envelope
- Client-side Zustand store consumes events and updates Cosmograph state

## 6. Herald Pipeline

AI-powered narrative summarization layer that transforms raw simulation events into human-readable notifications.

**Pipeline:**
1. **Event Aggregator**: Collects significant events over a sliding window (configurable, default ~30 seconds)
2. **Significance Filter**: Scores events by narrative impact (faction shifts, betrayals, consensus changes rank highest)
3. **Prose Generator**: LLM call (lightweight model) converts scored events into narrative prose
4. **Delivery**: Pushes Herald cards to the Omniscope notification system and stores in Herald history

**"Catch Me Up" Flow:**
1. Client requests summary since last-seen timestamp
2. Backend retrieves all Herald entries in range
3. LLM generates a condensed 3-5 sentence briefing
4. Delivered as a special Herald card with extended display time

## Architecture Flow

```
[Seed Prompt]
    ↓
[Genesis Node] → World Config + Agent Personas
    ↓
[Simulation Loop]
    ├── Agent Conversations (debate, negotiate, conspire)
    ├── Event System (random events, external injections, divine intervention)
    ├── Time Dilation (epoch progression)
    └── Consensus Engine (fact establishment)
    ↓
[Hive Mind] → Wiki Pages, Knowledge Graph
    ↓
[Storage Layer] → PostgreSQL + pgvector + Redis Cache
    ↓
[Event Stream] → WebSocket / SSE
    ↓
[Omniscope] → Cosmograph + Oracle Panel + Herald + Timeline Ribbon
    ↓
[Export] → JSON / CSV / Wiki / WebM / SVG / Markdown Narratives / Training Data (ChatML / Alpaca / ShareGPT)
    ↑
[Semantic Sediment] → Entity Mentions, Taxonomy Tree, Temporal Strata, Semantic Neighbors
```

## 7. Semantic Sediment Layer

AI-driven data organization paradigm that automatically discovers and connects meaning across agent-generated content.

**Core Concepts:**
- **Entity Mentions**: NER + fuzzy match detects references to agents, wiki pages, and factions in natural language. Creates bidirectional links automatically.
- **Emergent Taxonomy**: Bottom-up category tree auto-generated via embedding clustering. No human classification needed — LLM labels clusters hierarchically.
- **Temporal Strata**: Geological-time metaphor for epoch boundaries. Each stratum records emerged concepts, faded concepts, and dominant themes.

**Background Services:**

| Service | Interval | Role |
|---------|----------|------|
| `MentionExtractor` | On save | NER + fuzzy match entity mention extraction |
| `SemanticIndexer` | 60s | Embedding generation + semantic neighbor discovery |
| `TaxonomyBuilder` | 300s | Clustering → hierarchical tree auto-generation |
| `StratumDetector` | Epoch end | Temporal layer summary, concept emergence/decay |
| `ConvergenceDetector` | 120s | Cross-world resonance detection (existing) |

**New Database Tables:**
- `entity_mentions` — Auto-extracted entity references across conversations and wiki
- `semantic_neighbors` — Embedding-based similarity relationships
- `taxonomy_nodes` — Hierarchical classification tree (self-referential)
- `taxonomy_memberships` — Entity-to-taxonomy-node mappings
- `strata` — Epoch-level temporal summaries with JSONB concept tracking
- `bookmarks` — User session-based collections

## Data Flow

1. **Seed → Genesis:** Human provides a topic/scenario seed
2. **Genesis → Agents:** Engine spawns personas with distinct worldviews
3. **Agents → Conversations:** Multi-agent debates, alliances, conflicts
4. **Conversations → Hive Mind:** Structured documentation of outcomes
5. **Hive Mind → Storage:** Persistent knowledge base with vector embeddings
6. **Storage → Semantic Sediment:** MentionExtractor, SemanticIndexer, TaxonomyBuilder process new content
7. **Sediment → Strata:** StratumDetector summarizes epoch boundaries
8. **Storage → Event Stream:** Real-time WebSocket events to connected clients
9. **Event Stream → Omniscope:** Cosmograph visualization, Oracle Panel, Herald notifications
10. **Herald Pipeline:** Parallel processing of events into narrative prose
