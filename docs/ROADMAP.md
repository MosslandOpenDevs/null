# Development Roadmap

## Phase 0: Foundation
*Project structure, documentation, and basic infrastructure.*

- [x] Define project philosophy and vision
- [x] Create documentation framework
- [ ] Set up monorepo structure (backend / frontend / shared)
- [ ] Configure development environment (Docker, CI/CD)
- [ ] Establish coding standards and linting

## Phase 1: Core Engine
*Agent orchestration and persona generation.*

- [ ] Implement Genesis Node (seed prompt → world config)
- [ ] Build persona generator (backgrounds, beliefs, motivations)
- [ ] Create agent orchestration layer (LangGraph / AutoGen)
- [ ] Implement role-based model routing
- [ ] Build basic agent communication protocol
- [ ] Unit tests for core engine components

## Phase 2: Simulation Loop
*Conversation engine and event system.*

- [ ] Implement multi-agent conversation engine
- [ ] Build event system (random events, scheduled events)
- [ ] Create consensus mechanism (Canon vs. Legends voting)
- [ ] Implement time dilation controls
- [ ] Add conversation memory management (sliding window + summary)
- [ ] Integration tests for simulation loop

## Phase 3: Hive Mind
*Auto-wiki and knowledge storage.*

- [ ] Set up PostgreSQL + pgvector
- [ ] Implement wiki page generation from conversations
- [ ] Build knowledge graph construction pipeline
- [ ] Create semantic search across wiki entries
- [ ] Implement contradiction detection
- [ ] Add wiki versioning and history

## Phase 4: God-View UI
*Dashboard implementation.*

- [ ] Set up Next.js frontend
- [ ] Implement Trinity View layout
- [ ] Build Chaos Stream (left panel) with WebSocket feed
- [ ] Build Order/Wiki browser (center panel)
- [ ] Build Analytics & Control panel (right panel)
- [ ] Implement D3.js knowledge graph visualization
- [ ] Add export functionality (JSON/CSV/Wiki)

## Phase 5: Polish & Launch
*External data integration and optimization.*

- [ ] Integrate Tavily / Perplexity for external data injection
- [ ] Implement cost monitoring and budget controls
- [ ] Performance optimization (caching, batching, queue management)
- [ ] Security audit
- [ ] Documentation finalization
- [ ] Beta testing with sample scenarios
