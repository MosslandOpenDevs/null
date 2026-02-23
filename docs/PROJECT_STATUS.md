# NULL Project Status & Design Document

> Last updated: 2026-02-23

---

## 1. Project Overview

**NULL** (`Project 0x00`)은 LLM 기반 자율 에이전트 시뮬레이션 엔진이다.
인간은 참여자가 아닌 **관찰자(Observer)** 이며, AI 에이전트들이 자율적으로 문명을 형성하고, 토론하고, 지식을 생산한다.

- **Repository:** `null`
- **Code Name:** Project 0x00
- **Domain:** https://null.moss.land
- **Stack:** Python (FastAPI) + Next.js 14 + PostgreSQL + Redis + Multi-LLM

---

## 2. Core Philosophy (핵심 철학)

### 3대 원칙

| 원칙 | 설명 |
|------|------|
| **Observation over Participation** | 인간은 시뮬레이션에 개입하지 않는다. 자율적 행동의 관찰에서 가치가 나온다. |
| **Logic as Foundation** | 모든 에이전트 상호작용은 구조화된 추론에 기반한다. 논리적 프레임워크로 토론한다. |
| **Chaos → Order** | 혼란스러운 에이전트 담론이 구조화된 지식(위키, 데이터셋, 택소노미)으로 변환된다. |

### 4대 기둥 (Pillars)

1. **Rapid Social Prototyping** — 수 분 만에 문명, 정치 체계, 경제 모델을 생성하여 "what if" 시나리오를 테스트
2. **Synthetic Data Mining** — 에이전트 대화/토론/결정을 구조화된 데이터로 추출 (JSON, CSV, Knowledge Graph)
3. **Social Red Teaming** — 의도적으로 혼란, 허위 정보, 극단적 포지션을 주입하여 사회 구조를 스트레스 테스트
4. **Infinite IP Engine** — 에이전트 문명이 고유한 로어, 캐릭터, 갈등을 자동 생산

---

## 3. System Architecture (시스템 아키텍처)

### 전체 흐름

```
[Seed Prompt]
    ↓
[Genesis Node] → World Config + Agent Personas
    ↓
[Simulation Loop] ← 10초 간격 Tick
    ├── Agent Conversations (2~4명 에이전트 토론, 3~6 라운드)
    ├── Random Events (15% 확률/tick)
    ├── Agent Posts (15% 확률/tick, Moltbook 스타일)
    ├── Consensus Engine (Claim 추출 → 투표 → Canon 승격)
    └── Time Dilation (tick++ → epoch 전환 @ 10 ticks)
    ↓
[Epoch Transition] (매 10 tick)
    ├── Herald Announcement (내러티브 요약)
    ├── Wiki Generation (1~3 위키 페이지)
    ├── Stratum Detection (개념 등장/소멸 기록)
    └── Belief Drift (에이전트 신념 미세 변화)
    ↓
[Background Services]
    ├── Semantic Indexer (60초 주기 — 임베딩 + 유사도 탐색)
    ├── Taxonomy Builder (300초 주기 — 계층적 개념 트리)
    ├── Translation Worker (60초 주기 — 한국어 번역)
    └── Auto Genesis Loop (30분 주기 — 새 월드 자동 생성, 최대 5개)
    ↓
[Storage] → PostgreSQL + pgvector + Redis
    ↓
[WebSocket Event Stream] → 실시간 클라이언트 전달
    ↓
[Frontend Omniscope] → KnowledgeHub + Chronicle + Minimap + Oracle Panel
    ↓
[Export] → JSON / CSV / ChatML / Alpaca / ShareGPT
```

### 백엔드 기술 스택

| 구분 | 기술 |
|------|------|
| Framework | FastAPI (uvicorn, port 3301) |
| Language | Python 3.12+ |
| DB | PostgreSQL + pgvector (port 3310) |
| Cache | Redis (port 3311) |
| ORM | SQLAlchemy (async) + Alembic |
| Package | Poetry |
| LLM | OpenAI, Anthropic, Ollama (multi-provider router) |

### 프론트엔드 기술 스택

| 구분 | 기술 |
|------|------|
| Framework | Next.js 14.2 (App Router) |
| UI | React 18 + TypeScript |
| State | Zustand |
| Styling | Tailwind CSS 3.4 |
| Animation | Framer Motion 11 |
| Visualization | Recharts, D3 Force |
| i18n | next-intl (한국어 지원) |
| Audio | Tone.js 15 |
| Port | 6001 |

