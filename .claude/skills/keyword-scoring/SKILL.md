---
name: keyword-scoring
description: naver-keyword-api(검색량)와 naver-serp-collector(문서 수) 결과를 합쳐 포화도를 계산하고, blog-profile.yaml의 phase에 맞는 임계값 필터를 적용해 후보를 정렬하는 스크립트 스킬. S2에서 데이터 수집 완료 직후 쓴다.
---

# keyword-scoring

## 트리거 조건
`keyword-scout`가 S2에서 `naver-keyword-api`(검색량)와 `naver-serp-collector`(블로그 총 문서 수)를 모두 조회한 직후.

## 처리
1. 후보 키워드별로 `monthly_total`(검색량)과 `total`(블로그 총 문서 수)을 입력받는다
2. **포화도** = 블로그 총 문서 수 ÷ 월간 검색수 로 계산한다 (검색량 0이면 포화도는 정의하지 않고 자동 탈락)
3. `blog-profile.yaml`의 `phase` 값을 읽어 필터를 적용한다
   - Phase 1 기본값(설계서 §2.2 S2, 구현 시 조정 가능): 월간 검색수 300~3,000, 포화도 10 이하, 상위 10건 중 인플루언서/기업 공식 블로그 비중 40% 미만(`naver-serp-collector`의 `brand_like` 근사값 사용)
   - Phase 2는 키워드 난이도 상한만 완화(§1.3) — 이 스크립트에서는 Phase 1 임계값만 우선 구현하고, Phase 2 임계값은 실사용 데이터가 쌓인 뒤 확정한다
4. 필터 통과 후보를 점수 순으로 정렬한다. 점수는 "검색량이 높고 포화도가 낮을수록" 유리하게 `score = monthly_total / (saturation + 1)` 로 근사한다 (구현 시 조정 가능한 기본값)

## 입력 / 출력
- 입력: 후보 리스트 `[{keyword, monthly_total, blog_total, top10_brand_ratio}, ...]` (JSON, stdin 또는 파일)
- 출력: 필터 통과 후보를 점수 내림차순으로 정렬한 JSON — `[{keyword, monthly_total, saturation, score, passed: true}, ...]`. 탈락 후보도 `passed: false`와 탈락 사유를 남긴다

## 사용법
```bash
python .claude/skills/keyword-scoring/scripts/score.py candidates.json --phase 1
```

## 실패 처리
필터 통과 후보 0건이면 `keyword-scout`에게 "임계값 완화 후 1회 재시도" 신호를 반환한다 (자체 재시도 로직은 없음 — `keyword-scout`가 완화된 임계값으로 이 스크립트를 다시 호출).

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.
