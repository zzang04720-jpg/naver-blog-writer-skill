---
name: naver-keyword-api
description: 네이버 검색광고 API `/keywordstool`을 호출해 월간 검색수(PC+모바일)와 연관키워드를 반환하는 스크립트 스킬. HMAC-SHA256 서명을 스크립트가 처리하므로 에이전트는 결과 JSON만 소비한다. keyword-scout가 S1 확장 또는 S2 검증에 진입할 때 사용한다.
---

# naver-keyword-api

## 트리거 조건
`keyword-scout`가 S1(연관키워드 확장) 또는 S2(검색량 검증)에 진입할 때.

## 필요 자격 증명
`.env`(프로젝트 루트)의 `NAVER_AD_CUSTOMER_ID`, `NAVER_AD_API_KEY`, `NAVER_AD_SECRET_KEY`. 발급 경로: `searchad.naver.com` → 도구 → API 사용 관리 → 서비스 신청 (심사 없이 즉시 발급, 광고 집행 의무 없음).

## 처리
1. `timestamp.GET./keywordstool` 문자열을 Secret Key로 HMAC-SHA256 서명하고 base64 인코딩한다 (C7)
2. `X-Timestamp`, `X-API-KEY`, `X-Customer`, `X-Signature` 헤더를 붙여 `GET /keywordstool?hintKeywords=...&showDetail=1`을 호출한다
3. 응답의 `monthlyPcQcCnt`/`monthlyMobileQcCnt`를 합산해 `monthly_total`을 계산한다
4. **범위 문자열 처리**: 검색량이 `"< 10"` 같은 범위 문자열로 오면 하한값(0)으로 강제 변환한다. Phase 1 최소 검색량(300)보다 훨씬 낮으므로 파싱 예외 없이 자연스럽게 임계값 미달로 필터링된다 (설계서 §2.2 S2)

## 입력 / 출력
- 입력: 시드 키워드 목록 (CLI 인자, 최대 5개 — 네이버 API 제한)
- 출력: `[{keyword, monthly_pc, monthly_mobile, monthly_total, comp_idx}, ...]` JSON

## 사용법
```bash
python .claude/skills/naver-keyword-api/scripts/keywordstool.py 강아지훈련 강아지사료 강아지산책
```

## 실패 처리
- 자격 증명 없음 → 에스컬레이션 메시지 출력, `keyword-scout`가 §2.4 대체 경로(자동완성/연관검색어 기반 정성 판단, `volume_source: "estimated"`)로 분기
- API 호출 실패(HTTP 오류) → 에스컬레이션, 응답 본문을 그대로 출력해 원인 파악을 돕는다

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.