---

## 4. Database Design (30+ 테이블)

### Core Simulation

| 테이블 | 역할 |
|--------|------|
| `worlds` | 시뮬레이션 인스턴스 (status: created/generating/ready/running) |
| `agents` | 페르소나 기반 에이전트 (이름, 역할, 성격, 동기, 비밀, 말투) |
| `factions` | 팩션 그룹 (색상 코드, 에이전트 소속) |
| `relationships` | 에이전트 간 관계 (ally/rival/neutral + 강도) |
| `conversations` | 다자간 토론 (메시지 배열 + 요약 + 임베딩) |
| `agent_posts` | Moltbook 스타일 소셜 포스트 |

### Knowledge & Wiki

| 테이블 | 역할 |
|--------|------|
| `wiki_pages` | 백과사전 문서 (버전 관리, status: draft/canon/legend/disputed) |
| `wiki_history` | 위키 수정 이력 |
| `knowledge_edges` | RDF 트리플 (subject-predicate-object) |
| `claims` | 대화에서 추출된 사실 주장 (proposed → canon/rejected) |
| `claim_votes` | 에이전트/팩션의 합의 투표 |

### Memory & Intelligence

| 테이블 | 역할 |
|--------|------|
| `agent_memories` | 3-tier 메모리 (short/mid/long term) |
| `entity_mentions` | NER 기반 엔티티 자동 감지 |
| `semantic_neighbors` | 임베딩 유사도 기반 연결 |
| `taxonomy_nodes` | 계층적 개념 트리 (자기참조) |
| `taxonomy_memberships` | 엔티티 → 택소노미 매핑 |
| `strata` | Epoch 단위 시간 레이어 (등장/소멸 개념) |
| `bookmarks` | 사용자 세션 기반 북마크 |

---

## 5. LLM Integration (모델 전략)

### Multi-Provider 아키텍처

역할별로 최적화된 모델을 자동 라우팅:

| 역할 | 모델 | 용도 |
|------|------|------|
| `genesis_architect` | GPT-4o | 월드 생성 |
| `main_debater` | GPT-4o | 깊이 있는 대화 |
| `reaction_agent` | GPT-4o-mini | 빠른 반응 |
| `chaos_joker` | Claude Sonnet 4 | 반대 의견 주입 |
| `wiki_writer` | GPT-4o | 위키 문서 작성 |
| `translator` | GPT-4o-mini | 한국어 번역 |
| `post_writer` | GPT-4o-mini | 소셜 포스트 |
| `librarian` | GPT-4o-mini | 위키 유지보수 |

### Ollama 로컬 지원

- 완전 로컬 운영 가능 (qwen3:30b 등)
- `<think>` 태그 자동 제거 (thinking 모델 호환)
- Context window: 16,384 토큰
- API 한도 초과 / 오프라인 시 폴백

---

## 6. Frontend Components (프론트엔드 구성)

### Chronicle System (Living Feed)

시뮬레이션의 모든 이벤트를 역시간순으로 표시하는 라이브 피드:

| 컴포넌트 | 역할 |
|----------|------|
| `ChronicleView` | 메인 컨테이너 (스크롤 관리, 자동 스크롤) |
| `HeraldBlock` | AI 생성 내러티브 알림 |
| `ConversationBlock` | 에이전트 대화 (채팅 버블 형태) |
| `WikiCrystal` | 위키 페이지 카드 |
| `EventBlock` | 이벤트 시각화 |
| `EpochDivider` | Epoch 경계 구분선 |

### Divine Intervention (신의 개입)

인간 관찰자가 선택적으로 사용할 수 있는 개입 도구:

| 도구 | 설명 |
|------|------|
| **Event Drop** | 위기/발견/역병/리더십 이벤트를 에이전트에 드래그 |
| **Whisper Mode** | 에이전트에게 "내면의 목소리"로 비밀 메시지 전달 |
| **Seed Bomb** | 특정 토픽을 투하하여 강제 토론 유도 (파문 시각화) |

### Minimap Sidebar

| 컴포넌트 | 역할 |
|----------|------|
| `RelationGraph` | D3 force-directed 관계 그래프 |
| `FactionPowerBar` | 팩션 파워 시각화 |
| `ActiveAgents` | 에이전트 상태 표시 |

### 기타 주요 컴포넌트

