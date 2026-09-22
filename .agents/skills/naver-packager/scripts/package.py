#!/usr/bin/env python3
"""
naver-packager: 02_draft.md + 02_meta.json + images.json -> post.html + publish.md

S9(패키징) 단계 스크립트. 설계서(naver-blog-agent-design.md v1.2) §2.2 S9,
§3.6, SKILL.md의 변환 규칙을 그대로 따른다.

핵심 규칙
- 소제목은 <h2>를 쓰지 않는다. 스마트에디터가 h 태그 폰트 크기를 자기 기본값으로
  덮어쓰기 때문에, 인라인 스타일 span으로 크기를 박는다.
- 이미지는 <img src="https://..."> 로 본문 위치에 직접 삽입한다. 02_draft.md의
  [[IMG-01: 설명]] 마커는 정상 경로에서 최종 post.html에 남지 않는다 (마커 방식은
  붙여넣기 실패 시 폴백 전용).
- 굵게(**), 목록(-/1.), 표(|...|)는 그대로 유지한다.
- img 태그 수와 생성된 이미지 수가 다르면 실패로 처리하고 에스컬레이션한다
  (자동 재시도는 이 스크립트를 호출하는 오케스트레이터 쪽 책임 — 이 스크립트는
  1회 실행 결과만 돌려준다).

사용법:
    python package.py <output-dir>

<output-dir> 예: output/2026-09-04_puppy-vaccine-schedule
  해당 폴더 안에 02_draft.md, 02_meta.json, images.json이 있어야 한다.
  결과로 post.html, publish.md를 같은 폴더에 만든다.

Python 3.9 이상 필요.
"""
from __future__ import annotations

import json
import re
import sys
import webbrowser
from pathlib import Path

IMG_MARKER = re.compile(r"\[\[IMG-(\d+)(?::[^\]]*)?\]\]")
TITLE_LINE = re.compile(r"^#\s+")
HEADING_LINE = re.compile(r"^##\s+")
BULLET_LINE = re.compile(r"^[-*]\s+(.*)")
ORDERED_LINE = re.compile(r"^\d+\.\s+(.*)")
BOLD_INLINE = re.compile(r"\*\*(.+?)\*\*")
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def convert_inline(text: str) -> str:
    """굵게(**text**)만 처리한다. 그 외 마크다운 인라인 문법은 쓰지 않는다는 전제."""
    return BOLD_INLINE.sub(r"<b>\1</b>", text)


def build_image_map(images: list[dict]) -> dict[int, dict]:
    """images.json -> {position: entry}. 썸네일(position 0)은 본문 삽입 대상이 아니므로 뺀다."""
    result: dict[int, dict] = {}
    for img in images:
        pos = img.get("position")
        if pos is None or pos == 0:
            continue
        result[pos] = img
    return result


def convert_table(table_lines: list[str]) -> str:
    rows: list[list[str]] = []
    for idx, raw in enumerate(table_lines):
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if idx == 1 and all(SEPARATOR_CELL.fullmatch(c) for c in cells):
            continue  # 헤더 구분선(---) 행은 건너뛴다
        rows.append(cells)
    if not rows:
        return ""
    header, *body = rows
    thead = "".join(f"<th>{convert_inline(c)}</th>" for c in header)
    tbody = "".join(
        "<tr>" + "".join(f"<td>{convert_inline(c)}</td>" for c in row) + "</tr>"
        for row in body
    )
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"


def convert_markdown(md_text: str, image_map: dict[int, dict]) -> tuple[str, int, list[str]]:
    """
    반환: (본문 HTML, 실제 삽입된 img 태그 수, 미생성/미매칭 이미지 경고 목록)
    """
    lines = md_text.splitlines()
    html_parts: list[str] = []
    img_count = 0
    missing_images: list[str] = []

    list_buffer: list[str] = []
    list_type: str | None = None  # "ul" | "ol"

    def flush_list() -> None:
        nonlocal list_buffer, list_type
        if not list_buffer:
            return
        tag = list_type or "ul"
        items = "".join(f"<li>{convert_inline(item)}</li>" for item in list_buffer)
        html_parts.append(f"<{tag}>{items}</{tag}>")
        list_buffer = []
        list_type = None

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            flush_list()
            i += 1
            continue

        marker_match = IMG_MARKER.fullmatch(line.strip())
        if marker_match:
            flush_list()
            pos = int(marker_match.group(1))
            img = image_map.get(pos)
            if img and img.get("public_url") and img.get("status", "ok") != "failed":
                alt = img.get("alt", "")
                html_parts.append(f'<p><img src="{img["public_url"]}" alt="{alt}" /></p>')
                img_count += 1
            else:
                missing_images.append(f"IMG-{pos:02d}")
            i += 1
            continue

        if HEADING_LINE.match(line):
            flush_list()
            heading = HEADING_LINE.sub("", line).strip()
            html_parts.append(
                f'<p><span style="font-size:24px; font-weight:bold;">{convert_inline(heading)}</span></p>'
            )
            i += 1
            continue

        if line.startswith("|"):
            flush_list()
            table_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip())
                i += 1
            html_parts.append(convert_table(table_lines))
            continue

        bullet_match = BULLET_LINE.match(line)
        if bullet_match:
            if list_type == "ol":
                flush_list()
            list_type = "ul"
            list_buffer.append(bullet_match.group(1))
            i += 1
            continue

        ordered_match = ORDERED_LINE.match(line)
        if ordered_match:
            if list_type == "ul":
                flush_list()
            list_type = "ol"
            list_buffer.append(ordered_match.group(1))
            i += 1
            continue

        if TITLE_LINE.match(line):
            # 문서 제목(# ...)은 본문에 넣지 않는다 — 스마트에디터 제목란에 별도 입력
            flush_list()
            i += 1
            continue

        flush_list()
        html_parts.append(f"<p>{convert_inline(line.strip())}</p>")
        i += 1

    flush_list()
    return "\n".join(html_parts), img_count, missing_images


