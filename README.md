# NAVER Careers

GitHub Pages 기반 NAVER Tech Careers 사이트의 소스.

- 공개 URL: https://benelog.github.io/careers/
- 영문 입구: https://benelog.github.io/careers/en/
- 국문 입구: https://benelog.github.io/careers/kr/

원본 GitBook (`naver-career.gitbook.io/{en,kr}`) 의 콘텐츠를 일회성으로 가져와 직접 관리한다. 이후의 모든 갱신은 이 저장소에서 PR 로.

## 로컬 미리보기

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
# http://127.0.0.1:8000/careers/
```

## 빌드 검증

```bash
mkdocs build --strict
```

깨진 내부 링크가 있으면 빌드가 실패한다. CI 와 같은 조건이다.

## 콘텐츠 추가/수정

- 영문: `docs/en/` 아래의 마크다운 편집
- 국문: `docs/kr/` 아래의 마크다운 편집
- 이미지: `docs/assets/{en,kr}/` 에 두고 `/careers/assets/{en,kr}/파일명` 으로 참조
- 사이드바 순서: `mkdocs.yml` 의 `nav:` 직접 수정 (`# === NAV START ===` ~ `# === NAV END ===` 사이)

## 배포

`main` 푸시 → GitHub Actions 가 `mkdocs build --strict` 후 GitHub Pages 로 자동 배포.

GitHub repo 설정에서 한 번만 해두면 됨:

- **Settings → Pages → Source: GitHub Actions**

## 임포트 스크립트 (재실행)

원본 GitBook repo 의 내용을 다시 가져오고 싶을 때:

```bash
git clone https://github.com/NaverTechCareers/job_desc      tmp_sources/job_desc
git clone https://github.com/NaverTechCareers/job_desc_en   tmp_sources/job_desc_en
python3 scripts/import_gitbook.py tmp_sources/job_desc tmp_sources/job_desc_en
```

- `docs/en/`, `docs/kr/`, `docs/assets/` 가 갱신되고
- `mkdocs.yml` 의 nav 블록(`# === NAV START ===`~`# === NAV END ===`)이 다시 생성된다
