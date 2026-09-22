#!/usr/bin/env python3
"""
duplicate-check: history.jsonl과 후보 제목/키워드의 문자 2-gram Jaccard 유사도

형태소 분석기 없이 한국어 짧은 텍스트에도 잘 맞는 문자 2-gram 방식을 쓴다.
스크립트는 1차 분류(duplicate/boundary/distinct)까지만 한다 — boundary
판정에 대한 "같은 글인가 다른 각도인가" 의미 판단은 keyword-scout
에이전트(LLM)가 한다 (설계서 §2.3).

사용법:
    python similarity.py --title "제목" --keyword "키워드" --history history.jsonl

Python 3.9 이상, 표준 라이브러리만 사용.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DUPLICATE_THRESHOLD = 0.8
BOUNDARY_THRESHOLD = 0.5


def char_ngrams(text: str, n: int = 2) -> set[str]:
    cleaned = re.sub(r"\s+", "", text)
    if len(cleaned) < n:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i + n] for i in range(len(cleaned) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def load_history(history_path: Path) -> list[dict]:
    if not history_path.exists():
        return []
    entries = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def classify(similarity: float) -> str:
    if similarity >= DUPLICATE_THRESHOLD:
        return "duplicate"
    if similarity >= BOUNDARY_THRESHOLD:
        return "boundary"
    return "distinct"


def check(candidate_title: str, candidate_keyword: str, history: list[dict]) -> list[dict]:
    cand_title_ng = char_ngrams(candidate_title)
    cand_keyword_ng = char_ngrams(candidate_keyword)

    results = []
    for entry in history:
        hist_title = entry.get("title", "")
        hist_keyword = entry.get("keyword", "")

        title_sim = jaccard(cand_title_ng, char_ngrams(hist_title))
        keyword_sim = jaccard(cand_keyword_ng, char_ngrams(hist_keyword))
        similarity = round(max(title_sim, keyword_sim), 3)

        results.append({
            "history_title": hist_title,
            "history_keyword": hist_keyword,
            "history_url": entry.get("url", ""),
            "similarity": similarity,
            "verdict": classify(similarity),
        })

    results.sort(key=lambda x: -x["similarity"])
    return results


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--history", required=True)
    args = parser.parse_args()

    history = load_history(Path(args.history))
    results = check(args.title, args.keyword, history)

    top_verdict = results[0]["verdict"] if results else "distinct"
    print(json.dumps({
        "candidate_title": args.title,
        "candidate_keyword": args.keyword,
        "history_count": len(history),
        "top_verdict": top_verdict,
        "matches": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
