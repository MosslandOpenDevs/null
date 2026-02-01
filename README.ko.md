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
| **하이브 마인드** | 에이전트가 자체적으로 유지하는 실시간 위키 — 문명 진행을 자체 문서화 |
| **갓뷰 대시보드** | 관찰, 분석, 제어를 위한 트리니티 패널 인터페이스 |
| **데이터 내보내기** | 합성 데이터셋 원클릭 추출 (JSON/CSV/Wiki) |

## ◼ 기술 스택 (예정)

- **오케스트레이션:** Python + LangGraph / AutoGen
- **LLM:** GPT-4o (핵심), Claude (토론), GPT-4o-mini / Gemini Flash (대량)
- **저장소:** PostgreSQL + pgvector, Redis
- **프론트엔드:** Next.js + D3.js
- **검색:** Tavily / Perplexity API

## ◼ 문서

| 문서 | 설명 |
|---|---|
| [비전 & 철학](docs/VISION.ko.md) | 핵심 철학과 4대 기둥 |
| [시스템 아키텍처](docs/architecture/SYSTEM_ARCHITECTURE.ko.md) | 엔진 설계와 데이터 흐름 |
| [모델 전략](docs/architecture/MODEL_STRATEGY.ko.md) | LLM 역할 배분과 비용 최적화 |
| [UI/UX 명세](docs/architecture/UI_UX_SPEC.ko.md) | 갓뷰 대시보드 명세 |
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
- [ ] **Phase 4** — 갓뷰 UI (대시보드)
- [ ] **Phase 5** — 마무리 & 런칭 (외부 데이터, 최적화)

전체 [로드맵](docs/ROADMAP.ko.md)에서 상세 내용을 확인하세요.

## ◼ 연락처

현재 **기획 단계**입니다. 공허의 아키텍처에 관심이 있다면, 계속 주목해 주세요.

- **코드명:** Project 0x00
- **컨셉:** 고밀도 합성 담론
