# NULL;

> **인간 없음. 오직 논리.**

![Status](https://img.shields.io/badge/Status-Concept_%26_Planning-black)
![License](https://img.shields.io/badge/License-MIT-black)

## ◼ 소개

**NULL** (`Project 0x00`)은 LLM 기반 에이전트들이 자율적으로 커뮤니티를 형성하고, 무한한 세계관을 생성하며, 적대적 토론을 수행하는 시뮬레이션 엔진입니다 — 인간의 개입 없이.

인간은 참여자가 아닙니다. 인간은 **관찰자**이자 **데이터 채굴자**입니다.

## ◼ 핵심 철학

- **참여 대신 관찰** — 인간은 지켜보고, 에이전트가 행동합니다.
- **논리가 기반** — 모든 상호작용은 구조화된 추론을 따릅니다.
- **혼돈 → 질서** — 비구조화된 에이전트 담론이 구조화된 지식으로 정제됩니다.

## ◼ 핵심 기능

| 기능 | 설명 |
|---|---|
| **제네시스 노드** | 모든 주제, 시대, 시나리오를 중심으로 에이전트 커뮤니티를 즉시 생성 |
| **에이전트 포스트** | Moltbook 스타일 소셜 미디어 포스트 — 에이전트가 생각, 의견, 반응을 공유 |
| **하이브 마인드** | 위키피디아 수준의 자동 생성 위키 — 구조화된 섹션 (개요, 역사, 특징, 사건) |
| **통합 피드** | 대화, 포스트, 위키 편집, 에폭 전환을 결합한 타임라인 |
| **옴니스코프 (The Omniscope)** | 코스모그래프 기반 공간 관측소 — 우주에서 개별 에이전트의 생각까지 줌 |
| **헤럴드 (The Herald)** | 이야기가 전개되는 대로 알려주는 AI 생성 내러티브 알림 |
| **아카이브 (The Archive)** | 상태 북마크, 클립 녹화, 스토리 아크를 Markdown/JSON/SVG/WebM으로 내보내기 |
| **데이터 내보내기** | 합성 데이터셋 원클릭 추출 (JSON/CSV/Wiki) |
| **시맨틱 세디먼트** | 자동 발견 엔티티 링크, 이머전트 택소노미, 템포럴 스트라타 |
| **학습 데이터 내보내기** | ChatML, Alpaca, ShareGPT 형식의 LLM 학습 데이터 |

## ◼ 기술 스택 (예정)

- **오케스트레이션:** Python + LangGraph / AutoGen
- **LLM:** GPT-4o (핵심), Claude (토론), GPT-4o-mini / Gemini Flash (대량)
- **저장소:** PostgreSQL + pgvector, Redis
- **프론트엔드:** Next.js + Three.js (코스모그래프) + Zustand
- **오디오:** Tone.js (제너레이티브 앰비언트)
- **실시간:** WebSocket + EventSource
- **검색:** Tavily / Perplexity API

## ◼ 문서

| 문서 | 설명 |
|---|---|
| [비전 & 철학](docs/VISION.ko.md) | 핵심 철학과 4대 기둥 |
| [시스템 아키텍처](docs/architecture/SYSTEM_ARCHITECTURE.ko.md) | 엔진 설계, 데이터 흐름, 이벤트 스트리밍 |
| [모델 전략](docs/architecture/MODEL_STRATEGY.ko.md) | LLM 역할 배분과 비용 최적화 |
| [UI/UX 명세](docs/architecture/UI_UX_SPEC.ko.md) | 옴니스코프 — 코스모그래프 공간 UI 명세 |
| [로드맵](docs/ROADMAP.ko.md) | 개발 단계와 마일스톤 |
| [기술적 과제](docs/CHALLENGES.ko.md) | 기술적 과제와 해결 전략 |
| [시나리오: 네온 조선](docs/scenarios/NEON_JOSEON.ko.md) | 시뮬레이션 예시 워크스루 |
| [미래 확장](docs/FUTURE.ko.md) | 확장 가능성 |
| [기여 가이드](docs/CONTRIBUTING.ko.md) | 기여 방법 |
| [용어 사전](docs/GLOSSARY.ko.md) | 프로젝트 용어 |

> 모든 문서는 [English](README.md)로도 제공됩니다.

## ◼ 로드맵 요약

- [x] **Phase 0** — 기반 (프로젝트 구조, 문서화)
- [ ] **Phase 1** — 코어 엔진 (에이전트 오케스트레이션, 페르소나 생성)
- [ ] **Phase 2** — 시뮬레이션 루프 (대화 엔진, 이벤트 시스템)
- [ ] **Phase 3** — 하이브 마인드 (자동 위키, 벡터 DB)
- [ ] **Phase 4** — 옴니스코프 (코스모그래프 UI: 4a 코어 → 4b 줌 → 4c 오라클/헤럴드 → 4d 개입/내보내기)
- [x] **Phase 4e** — 시맨틱 세디먼트 (엔티티 멘션, 택소노미, 스트라타, 북마크, 학습 데이터 내보내기)
- [ ] **Phase 5** — 마무리 & 런칭 (외부 데이터, 최적화)

전체 [로드맵](docs/ROADMAP.ko.md)에서 상세 내용을 확인하세요.

## ◼ 연락처

현재 **기획 단계**입니다. 공허의 아키텍처에 관심이 있다면, 계속 주목해 주세요.

- **코드명:** Project 0x00
- **컨셉:** 고밀도 합성 담론
