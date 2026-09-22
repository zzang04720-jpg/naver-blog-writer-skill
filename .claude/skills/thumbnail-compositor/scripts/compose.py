#!/usr/bin/env python3
"""
thumbnail-compositor (폴백 전용): 배경 사진 + 텍스트 4개(line1~3, sub) -> 완성된 썸네일

v1.6 기준 정상 흐름에서는 사용하지 않는다. 썸네일은 사람이 캔바
"대량 제작"으로 직접 만든다. 이 스크립트는 캔바를 쓸 수 없는 상황을
대비한 폴백으로만 보존한다.

사용법:
    python compose.py --background <사진경로> --line1 "강아지가" \
        --line2 "피하는이유" --line3 "따로있다" \
        --sub "손이 아니라 태도가 만드는 차이" --output <출력경로>

배경 사진이 없으면 임시 그라데이션으로 대체한다 (개발/테스트용).
"""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).parent.parent / "assets"
BLACK_HAN = str(ASSETS_DIR / "BlackHanSans.ttf")
NOTO_BOLD = str(ASSETS_DIR / "NotoSansKR-Bold.ttf")

W, H = 1264, 1264
PHOTO_RATIO = 0.42
FRAME_COLOR = (60, 200, 190)
LINE1_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 212, 0)
OUTLINE_COLOR = (0, 0, 0)
TEXT_X = 90
LINE_START_Y = 220
LINE_GAP = 130


def draw_outlined_text(draw_obj, pos, text, font, fill, outline_width=7):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1, 2):
        for dy in range(-outline_width, outline_width + 1, 2):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw_obj.text((x + dx, y + dy), text, font=font, fill=OUTLINE_COLOR)
    draw_obj.text((x, y), text, font=font, fill=fill)


def compose(background_path: str | None, line1: str, line2: str, line3: str,
            sub: str, output_path: str) -> None:
    photo_w = int(W * PHOTO_RATIO)

    if background_path and Path(background_path).exists():
        bg = Image.open(background_path).convert("RGB")
        bg_ratio = bg.width / bg.height
        target_ratio = photo_w / H
        if bg_ratio > target_ratio:
            new_h = bg.height
            new_w = int(new_h * target_ratio)
            left = (bg.width - new_w) // 2
            bg = bg.crop((left, 0, left + new_w, new_h))
        else:
            new_w = bg.width
            new_h = int(new_w / target_ratio)
            top = (bg.height - new_h) // 2
            bg = bg.crop((0, top, new_w, top + new_h))
        bg = bg.resize((photo_w, H))
        img = Image.new("RGB", (W, H), (10, 12, 22))
        img.paste(bg, (W - photo_w, 0))
    else:
        img = Image.new("RGB", (W, H), (10, 12, 22))
        d = ImageDraw.Draw(img)
        for x in range(W - photo_w, W):
            t = (x - (W - photo_w)) / photo_w
            d.line([(x, 0), (x, H)], fill=(int(40 + t * 60), int(35 + t * 50), int(45 + t * 60)))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(0, W - photo_w + 100):
        t = x / (W - photo_w + 100)
        od.line([(x, 0), (x, H)], fill=(8, 10, 20, int(230 * (1 - t * 0.3))))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    frame_box = [40, 40, W - photo_w - 20, H - 40]
    draw.rectangle(frame_box, outline=FRAME_COLOR, width=6)
    draw.rectangle(
        [frame_box[0] + 20, frame_box[1] + 20, frame_box[2] - 20, frame_box[3] - 20],
        outline=FRAME_COLOR, width=2,
    )

    line_font = ImageFont.truetype(BLACK_HAN, 92)
    for i, (text, color) in enumerate([(line1, LINE1_COLOR), (line2, ACCENT_COLOR), (line3, ACCENT_COLOR)]):
        draw_outlined_text(draw, (TEXT_X, LINE_START_Y + i * LINE_GAP), text, line_font, color)

    sub_y = H - 160
    draw.ellipse([TEXT_X, sub_y, TEXT_X + 50, sub_y + 50], fill=FRAME_COLOR)
    bar_x1 = frame_box[2] - 30
    draw.rectangle([TEXT_X + 65, sub_y + 5, bar_x1, sub_y + 45], fill=(10, 10, 15))
    sub_font = ImageFont.truetype(NOTO_BOLD, 34)
    try:
        sub_font.set_variation_by_axes([700])
    except Exception:
        pass
    draw.text((TEXT_X + 80, sub_y + 8), sub, font=sub_font, fill=(255, 255, 255))

    img.save(output_path, quality=95)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--background", default=None)
    p.add_argument("--line1", required=True)
    p.add_argument("--line2", required=True)
    p.add_argument("--line3", required=True)
    p.add_argument("--sub", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    compose(args.background, args.line1, args.line2, args.line3, args.sub, args.output)
    print(f"완료: {args.output}")


if __name__ == "__main__":
    main()
