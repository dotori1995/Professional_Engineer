# 정보관리기술사 단어장 (Professional_Engineer)

휴대폰에서 보기 좋은 **정보관리기술사 토픽 단어장 / 플래시카드** 사이트입니다. Jekyll + 순수 JavaScript, 백엔드 없음.

👉 사이트 주소: **https://dotori1995.github.io/Professional_Engineer/**

## 기능
- **목록**: 제목·키워드·정의 통합 검색(공백 무시), 도메인 필터(NW, DB, SE…), 학습 상태 필터(몰라요/알아요/미학습)
- **토픽 상세**: 정의, 핵심 키워드, 두음(원문에 있을 때만), 특징·구성·비교(원문 발췌), 원문 쪽수
- **플래시카드**: 앞면 = 토픽명, 탭하면 뒷면 = 정의·키워드·두음 / 이전·다음 버튼 + 좌우 스와이프 / 🔀 섞기 /
  ✅ 알아요·🤔 몰라요 기록(브라우저 localStorage) / **몰라요만 복습** / 진행률
- 다크 모드(시스템 설정 따름 + 🌓 버튼), 큰 터치 영역, 한글 시스템 폰트
- **PWA**: 휴대폰에서 "홈 화면에 추가" 하면 앱처럼 실행, 한 번 열면 오프라인에서도 동작
  - iPhone(Safari): 공유 버튼 → 홈 화면에 추가
  - Android(Chrome): ⋮ 메뉴 → 홈 화면에 추가 / 앱 설치

> 학습 기록(알아요/몰라요)은 각 기기 브라우저에만 저장됩니다(서버 없음).

## GitHub Pages 배포
1. 이 폴더 내용을 `dotori1995/Professional_Engineer` 저장소의 `main` 브랜치에 push
2. 저장소 **Settings → Pages → Build and deployment → Source: `GitHub Actions`** 선택
3. `main`에 push할 때마다 `.github/workflows/pages.yml`이 Jekyll로 빌드해서 배포합니다 (Actions 탭에서 진행 확인)
4. 배포 후 주소: https://dotori1995.github.io/Professional_Engineer/

`_config.yml`의 `baseurl: "/Professional_Engineer"`는 저장소 이름과 같아야 합니다.

## 로컬 미리보기
```bash
bundle install
bundle exec jekyll serve      # http://localhost:4000/Professional_Engineer/
```

## 데이터 구조
```
_data/nw.json             # 네트워크(NW) 토픽 127개 (파서 출력물)
_data/overrides/nw.json   # 수동 보정(정의 다듬기, 비어 있던 키워드 본문 발췌, 원문 오류 메모)
_config.yml → domains     # 사이트에 노출할 도메인 목록
data.json                 # 빌드 시 모든 도메인을 합쳐 /data.json 으로 출력 (JS가 읽음)
```
토픽 항목 필드: `id`, `title`, `subtitle`, `domain`, `category`, `definition`(정의), `keywords`(핵심 키워드),
`dueum`(두음 — **원문 '암기법' 칸에 값이 있을 때만**), `sections`(특징·구성·비교 원문 발췌), `pages`(원문 쪽),
`keywords_note`/`note`(보정 메모), `reviewed`(수동 보정 여부)

## 새 도메인 PDF 추가하기 (DB, SE, AI, 보안 …)
PDF는 같은 양식(앞쪽 `목록` 목차 `DB_001_제목 ····· 1`, 토픽마다 `토픽 이름/분류/키워드(암기)/암기법` 헤더 표)이라고 가정합니다.

```bash
# 1) 파싱 (poppler-utils의 pdftotext 필요: apt install poppler-utils / brew install poppler)
python3 scripts/parse_topics.py ~/Downloads/DB_topics.pdf --domain DB --out _data/db.json
#    → "TOC n개, 헤더 매칭 n개, 출력 n개" 와 WARN(키워드 칸 비어 있음, 정의 추출 실패 등) 목록 출력

# 2) (선택) 보정: _data/overrides/db.json 에 {"DB_001": {"definition": "...", "keywords": [...]}} 형태로 작성 후 1) 재실행
#    값을 null로 두면 해당 필드 삭제 (예: "dueum": null)

# 3) _config.yml 의 domains 에 추가
#   - key: db
#     code: DB
#     name: 데이터베이스
```
그다음 commit/push 하면 자동 배포됩니다. 파서는 Python 3 표준 라이브러리만 사용합니다.

### 파서 동작 요약 (`scripts/parse_topics.py`)
1. `pdftotext -layout`으로 텍스트 추출(또는 이미 추출한 .txt 입력 가능)
2. 목차에서 `코드_제목 ··· 쪽` 추출 → 각 토픽 시작 페이지 근처의 `토픽 이름` 헤더와 순서대로 매칭(한 페이지에 여러 토픽이 있어도 분리)
3. 헤더 표에서 분류·키워드·암기법(두음) 읽기
4. 본문 첫 섹션(I.)의 첫 불릿을 정의로, 각 섹션(II., III. …)의 불릿 일부를 특징·구성·비교로 발췌(표 왼쪽 라벨 제거, 줄바꿈 이어붙이기)
5. `_data/overrides/<domain>.json` 적용

본문이 이미지로만 된 페이지는 텍스트가 없어서 자동 추출이 안 됩니다 → WARN을 보고 overrides로 보정하세요.
