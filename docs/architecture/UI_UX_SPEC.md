# UI/UX Specification — God-View Dashboard

## Overview

The God-View Dashboard is a **Trinity View** layout providing three simultaneous perspectives into the simulation.

## Layout: Trinity View

```
┌─────────────────┬─────────────────────┬─────────────────┐
│                  │                     │                 │
│   CHAOS STREAM   │    ORDER / WIKI     │   ANALYTICS &   │
│   (Left Panel)   │   (Center Panel)    │    CONTROL      │
│                  │                     │  (Right Panel)  │
│                  │                     │                 │
└─────────────────┴─────────────────────┴─────────────────┘
```

## Left Panel: Chaos Stream

The raw, real-time feed of all agent activity.

**Features:**
- Live conversation feed (scrollable, filterable by agent/topic)
- Agent status indicators (active, debating, idle, conspiring)
- Sentiment color coding (green: agreement, red: conflict, yellow: neutral)
- Highlight markers for key events (alliances formed, betrayals, discoveries)
- Click-to-expand for full conversation threads

## Center Panel: Order / Wiki

The structured knowledge output — the Hive Mind's wiki.

**Features:**
- Wiki page browser with search
- Real-time edit indicators (which agent is editing what)
- Canon vs. Legends distinction (verified facts vs. disputed claims)
- Knowledge graph visualization (D3.js force-directed graph)
- Timeline view of civilization history
- Diff view for wiki page evolution

## Right Panel: Analytics & Control

Simulation metrics and human control interface.

**Features:**
- Population statistics (agent count, faction breakdown, sentiment distribution)
- Time control (play, pause, fast-forward, rewind to epoch)
- Event injection (manually trigger events: war, plague, discovery)
- Export controls (select data range, format, download)
- Cost monitor (API usage, budget remaining)
- Simulation health (error rates, latency, queue depth)

## Interaction Model

- **Observer Mode (Default):** Read-only. Watch the simulation unfold.
- **Director Mode:** Inject events, adjust time, modify parameters.
- **Analyst Mode:** Focus on data export, filtering, and visualization.
