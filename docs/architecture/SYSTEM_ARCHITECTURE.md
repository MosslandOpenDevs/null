# System Architecture

## Overview

NULL operates through four core engines working in sequence: **Genesis → Simulation → Documentation → Storage**.

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

## Architecture Flow

```
[Seed Prompt]
    ↓
[Genesis Node] → World Config + Agent Personas
    ↓
[Simulation Loop]
    ├── Agent Conversations (debate, negotiate, conspire)
    ├── Event System (random events, external injections)
    ├── Time Dilation (epoch progression)
    └── Consensus Engine (fact establishment)
    ↓
[Hive Mind] → Wiki Pages, Knowledge Graph
    ↓
[Storage Layer] → PostgreSQL + pgvector + Redis Cache
    ↓
[Export] → JSON / CSV / Wiki / API
```

## Data Flow

1. **Seed → Genesis:** Human provides a topic/scenario seed
2. **Genesis → Agents:** Engine spawns personas with distinct worldviews
3. **Agents → Conversations:** Multi-agent debates, alliances, conflicts
4. **Conversations → Hive Mind:** Structured documentation of outcomes
5. **Hive Mind → Storage:** Persistent knowledge base with vector embeddings
6. **Storage → Dashboard:** God-View visualization and export
