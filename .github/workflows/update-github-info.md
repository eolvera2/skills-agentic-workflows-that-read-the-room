---
name: update-github-info
description: Refreshes site/content/github-info.md with recent GitHub Blog and Changelog highlights, guided by Mona's editorial notes.
on:
  schedule: daily
  workflow_dispatch:
permissions:
  contents: read
  actions: read
strict: true
network:
  allowed:
    - defaults
    - github.blog
    - github.com
    - awesome-copilot.github.com
tools:
  edit:
  web-fetch:
safe-outputs:
  create-pull-request:
    title-prefix: "[update-github-info] "
    labels: [automation]
    allowed-files:
      - "site/content/github-info.md"
---

# Update GitHub Info

Keep `site/content/github-info.md` current with practical, developer-friendly GitHub guidance.

1. Read `notes/mona-notes.md` for Mona's editorial angle and preferences.
2. Web fetch `https://github.blog/latest/` for recent GitHub Blog posts.
3. Web fetch `https://github.blog/changelog/` for recent Changelog entries.
4. Web fetch `https://awesome-copilot.github.com/workflows/` for relevant Awesome Copilot workflows.
5. Using Mona's notes as guidance, update `site/content/github-info.md` with short, practical summaries of the most relevant recent stories and workflows. Mention the source (GitHub Blog, GitHub Changelog, or Awesome Copilot) for each item you add or update.
6. Only modify `site/content/github-info.md`. If nothing meaningful has changed since the last update, make no changes.
7. Open a pull request with your proposed changes so Mona can review them before they go live.
