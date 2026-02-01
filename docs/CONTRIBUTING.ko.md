# NULL에 기여하기

## 시작하기

1. 레포지토리를 포크합니다
2. 포크를 로컬에 클론합니다
3. `main`에서 기능 브랜치를 생성합니다

## 브랜치 전략

| 브랜치 | 목적 |
|---|---|
| `main` | 안정 릴리스 브랜치 |
| `dev` | 활성 개발 브랜치 |
| `feature/*` | 새 기능 |
| `fix/*` | 버그 수정 |
| `docs/*` | 문서 업데이트 |

## 커밋 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/)를 따릅니다:

```
<type>(<scope>): <description>

[선택적 본문]
```

**타입:**
- `feat` — 새 기능
- `fix` — 버그 수정
- `docs` — 문서 변경
- `refactor` — 코드 리팩토링
- `test` — 테스트 추가 또는 업데이트
- `chore` — 유지보수 작업

**예시:**
```
feat(genesis): implement seed prompt parser
fix(hivemind): resolve wiki page duplication
docs(readme): update roadmap section
```

## Pull Request 프로세스

1. 브랜치가 `main`과 최신 상태인지 확인
2. 명확한 PR 제목과 설명 작성
3. 관련 이슈 연결
4. 최소 1명의 메인테이너에게 리뷰 요청
5. 모든 CI 검사가 통과해야 머지 가능

## 코드 표준

- Python: PEP 8 준수, 타입 힌트 사용
- TypeScript: ESLint 설정 준수
- 모든 함수에 docstring/JSDoc 필수
- 새 기능에 테스트 필수

## 문서

- 모든 문서는 영어 + 한국어 (`.ko.md`) 버전을 유지합니다
- 문서 변경 시 양쪽 버전을 모두 업데이트하세요
- 새 용어가 추가되면 용어 사전을 최신 상태로 유지하세요

## 질문이 있으신가요?

`question` 라벨로 이슈를 열어주세요.