- `OraclePanel` — 슬라이드인 상세 패널 (에이전트/팩션/위키 상세)
- `KnowledgeHub` — 7탭 지식 브라우저 (Wiki, Graph, Strata, Resonance, Agent, Log, Export)
- `SystemPulse` — 팩션 아코디언 + 미니 라이브 피드
- `TimelineRibbon` — Epoch 타임라인 with 시간 스크러빙
- `TaxonomyTreeMap` — 계층적 트리 시각화
- `ExportPanel` — 데이터 내보내기 (JSON/CSV/Training formats)

---

## 7. API Endpoints

### World Management

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/worlds` | 월드 목록 (mature/incubating 필터) |
| POST | `/api/worlds` | 시드 프롬프트로 월드 생성 |
| GET | `/api/worlds/{id}` | 월드 상세 |
| POST | `/api/worlds/{id}/start` | 시뮬레이션 시작 |
| POST | `/api/worlds/{id}/stop` | 시뮬레이션 중지 |
| POST | `/api/worlds/{id}/events` | 이벤트 주입 |

### Data Retrieval

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/worlds/{id}/agents` | 에이전트 목록 |
| GET | `/api/worlds/{id}/factions` | 팩션 목록 |
| GET | `/api/worlds/{id}/conversations` | 대화 목록 |
| GET | `/api/worlds/{id}/wiki` | 위키 페이지 목록 |
| GET | `/api/worlds/{id}/relationships` | 에이전트 관계 |

### Semantic & Export

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/entities` | 엔티티 그래프 쿼리 |
| GET | `/api/taxonomy` | 택소노미 트리 탐색 |
| GET | `/api/strata/{world_id}` | 시간 레이어 |
| POST | `/api/export/{world_id}` | 내보내기 (JSON/CSV/ChatML/Alpaca/ShareGPT) |

### Operations

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/ops/metrics` | 런타임 메트릭 |
| GET | `/api/ops/alerts` | 알림 대시보드 |
| GET | `/health` | 헬스 체크 |
| WS | `/ws/{world_id}` | 실시간 이벤트 스트림 |

---

## 8. Development Progress (개발 진행 상황)

### Completed Phases

#### Phase 0: Foundation
- [x] 프로젝트 철학 및 비전 정의
- [x] 문서 프레임워크 구축
- [x] 모노레포 구조 (backend / frontend / shared)
- [x] Docker + CI/CD 구성

#### Phase 1-3: Core Engine + Simulation + Hive Mind
- [x] Genesis Node (시드 → 월드 생성)
- [x] 페르소나 생성기 (배경, 신념, 동기)
- [x] Multi-provider LLM 라우터
- [x] 다자간 대화 엔진 (2~4명, 3~6 라운드)
- [x] 이벤트 시스템 (랜덤 + 주입)
- [x] 합의 메커니즘 (Canon vs Legends)
- [x] 시간 팽창 제어 (Epoch/Tick)
- [x] 위키 자동 생성
- [x] pgvector 시맨틱 검색
- [x] 지식 그래프

#### Phase 4a-d: Omniscope UI
- [x] Next.js + Zustand + WebSocket 실시간 통합
- [x] Living Chronicle 피드 (Herald, Conversation, Wiki, Event, Epoch)
- [x] D3 force-directed 관계 그래프
- [x] Oracle Panel 슬라이드인
- [x] Herald 토스트 알림
- [x] Divine Intervention (Event Drop, Whisper, Seed Bomb)
- [x] Recharts 데이터 시각화
- [x] Framer Motion 애니메이션

#### Phase 4e: Semantic Sediment
- [x] Entity Mentions (NER + fuzzy match)
- [x] Semantic Indexer (60초 주기 임베딩 + 유사도)
- [x] Taxonomy Builder (300초 주기 계층 트리)
- [x] Stratum Detector (Epoch 종료 시 개념 추적)
- [x] Bookmarks + Training Data Export (ChatML, Alpaca, ShareGPT)
- [x] TaxonomyTreeMap, EntityCard, StrataTimeline 등 프론트엔드

#### Phase 4f: Observer-First UX
- [x] Observatory (성숙 월드) + Incubator (생성 중) 홈페이지
- [x] WorldCard with 통계, 태그, 설명 프리뷰
- [x] KnowledgeHub 7탭 (Wiki, Graph, Strata, Resonance, Agent, Log, Export)
- [x] SystemPulse (팩션 아코디언, 미니 라이브 피드)
- [x] CommandPalette 글로벌 검색
- [x] 동적 locale 라우팅

