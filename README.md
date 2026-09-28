# 네이버 블로그 반자동화 글쓰기 에이전트

네이버 블로그 초안을 만들고 검토하는 **Claude Code용 프로젝트 스킬 묶음**입니다. 독립된 앱이나 자동 발행 서비스가 아닙니다. 이 저장소 전체를 전용 폴더에 설치하면 키워드 조사 → 초안 → 독립 검증 → 이미지 준비 → 붙여넣기용 HTML을 진행합니다. **최종 검토와 네이버 발행은 사람이 직접 합니다.**

인스타그램·Threads 스킬이나 다른 저장소의 파일은 필요하지 않습니다. 기본 예시는 반려동물 블로그이며 실제 블로그 정보와 연결 계정은 설치자가 설정합니다. 검색 노출, 애드포스트 승인, 수익은 보장하지 않습니다.

## 준비할 것

- Git 또는 GitHub의 Download ZIP (압축을 풀 때 `.claude`, `.agents` 숨김 폴더도 포함)
- [Claude Code CLI](https://code.claude.com/docs/en/setup) 설치와 로그인. 이 폴더를 신뢰하고 필요한 도구 권한을 직접 승인할 수 있어야 합니다.
- Python 3.9 이상. 검색·점수·중복·패키징은 표준 라이브러리만 사용합니다. 썸네일 합성 폴백에만 Pillow가 필요합니다.
- 실제 검색량 조회용 [네이버 검색광고 API](https://searchad.naver.com/) 키 3개
- 경쟁 블로그·뉴스 조회용 [NAVER API HUB Application](https://guide.ncloud-docs.com/docs/apihub-application)의 인증 키. 검색 API 주소는 `naverapihub.apigw.ntruss.com/search/v1`입니다. 이전 개발자센터 키와 구분하고 현재 이용 조건은 제공자의 안내를 확인하세요.
- 이미지 호스팅을 사용할 때: 본인 소유의 공개 GitHub 이미지 저장소와 해당 저장소만 선택한 fine-grained PAT. `Contents: Read and write` 권한이 필요합니다. [GitHub 권한 안내](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents)
- 선택: Canva MCP 연결. 연결이 없으면 본문 이미지와 썸네일을 직접 준비합니다. 개인 Canva 템플릿은 포함되어 있지 않습니다.
- 선택 GUI: Node.js 20 이상과 npm. GUI에서도 Claude Code CLI 설치와 로그인이 필요합니다.

## 설치 — Windows PowerShell

새 전용 폴더에 저장소 전체를 받습니다. 다른 프로젝트의 스킬 폴더와 합치지 마세요.

```powershell
git clone https://github.com/zzang04720-jpg/naver-blog-writer-skill.git
cd naver-blog-writer-skill
python scripts/doctor.py --offline
python -m unittest discover -s tests -v
Copy-Item .env.example .env
Copy-Item blog-profile.example.yaml blog-profile.yaml
```

이미 설정 파일이 있으면 복사 명령을 다시 실행하지 말고 기존 파일을 수정하세요. `.env`는 API 키를, `blog-profile.yaml`은 본인의 `blog_url`, `niche`, `tone`, `seed_keywords`, `phase`를 채웁니다. 빈 블로그 URL로는 S1 소재 발굴을 시작하지 않습니다. 예시 프로필은 실제 운영 설정이 아닙니다. `.env`, 실제 프로필, 발행 이력, 산출물은 Git에 포함되지 않습니다.

macOS/Linux에서는 `python` 대신 `python3`, `Copy-Item` 대신 `cp`를 사용할 수 있습니다.

필요할 때만 썸네일 합성용 패키지를 별도 환경에 설치합니다.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 시작하기

저장소 루트에서 실행합니다.

```powershell
python scripts/doctor.py
claude
```

doctor는 파일·도구 설치 여부를 확인하며 키 값이나 프로필 내용을 출력하지 않습니다. API 인증, 계정 권한, 실제 블로그 URL은 별도로 확인해야 합니다. Claude Code에서 `/agents`로 `keyword-scout`, `post-writer`, `quality-auditor`, `visual-producer` 네 역할이 보이는지 확인한 뒤 요청합니다.

> 내 blog-profile.yaml 설정을 확인하고, 오늘 쓸 네이버 블로그 소재 후보를 찾아줘. 키워드·제목 승인 전에는 본문을 쓰지 마.

키워드만 주면 검색형, 기사 URL·원문을 주면 홈피드형으로 진행합니다. 검색 수치와 출처가 확보되지 않으면 확인된 것처럼 작성하지 않습니다.

1. 프로필 확인 → 키워드·검색량·경쟁·중복 조사
2. **승인 1:** 키워드, 제목 후보, 구성안을 사용자가 선택
3. 초안 작성 → 별도 에이전트가 사실·표현·도메인 규칙 검증
4. 이미지 준비, 사용자 썸네일 파일 확인, 필요 시 본인 이미지 저장소에 업로드
5. `output/<날짜_주제>/post.html`, `publish.md` 생성
6. **승인 2:** HTML 검토 → 복사 → 스마트에디터 붙여넣기 → 이미지·서식 확인 → 직접 발행
7. 사용자가 실제 발행 URL을 알려준 뒤 `history.jsonl` 기록

붙여넣기 결과는 브라우저와 네이버 에디터에서 직접 확인하세요. 이미지 복사가 되지 않으면 저장된 이미지를 직접 첨부합니다. 검증을 통과했다는 것은 품질 규칙 검사 결과이며, 모든 사실의 정확성이나 노출 성과를 보장하지 않습니다.

## 선택 GUI

루트에서 CLI 설치·로그인·권한 설정을 먼저 확인한 다음 실행합니다.

```powershell
cd gui
npm ci
npm test
npm run smoke
npm start
```

GUI는 `claude -p` 응답을 표시하는 채팅 창입니다. 현재 GUI의 세션 ID를 이어 쓰며, 입력은 셸 명령에 넣지 않고 stdin으로 전달합니다. 권한 요청을 GUI에서 직접 승인하는 기능은 없습니다. 권한 거부가 표시되면 안내된 `claude --resume <세션ID>` 명령을 저장소 루트 터미널에서 실행해 확인하세요. 처음 설치하거나 도구를 연결하는 작업은 CLI에서 시작하는 것이 좋습니다. 새 대화 버튼은 현재 응답이 끝난 뒤 사용할 수 있습니다.

`npm run smoke`는 숨겨진 창에서 화면과 preload 연결만 확인하고 종료합니다. Claude 요청·API 호출·업로드를 하지 않습니다. Electron 설치 스크립트를 막는 npm 설정을 쓰는 경우 `npm install-scripts ls`로 `electron@32.3.3`을 확인하고 해당 패키지의 스크립트만 허용하세요.

## 오프라인 점검과 스크립트

```powershell
python scripts/doctor.py --offline
python -m unittest discover -s tests -v
python .claude/skills/keyword-scoring/scripts/score.py examples/candidates.json --phase 1
python .claude/skills/naver-packager/scripts/package.py output/my-draft --no-open
```

테스트와 `examples/candidates.json`은 **가상 데이터**입니다. 테스트는 임시 폴더에서만 HTML을 만들며 네트워크·브라우저 열기·실제 발행 이력을 사용하지 않습니다. 마지막 패키징 명령은 본인의 `02_draft.md`, `02_meta.json`, `images.json`이 이미 있는 폴더가 필요합니다. `--no-open`을 빼면 완성 HTML을 브라우저로 엽니다. 실제 파이프라인은 S7 검증을 통과한 초안만 패키징합니다.

## 구조와 다른 런타임

| 위치 | 역할 |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | 현재 실행 규칙, 승인 게이트, 프로필 확인 |
| `.claude/agents/*.md` | Claude Code 서브에이전트 4개 |
| `.claude/skills/` | 스킬 12개와 스크립트·참조·폰트 |
| `.agents/skills/` | 같은 12개 스킬의 동기화된 복사본 |
| `scripts/doctor.py`, `tests/` | 설치 구조와 오프라인 회귀 검사 |
| `docs/design.md` | 초기 설계 배경과 운영 목표 |
| `history.schema.md` | 실제 발행 이력 형식 |
| `gui/` | 선택 Electron 채팅 창 |

`.agents/skills`를 읽는 런타임에서도 스크립트를 사용할 수 있습니다. 전체 워크플로우에는 파일 접근과 독립 서브에이전트 호출이 필요하며, 런타임이 `.claude/agents`를 자동 인식한다고 가정하지 않습니다. `AGENTS.md`의 역할 정의 경로를 따라 별도 컨텍스트로 호출하세요. 이 기능이 없는 런타임은 개별 스크립트 사용에 한정합니다.

다른 주제로 바꾸려면 프로필과 `pet-domain-guard/references/rules.md`를 함께 수정하세요. `niche`만 바꿔도 규칙이 자동 전환되지는 않습니다. `.claude/skills` 수정 후 `.agents/skills`에도 같은 변경을 반영하고 doctor로 확인합니다.

## 라이선스

코드와 프로젝트 문서는 루트 [LICENSE](LICENSE)의 MIT 라이선스로 배포됩니다. 동봉 폰트에는 별도의 **SIL Open Font License 1.1**이 적용됩니다.

- Black Han Sans: [저작권 고지 및 OFL 전문](.claude/skills/thumbnail-compositor/assets/BlackHanSans-OFL.txt)
- Noto Sans KR 가변 폰트: [저작권 고지 및 OFL 전문](.claude/skills/thumbnail-compositor/assets/NotoSansKR-Bold-OFL.txt)
- [공식 원본 경로, 고정 커밋 및 SHA-256 검증 기록](.claude/skills/thumbnail-compositor/assets/FONT-SOURCES.md)

동일한 고지 파일은 `.agents/skills/thumbnail-compositor/assets/`에도 포함됩니다. 폰트를 재배포할 때 해당 라이선스와 저작권 고지도 함께 유지하세요.
