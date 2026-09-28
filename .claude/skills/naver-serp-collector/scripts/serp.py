#!/usr/bin/env python3
"""
naver-serp-collector: NAVER API HUB 검색 API(블로그/뉴스) 호출

NAVER API HUB 검색 API의 엔드포인트와 인증 헤더를 사용한다.
새 설치의 인증 성공 여부는 사용자 계정에서 별도로 확인한다.

사용법:
    python serp.py blog "강아지 사료" --display 30
    python serp.py news "강아지" --days 7
    python serp.py total "강아지 사료 추천"

.env(프로젝트 루트)에서 NAVER_SEARCH_CLIENT_ID, NAVER_SEARCH_CLIENT_SECRET을 읽는다
(변수명은 그대로 두되, 실제로는 API HUB의 Client ID/Secret 값이다).
Python 3.9 이상, 표준 라이브러리만 사용.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE_URL = "https://naverapihub.apigw.ntruss.com/search/v1"

# 인플루언서/기업 공식 블로그 근사 판단용 키워드 (§2.2 S2 40% 임계값용 휴리스틱).
# 정교한 판별기가 아니라 근사치 신호이며, 실사용 중 목록을 넓혀갈 수 있다.
BRAND_HINTS = ["공식", "official", "블로그팀", "마케팅", "PR", "주식회사", "(주)"]


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "blog-profile.example.yaml").is_file() and (parent / "CLAUDE.md").is_file():
            return parent
    raise RuntimeError("이 저장소 안에서 실행하세요. blog-profile.example.yaml과 CLAUDE.md가 필요합니다.")


def get_credentials(project_root: Path) -> tuple[str, str]:
    env = load_env(project_root / ".env")
    client_id = env.get("NAVER_SEARCH_CLIENT_ID")
    client_secret = env.get("NAVER_SEARCH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "NAVER_SEARCH_CLIENT_ID/NAVER_SEARCH_CLIENT_SECRET 없음. "
            "console.ncloud.com → NAVER API HUB 콘솔에서 발급 필요 "
        )
    return client_id, client_secret


def call_search_api(endpoint: str, query: str, display: int, start: int, sort: str,
                     client_id: str, client_secret: str) -> dict:
    params = urllib.parse.urlencode({
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
        "format": "json",
    })
    url = f"{BASE_URL}/{endpoint}?{params}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
    req.add_header("X-NCP-APIGW-API-KEY", client_secret)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_brand_like(name: str) -> bool:
    return any(hint.lower() in name.lower() for hint in BRAND_HINTS)


def search_blog(query: str, display: int, client_id: str, client_secret: str) -> dict:
    data = call_search_api("blog", query, display=display, start=1, sort="sim",
                            client_id=client_id, client_secret=client_secret)
    items = []
    for it in data.get("items", []):
        blogger = it.get("bloggername", "")
        items.append({
            "title": it.get("title", ""),
            "description": it.get("description", ""),
            "link": it.get("link", ""),
            "blogger_or_source": blogger,
            "date": it.get("postdate", ""),
            "brand_like": is_brand_like(blogger),
        })
    return {"total": data.get("total", 0), "items": items}


def search_news(query: str, days: int, client_id: str, client_secret: str) -> dict:
    data = call_search_api("news", query, display=100, start=1, sort="date",
                            client_id=client_id, client_secret=client_secret)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for it in data.get("items", []):
        pub_raw = it.get("pubDate", "")
        try:
            pub_dt = parsedate_to_datetime(pub_raw)
        except (TypeError, ValueError):
            continue
        if pub_dt >= cutoff:
            items.append({
                "title": it.get("title", ""),
                "description": it.get("description", ""),
                "link": it.get("link", ""),
                "blogger_or_source": it.get("originallink", ""),
                "date": pub_raw,
            })
    return {"total": data.get("total", 0), "items": items}


def search_total(query: str, client_id: str, client_secret: str) -> dict:
    data = call_search_api("blog", query, display=1, start=1, sort="sim",
                            client_id=client_id, client_secret=client_secret)
    return {"total": data.get("total", 0)}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["blog", "news", "total"])
    parser.add_argument("query")
    parser.add_argument("--display", type=int, default=30)
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    project_root = find_project_root(Path(__file__).parent)

    try:
        client_id, client_secret = get_credentials(project_root)
    except RuntimeError as e:
        print(f"[에스컬레이션] {e}")
        sys.exit(1)

    try:
        if args.mode == "blog":
            result = search_blog(args.query, args.display, client_id, client_secret)
        elif args.mode == "news":
            result = search_news(args.query, args.days, client_id, client_secret)
        else:
            result = search_total(args.query, client_id, client_secret)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[에스컬레이션] API 호출 실패: HTTP {e.code}\n{body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[에스컬레이션] 네트워크 오류: {e}")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
