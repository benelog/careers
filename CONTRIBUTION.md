# 기여 가이드

이 사이트는 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)로 빌드되며, `main` 브랜치 푸시 시 GitHub Actions가 자동으로 [https://naver-career.github.io/](https://naver-career.github.io/) 에 배포합니다.

---

## 로컬 미리보기

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
# http://127.0.0.1:8000/
```

파일을 저장하면 브라우저가 자동으로 새로고침됩니다.

---

## 파일 구조와 URL 대응

```
docs/
├── assets/
│   ├── en/          # 영문 페이지용 이미지
│   ├── kr/          # 국문 페이지용 이미지
│   └── logo.png
├── en/              # 영문 콘텐츠
│   ├── index.md
│   ├── positions/
│   ├── teams/
│   └── publications/
└── kr/              # 국문 콘텐츠
    ├── index.md
    ├── service/
    ├── tech/
    └── ...
```

| 파일 경로 | 배포 URL |
|---|---|
| `docs/kr/index.md` | `https://naver-career.github.io/kr/` |
| `docs/kr/service/media/index.md` | `https://naver-career.github.io/kr/service/media/` |
| `docs/kr/service/media/back-end.md` | `https://naver-career.github.io/kr/service/media/back-end/` |
| `docs/en/teams/naver-ai-lab.md` | `https://naver-career.github.io/en/teams/naver-ai-lab/` |

- 폴더 진입점은 `index.md`
- 루트(`/`)는 `/kr/`로 자동 리다이렉트

---

## 콘텐츠 수정

`docs/kr/` 또는 `docs/en/` 아래의 마크다운 파일을 직접 편집합니다.

파일 상단의 frontmatter는 그대로 두세요.

```markdown
---
description: 페이지 설명
---

# 제목
...
```

---

## 새 페이지 추가

**1단계: 파일 생성**

```
docs/kr/service/<서비스명>/<역할>.md
```

**2단계: `mkdocs.yml`의 `nav` 블록에 등록**

`# === NAV START ===`와 `# === NAV END ===` 사이에 추가합니다.

```yaml
nav:
  - 한국어:
    - 서비스 소개:
      - 새 서비스:
        - kr/service/new-service/index.md
        - Back-end: kr/service/new-service/back-end.md  # ← 추가
```

`nav`에 등록하지 않으면 사이드바에 나타나지 않고, `mkdocs build --strict`에서 경고가 발생합니다.

---

## 이미지 추가

이미지 파일은 언어별 assets 폴더에 저장합니다.

```
docs/assets/kr/이미지파일.png
docs/assets/en/이미지파일.png
```

마크다운에서 참조할 때는 **절대 경로** `/assets/...` 형식을 사용합니다.

```markdown
![설명](/assets/kr/이미지파일.png)
```

HTML `<img>` 태그도 동일하게:

```html
<img src="/assets/kr/이미지파일.png" alt="설명">
```

> `/careers/assets/...` 형식은 사용하지 마세요. 이 사이트는 루트(`/`)에서 서빙됩니다.

---

## 페이지 리다이렉트 추가

URL이 바뀐 경우 `mkdocs.yml`의 `redirect_maps`에 등록합니다.

```yaml
plugins:
  - redirects:
      redirect_maps:
        'index.md': 'kr/index.md'                    # 기존 예시
        'kr/old/path.md': 'kr/new/path/index.md'     # 추가 예시
```

---

## 빌드 검증

PR을 올리기 전에 로컬에서 빌드를 확인합니다.

```bash
mkdocs build --strict
```

깨진 내부 링크나 `nav` 미등록 파일이 있으면 빌드가 실패합니다. CI와 동일한 조건입니다.

---

## 배포

`main` 브랜치에 푸시하면 GitHub Actions(`.github/workflows/deploy.yml`)가 자동으로 빌드하고 GitHub Pages에 배포합니다. 별도 작업 불필요.

배포 상태 확인:
```bash
gh run list --repo naver-career/naver-career.github.io --limit 5
```

---

