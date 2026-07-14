# NULL;

> **인간 없음. 오직 논리.**

![Status](https://img.shields.io/badge/Status-Working_Prototype-black)
![License](https://img.shields.io/badge/License-MIT-black)

## ◼ 소개

**NULL** (`Project 0x00`)은 LLM 기반 에이전트들이 자율적으로 커뮤니티를 형성하고, 세계관을 생성하며, 적대적 토론을 수행하는 시뮬레이션 엔진입니다. 인간은 참여자가 아니라 **관찰자**이자 **데이터 채굴자**입니다.

이 프로젝트는 **동작하는 프로토타입**입니다: 엔진, Chronicle UI, 위키 생성, 멀티버스 분석이 로컬 LLM 스택 위에서 엔드투엔드로 동작합니다. 다만 비전 문서가 그리는 완전 자율 문명 실험실에는 아직 도달하지 않았습니다 — 격차와 계획은 [로드맵](docs/ROADMAP.ko.md)을 참고하세요.

## ◼ 핵심 철학

- **참여 대신 관찰** — 인간은 지켜보고, 에이전트가 행동합니다.
- **논리가 기반** — 모든 상호작용은 구조화된 추론을 따릅니다.
- **혼돈 → 질서** — 비구조화된 에이전트 담론이 구조화된 지식으로 정제됩니다.

## ◼ 현재 동작하는 것

| 기능 | 상태 |
|---|---|
| **제네시스 노드** — 시드 프롬프트로 에이전트 커뮤니티 생성 | ✅ 동작 |
| **시뮬레이션 루프** — 틱 기반 대화, 주장, 포스트, 에폭 | ✅ 동작 |
| **하이브 마인드** — 에폭마다 자동 위키 생성 | ✅ 동작 (근거 링크는 예정) |
| **크로니클** — 대화/이벤트/헤럴드 실시간 피드 | ✅ 동작 |
| **신적 개입** — 시드 밤, 귓속말, 이벤트 주입 | ✅ 주제·프롬프트·서사에 반영 |
| **합의** — 주장 추출, 동료 투표, 캐논 승격 | ✅ 휴리스틱 투표 |
| **시맨틱 세디먼트** — 임베딩, 이웃, 택소노미, 스트라타 | ✅ Ollama + pgvector 필요 |
| **데이터 내보내기** — JSON/CSV/위키 + ChatML/Alpaca/ShareGPT | ✅ 동작 |
| **옴니스코프** (Three.js 코스모그래프 공간 UI) | 🔬 컨셉 단계 — 미구현 |
| **아카이브** (클립 녹화, WebM 내보내기) | 🔬 예정 |

## ◼ 기술 스택 (실제)

- **엔진:** Python 3.12, FastAPI, SQLAlchemy (async), LangGraph
- **LLM:** Ollama 로컬 우선 (`qwen3.5:9b` 생성, `qwen3-embedding:0.6b` 1024차원 임베딩); OpenAI/Anthropic 클라우드 역할은 선택
- **저장소:** PostgreSQL + pgvector (Alembic 마이그레이션), Redis
- **프론트엔드:** Next.js 16 (App Router, Turbopack), React 19, Zustand, next-intl (EN/KO)
- **실시간:** WebSocket (뷰어에게 브로드캐스트 전용)

## ◼ 빠른 시작

```bash
# 1. 인프라
docker compose up -d postgres redis

# 2. 백엔드 (로컬 Ollama :11434 필요)
cd backend && poetry install && poetry run uvicorn null_engine.main:app --port 3301

# 3. 프론트엔드
pnpm install && pnpm dev:frontend   # http://localhost:6001
```

설정은 `.env`에 있습니다 ([.env.example](.env.example) 참고). 주의:

- 쓰기 엔드포인트(월드 생성, 시작/정지, 개입)는 `API_WRITE_TOKEN`(`X-API-Key` 헤더)이 필요하며, 로컬 개발은 `ALLOW_ANONYMOUS_WRITES=true`로 허용할 수 있습니다.
- 자율 월드 생성은 명시적 옵트인입니다: `AUTO_GENESIS_ENABLED=true`.

## ◼ 문서

| 문서 | 설명 |
|---|---|
| [비전 & 철학](docs/VISION.ko.md) | 핵심 철학과 4대 기둥 |
| [시스템 아키텍처](docs/architecture/SYSTEM_ARCHITECTURE.ko.md) | 엔진 설계, 데이터 흐름, 이벤트 스트리밍 |
| [모델 전략](docs/architecture/MODEL_STRATEGY.ko.md) | LLM 역할 배분과 비용 최적화 |
| [UI/UX 명세](docs/architecture/UI_UX_SPEC.ko.md) | 옴니스코프 — 코스모그래프 공간 UI 명세 (컨셉) |
| [로드맵](docs/ROADMAP.ko.md) | 개발 단계와 마일스톤 |
| [프로젝트 현황](docs/PROJECT_STATUS.md) | 상세 구현 로그 |
| [기술적 과제](docs/CHALLENGES.ko.md) | 기술적 과제와 해결 전략 |
| [시나리오: 네온 조선](docs/scenarios/NEON_JOSEON.ko.md) | 시뮬레이션 예시 워크스루 |
| [미래 확장](docs/FUTURE.ko.md) | 확장 가능성 |
| [기여 가이드](docs/CONTRIBUTING.ko.md) | 기여 방법 |
| [용어 사전](docs/GLOSSARY.ko.md) | 프로젝트 용어 |

> 모든 문서는 [English](README.md)로도 제공됩니다.

## ◼ 로드맵 요약

- [x] **Phase 0** — 기반 (프로젝트 구조, 문서화, CI, Docker)
- [x] **Phase 1** — 코어 엔진 (에이전트 오케스트레이션, 페르소나 생성)
- [x] **Phase 2** — 시뮬레이션 루프 (대화 엔진, 이벤트 시스템)
- [x] **Phase 3** — 하이브 마인드 (자동 위키, 벡터 DB)
- [x] **Phase 4a–4e** — Chronicle UI, 분석, 시맨틱 세디먼트, 학습 데이터 내보내기
- [ ] **v0.3 Grounding** — 위키 근거 링크, 결정적 리플레이, UI 통합, E2E 테스트
- [ ] **v1 Research Preview** — 시나리오 포맷, 배치 비교, 모델 카드

전체 [로드맵](docs/ROADMAP.ko.md)에서 상세 내용을 확인하세요.

## ◼ 라이선스

[MIT](LICENSE)

- **코드명:** Project 0x00
- **컨셉:** 고밀도 합성 담론
