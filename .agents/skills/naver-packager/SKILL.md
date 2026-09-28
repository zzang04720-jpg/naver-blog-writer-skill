---
name: naver-packager
description: 02_draft.md를 붙여넣기용 post.html로 변환하고 publish.md 체크리스트를 생성하는 스크립트 스킬. S9 진입 시 메인이 직접 실행한다 (서브에이전트를 거치지 않는다).
---

# naver-packager

## 트리거 조건
S9(패키징) 진입 시. 메인 오케스트레이터가 `visual-producer`의 `images.json`(공개 URL 포함)과 `post-writer`의 `02_draft.md`를 받아 직접 실행한다.

## 입력
- `output/<slug>/02_draft.md`
- `output/<slug>/02_meta.json`
- `output/<slug>/images.json`

## 출력
- `output/<slug>/post.html`
- `output/<slug>/publish.md`

## post.html 변환 규칙
- 굵게, 목록, 표는 마크다운을 그대로 HTML로 옮긴다. 현재 스마트에디터의 서식·이미지 복사 결과는 사람이 확인한다
- **소제목은 `<h2>`를 쓰지 않는다.** 스마트에디터가 h 태그의 폰트 크기를 자기 기본값으로 덮어써 본문과 구분이 사라지기 때문이다. 대신 인라인 스타일로 크기를 박는다:
  ```html
  <p><span style="font-size:24px; font-weight:bold;">소제목</span></p>
  ```
- **이미지는 `<img src="https://...">`로 본문 해당 위치에 직접 삽입한다.** `02_draft.md`의 이미지 삽입 위치 표시(`[[IMG-01: ...]]`)를 `images.json`의 `position`으로 매칭해 실제 `public_url`로 치환한다. 변환이 끝나면 `post.html`에는 삽입 위치 표시가 전혀 남지 않는다
- **마커(`[[IMG-01]]` 형태의 표시자)를 최종 결과물에 남기는 것은 정상 경로가 아니다.** 이 방식은 붙여넣기 실패 시의 폴백으로만 보존한다 (향후 스마트에디터 UI 변경으로 이미지가 함께 전송되지 않게 되면 그때 복귀)

## publish.md 생성 필드
- 제목 후보 3개 (`02_meta.json`의 `titles[8]` 중 상위 3개)
- 태그 5~8개
- 카테고리
- 주제 분류 (내 블로그와 글에 맞게 선택)
- 대표사진 지정 (썸네일)
- 검색 허용 ON 확인 체크박스
- 출처 한 줄
- 누락 이미지나 URL 불일치가 있으면 패키징 실패. 의도적으로 제외할 이미지는 검토 후 마커와 이미지 목록을 함께 수정하고 다시 실행한다
- **발행 직후 체감 수정도 입력란 (1~5점)** — 사람이 스마트에디터에 붙여넣고 발행을 마친 뒤 얼마나 고쳤는지 직접 적는 칸. 이 값은 나중에 S10에서 `history.jsonl`의 `revision_score`로 옮겨 적힌다. **하드 게이트가 아니다** — 이 값 자체는 재시도나 실패 판정에 영향을 주지 않으며, Phase 1 성공 기준의 참고 로그로만 쓰인다

## 게이트 2 연동
`post.html`을 생성한 직후 **OS 기본 브라우저로 자동으로 연다** (`start`/`open`/`xdg-open` 등 OS별 명령). 사람이 파일을 따로 찾아 열 필요 없이 바로 시각 확인 → 전체선택 → 복사로 이어가게 한다.

## 성공 기준
`post.html`이 브라우저에서 이미지 포함 정상 렌더되고, `<img>` 태그 수가 생성된 이미지 수와 같다.

## 실패 처리
1회 자동 재시도한다. 재시도도 실패하면 메인에 에스컬레이션한다.

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.

## 실행

저장소 루트에서 `python .claude/skills/naver-packager/scripts/package.py output/<slug>`를 실행한다. 오프라인 검사·서버 환경은 `--no-open`을 추가한다. 이 스크립트 자체는 사실 검증을 하지 않으므로 오케스트레이터가 S7 통과를 확인해야 한다.