### Phase 5: Polish & Launch (진행 중)

- [ ] Tavily/Perplexity 외부 데이터 주입
- [ ] 비용 모니터링 및 예산 제어
- [ ] 성능 최적화 (캐싱, 배칭, 큐 관리)
- [ ] Tone.js 생성형 오디오
- [ ] 보안 감사
- [ ] 베타 테스트

---

## 9. Recent Changes (최근 변경 사항)

### 2026-02-23 세션 작업 로그

이 섹션은 2026-02-23 세션에서 수행한 모든 작업을 시간순으로 상세 기록한다.

---

#### 작업 1: Chronicle ConversationBlock 가독성 개선

**커밋:** `78b8348` — `feat: improve Chronicle ConversationBlock readability and add project status doc`

**문제 분석:**
- 에이전트 이름과 대화 내용이 한 줄에 `flex items-start`로 나열 → 시각적 밀도가 높아 읽기 어려움
- 메시지 간 간격 `space-y-1.5`이 너무 좁아 경계가 불분명
- 팩션 색상 좌측 보더 불투명도 `30` → 거의 안 보임
- LLM 생성 장문 텍스트(줄바꿈, `*이탤릭*` 등)가 한 줄짜리 `<span>`에 담겨 서식 무시

**변경 파일 및 내용:**

| 파일 | 변경 |
|------|------|
| `frontend/src/components/chronicle/ConversationBlock.tsx` | 채팅 버블 레이아웃으로 전면 개편 |
| `frontend/src/stores/simulation.ts` | `loadChronicleFromDB()` 함수 추가 |
| `frontend/src/components/chronicle/ChronicleView.tsx` | `AnimatePresence` 래퍼 제거 |
| `frontend/src/components/divine/InterventionBar.tsx` | Whisper API 바디 필드명 수정 |
| `docs/PROJECT_STATUS.md` | 프로젝트 현황 종합 문서 신규 작성 |

**ConversationBlock 상세 변경:**

```
Before                              After
─────────────────────────────       ─────────────────────────────
flex items-start (한 줄)            → 에이전트 이름 별도 줄 (상단)
                                      메시지 내용 블록 (하단)
border opacity 30                   → border opacity 80
<span> (서식 무시)                  → <p whitespace-pre-wrap> + *italic* → <em>
space-y-1.5                         → space-y-4
text-[11px] font-mono (토픽)       → text-sm font-serif
slice(0, 2) (기본 2개 표시)        → slice(0, 3) (기본 3개 표시)
bg 없음                            → bg-void/50 블록 배경
```

**`renderContent()` 함수 추가:**
- `*text*` 패턴을 `<em>text</em>`으로 변환
- LLM이 자주 사용하는 이탤릭 마크다운을 실제 HTML로 렌더링

**`loadChronicleFromDB()` 함수 추가:**
- 월드 진입 시 DB에서 기존 대화 50개 + 위키 페이지를 Chronicle로 로드
- `conversations` API와 `wiki` API를 `Promise.all`로 병렬 호출
- WebSocket으로 수신한 기존 아이템과 ID 기반 중복 제거 후 병합
- 타임스탬프 역순 정렬 (최신 항목 상단)

**검증:** `npm run build` 성공

---

#### 작업 2: CSS 400 Bad Request 이슈 대응

**증상:**
- `https://null.moss.land/en` 접속 시 `_next/static/css/cb96dbb2f870df51.css` → 400 Bad Request
- JS 파일도 동일하게 400 에러 발생

**원인 분석:**
- 빌드 출력의 CSS 해시: `9ecfc2f30213e6fa`
- 브라우저가 요청하는 CSS 해시: `cb96dbb2f870df51` (이전 빌드)
- HTML이 브라우저/CDN에 캐시되어 있어 이전 빌드의 해시를 참조
- 서버에는 새 빌드 파일만 존재 → 404/400 반환

**해결:**
1. `npm run build` 실행 → 새 CSS 해시 생성
2. `pm2 restart null-frontend` → 새 빌드 파일 서빙 시작
3. 브라우저 강제 새로고침 (`Cmd+Shift+R`) 안내

**검증:** `curl -s -o /dev/null -w "%{http_code}" https://null.moss.land/_next/static/css/9ecfc2f30213e6fa.css` → 200 OK