def build_publish_md(meta: dict, images: list[dict], missing_images: list[str]) -> str:
    titles = (meta.get("titles") or [])[:3]
    hashtags = meta.get("hashtags") or []
    thumbnail = next((i for i in images if i.get("position") == 0), None)

    lines: list[str] = ["# 발행 체크리스트", ""]

    lines.append("## 제목 후보 (택 1)")
    if titles:
        for t in titles:
            lines.append(f"- [ ] {t}")
    else:
        lines.append("- [ ] _(02_meta.json에 titles 없음 — 직접 입력)_")
    lines.append("")

    lines.append("## 태그")
    lines.append(", ".join(hashtags) if hashtags else "_(02_meta.json에 hashtags 없음 — 직접 입력)_")
    lines.append("")

    lines.append("## 카테고리 / 주제 분류")
    lines.append("- [ ] 카테고리: (블로그 카테고리 선택)")
    lines.append("- [ ] 주제 분류: 반려동물")
    lines.append("")

    lines.append("## 대표사진")
    if thumbnail and thumbnail.get("public_url"):
        lines.append(f"- [ ] {thumbnail['public_url']} 를 대표사진으로 지정")
    else:
        lines.append("- [ ] ⚠ 썸네일 이미지가 없습니다. 직접 지정하세요")
    lines.append("")

    lines.append("## 발행 설정")
    lines.append("- [ ] 검색 허용 ON 확인")
    lines.append("- [ ] 출처 한 줄 표기 확인")
    lines.append("")

    if missing_images:
        lines.append("## ⚠ 미생성 이미지 경고")
        for m in missing_images:
            lines.append(f"- {m} 이미지가 본문에 삽입되지 않았습니다. 위치를 확인하세요")
        lines.append("")

    lines.append("## 발행 직후 체감 수정도 (1~5점)")
    lines.append(
        "발행 후 실제로 얼마나 고쳤는지 숫자만 적어주세요 (1=거의 안 고침 ~ 5=거의 새로 씀). "
        "이 값은 history.jsonl의 revision_score로 옮겨 적히며, 참고 로그로만 쓰입니다 — "
        "자동 재시도나 성공/실패 판정에 영향을 주지 않습니다."
    )
    lines.append("")
    lines.append("revision_score: ")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        print("사용법: python package.py <output-dir>")
        sys.exit(1)

    out_dir = Path(sys.argv[1])
    draft_path = out_dir / "02_draft.md"
    meta_path = out_dir / "02_meta.json"
    images_path = out_dir / "images.json"

    if not draft_path.exists():
        print(f"[에스컬레이션] {draft_path} 가 없습니다.")
        sys.exit(1)

    meta = load_json(meta_path) or {}
    images = load_json(images_path) or []

    md_text = draft_path.read_text(encoding="utf-8")
    image_map = build_image_map(images)
    body_html, img_count, missing_images = convert_markdown(md_text, image_map)

    expected_img_count = len(
        [i for i in images if i.get("position") != 0 and i.get("status", "ok") != "failed"]
    )

    html = f"<!-- post.html — {out_dir.name} -->\n{body_html}\n"
    post_html_path = out_dir / "post.html"
    post_html_path.write_text(html, encoding="utf-8")

    publish_md = build_publish_md(meta, images, missing_images)
    publish_md_path = out_dir / "publish.md"
    publish_md_path.write_text(publish_md, encoding="utf-8")

    if img_count != expected_img_count:
        print(
            f"[에스컬레이션] img 태그 수({img_count})가 생성된 이미지 수({expected_img_count})와 "
            f"다릅니다. post.html과 images.json / 02_draft.md의 이미지 마커를 확인하세요."
        )
        sys.exit(1)

    print(f"post.html, publish.md 생성 완료 → {out_dir}")

    # 승인 게이트 2: post.html을 기본 브라우저로 자동으로 연다
    webbrowser.open(post_html_path.resolve().as_uri())


if __name__ == "__main__":
    main()
