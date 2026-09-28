#!/usr/bin/env python3
"""
image-uploader: images/ -> GitHub 공개 레포 push -> images.json에 공개 URL 기록

S8.5(이미지 호스팅) 단계 스크립트. 스마트에디터는 base64 삽입과 로컬 경로를
차단하므로(C9), 붙여넣기로 이미지가 함께 들어가려면 공개 https URL이 이미
있어야 한다. 이 스크립트가 그 URL을 만든다.

사용법:
    python upload_images.py <output-dir> <date>

<output-dir> 예: output/2026-09-04_puppy-vaccine-schedule
<date>       예: 2026-09-04   (레포 안에서 이 날짜 폴더 아래로 push)

.env(프로젝트 루트, blog-profile.yaml이 있는 폴더)에서
GITHUB_TOKEN, GITHUB_REPO(형식: owner/repo)를 읽는다. 값이 비어 있으면
바로 에스컬레이션하고 종료한다.

주의: 이 스크립트는 실제 GitHub 공개 레포가 만들어지고 GITHUB_TOKEN이
발급된 뒤에만 실행 테스트가 가능하다. 레포/토큰 정보는 하드코딩하지 않고
.env에서만 읽는다.

Python 3.9 이상, 표준 라이브러리만 사용 (추가 설치 불필요).
"""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote
from pathlib import Path

MAX_RETRY = 1
GITHUB_API = "https://api.github.com"
GITHUB_BRANCH = "main"


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
    """blog-profile.yaml이 있는 상위 폴더를 프로젝트 루트로 본다 (.env도 거기 있다)."""
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "blog-profile.example.yaml").is_file() and (parent / "CLAUDE.md").is_file():
            return parent
    raise RuntimeError("이 저장소 안에서 실행하세요. blog-profile.example.yaml과 CLAUDE.md가 필요합니다.")


def github_request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "naver-blog-agent-image-uploader")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_file(repo: str, token: str, repo_path: str, local_path: Path, branch: str = GITHUB_BRANCH) -> str:
    """파일을 GitHub Contents API로 push하고 raw.githubusercontent.com URL을 반환한다."""
    content_b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
    encoded_path = quote(repo_path, safe="/")
    url = f"{GITHUB_API}/repos/{repo}/contents/{encoded_path}"

    # 같은 경로에 파일이 이미 있으면(재실행 등) 업데이트에 sha가 필요하다
    sha = None
    try:
        existing = github_request("GET", f"{url}?ref={quote(branch, safe='')}", token)
        sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    payload = {"message": f"add {repo_path}", "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha

    github_request("PUT", url, token, payload)
    return f"https://raw.githubusercontent.com/{repo}/{quote(branch, safe='')}/{encoded_path}"


def verify_url(url: str) -> bool:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.URLError:
        return False


def load_or_build_entries(images_dir: Path, images_json_path: Path) -> list[dict]:
    """
    S8(visual-producer/canva-visuals)가 만들어둔 images.json 초안(파일명/포지션/alt/source,
    public_url은 아직 없음)이 있으면 그걸 기준으로 채운다. 없으면 images/ 폴더를 훑어
    새로 만든다 (이 경우 alt/source는 빈 값이 되므로 나중에 보완이 필요하다).
    """
    if images_json_path.exists():
        return json.loads(images_json_path.read_text(encoding="utf-8"))

    files = sorted(f for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    thumbnails = [f for f in files if f.stem.lower() == "thumbnail"]
    body = [f for f in files if f not in thumbnails]
    positioned = [(0, f) for f in thumbnails] + list(enumerate(body, 1))
    return [
        {
            "position": idx,
            "filename": f.name,
            "public_url": None,
            "alt": "",
            "source": "unknown",
            "status": "pending",
        }
        for idx, f in positioned
    ]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        print("사용법: python upload_images.py <output-dir> <date:YYYY-MM-DD>")
        sys.exit(1)

    out_dir = Path(sys.argv[1])
    date_str = sys.argv[2]
    images_dir = out_dir / "images"
    images_json_path = out_dir / "images.json"

    project_root = find_project_root(Path(__file__).parent)
    env = load_env(project_root / ".env")
    token = env.get("GITHUB_TOKEN")
    repo = env.get("GITHUB_REPO")
    branch = env.get("GITHUB_BRANCH") or GITHUB_BRANCH

    if not token or not repo:
        print(
            "[에스컬레이션] .env에 GITHUB_TOKEN / GITHUB_REPO가 없습니다. "
            ".env.example을 참고해 프로젝트 루트의 .env를 채워주세요."
        )
        sys.exit(1)

    if not images_dir.exists():
        print(f"[에스컬레이션] {images_dir} 가 없습니다.")
        sys.exit(1)

    entries = load_or_build_entries(images_dir, images_json_path)

    failures: list[str] = []
    for entry in entries:
        local_path = images_dir / entry["filename"]
        if not local_path.exists():
            entry["status"] = "failed"
            entry["public_url"] = None
            failures.append(entry["filename"])
            continue

        # 같은 날 작성한 다른 글의 thumbnail.jpg를 덮어쓰지 않는다.
        repo_path = f"{date_str}/{out_dir.resolve().name}/{entry['filename']}"
        url = None
        for attempt in range(1 + MAX_RETRY):
            try:
                candidate = upload_file(repo, token, repo_path, local_path, branch)
                if verify_url(candidate):
                    url = candidate
                    break
                print(f"  {entry['filename']}: 업로드는 됐지만 URL이 200을 반환하지 않음 (시도 {attempt + 1})")
            except Exception as e:  # noqa: BLE001 — 네트워크/API 오류를 모두 재시도 대상으로 취급
                print(f"  {entry['filename']} 업로드 시도 {attempt + 1} 실패: {e}")
            if attempt < MAX_RETRY:
                time.sleep(2)

        if url:
            entry["public_url"] = url
            entry["status"] = "ok"
        else:
            entry["public_url"] = None
            entry["status"] = "failed"
            failures.append(entry["filename"])

    images_json_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if failures:
        print(f"[에스컬레이션] 다음 이미지는 공개 URL 확보에 실패했습니다: {', '.join(failures)}")
        print("이 단계는 스킵할 수 없습니다 — 실패하면 이미지 없는 글이 그대로 나갑니다.")
        sys.exit(1)

    print(f"이미지 {len(entries)}개 업로드 완료 → {images_json_path}")


if __name__ == "__main__":
    main()