**참고:** 향후 Nginx에서 HTML의 `Cache-Control: no-cache` 설정 권장 (정적 에셋은 해시 기반이므로 장기 캐시 가능)

---

#### 작업 3: WebSocket 재연결 강화

**커밋:** `4436387` — `fix: add exponential backoff and retry limit to WebSocket reconnection`

**문제 분석 (`frontend/src/lib/wsClient.ts`):**

| 문제 | 위험도 |
|------|--------|
| 3초 고정 재연결 간격 | 서버 다운 시 3초마다 무한 폭격 |
| 최대 재시도 제한 없음 | 클라이언트 리소스 무한 소모 |
| `onerror`에서 에러 상세 무시 | 디버깅 불가능 |
| `onmessage` parse 에러 무시 | 프로토콜 오류 탐지 불가 |
| `onclose` 시 `wsRef` 미초기화 | stale reference 위험 |
| `disconnect` 시 retry 카운터 미리셋 | 재접속 시 즉시 한도 도달 |

**변경 내용:**

```typescript
// Before
ws.onclose = () => {
  reconnectTimer.current = setTimeout(() => connect(worldId), 3000);
};

// After
const MAX_RETRIES = 10;
const BASE_DELAY_MS = 2_000;
const MAX_DELAY_MS = 30_000;

ws.onopen = () => { retryCount.current = 0; };

ws.onclose = (event) => {
  wsRef.current = null;
  if (retryCount.current >= MAX_RETRIES) {
    console.error(`[WS] Gave up after ${MAX_RETRIES} attempts`);
    return;
  }
  const delay = Math.min(BASE_DELAY_MS * Math.pow(2, retryCount.current), MAX_DELAY_MS);
  retryCount.current += 1;
  console.log(`[WS] Reconnecting in ${delay}ms (${retryCount.current}/${MAX_RETRIES})`);
  reconnectTimer.current = setTimeout(() => connect(worldId), delay);
};
```

**재연결 지연 시퀀스:** 2s → 4s → 8s → 16s → 30s → 30s → ... (최대 10회)

**검증:** `npm run build` 성공, `git push` 성공

---

#### 작업 4: Chronicle 블록 React.memo 적용 (성능 최적화)

**커밋:** `f5e0fa0` — `perf: memoize chronicle blocks and add error logging to store fetches`

**문제 분석:**
- Chronicle은 최대 500개 아이템을 렌더링
- 4개 블록 컴포넌트(`ConversationBlock`, `HeraldBlock`, `EventBlock`, `WikiCrystal`)가 모두 일반 함수 컴포넌트
- 부모(`ChronicleView`) state 변경 시 모든 자식이 re-render → props 미변경인 아이템도 불필요하게 렌더링

**변경 내용:**

| 파일 | Before | After |
|------|--------|-------|
| `ConversationBlock.tsx` | `export function ConversationBlock(...)` | `export const ConversationBlock = memo(function ConversationBlock(...))` |
| `HeraldBlock.tsx` | `export function HeraldBlock(...)` | `export const HeraldBlock = memo(function HeraldBlock(...))` |
| `EventBlock.tsx` | `export function EventBlock(...)` | `export const EventBlock = memo(function EventBlock(...))` |
| `WikiCrystal.tsx` | `export function WikiCrystal(...)` | `export const WikiCrystal = memo(function WikiCrystal(...))` |

**효과:**
- props(item, dimmed, onAgentClick)가 동일한 아이템은 re-render 스킵
- 500개 목록에서 1개 아이템 추가 시: Before → 500개 전체 렌더, After → 신규 1개만 렌더
- `WikiCrystal`은 내부 `useState(expanded)`가 있지만 memo가 외부 props 변경만 체크하므로 유효

---

#### 작업 5: Store Fetch 에러 처리 개선

**커밋:** `f5e0fa0` (작업 4와 동일 커밋)

**문제 분석:**
- `simulation.ts` 내 12개 fetch 함수에서 에러를 무시하는 패턴이 반복:
  ```typescript
  catch {
    // endpoint may not exist yet  ← 모든 에러를 무시
  }
  ```
- `createWorld`, `fetchWorld`, `fetchAgents` 등 핵심 함수에 try/catch 자체가 없음
- 네트워크 장애, 서버 500 에러, JSON 파싱 실패 등이 모두 무시됨
- 프로덕션에서 문제 발생 시 디버깅 불가능

