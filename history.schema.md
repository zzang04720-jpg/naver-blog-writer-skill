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

## 새 설치

`history.jsonl`이 없으면 빈 이력으로 시작한다. 기존 발행 글이 있으면 본인의 실제 제목·URL을 이 스키마로 추가해야 중복 검사에 포함된다. 예시 데이터는 발행 이력으로 추가하지 않는다.
