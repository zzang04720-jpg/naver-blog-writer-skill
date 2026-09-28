---
name: naver-serp-collector
description: NAVER API HUB 검색 API(blog/news)로 블로그 상위 N건, 뉴스 최근 N일, 특정 키워드의 총 문서 수를 수집하는 스크립트 스킬. S1(뉴스 소재), S2(문서 수), S4(상위글)에서 쓴다.
---

# naver-serp-collector

## 트리거 조건
`keyword-scout`가 S1(뉴스 소재 발굴), S2(블로그 총 문서 수 조회), S4(경쟁 블로그 상위글 수집)에 진입할 때.

## 필요 자격 증명
`.env`(프로젝트 루트)의 `NAVER_SEARCH_CLIENT_ID`, `NAVER_SEARCH_CLIENT_SECRET`. 네이버 검색광고 API와는 **별개의 자격 증명**이다. 발급 경로: `console.ncloud.com` → NAVER API HUB → Application에서 검색 API 사용 설정.

> 이 스크립트는 NAVER API HUB 검색 API를 사용한다. `.env`의 기존 변수명에 API HUB Application의 인증 키를 넣는다. 새 설치에서는 사용자 계정으로 연결을 확인해야 하며 오프라인 테스트는 인증 성공을 보장하지 않는다.

## 처리
1. `X-NCP-APIGW-API-KEY-ID`, `X-NCP-APIGW-API-KEY` 헤더로 `GET https://naverapihub.apigw.ntruss.com/search/v1/blog` 또는 `.../news`을 호출한다
2. **블로그 상위 N건**: `query`(대상 키워드), `display`(최대 100), `sort=sim`으로 호출해 `items[]`의 `title`/`description`/`bloggername`/`postdate`/`link`를 추출한다
3. **최근 7일 뉴스**: `.../news`을 `sort=date`로 호출한 뒤, 응답의 `pubDate`를 파싱해 7일 이내 항목만 남긴다
4. **총 문서 수(포화도용)**: `display=1`로 블로그 검색을 호출해 응답의 `total` 필드만 사용한다 (실제 항목은 안 봐도 됨)
5. **인플루언서/기업 블로그 근사 판단**: `bloggername`에 브랜드성 키워드(예: 특정 업체명 패턴, "공식", "official", 특정 대형 커뮤니티/미디어명)가 있는지 체크하는 근사치 휴리스틱을 쓴다. 정교한 판별이 아니라 `keyword-scoring`이 40% 임계값 계산에 쓸 근사값을 제공하는 용도다

## 입력 / 출력
- 입력: 검색어, 검색 종류(`blog`/`news`), 옵션(`--display`, `--days`)
- 출력: JSON — `{total, items: [{title, description, link, blogger_or_source, date}]}`

## 사용법
```bash
python .claude/skills/naver-serp-collector/scripts/serp.py blog "강아지 사료" --display 30
python .claude/skills/naver-serp-collector/scripts/serp.py news "강아지" --days 7
python .claude/skills/naver-serp-collector/scripts/serp.py total "강아지 사료 추천"
```

## 실패 처리
- 자격 증명 없음 → 에스컬레이션. keyword-scout는 이 스킬 없이는 S2의 포화도 계산과 S4의 경쟁글 분석을 진행할 수 없으므로, 이 경우 S1~S5 전체가 막힌다는 것을 사람에게 알려야 한다
- API 호출 실패(HTTP 오류, 특히 일일 호출 한도 초과 429) → 에스컬레이션, 응답 본문 그대로 출력

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.