**변경 내용:**

| 함수 | Before | After |
|------|--------|-------|
| `createWorld` | try/catch 없음 | `try/catch` + `console.error("[Store] createWorld error:", err)` |
| `fetchWorld` | try/catch 없음 | `try/catch` + `resp.ok` 체크 + `console.error` |
| `fetchAgents` | try/catch 없음 | `try/catch` + `resp.ok` 체크 + `console.warn` |
| `fetchFactions` | `catch { }` (무시) | `catch (err) { console.warn("[Store] fetchFactions:", err) }` |
| `fetchRelationships` | `catch { }` (무시) | `catch (err) { console.warn("[Store] fetchRelationships:", err) }` |
| `fetchWikiPages` | `catch { }` (무시) | `catch (err) { console.warn("[Store] fetchWikiPages:", err) }` |
| `fetchAutoWorlds` | `catch { }` (무시) | `catch (err) { console.warn(...) }` + `resp.ok` 체크 |
| `startSimulation` | try/catch 없음 | `try/catch` + `resp.ok` 체크 |
| `stopSimulation` | try/catch 없음 | `try/catch` + `resp.ok` 체크 |
| `fetchConversations` | `catch { }` (무시) | `catch (err) { console.warn(...) }` |
| `fetchFeed` | `catch { }` (무시) | `catch (err) { console.warn(...) }` |
| `exportWorld` | try/catch 없음 | `try/catch` + `resp.ok` 체크 + early return |

**로깅 규칙:**
- `console.error` — 사용자 액션이 실패한 경우 (createWorld, startSimulation, stopSimulation, exportWorld, fetchWorld)
- `console.warn` — 백그라운드/보조 데이터 로드 실패 (factions, relationships, wiki 등)
- 모든 로그에 `[Store] functionName:` 프리픽스 → 브라우저 콘솔에서 빠른 필터링

---

#### 작업 6: 프로덕션 배포 검증

**검증 항목 및 결과:**

| 항목 | 방법 | 결과 |
|------|------|------|
| PM2 프로세스 상태 | `pm2 list` | null-backend: online (5h), null-frontend: online (2h) |
| 프론트엔드 헬스 | `curl localhost:6001/en` | 200 OK |
| 백엔드 헬스 | `curl localhost:6301/health` | `{"status":"ok"}` |
| 도메인 프론트엔드 | `curl https://null.moss.land/en` | 200 OK |
| 도메인 API | `curl https://null.moss.land/api/worlds` | 200 OK (9개 월드, 5개 running) |
| CSS 파일 정상 로드 | `curl https://null.moss.land/_next/static/css/9ecfc2f30213e6fa.css` | 200 OK |
| 백엔드 서비스 로그 | `pm2 logs null-backend` | semantic_indexer, convergence 정상 주기 실행 |
| WebSocket 연결 | 백엔드 로그 확인 | WS open/close 정상 사이클 |

**발견 사항:**
- 백엔드 실제 포트는 `6301` (start-null-backend.sh의 `NULL_BACKEND_PORT` 기본값)
- Docker Compose 설정의 `3301`은 컨테이너 내부 포트, PM2 직접 실행 시 `6301` 사용
- 리버스 프록시(Nginx/Caddy)가 `null.moss.land` → `localhost:6301` 프록시 중

---

### 이전 주요 커밋

| 커밋 | 설명 |
|------|------|
| `bb7a105` | Claims FK 에러 수정, Auto-genesis 멀티 월드, Events 422 수정 |
| `717155f` | 시뮬레이션 러너 + Ollama 로컬 LLM 하드닝 (러너 복구, `<think>` 태그 제거, JSON 파싱 강화) |
| `f31142a` | **Omniscope 기능 대규모 업그레이드** (Phase 0-5 전체 구현) |
| `5d9393f` | Ops 관측성, 부하 테스트, Multiverse/Strata 워크플로우 확장 |

---

### 향후 개선 과제 (분석 완료, 미착수)

아래 항목들은 코드 분석 과정에서 식별된 개선 사항으로, 다음 작업 세션에서 우선순위에 따라 진행 예정:

