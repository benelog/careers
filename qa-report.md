# QA Report: GitBook → MkDocs

Source A: https://naver-career.gitbook.io/kr  
Site B:   https://benelog.github.io/careers/kr  
Script:   `scripts/qa_compare.py`

---

## 요약

| 항목 | 결과 | 심각도 |
|------|------|--------|
| 페이지 구조 | 214/214 완전 일치 | ✅ 통과 |
| 깨진 이미지 자산 | **53개** | 🔴 수정 필요 |
| 고아 페이지 (nav 미등록) | 1개 (`undefined/undefined.md`) | 🟡 확인 필요 |
| broken-reference 링크 | 1개 (`service/clova/`) | 🟡 수정 필요 |
| 라이브 B 깨진 이미지 | 0개 (샘플 10 페이지) | ✅ 통과 |
| 이미지 수 delta (-2) | GitBook 테마 이미지 차이 (정상) | ℹ️ 설계 차이 |
| 이미지 width/height 속성 | A는 HTML 인라인, B는 CSS 의존 | ℹ️ 설계 차이 |

---

## Tier 1 — 페이지 구조 완전성

| | Count |
|---|---|
| GitBook pages (A) | 214 |
| MkDocs pages (B)  | 214 |
| Missing in B      | **0** |
| Extra in B        | 0 |

✅ 모든 페이지가 완벽하게 대응됩니다. (`SUMMARY.md`는 GitBook 자동생성 TOC이므로 제외)

---

## Tier 2 — 이미지 자산 완전성

| | Count |
|---|---|
| Assets in docs/assets/kr/ | 430 |
| 깨진 이미지 참조 (로컬)    | **53** |

### Root cause 분류

