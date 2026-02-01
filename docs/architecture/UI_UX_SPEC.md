# UI/UX Specification — The Omniscope

## Overview

The Omniscope is a **living window into the simulation world** — not a dashboard, but a cosmic observatory. The core experience is a fullscreen spatial visualization (the Cosmograph) where agents exist as luminous nodes in deep space, connected by glowing filaments of relationship.

> Metaphor shift: "Admin Panel" → "God's Observatory"

## 1. Main View: THE COSMOGRAPH

Fullscreen WebGL spatial visualization. The first screen and core experience, replacing the Trinity View 3-panel layout.

**Visual Composition:**
- Softly glowing node clusters floating over cosmic darkness (`#0a0a0f`)
- Each node = one agent. Grouped by faction like nebulae
- Luminous filaments representing relationships (alliance=blue, hostility=red, trade=gold)
- The entire visualization "breathes" — pulsing when active, electric discharge during debates, red flashes on betrayal

**Semantic Zoom (Core Innovation):**

| Zoom Level | What You See |
|---|---|
| **L1: Cosmos** | Entire factions as colored nebulae, macro statistics overlay |
| **L2: Faction** | Individual agents within a faction, internal relationships |
| **L3: Cluster** | Agents actively participating in a specific discussion |
| **L4: Conversation** | Actual messages between agents (rendered as speech bubbles) |
| **L5: Agent** | Single agent profile — beliefs, history, relationships, influence |

Continuous zoom via scroll/pinch. No discrete steps — crossfade between levels. The sensation of "a god zooming into their creation."

**Sound Design (Tone.js, Optional):**
- L1: Low drone hum, pitch shifts with overall sentiment
- Zooming in: individual agent "voices" emerge as tonal pings
- Conflict: dissonance. Alliance: harmonic resolution. Epoch transition: deep resonance

## 2. Timeline Ribbon

Horizontal strip at the bottom of the screen (~60px). Replaces discrete time controls.

- Continuous ribbon displaying simulation history (present = bright line on the right)
- Color-coded by epoch (green=prosperity, red=conflict, gold=discovery, purple=paradigm shift)
- Drag to scrub through time → Cosmograph animates to past/future states
- **Timelapse**: compress entire simulation into 60-second playback
- Click event markers → jump to that point in time + zoom to relevant agents

## 3. Oracle Panel (Replaces 3-Panel Layout)

Instead of three fixed panels, a single contextual panel that slides in from the right (frosted glass blur).

**Triggers:**
- Click agent node → Agent profile
- Click filament → Relationship history
- Click faction cluster → Faction wiki page
- Click event marker → Event details
- `/` key → Universal search / command palette

Canon text renders as solid. Legends text renders with a subtle shimmer/uncertainty effect.

## 4. Divine Intervention (Replaces Director Mode)

Spatial gestures instead of form-based controls:

- **Event Drop**: Drag event tokens from top toolbar onto the map (lightning=crisis, scroll=discovery, skull=plague, crown=leadership change)
  - Drop on empty space = global event
  - Drop on faction = faction event
  - Drop on agent = personal event
- **Whisper Mode**: Right-click an agent → text input → injected as "inner voice" into the agent's next reasoning cycle
- **Seed Bomb**: Drop a topic onto a region → agents in that area begin discussing the topic → ripple visualization

## 5. Notification System: THE HERALD

Non-intrusive notification cards in the upper-left corner (auto-dismiss after 8 seconds).

- **Narrative Beats**: "The Harmony Collective has proposed a compromise on the neural implant legislation" (AI-generated prose)
- **Paradigm Shifts**: "Agent-023 has defected from Royal Loyalists to the Free Spirit Union" + [Observe] button
- **Tension Alerts**: Displayed before conflict erupts → builds anticipation
- **"Catch me up" button**: AI summary of events since last check (3-5 sentences)

## 6. Bookmarks & Export: THE ARCHIVE

- `B` key for one-click bookmark of current view state
- **Story Arc Export**: System auto-detects narrative arcs (setup→crisis→climax→resolution) and exports as Markdown narrative / JSON / SVG timeline
- **Clip Recording**: `R` key to start/stop recording → export as WebM video or data bundle

## 7. Ambient/Mobile Mode: THE AQUARIUM

- UI chrome removed, Cosmograph fullscreen only — for second screens or screensavers
- Mobile: tap=zoom, swipe=timeline scrub, long-press=Oracle card
- Push notifications (paradigm shifts, major events) opt-in
- Portrait mode: Cosmograph on top + Herald feed on bottom

## 8. Visual Language

- **Background**: `#0a0a0f` (cosmic black)
- **Nodes**: Faction-colored, bioluminescent feel (not neon)
- **Typography**: UI=Inter, Wiki/Narrative=Serif (Source Serif Pro), Agent quotes=Monospace
- **Animation**: Slow and organic. No Material Design snaps. Gravitational easing
- **UI Separation**: No borders/cards/shadows. Brightness differentiates elements. Emerging from darkness into light

## 9. Interaction Modes

- **Observer Mode (Default):** Explore the Cosmograph, browse the Oracle Panel, scrub the Timeline. Read-only.
- **Intervener Mode:** Drag event tokens, whisper to agents, drop seed bombs. Spatial interaction with the simulation.
- **Archivist Mode:** Bookmark states, record clips, export story arcs. Focus on capture and documentation.

## 10. Internationalization (i18n)

- **Default language**: English
- **Supported languages**: English, Korean (한국어)
- Language toggle in the Omniscope UI (top-right corner, minimal icon)
- User preference persisted in `localStorage` and respected across sessions
- All Herald notifications, Oracle Panel content, and UI labels rendered in the selected language
- Wiki content (agent-generated) remains in the simulation's native language; UI chrome switches independently
- URL structure: `/en/...` (default), `/ko/...` for Korean

## 11. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Framework | Next.js (App Router) | Maintained from previous spec |
| Cosmograph Rendering | **Three.js + Custom Shaders** | D3 cannot achieve organic particle effects at 150+ nodes |
| Physics Layout | d3-force | Physics engine only (rendering via Three.js) |
| Audio | Tone.js | Generative ambient soundscape |
| State Management | Zustand | Lightweight, suited for real-time streaming |
| Real-time Data | WebSocket + EventSource | Agent activity streams |
| Mobile | PWA | Offline bookmarks, push notifications |
