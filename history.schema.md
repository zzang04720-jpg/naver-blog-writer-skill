# history.jsonl 스키마

`history.jsonl`은 한 줄당 발행 글 1건을 JSON으로 기록한다 (JSON Lines). 각 줄이 파서가 읽을 유효한 JSON이어야 하므로 파일 안에 주석을 넣지 않고, 스키마 설명은 이 파일에 별도로 둔다.

## 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `date` | string | 발행일 (`YYYY-MM-DD`) |
| `title` | string | 실제 발행된 제목 |
| `keyword` | string | 확정 키워드 |
| `track` | string | `search` 또는 `homefeed` |
| `url` | string | 발행된 글의 블로그 URL |
| `revision_score` | number \| null | 발행 직후 사람이 `publish.md`에 남긴 체감 수정도 self-report (1~5). **참고 로그 전용 — 자동 재시도나 성공/실패 판정에 쓰지 않는다** (설계서 §1.3, §2.2 S9·S10) |

## 예시 한 줄

```json
{"date": "2026-09-10", "title": "강아지 첫 산책, 언제부터 얼마나 해야 할까", "keyword": "강아지 산책 시기", "track": "search", "url": "https://blog.naver.com/xxxxx/2231xxxxxxxx", "revision_score": 2}
```

## 현재 상태

이 프로젝트를 시작하는 시점에는 비어 있다. 기존에 수동으로 발행한 34건은 이 파일에 소급 기록하지 않는다 — 에이전트가 발행한 글부터 여기 누적된다. (기존 34건은 `duplicate-check` 단계에서 참조할 별도 이력이 필요하면 추후 논의한다.)
