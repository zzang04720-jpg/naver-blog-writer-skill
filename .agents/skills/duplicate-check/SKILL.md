---
name: duplicate-check
description: history.jsonl의 기존 제목·키워드와 후보를 대조해 문자열 유사도를 계산하는 스크립트 스킬. 경계값 부근 판단은 스크립트가 하지 않고 keyword-scout 에이전트(LLM)가 의미 수준에서 내린다. S3 진입 시 항상 쓴다.
---

# duplicate-check

## 트리거 조건
`keyword-scout`가 S3(중복 체크)에 진입할 때 항상.

## 코드/판단 분리 (설계서 §2.3 원칙)
- **스크립트가 하는 일**: `history.jsonl`의 각 기존 항목과 후보 제목·키워드 사이의 문자열 유사도를 계산하고, 임계값에 따라 `duplicate`(중복 확정) / `boundary`(경계, 의미 판단 필요) / `distinct`(다름)로 1차 분류한다
- **에이전트(LLM)가 하는 일**: `boundary`로 분류된 건에 한해 "같은 글인가, 다른 각도인가"를 의미 수준에서 판단한다. 이건 스크립트에 넣지 않는다 — 문자열이 비슷해도 각도가 다르면 통과시켜야 하는데, 그 판단은 코드가 아니라 LLM의 몫이다

## 유사도 계산 방법
형태소 분석기 없이도 한국어 짧은 텍스트에 잘 작동하는 **문자 2-gram Jaccard 유사도**를 쓴다 (공백 제거 후 2글자씩 슬라이딩). 제목 유사도와 키워드 유사도 중 큰 값을 최종 유사도로 쓴다.

## 임계값 (구현 시 조정 가능한 기본값)
- 유사도 ≥ 0.8 → `duplicate` (자동 탈락)
- 0.5 ≤ 유사도 < 0.8 → `boundary` (LLM 판단 필요)
- 유사도 < 0.5 → `distinct` (통과)

## 입력 / 출력
- 입력: 후보 제목, 후보 키워드, `history.jsonl` 경로
- 출력: `history.jsonl`의 각 기존 항목에 대해 `{history_title, history_keyword, similarity, verdict}`를 유사도 내림차순으로 나열한 JSON

## 사용법
```bash
python .claude/skills/duplicate-check/scripts/similarity.py --title "강아지 중성화 수술 비용" --keyword "강아지 중성화 수술 비용" --history history.jsonl
```

## 실패 처리
`duplicate` 판정이 나오면 `keyword-scout`가 해당 후보를 스킵하고 다음 후보로 이동한다 (최대 3회 후 S1 복귀). `boundary` 판정은 실패가 아니다 — LLM이 판단할 대상일 뿐이다.

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.
