# NULL

> **No humans in the loop. Observe the simulation.**

<p align="center">
  <img src="./docs/assets/readme/hero.svg" alt="NULL hero" width="100%"/>
</p>

## Vision

NULL is a synthetic society laboratory:
- run forward simulations,
- inspect emergent behavior,
- and build reverse-inference hypotheses from outcomes.

## Core Modes

- **Forward**: initial rules/conditions → outcome trajectories
- **Inverse**: observed outcomes → plausible generating conditions

## Screenshots

![NULL Home](./docs/assets/screenshots/home.png)

## Architecture Direction

```mermaid
flowchart LR
  Seed[Seed Scenario] --> Swarm[Agent Swarm]
  Swarm --> Events[Event Stream]
  Events --> Knowledge[Structured Knowledge Layer]
  Events --> UI[Observer UI]
  Knowledge --> Export[JSON/CSV/Training Exports]
```

## Repo Map

- `backend/` simulation runtime
- `frontend/` observer interface
- `docs/` design and roadmap
- `scripts/ops-check.sh` operational verifier

## Quick Start

```bash
npm install
docker compose up -d
```

## Operations

```bash
bash scripts/ops-check.sh
```

## Security Notes

- Use synthetic datasets in examples.
- Do not expose private infrastructure metadata in docs/screenshots.

## License

MIT (or project-defined license)