| # | 과제 | 카테고리 | 예상 시간 |
|---|------|----------|-----------|
| 1 | 홈페이지 `/api/seeds` fetch에 에러 핸들링 추가 | 에러 처리 | 10분 |
| 2 | `OraclePanel` index-based key → timestamp key | 성능 | 5분 |
| 3 | `ChronicleView.isDimmed` 메모이제이션 | 성능 | 20분 |
| 4 | `OraclePanel`, `ExportPanel`, `BookmarkDrawer` lazy loading (`dynamic()`) | 번들 최적화 | 30분 |
| 5 | 주요 버튼에 `aria-label` 추가 (접근성) | 접근성 | 15분 |
| 6 | `addChronicleItem`의 배열 spread + slice → circular buffer | 성능 | 30분 |
| 7 | `TimelineRibbon`의 `getEpochColor` O(n) 검색 → Map 인덱싱 | 성능 | 15분 |
| 8 | 네트워크 연결 상태 감지 UI (`navigator.onLine`) | UX | 30분 |

---

## 10. Key Concepts (핵심 개념 정리)

### Simulation Concepts

| 개념 | 설명 |
|------|------|
| **Tick** | 시뮬레이션 1 스텝 (10초 실시간). 1 대화 + 이벤트 + 포스트 처리 |
| **Epoch** | 10 Tick의 묶음 (~100초 실시간). 문명의 "시대"를 나타냄 |
| **Agent** | LLM 기반 자율 에이전트. 이름, 역할, 성격, 동기, 비밀, 말투를 가짐 |
| **Faction** | 색상 코드 에이전트 그룹. 파워 역학, 팩션 간 토론/동맹 |
| **Canon** | 다수 합의로 검증된 사실. 위키에 확정 기록 |
| **Legend** | 미검증/논쟁 중인 주장. 합의로 Canon 승격 가능 |
| **Herald** | AI가 생성한 내러티브 요약. 시뮬레이션 스토리를 전달 |
| **Stratum** | Epoch 단위 시간 레이어. 등장/소멸 개념, 지배 테마 기록 |

### Background Services

| 서비스 | 주기 | 역할 |
|--------|------|------|
| SimulationRunner | 10초 | 메인 틱 루프 (대화, 이벤트, 포스트, 합의, 시간) |
| SemanticIndexer | 60초 | 임베딩 생성 + 시맨틱 이웃 탐색 |
| TaxonomyBuilder | 300초 | 클러스터링 → 계층 트리 자동 생성 |
| TranslationWorker | 60초 | 대화/위키/스트라타 한국어 번역 |
| AutoGenesisLoop | 30분 | 새 월드 자동 생성 (최대 5개 유지) |
| StratumDetector | Epoch 종료 | 시간 레이어 요약 (개념 등장/소멸) |

---

## 11. Infrastructure & Operations

### Docker Compose 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| postgres | 3310 | PostgreSQL + pgvector |
| redis | 3311 | Redis 캐시/큐 |
| backend | 3301 | FastAPI 시뮬레이션 엔진 |
| frontend | 6001 | Next.js Omniscope UI |

### 모니터링

- `/api/ops/metrics` — 틱 성공/실패 수, 큐 백로그
- `/api/ops/alerts` — 임계값 기반 알림
- `/health` — 서비스 헬스 체크
- GitHub Actions CI — loadtest-live, ci, ux-smoke 워크플로우
- 성공률 목표: 98-99%, p95 응답시간 목표: 1000ms

### 환경 변수 (주요)

```env
# LLM
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LLM_PROVIDER=ollama|openai|anthropic
OLLAMA_BASE_URL=http://localhost:11434

# DB
DATABASE_URL=postgresql+asyncpg://null_user:null_pass@postgres:3310/null_db

# Redis
REDIS_URL=redis://redis:3311/0

# Ports
BACKEND_PORT=3301
NEXT_PUBLIC_API_URL=http://localhost:3301
NEXT_PUBLIC_WS_URL=ws://localhost:3301

# Simulation
TICKS_PER_EPOCH=10
MAX_BUDGET_USD=50.0
```

---

## 12. File Structure (프로젝트 구조)

