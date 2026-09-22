# 네이버 블로그 반자동화 글쓰기 에이전트

[Claude Code](https://claude.com/claude-code)용 서브에이전트 + 스킬 묶음입니다. 키워드 발굴부터 검색량 검증, 본문 작성, 자체 검증, 이미지 준비, 붙여넣기용 패키징까지 자동으로 진행하고, **최종 발행 버튼은 항상 사람이 직접 누릅니다.** 자동 로그인·자동 발행은 하지 않습니다.

## 이게 뭘 해주나요

1. 오늘 쓸 만한 소재/키워드를 찾고, 실제 검색량과 경쟁 정도를 확인합니다
2. 예전에 이미 쓴 글과 겹치지 않는지 확인합니다
3. **[승인 게이트 1]** 후보 키워드·제목안을 보여주고 사람의 선택을 기다립니다
4. 본문을 쓰고, 다른 에이전트가 독립적으로 7개 항목을 검증합니다 (사실 창작·과장 표현·반려동물 안전 규칙 위반 등)
5. 본문에 들어갈 이미지를 준비합니다 (실사 이미지는 Canva, 썸네일은 사람이 캔바에서 직접 제작 — 자동화 폴백 스크립트도 포함)
6. 스마트에디터에 그대로 붙여넣을 수 있는 `post.html`을 만들어 브라우저로 엽니다
7. **[승인 게이트 2]** 사람이 전체선택 → 복사 → 스마트에디터 붙여넣기 → 직접 발행

기본값은 반려동물(강아지) 블로그로 맞춰져 있지만, 도메인 규칙 파일 하나만 바꾸면 다른 주제로도 쓸 수 있습니다 (아래 "다른 주제로 바꾸기" 참고).

## 시작하기 전에 필요한 것

- [Claude Code](https://claude.com/claude-code) CLI 설치 및 로그인
- Python 3.9 이상 (스킬 스크립트 실행용, 대부분 표준 라이브러리만 씁니다)
- 무료로 발급되는 API 키 2종
  - **네이버 검색광고 API**: [searchad.naver.com](https://searchad.naver.com) → 도구 → API 사용 관리. 심사 없이 즉시 발급, 광고 집행 의무 없음. 검색량 조회에 씀
  - **네이버 개발자센터 검색 API**: [developers.naver.com](https://developers.naver.com) → Application 등록 → "검색" API 선택. 경쟁 블로그/뉴스 수집에 씀
- 이미지 공개 호스팅용 GitHub 저장소 + Personal Access Token (`repo` 권한). 스마트에디터가 base64/로컬 이미지를 막기 때문에, 공개 https URL이 필요해서 씁니다
- (선택) [Canva MCP](https://www.canva.com) — 본문 이미지 자동 생성에 씀. 없어도 동작하지만 이미지 단계는 사람이 더 개입해야 합니다

## 설치

```bash
git clone https://github.com/<your-username>/naver-blog-writer-skill.git
cd naver-blog-writer-skill

# 1) API 키 채우기
cp .env.example .env
# .env 파일을 열어 NAVER_AD_*, NAVER_SEARCH_*, GITHUB_TOKEN, GITHUB_REPO 값을 채워주세요

# 2) 내 블로그 정보로 프로필 만들기
cp blog-profile.example.yaml blog-profile.yaml
# niche, tone, blog_url, seed_keywords를 내 블로그에 맞게 수정

# 3) (선택) 썸네일 폴백 스크립트를 쓸 거라면
pip install -r requirements.txt
```

이제 이 폴더에서 Claude Code를 실행하면 `.claude/agents`와 `.claude/skills`를 자동으로 인식합니다.

```bash
claude
```

## 사용법 1 — Claude Code 채팅으로

Claude Code 대화창에 이렇게 요청하면 됩니다.

> 오늘 쓸 강아지 블로그 글 하나 뽑아서 진행해줘

에이전트가 소재 발굴 → 검색량 검증 → 중복 체크를 마치면 후보 키워드와 제목안을 보여주고 멈춥니다(승인 게이트 1). 승인하면 본문 작성 → 검증 → 이미지 준비 → 패키징까지 진행한 뒤 `post.html`을 브라우저로 엽니다(승인 게이트 2). 이후 전체선택·복사해서 스마트에디터에 붙여넣고 `publish.md` 체크리스트를 확인한 뒤 직접 발행하면 됩니다.

특정 기사를 소재로 쓰고 싶다면 기사 URL이나 원문을 함께 주면 "홈피드형" 트랙으로, 키워드만 주면 "검색형" 트랙으로 자동 판단합니다.

## 사용법 2 — 클릭형 GUI로 (`gui/`)

터미널 명령이 낯설다면 `gui/` 폴더의 데스크톱 창을 쓰세요. 버튼을 누르면 그 내용을 그대로 Claude Code CLI에 전달하고 응답을 화면에 보여주는 얇은 래퍼입니다 — 실제 작업은 여전히 위 스킬/에이전트가 합니다.

```bash
cd gui
npm install     # 최초 1회, Electron 다운로드 (몇 분 걸릴 수 있음)
npm start
```

창이 뜨면 "오늘 글 시작하기"를 누르고, 승인이 필요한 순간에 "승인 / 다른 후보로 교체 / 각도 변경 / 중단" 버튼을 누르면 됩니다. 직접 메시지를 입력해도 됩니다.

> **주의**: 이 GUI는 한 번에 하나의 대화만 이어갑니다(`claude --continue` 사용). 같은 폴더에서 터미널로 별도 `claude` 세션을 동시에 열면 대화가 섞일 수 있으니, GUI를 쓸 때는 터미널 세션은 닫아두세요.

## 구조

```
CLAUDE.md / AGENTS.md   오케스트레이터(메인 에이전트) 동작 규칙
.claude/agents/          서브에이전트 4개 (keyword-scout, post-writer, quality-auditor, visual-producer)
.claude/skills/          스크립트/작법 스킬 10개 (검색량 조회, 중복 체크, 이미지 업로드, 패키징 등)
.agents/skills/          .claude/skills와 동일 — AGENTS.md 규약을 쓰는 다른 에이전트 런타임 호환용
blog-profile.example.yaml  블로그 프로필 템플릿 (복사해서 blog-profile.yaml로 사용)
docs/design.md            전체 설계 근거 문서 (왜 이렇게 나눴는지, 실패 처리 정책 등)
history.schema.md         history.jsonl 스키마 설명 (중복 체크가 참조하는 발행 이력)
gui/                       클릭형 데스크톱 GUI (Electron, Claude Code CLI 래퍼) — 선택 사항
```

각 에이전트/스킬이 어떤 단계에서 호출되는지, 실패하면 어떻게 처리하는지는 `CLAUDE.md`와 `docs/design.md`에 자세히 정리되어 있습니다.

## 다른 주제로 바꾸기

기본값은 반려동물(강아지) 블로그입니다. 안전 규칙(`pet-domain-guard` 스킬)만 도메인 전용이고, 나머지 워크플로우는 범용입니다.

1. `blog-profile.yaml`의 `niche`, `tone`, `seed_keywords`를 내 주제로 수정
2. `.claude/skills/pet-domain-guard/references/rules.md`를 내 도메인의 안전/품질 규칙으로 새로 작성 (또는 규칙이 필요 없는 주제라면 스킬을 비활성화)

## 안전장치

- **자동 발행 없음**: 항상 패키징(post.html 생성)에서 멈추고 사람의 붙여넣기·발행을 기다립니다
- **미검증 발행 없음**: 자체 검증(7개 항목)을 통과하지 못한 초안은 다음 단계로 넘어가지 않습니다
- **사실 창작 금지**: 근거 없는 수치·인용·경험을 만들지 않고, 확인 안 된 정보는 명시적으로 "확인 필요"로 표시합니다
- 자세한 실패 처리·에스컬레이션 정책은 `CLAUDE.md` §7 참고

## 라이선스

MIT License. 자유롭게 가져다 쓰고, 고치고, 배포해도 됩니다.
