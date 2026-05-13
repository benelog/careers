# CLAUDE.md

This repository is a migration of GitBook (`naver-career.gitbook.io/{en,kr}`) content to an MkDocs Material site.

- A: the source GitBook site (https://naver-career.gitbook.io/)
- B: the site this repository builds and deploys to GitHub Pages (https://benelog.github.io/careers/)

## B's URL ↔ md file mapping

The build tool is MkDocs (Material theme) and the site base is `https://benelog.github.io/careers/`.
`docs_dir: docs` in `mkdocs.yml`. All pages are exposed in directory + trailing-slash form.

| md file                                        | Published URL                                                 |
| ---------------------------------------------- | ------------------------------------------------------------- |
| `docs/index.md`                                | `https://benelog.github.io/careers/` *(→ redirects to `/kr/`)* |
| `docs/<lang>/index.md`                         | `https://benelog.github.io/careers/<lang>/`                   |
| `docs/<lang>/<path>/index.md`                  | `https://benelog.github.io/careers/<lang>/<path>/`            |
| `docs/<lang>/<path>/<slug>.md`                 | `https://benelog.github.io/careers/<lang>/<path>/<slug>/`     |

`<lang>` is either `kr` or `en`. Examples:

- `docs/kr/service/media/index.md` → `https://benelog.github.io/careers/kr/service/media/`
- `docs/kr/service/media/back-end.md` → `https://benelog.github.io/careers/kr/service/media/back-end/`
- `docs/en/teams/naver-ai-lab.md` → `https://benelog.github.io/careers/en/teams/naver-ai-lab/`

## A's URL ↔ repository mapping

GitBook site A keeps a separate repository per language. Each repository root is the root of the GitBook space for that language.

| GitBook URL prefix                          | Source repository                                               |
| ------------------------------------------- | --------------------------------------------------------------- |
| `https://naver-career.gitbook.io/kr/...`    | https://github.com/NaverTechCareers/job_desc                    |
| `https://naver-career.gitbook.io/en/...`    | https://github.com/NaverTechCareers/job_desc_en                 |

Rules for how md files inside the repository map to URLs:

| Path in repository        | URL                                                                |
| ------------------------- | ------------------------------------------------------------------ |
| `README.md` (repo root)   | `https://naver-career.gitbook.io/<lang>/`                          |
| `<path>/README.md`        | `https://naver-career.gitbook.io/<lang>/<path>`                    |
| `<path>/<slug>.md`        | `https://naver-career.gitbook.io/<lang>/<path>/<slug>`             |

`<lang>` is fixed to `kr` or `en` depending on the repository. Examples:

- `job_desc/service/media/README.md` → `https://naver-career.gitbook.io/kr/service/media`
- `job_desc/service/media/back-end.md` → `https://naver-career.gitbook.io/kr/service/media/back-end`
- `job_desc_en/teams/naver-ai-lab.md` → `https://naver-career.gitbook.io/en/teams/naver-ai-lab`

## A → B conversion notes

- `<path>/README.md` (GitBook) → `docs/<lang>/<path>/index.md` (MkDocs). `scripts/import_gitbook.py` renames this automatically.
- GitBook `{% embed url="..." %} caption {% endembed %}` is converted at import time.
  - YouTube URL → `<div class="video-embed"><iframe ...></iframe></div>` (with `<p class="video-caption">` if needed)
  - Other URLs → `[caption](url)` or `[url](url)`
