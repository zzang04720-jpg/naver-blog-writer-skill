#!/usr/bin/env python3
"""
naver-keyword-api: 네이버 검색광고 API /keywordstool 호출

HMAC-SHA256 서명을 직접 구현한다 (설계서 C7).
입력: 시드 키워드 목록 (최대 5개, 네이버 API 제한)
출력: 키워드별 월간 검색수(PC+모바일 합산), 경쟁 지수

사용법:
    python keywordstool.py 키워드1 [키워드2 ...]

.env(프로젝트 루트, blog-profile.yaml이 있는 폴더)에서
NAVER_AD_CUSTOMER_ID, NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY를 읽는다.

Python 3.9 이상, 표준 라이브러리만 사용.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.naver.com"
URI = "/keywordstool"


def load_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "blog-profile.yaml").exists():
            return parent
    return start.resolve()


def build_signature(timestamp: str, method: str, uri: str, secret_key: str) -> str:
    message = f"{timestamp}.{method}.{uri}"
    digest = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def call_keywordstool(hint_keywords: list[str], customer_id: str, api_key: str, secret_key: str) -> dict:
    timestamp = str(int(time.time() * 1000))
    signature = build_signature(timestamp, "GET", URI, secret_key)

    query = urllib.parse.urlencode({
        "hintKeywords": ",".join(hint_keywords),
        "showDetail": "1",
    })
    url = f"{BASE_URL}{URI}?{query}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Timestamp", timestamp)
    req.add_header("X-API-KEY", api_key)
    req.add_header("X-Customer", customer_id)
    req.add_header("X-Signature", signature)

    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_volume(value) -> int:
    """'< 10' 같은 범위 문자열은 하한값(0)으로 취급한다 (설계서 §2.2 S2)."""
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if s.startswith("<"):
        return 0
    try:
        return int(s.replace(",", ""))
    except ValueError:
        return 0


def fetch_keywords(keywords: list[str], project_root: Path) -> list[dict]:
    env = load_env(project_root / ".env")
    customer_id = env.get("NAVER_AD_CUSTOMER_ID")
    api_key = env.get("NAVER_AD_API_KEY")
    secret_key = env.get("NAVER_AD_SECRET_KEY")

    if not all([customer_id, api_key, secret_key]):
        raise RuntimeError(
            "NAVER_AD_CUSTOMER_ID/NAVER_AD_API_KEY/NAVER_AD_SECRET_KEY 없음. "
            "searchad.naver.com → 도구 → API 사용 관리에서 발급 필요."
        )

    data = call_keywordstool(keywords[:5], customer_id, api_key, secret_key)

    results = []
    for item in data.get("keywordList", []):
        pc = parse_volume(item.get("monthlyPcQcCnt", 0))
        mobile = parse_volume(item.get("monthlyMobileQcCnt", 0))
        results.append({
            "keyword": item.get("relKeyword"),
            "monthly_pc": pc,
            "monthly_mobile": mobile,
            "monthly_total": pc + mobile,
            "comp_idx": item.get("compIdx"),
        })
    return results


def main() -> None:
    # Windows 콘솔 기본 코드페이지(cp949 등)로 인해 한글 출력이 깨지는 걸 방지한다.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    if len(sys.argv) < 2:
        print("사용법: python keywordstool.py 키워드1 [키워드2 ...] (최대 5개)")
        sys.exit(1)

    keywords = sys.argv[1:]
    if len(keywords) > 5:
        print(f"[경고] 네이버 API는 최대 5개 키워드만 허용한다. 초과분 무시: {keywords[5:]}", file=sys.stderr)
        keywords = keywords[:5]

    project_root = find_project_root(Path(__file__).parent)

    try:
        results = fetch_keywords(keywords, project_root)
    except RuntimeError as e:
        print(f"[에스컬레이션] {e}")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[에스컬레이션] API 호출 실패: HTTP {e.code}\n{body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[에스컬레이션] 네트워크 오류: {e}")
        sys.exit(1)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