| 분류 | 건수 | 원인 |
|------|------|------|
| 한국어 파일명 → 하이픈 치환 | 23 | 원본 파일명 내 한국어를 `-_-` 등으로 치환. 실제 자산이 없음 |
| 기타 한국어/특수문자 | 18 | 같은 유형의 변형 패턴 |
| 이중 인코딩 (`%2520`) | 6 | `%20`(공백)이 한 번 더 인코딩됨 — 실제 파일은 다른 이름으로 존재 가능 |
| 백슬래시 인코딩 (`%5C`) | 6 | 원본 파일명의 `\`가 `%5C`로 인코딩됨 — 실제 파일은 `_`로 존재 가능 |

### 깨진 이미지 참조 목록 (전체)

| File | Missing asset |
|------|--------------|
| `business/forest-cic.md` | `1-1.-_-.png` |
| `business/forest-cic.md` | `1-2.-_-.png` |
| `business/forest-cic.md` | `1-3.-_-.png` |
| `business/forest-cic.md` | `1-4.-_foryou.png` |
| `business/forest-cic.md` | `1-5.-_-.png` |
| `business/forest-cic.md` | `1-6.-_-.png` |
| `business/forest-cic.md` | `2-1.-_-.png` |
| `business/forest-cic.md` | `2-2.-_-.png` |
| `business/forest-cic.md` | `2-3.-_-_-.png` |
| `business/forest-cic.md` | `3-1.-.png` |
| `business/forest-cic.md` | `3-2.-.png` |
| `business/forest-cic.md` | `3-3.-.png` |
| `business/whale.md` | `_1-.jpeg` |
| `business/whale.md` | `_2-.jpeg` |
| `business/whale.md` | `_0-.jpeg` |
| `business/whale.md` | `_3-.jpeg` |
| `business/whale.md` | `_4-.jpeg` |
| `business/whale.md` | `_5-.jpeg` |
| `business/whale.md` | `_-.png` |
| `business/whale.md` | `_-%2520%25281%2529.png` (이중인코딩) |
| `business/whale.md` | `_-%2520%25282%2529.png` (이중인코딩) |
| `business/whale.md` | `_hwp-.png` |
| `service/maps/index.md` | `Maps%5C_20212Deview%5C_02.png` (백슬래시 인코딩) |
| `service/media/index.md` | `%25EC%2584%259C...` (이중인코딩된 한국어) |
| `service/naver-etech/homebuilder/index.md` | `1.gif` |
| `service/naver-etech/homebuilder/index.md` | `2%2520%25281%2529.gif` (이중인코딩) |
| `service/naver-etech/index.md` | `2021-08-19-19.19.21.png` |
| `service/naver-etech/index.md` | `2021-08-19-22.57.04.png` |
| `service/naver-etech/index.md` | `2021-08-19-18.53.54.png` |
| `service/naver-etech/index.md` | `2021-08-19-17.45.37.png` |
| `service/naver-etech/index.md` | `2021-08-19-17.51.11.png` |
| `service/naver-etech/index.md` | `2021-08-19-18.05.07.png` |
| `service/naver-etech/index.md` | `s_1%2520%25281%2529.png` (이중인코딩) |
| `service/naver-etech/index.md` | `s_2%2520%25281%2529.png` (이중인코딩) |
| `service/naver-etech/index.md` | `1%2520%25281%2529.gif` (이중인코딩) |
| `service/naver-etech/smarteditor/index.md` | `s_1.png` |
| `service/search/undefined-1.md` | `%EC%8A%A4...%5C(...%5C).jpg` (백슬래시+한국어) |
| `service/tech/naver-app/index.md` | `napp%5C_main.png` (백슬래시 인코딩) |
| `service/tech/pwe/index.md` | `calendar%5C_main.png` (백슬래시 인코딩) |
| `service/tech/pwe/index.md` | `memo%5C_main.png` (백슬래시 인코딩) |
| `service/tech/pwe/index.md` | `mail%5C_main.png` (백슬래시 인코딩) |
| `undefined/undefined.md` | `1-1.-_-.png` _(고아 페이지 포함 12건)_ |

### 고아 페이지

`docs/kr/undefined/undefined.md` — 쇼핑 팀 콘텐츠를 담고 있으나 `mkdocs.yml` nav에 미등록. 사용자가 접근 불가.

---

## Tier 3 — 라이브 B 깨진 링크·이미지 (샘플 10 페이지)

| | Count |
|---|---|
| 깨진 이미지 (HTTP 비 200) | **0** |
| 깨진 링크               | **1** |

### 깨진 링크

| Page | href | HTTP |
|------|------|------|
| https://benelog.github.io/careers/kr/service/clova/ | `broken-reference` | 404 |

`broken-reference`는 GitBook이 끊긴 내부 링크에 삽입하는 플레이스홀더입니다.  
`docs/kr/service/clova/index.md` 내 `[AI Assistant Platform 개발](broken-reference)` 링크를 수정 필요.

---

## Tier 4 & 5 — 콘텐츠 지표 & 이미지 크기 (샘플 10 페이지)

### 이미지 수 delta 해석

모든 페이지에서 **A가 B보다 일관되게 2개 더 많음** → GitBook 테마가 매 페이지에 2개의 UI 이미지(로고/헤더 등)를 삽입하기 때문. 콘텐츠 이미지 손실이 아님. _(확인: `vision.md`는 원본 소스에도 이미지 없음, B도 콘텐츠 이미지 0개)_

### 이미지 크기 속성 해석

| | A (GitBook) | B (MkDocs) |
|--|-------------|-----------|
| 256×256 아이콘 | `width="256" height="256" style="aspect-ratio:1"` 인라인 | 속성 없음, CSS로 제어 |
| 콘텐츠 이미지 | `style="max-width:100%;height:auto"` 인라인 | 속성 없음, MkDocs Material CSS로 제어 |

B가 HTML 인라인 치수 속성을 갖지 않는 것은 **의도된 설계 차이**입니다. MkDocs Material의 기본 CSS가 반응형 이미지 처리를 담당합니다.

### 페이지별 상세

| Page | A 이미지 | B 이미지 | 이미지 delta | 헤딩 delta |
|------|---------|---------|------------|-----------|
| `service/search/ai-and-data-platform` | 7 | 4 | **-3** | 0 |
| `service/clova` | 7 | 5 | -2 | 0 |
| `service/search/vision` | 4 | 2 | -2 | 0 |
| `service/search/nlp` | 4 | 2 | -2 | 0 |
| `service/media` | 11 | 9 | -2 | 0 |
| `service/band` | 4 | 2 | -2 | 0 |
| `service/search/nlp/text-analysis` | 9 | 7 | -2 | 0 |
| `service/search/websearch` | 4 | 2 | -2 | 0 |
| `service/shopping/smartstore` | 4 | 2 | -2 | 0 |
| `service/whale/browser` | 4 | 2 | -2 | 0 |

> `service/search/ai-and-data-platform`의 -3은 GitBook 테마 2개 + 콘텐츠 이미지 1개 추가 차이.  
> 헤딩 수는 모든 페이지에서 완전히 일치 ✅

---

## 권장 조치

| 우선순위 | 항목 | 조치 |
|---------|------|------|
| 🔴 High | 53개 깨진 이미지 자산 | import 스크립트에서 한국어 파일명 처리, 이중인코딩, 백슬래시 처리 개선 후 재임포트 |
| 🟡 Med | `service/clova/index.md` broken-reference | 원본 GitBook에서 링크 대상 확인 후 올바른 상대경로로 수정 |
| 🟡 Med | `undefined/undefined.md` 고아 페이지 | nav 등록 또는 파일 삭제 |
