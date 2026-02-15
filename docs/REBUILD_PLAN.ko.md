# NULL 재작업 계획 (2026-02-12)

## 진행 상태
- 상태: **진행 중 (Sprint 1 착수)**
- 최근 완료:
  - `export` API의 deprecated `Query(regex=...)` 제거 (`pattern` 전환)
  - 학습 데이터 포맷 변환 로직을 테스트 가능한 함수로 분리
  - 백엔드 단위 테스트 추가 (`backend/tests/test_export_training_formats.py`)
  - 백엔드 API 스모크 테스트 추가
    - `backend/tests/test_bookmarks_api_smoke.py`
    - `backend/tests/test_conversations_api_smoke.py`
    - `backend/tests/test_export_api_smoke.py`
    - `backend/tests/test_worlds_api_smoke.py`
    - `backend/tests/test_events_api_smoke.py`
  - `export/agents` 응답 스키마 고정 (`AgentExportOut`)
  - `world start/stop`, `event inject` 응답 스키마 고정
  - `conversations/feed`, `bookmarks delete/export` 응답 스키마 반영
  - 모든 API 라우트에 `response_model` 명시 완료
  - 프론트 상태스토어 테스트 추가
    - `frontend/tests/simulation.store.test.ts`
    - `frontend/tests/taxonomy.store.test.ts`
  - 프론트 테스트 스크립트 전환 (`node --test --experimental-strip-types`)
  - CI 프론트 잡에 `pnpm test` 추가 및 Node 22 정렬
  - 로컬 Python 버전 고정 파일 추가 (`.python-version`)
  - `make doctor` 추가로 환경 진단 루틴 도입
  - Poetry 런타임 Python 3.12 전환 완료 및 의존성 재설치 완료
  - 앱 수명주기에서 백그라운드 루프 복원력 강화(예외 시 재시작, 종료 시 일괄 취소)
  - 운영 메트릭 로깅 1차 표준화
    - `runner`: tick 지연/실행시간/성공률 + 활동량 메트릭
    - `translator`: 번역 큐 길이 + 배치 처리 시간
    - `convergence`/`semantic_indexer`/`taxonomy_builder`: cycle 처리 시간
  - API 전역 예외 핸들러 도입으로 에러 응답 포맷 표준화(`detail` 유지 + `error` 객체 추가)
  - 에러 응답 shape 스모크 테스트 보강(404/422)
  - Multiverse API 고도화 1차
    - `/multiverse/worlds/map` 무방향 링크 집계(중복 제거) + 필터링(`min_strength`, `min_count`, `link_limit`, `world_limit`)
    - `/multiverse/worlds/{world_id}/neighbors` 추가(공명 강도 기반 인접 월드 랭킹)
    - 멀티버스 스모크 테스트 추가 (`backend/tests/test_multiverse_api_smoke.py`)
  - Semantic Sediment(지층) API 고도화 1차
    - `/worlds/{world_id}/strata/compare` 추가(최신 2개 또는 지정 에포크 비교)
    - 지층 비교 스모크 테스트 추가 (`backend/tests/test_strata_api_smoke.py`)
    - 프론트 `StrataTimeline`에 에포크 비교 패널 연동
  - Multiverse/Strata UI 상태스토어 통합
    - `StrataTimeline` 직접 fetch 제거, Zustand `strata` 스토어로 전환
    - `ResonanceTab`를 월드 이웃 랭킹(`world neighbors`) 기반으로 전환
    - 프론트 스토어 테스트 추가
      - `frontend/tests/strata.store.test.ts`
      - `frontend/tests/multiverse.store.test.ts`
  - 핵심 흐름 E2E 스모크 테스트 보강
    - 월드 생성 → 시뮬레이션 시작 → 지층 비교 → 공명 이웃 조회 시나리오 테스트 추가
    - `backend/tests/test_workflow_e2e_smoke.py`
  - 멀티버스 맵 데이터 UI 연결
    - `ResonanceTab`에 `worlds/map` 링크 섹션 추가
  - 운영 관측(대시보드/알람) 고도화
    - `/api/ops/metrics`, `/api/ops/alerts` 추가
    - 루프/러너 런타임 메트릭 수집 연동(`runtime_metrics`)
    - 프론트 `OPS` 탭 추가(루프/큐/알람 대시보드)
    - 운영 API 스모크 테스트 추가 (`backend/tests/test_ops_api_smoke.py`)
  - 실데이터 부하 테스트 도구 추가
    - `backend/scripts/loadtest.py` 추가
    - `make loadtest`, `pnpm run loadtest:backend` 실행 경로 추가
    - 백엔드 문서에 운영/부하 테스트 커맨드 반영
  - CI 부하 테스트 리포트 아티팩트 연결
    - `.github/workflows/ci.yml`에 `loadtest-report` 잡 추가
    - 드라이런 리포트(`artifacts/loadtest-report.json`) 업로드
  - 알람 임계치 설정 외부화
    - `config.py`에 운영 알람 임계치 추가
    - `ops` 라우트가 설정값 기준으로 경보 판정