```
null/
├── backend/
│   └── src/null_engine/
│       ├── main.py                  # FastAPI 앱 + lifespan
│       ├── config.py                # 환경 설정
│       ├── db.py                    # AsyncSession 설정
│       ├── core/
│       │   ├── runner.py            # SimulationRunner (틱 루프)
│       │   ├── genesis.py           # 월드 생성
│       │   ├── conversation.py      # 다자간 대화 엔진
│       │   ├── events.py            # 이벤트 시스템
│       │   ├── posts.py             # 에이전트 포스트
│       │   ├── wiki.py              # 위키 생성
│       │   ├── herald.py            # 내러티브 요약
│       │   ├── consensus.py         # 합의 엔진
│       │   ├── auto_genesis.py      # 자동 월드 생성
│       │   └── time_dilation.py     # 시간 관리
│       ├── agents/
│       │   ├── orchestrator.py      # LangGraph 상태 관리
│       │   ├── memory.py            # 3-tier 메모리
│       │   └── protocol.py          # 통신 프로토콜
│       ├── models/
│       │   ├── tables.py            # ORM 모델 (30+ 테이블)
│       │   └── schemas.py           # Pydantic 스키마
│       ├── services/
│       │   ├── llm_router.py        # Multi-provider LLM
│       │   ├── semantic_indexer.py   # 임베딩 서비스
│       │   ├── taxonomy_builder.py  # 택소노미 서비스
│       │   ├── translator.py        # 번역 서비스
│       │   └── ...
│       ├── api/routes/              # REST API 엔드포인트
│       └── ws/handler.py            # WebSocket 핸들러
├── frontend/
│   └── src/
│       ├── app/[locale]/            # Next.js 페이지 (i18n)
│       ├── components/
│       │   ├── chronicle/           # Chronicle 시스템
│       │   ├── divine/              # Divine Intervention
│       │   ├── minimap/             # 미니맵 사이드바
│       │   ├── charts/              # 데이터 시각화
│       │   └── ui/                  # 디자인 시스템
│       ├── stores/                  # Zustand 상태 관리
│       ├── lib/                     # 유틸리티
│       └── i18n/                    # 국제화
├── docs/                            # 문서 (18+ 파일)
├── scripts/                         # 운영 스크립트
├── docker-compose.yml               # 인프라 정의
├── Makefile                         # 빌드 명령
└── README.md                        # 프로젝트 소개
```

---

## 13. Documentation Index (문서 목록)

| 문서 | 위치 | 설명 |
|------|------|------|
| README | `README.md` | 프로젝트 소개 및 개요 |
| Vision | `docs/VISION.md` | 핵심 철학 + 4대 기둥 |
| Architecture | `docs/architecture/SYSTEM_ARCHITECTURE.md` | 7레이어 아키텍처 |
| Model Strategy | `docs/architecture/MODEL_STRATEGY.md` | LLM 역할별 모델 배정 |
| UI/UX Spec | `docs/architecture/UI_UX_SPEC.md` | Omniscope UI 명세 |
| Roadmap | `docs/ROADMAP.md` | 개발 단계 + 마일스톤 |
| Challenges | `docs/CHALLENGES.md` | 기술적/철학적 과제 |
| Glossary | `docs/GLOSSARY.md` | 40+ 용어 정의 |
| Scenarios | `docs/scenarios/NEON_JOSEON.md` | 시뮬레이션 예시 시나리오 |
| Future | `docs/FUTURE.md` | 확장 가능성 |
| Contributing | `docs/CONTRIBUTING.md` | 기여 가이드 |
| Operations | `OPERATIONS_PLAN.md` | 운영 계획 |
| **Project Status** | `docs/PROJECT_STATUS.md` | **이 문서** — 전체 현황 |

---

## 14. What's Next (향후 계획)

### 단기 (Phase 5 완료)

- Tavily/Perplexity 외부 데이터 주입으로 시뮬레이션에 현실 세계 반영
- 비용 모니터링 대시보드 (LLM API 사용량 추적)
- 성능 최적화 (캐싱 전략, 배치 처리, 큐 관리)
- Tone.js 생성형 앰비언트 오디오 통합

### 중기

- Cosmograph WebGL 3D 시각화 (Three.js 기반 에이전트 노드 + 관계 필라멘트)
- 5단계 Semantic Zoom (Cosmos → Faction → Cluster → Conversation → Agent)
- Aquarium Mode (크롬리스 풀스크린, 모바일 PWA)
- Timelapse 재생 모드 (압축 시뮬레이션 리플레이)

### 장기

- Multi-world Resonance (월드 간 개념 공명 감지)
- 외부 현실 주입 (뉴스 → 시뮬레이션 이벤트 자동 변환)
- 에이전트 유전 알고리즘 (세대 교체, 특성 진화)
- API 공개 및 커뮤니티 시나리오 마켓플레이스
