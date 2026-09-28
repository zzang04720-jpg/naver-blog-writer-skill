---
name: thumbnail-compositor
description: Pillow(PIL)로 배경 사진 위에 텍스트 4개(line1~3, sub)를 직접 렌더링해 썸네일을 합성하는 스크립트. v1.6부터 폴백 전용이며 정상 흐름(S8)에서는 호출하지 않는다. 썸네일은 사람이 캔바에서 직접 만든다 (.claude/agents/visual-producer.md 참조).
---

# thumbnail-compositor

> **폴백 전용 — 정상 흐름에서 호출하지 않는다.** v1.6 기준 S8의 썸네일은 사람이 캔바 "강아지" 브랜드 템플릿 → 대량 제작에서 직접 만든다. 이 스크립트는 캔바를 쓸 수 없는 예외 상황(계정 문제, 오프라인 등)에서만 사람이 수동으로 실행하는 대비책이다.

## 왜 폴백으로 강등됐는가
이 스크립트는 실제로 만들고 검증됐다 — Canva Autofill API가 Enterprise 전용이라는 걸 확인한 뒤, PIL로 직접 텍스트를 합성해 자동화를 유지하려 시도한 결과물이다. 하지만 실제 출력물을 캔바 원본과 나란히 놓고 비교하니 품질 격차가 뚜렷했다(외곽선 렌더링이 거칠고, 그라데이션 오버레이가 계단현상을 보이며, 폰트 렌더링이 캔바만큼 매끈하지 않음). 자동화보다 품질을 우선하기로 하면서 이 스크립트는 주 경로에서 빠졌다.

**개선하고 싶다면 여기부터 손대는 게 좋다**: `draw_outlined_text`의 원형 스탬핑 방식 외곽선(계단현상의 주 원인), 좌측 그라데이션 오버레이의 픽셀 단위 라인 그리기(안티앨리어싱 없음). 더 매끈한 결과를 원하면 벡터 기반 외곽선(예: `ImageDraw`의 `stroke_width` 옵션)이나 고해상도 렌더링 후 다운샘플링을 검토한다.

## 트리거 조건
자동으로 호출되지 않는다. 캔바를 쓸 수 없어 사람이 직접 이 스크립트를 실행해야 할 때만 쓴다.

## 필요 패키지
```bash
pip install Pillow --break-system-packages
```

## 에셋
- `/assets/BlackHanSans.ttf` — 3줄 문구(line1~3)용 굵은 제목 폰트
- `/assets/NotoSansKR-Bold.ttf` — 보조문구(sub)용 폰트 (variable font, weight 700 적용 시도)

## 사용법
```bash
python .claude/skills/thumbnail-compositor/scripts/compose.py \
  --background <사진경로> \
  --line1 "강아지가" --line2 "피하는이유" --line3 "따로있다" \
  --sub "손이 아니라 태도가 만드는 차이" \
  --output <출력경로>
```
`--background`를 생략하거나 파일이 없으면 임시 그라데이션 배경으로 대체한다 (개발/테스트용이며 실제 발행용 결과물로는 부족하다).

## 처리
1. 1264×1264 캔버스에서 오른쪽 42%를 배경 사진 영역으로 자르고 채운다 (사진 없으면 그라데이션)
2. 왼쪽에서 사진 영역으로 갈수록 어두워지는 그라데이션 오버레이를 얹어 텍스트 가독성을 확보한다
3. 프레임(이중 사각형 테두리)을 그린다
4. `line1`(흰색)/`line2`/`line3`(포인트색)을 BlackHanSans로 외곽선과 함께 렌더링한다
5. 하단에 원형 불릿 + 바 + `sub` 텍스트(NotoSansKR-Bold)를 렌더링한다
6. 결과를 저장한다 (quality=95)

## 출력
`--output`에 지정한 경로에 JPG/PNG로 저장된다. 정상 흐름에서 쓸 경우 `output/<slug>/images/thumbnail.jpg`로 저장하면 이후 S8.5(`image-uploader`)가 그대로 처리한다.

## 실패 처리
1회 재시도한다. 재시도도 실패하면 스킵하고 로그에 남긴다 (재활성화 시 기준. 현재는 사람이 직접 실행하므로 실패 시 사람이 바로 재시도 여부를 판단한다).

## 경로 기준

위 실행 명령은 저장소 루트에서 실행한다. `references/`와 `assets/`는 이 SKILL.md가 있는 폴더 기준이다. 다른 런타임에서는 `.claude/skills/` 대신 `.agents/skills/`의 동일한 스크립트를 사용할 수 있다.
