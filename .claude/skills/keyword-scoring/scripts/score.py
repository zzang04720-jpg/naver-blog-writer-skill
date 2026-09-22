#!/usr/bin/env python3
"""
keyword-scoring: 포화도 계산 + phase별 임계값 필터 + 점수 정렬

입력 후보 형식 (JSON 배열):
    [{"keyword": "...", "monthly_total": 970, "blog_total": 15000,
      "top10_brand_ratio": 0.2}, ...]

- monthly_total: naver-keyword-api의 monthly_total
- blog_total: naver-serp-collector의 total (display=1 조회 결과)
- top10_brand_ratio: 상위 10건 중 brand_like==true 비율 (0~1). 없으면 0으로 간주

사용법:
    python score.py candidates.json --phase 1
    cat candidates.json | python score.py - --phase 1

Python 3.9 이상, 표준 라이브러리만 사용.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Phase 1 기본 임계값 (설계서 §2.2 S2, 구현 시 조정 가능)
PHASE1_MIN_VOLUME = 300
PHASE1_MAX_VOLUME = 3000
PHASE1_MAX_SATURATION = 10
PHASE1_MAX_BRAND_RATIO = 0.4

# Phase 2는 키워드 난이도 상한만 완화한다 (§1.3). 실사용 데이터가 쌓이기 전까지의 잠정값.
PHASE2_MIN_VOLUME = 300
PHASE2_MAX_VOLUME = 10000
PHASE2_MAX_SATURATION = 30
PHASE2_MAX_BRAND_RATIO = 0.4


def load_candidates(path: str) -> list[dict]:
    if path == "-":
        text = sys.stdin.read()
    else:
        text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def score_candidate(c: dict, phase: int) -> dict:
    keyword = c.get("keyword", "")
    volume = c.get("monthly_total", 0)
    blog_total = c.get("blog_total")
    brand_ratio = c.get("top10_brand_ratio", 0.0)

    if phase == 2:
        min_v, max_v, max_sat, max_brand = (
            PHASE2_MIN_VOLUME, PHASE2_MAX_VOLUME, PHASE2_MAX_SATURATION, PHASE2_MAX_BRAND_RATIO
        )
    else:
        min_v, max_v, max_sat, max_brand = (
            PHASE1_MIN_VOLUME, PHASE1_MAX_VOLUME, PHASE1_MAX_SATURATION, PHASE1_MAX_BRAND_RATIO
        )

    reasons = []

    if volume <= 0:
        return {
            "keyword": keyword, "monthly_total": volume, "saturation": None,
            "score": 0.0, "passed": False, "reasons": ["검색량 0 — 포화도 정의 불가"],
        }

    if volume < min_v:
        reasons.append(f"검색량 {volume} < 최소 {min_v}")
    if volume > max_v:
        reasons.append(f"검색량 {volume} > 최대 {max_v}")

    saturation = None
    if blog_total is not None:
        saturation = round(blog_total / volume, 2)
        if saturation > max_sat:
            reasons.append(f"포화도 {saturation} > 상한 {max_sat}")
    else:
        reasons.append("blog_total 없음 — 포화도 계산 불가 (naver-serp-collector 필요)")

    if brand_ratio > max_brand:
        reasons.append(f"상위 10건 브랜드 비중 {brand_ratio:.0%} > 상한 {max_brand:.0%}")

    passed = len(reasons) == 0
    score = round(volume / ((saturation or 0) + 1), 2) if passed else 0.0

    return {
        "keyword": keyword,
        "monthly_total": volume,
        "saturation": saturation,
        "score": score,
        "passed": passed,
        "reasons": reasons if reasons else ["통과"],
    }


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("candidates_file", help="후보 JSON 파일 경로, 또는 '-'로 stdin")
    parser.add_argument("--phase", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()

    candidates = load_candidates(args.candidates_file)
    scored = [score_candidate(c, args.phase) for c in candidates]
    scored.sort(key=lambda x: (-x["passed"], -x["score"]))

    passed_count = sum(1 for s in scored if s["passed"])
    print(json.dumps({"phase": args.phase, "passed_count": passed_count, "candidates": scored},
                      ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
