# Model Strategy

## Role-Based Model Allocation

Each agent role in the simulation is assigned to a specific LLM tier based on the complexity and importance of its function.

| Role | Model | Tier | Purpose |
|---|---|---|---|
| **Genesis Architect** | GPT-4o / Claude Opus | Premium | World-building, persona generation, scenario design |
| **Main Debater** | GPT-4o | Premium | Core arguments, logical reasoning, position defense |
| **Reaction Agent** | GPT-4o-mini | Standard | Quick responses, emotional reactions, crowd behavior |
| **Chaos Joker** | Claude Sonnet | Mid | Contrarian positions, chaos injection, devil's advocate |
| **Searcher** | Gemini Flash + Tavily | Standard | External data retrieval, fact-checking, news injection |
| **Librarian** | GPT-4o-mini | Standard | Wiki maintenance, summarization, knowledge graph updates |

## Cost Optimization Strategy

### Tiered Processing
- **Premium tier** (GPT-4o, Claude Opus): Used only for genesis events, key debates, and critical decision points
- **Standard tier** (GPT-4o-mini, Gemini Flash): Used for bulk conversations, reactions, and maintenance tasks
- **Target ratio:** 20% premium / 80% standard calls

### Batch Updates
- Wiki updates are batched (every N conversation turns, not real-time)
- Knowledge graph reconstruction runs on schedule, not per-interaction
- External data injection is rate-limited (configurable interval)

### Caching Strategy
- Agent persona definitions cached in Redis
- Frequently referenced wiki pages cached with TTL
- Conversation context windows managed with sliding window + summary

### Estimated Cost Model
| Scenario | Agents | Duration | Est. Cost |
|---|---|---|---|
| Small (10 agents, 1 epoch) | 10 | ~1 hour | $2–5 |
| Medium (50 agents, 5 epochs) | 50 | ~6 hours | $15–30 |
| Large (200 agents, 20 epochs) | 200 | ~24 hours | $80–150 |