## 목표
- 문서 중심 상태에서 실행 가능한 제품 기준선으로 전환
- 프론트/백엔드 품질 게이트를 루트 명령 기준으로 통합
- 기능 확장 전에 안정성, 관측성, 테스트 범위를 우선 강화

## 현재 진단
- 루트 워크스페이스 스크립트가 실제 패키지명과 불일치해 실행 실패
- 프론트에 React Hook 의존성 경고 존재
- 백엔드 Ruff 오류가 대량 누적되어 정적검사 기준선 붕괴
- 테스트는 헬스체크 1건만 존재하여 회귀 방어력이 낮음

## 이번 턴에서 완료한 재정비
- 루트 스크립트 정상화 (`null-frontend` 기준으로 수정)
- 루트 기준 명령 추가: `typecheck:frontend`, `lint:backend`, `test:backend`
- 프론트 Hook 경고 2건 제거
- 백엔드 Ruff 자동 정리 및 잔여 이슈 해소
- 백엔드 린트/테스트 통과 상태 확보

## 다음 재작업 우선순위
1. 실행 환경 고정
- Poetry가 Python 3.14를 임시 선택하지 않도록 3.12 고정 가이드 추가(완료)
- `make doctor` 또는 동등한 환경 검증 커맨드 도입(완료)
- Poetry 가상환경을 `3.12`로 강제 재생성(`poetry env use 3.12`) 완료

2. 테스트 확장
- 백엔드 핵심 API 스모크 테스트(월드 생성/조회, 대화/피드, 위키/익스포트, 이벤트, start/stop) 완료
- 백엔드 스모크 테스트 확대(북마크) 완료
- 프론트 주요 상태스토어 단위 테스트 추가 완료

3. API/스키마 안정화
- `Query(regex=...)`를 `pattern=...`으로 전환(완료)
- 응답 스키마 표준화(완료: 전 라우트 `response_model` 명시)
- 에러 포맷 표준화(완료: 전역 예외 핸들러 + 테스트 반영)

4. 관측성과 운영 안정성
- 백그라운드 루프(autogenesis/convergence/indexer/taxonomy/translator) 실패 격리 및 재시도 정책 명시(완료)
- 핵심 메트릭(틱 지연, 큐 길이, 생성 성공률) 로깅 표준화(1차 완료)

5. 기능 재추진 기준
- 위 1~4 충족 후, Semantic Sediment/Multiverse 고도화 작업 재개
- 멀티버스 고도화 1차 완료(맵 집계 개선 + 이웃 월드 API)
- 지층 고도화 1차 완료(비교 API + 타임라인 비교 패널)
- Multiverse/Strata UI 상태스토어 통합 완료
- 월드 생성→시뮬레이션→지층/공명 확인 E2E 시나리오 테스트 보강 완료
- 운영 관측(대시보드/알람) 및 실데이터 부하 테스트 완료
- CI에 부하 테스트 리포트 아티팩트 연결 완료
- 알람 임계치 설정 외부화 완료
- 다음 단계: 실제 런타임 부하 벤치마크 자동화(주기 실행 + 결과 추세 저장)

## 완료 기준 (Definition of Done)
- 루트에서 아래 명령이 모두 성공
  - `pnpm run lint:frontend`
  - `pnpm run typecheck:frontend`
  - `pnpm run lint:backend`
  - `pnpm run test:backend`
- CI에서 동일 게이트 재현(워크플로우 반영 완료)
- 최소 핵심 흐름(월드 생성→대화/이벤트→위키/익스포트) 테스트 보장
