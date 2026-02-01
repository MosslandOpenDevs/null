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

## Phase 4: The Omniscope
*Cosmograph-based spatial UI implementation.*

### Phase 4a: Cosmograph Core
- [ ] Set up Next.js frontend with Three.js integration
- [ ] Implement WebGL Cosmograph renderer (nodes, filaments, faction nebulae)
- [ ] Build d3-force physics layout feeding into Three.js
- [ ] Implement custom shaders for bioluminescent node effects
- [ ] Create breathing/pulsing animation system
- [ ] WebSocket event stream integration with Zustand store

### Phase 4b: Semantic Zoom & Navigation
- [ ] Implement 5-level semantic zoom (Cosmos → Faction → Cluster → Conversation → Agent)
- [ ] Build crossfade transitions between zoom levels
- [ ] Implement Timeline Ribbon with epoch color-coding and time scrubbing
- [ ] Add timelapse playback mode (compressed simulation replay)

### Phase 4c: Oracle Panel & Herald
- [ ] Build slide-in Oracle Panel (frosted glass, context-triggered)
- [ ] Implement agent profile, relationship history, faction wiki views
- [ ] Build Herald notification system (narrative beats, paradigm shifts, tension alerts)
- [ ] Implement "Catch me up" AI summary feature
- [ ] Add universal search / command palette (`/` key)

### Phase 4d: Divine Intervention & Export
- [ ] Implement Event Drop system (drag tokens onto Cosmograph)
- [ ] Build Whisper Mode (right-click agent → inject inner voice)
- [ ] Create Seed Bomb mechanic (topic drop → ripple visualization)
- [ ] Implement Archive system (bookmarks with `B`, clip recording with `R`)
- [ ] Build story arc auto-detection and export (Markdown / JSON / SVG)
- [ ] Add Aquarium Mode (chromeless fullscreen, mobile PWA)

## Phase 4e: Semantic Sediment
*Automatic data organization and entity intelligence.*

- [x] Entity Mentions — NER + fuzzy match auto-detection in conversations and wiki
- [x] Semantic Indexer — Background embedding generation + neighbor discovery (60s)
- [x] Taxonomy Builder — Bottom-up clustering into hierarchical tree (300s)
- [x] Stratum Detector — Epoch-level temporal summaries with concept tracking
- [x] Entity Graph API — Mentions, neighbors, full entity graph per world
- [x] Taxonomy API — Tree browsing, node details, world filtering
- [x] Strata API — Temporal layer listing and details
- [x] Bookmarks — User session-based collections with bulk export
- [x] Training Data Export — ChatML, Alpaca, ShareGPT format support
- [x] Frontend: TaxonomyTreeMap, EntityCard, StrataTimeline, BreadcrumbBar
- [x] Frontend: BookmarkDrawer, SemanticSidebar, StrataTab in IntelPanel
- [x] Frontend: Wiki mention highlighting, entity graph overlay, taxonomy CommandPalette

## Phase 5: Polish & Launch
*External data integration and optimization.*

- [ ] Integrate Tavily / Perplexity for external data injection
- [ ] Implement cost monitoring and budget controls
- [ ] Performance optimization (caching, batching, queue management)
- [ ] Optional Tone.js generative audio integration
- [ ] Security audit
- [ ] Documentation finalization
- [ ] Beta testing with sample scenarios
