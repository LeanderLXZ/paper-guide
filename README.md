# Paper Guide

<p align="left">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-7857ED" alt="Claude Code Plugin">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/LeanderLXZ/paper-guide?color=blue" alt="License: MIT"></a>
</p>

**Turn an English research paper into a complete, offline Chinese reading
guide — one HTML file you can open anywhere.** Give Claude a PDF. It reads
every page, writes a page-aligned Chinese translation and a Chinese
explanation for each page, keeps the original figures and the original PDF,
and packages everything into a single self-contained reader with an
interactive map of the paper's argument.

- 📖 **Three reading modes** — Chinese → English → 中文/英文 side by side,
  over one page-aligned source/translation pair.
- 🤖 **Page-level AI notes** — a Chinese note card beside every page (summary,
  key concepts, how to read its figures and tables), toggled in any mode.
- 🗺️ **Research roadmap** — the paper's own progression (question → method →
  evidence → robustness → limitations) as stages and numbered steps, each
  linked to its physical PDF page.
- 🖼️ **Original figures, not redraws** — figures and tables cropped from the
  PDF, rotated upright and zoomable, with Chinese explanations kept outside
  the image.
- 📦 **Fully offline** — styles, scripts, images and a byte-identical copy of
  the PDF are embedded; no network is needed to read.
- 🔍 **Auditable provenance** — the file records the PDF's SHA-256, the
  physical/printed page mapping, each page's verification status and every
  crop box.

### 中文简介

把英文论文 PDF 变成一份**可离线打开的中文导读 HTML**：逐页中文译文、恢复成自然段落的英文原文、原版 PDF 与原图、交互式「研究路线图」，以及每页一张中文 AI 解读卡。阅读模式在 中文 / 英文 / 中文/英文 对照 之间切换，AI 解读可随时开关；所有内容都内嵌在一个 HTML 文件里，断网也能读。

<p align="center">
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-the-reader">The Reader</a> ·
  <a href="#%EF%B8%8F-bundled-scripts">Bundled Scripts</a> ·
  <a href="#-installation">Installation</a> ·
  <a href="#%EF%B8%8F-scope-and-responsibility">Scope</a>
</p>

---

## 🚀 Quick Start

### 1. Install the Plugin

In Claude Code:

```
/plugin marketplace add https://github.com/LeanderLXZ/paper-guide.git
/plugin install paper-guide@paper-guide
```

### 2. Ask for a Guide

```
/paper-guide Turn ./papers/my-paper.pdf into a complete Chinese reading guide.
```

```
/paper-guide 把 ./papers/my-paper.pdf 做成完整的论文导读
```

`/paper-guide` is the short form; the full name is `/paper-guide:paper-guide`,
which you can use if another command already claims `/paper-guide`. You can
also just ask for a paper guide or 论文导读 — Claude loads the skill on its own.

### 3. What Claude Does

1. **Inspects the source** — the exact PDF and its SHA-256, page count,
   printed page labels, figures, tables and rotated pages. It looks at the
   rendered pages, not only at extracted text.
2. **Authors the content** into an editable `guide.json` — research stages,
   the English source and Chinese translation page by page, a Chinese note
   for every page, and the empirical setup (data, periods, splits, baselines)
   when it matters.
3. **Crops the original figures and builds** one self-contained HTML.
4. **Validates** structure and provenance against the PDF and, when a browser
   is available, exercises the reader in Chromium.
5. **Delivers** the HTML path, the source identity, the actual coverage and
   any unresolved pages. `guide.json` and the cropped images stay in a working
   directory, so the guide can be continued or edited later.

Long papers are written in batches and resume from saved coverage. Edits
change only what you ask for — a wording fix doesn't regenerate the paper:

```
/paper-guide Continue the guide in ./work — pages 18–40 are still missing.
/paper-guide In ./guides/Paper_Guide.html, the AI note on page 7 misstates the sample size. Fix only that.
```

---

## 📘 The Reader

| Feature | Behavior |
|---|---|
| **Reading modes** | Chinese (default) → English → 中文/英文, cycled from one control |
| **AI notes** | On by default, always in Chinese, toggled independently of the language |
| **Original PDF** | A second view in the same file; each page's button opens that exact PDF page, and switching back keeps your position |
| **Navigation** | Hierarchical contents and the roadmap share one stage model, with active-stage highlighting, a progress bar and a page jump |
| **Search** | Searches the selected language(s), shows match counts, and hides non-matching pages together with their AI notes |
| **Figures** | Click or press Enter to enlarge; fit-to-window or original size |
| **Themes & print** | Light and dark themes; prints the selected language at 100% with notes and navigation hidden |
| **Screen size** | 125% effective zoom, applied once |

Ask for different defaults when you need them — for example, open in English
(`initial_mode`), start with the notes hidden (`ai_default`), or use another
zoom level (`screen_zoom`).

---

## 🛠️ Bundled Scripts

Claude runs these for you; you can also run them yourself from a clone. With
[uv](https://docs.astral.sh/uv/) there is no install step:

```bash
S=skills/paper-guide/scripts

# Page count, SHA-256, rotations, extracted text and a PNG per page
# (evidence for authoring — not a verified transcript)
uv run --no-project --with pymupdf python $S/source_pdf.py inspect paper.pdf --out work/source --render-pages

# Crop a figure or table: bbox in PDF points on the unrotated page, top-left origin
# (placeholder coordinates — read them off the inspected page)
uv run --no-project --with pymupdf python $S/source_pdf.py crop paper.pdf --page 6 --bbox 40 80 570 700 --out work/images/figure-1.png

# Package guide.json + images + PDF into one HTML
uv run --no-project --with beautifulsoup4 --with pymupdf python $S/build_reader.py work/guide.json --out Paper_Guide.html

# Static structure/provenance check; add --browser for the Chromium pass
uv run --no-project --with beautifulsoup4 --with pymupdf python $S/validate_reader.py Paper_Guide.html --pdf paper.pdf
```

`build_reader.py` refuses pages that are unverified or incompletely translated
unless you pass `--allow-incomplete`, and a partial build stays visibly
labeled as partial. The `guide.json` format (`paper-guide/v1`) is documented
in [`references/content-model.md`](skills/paper-guide/references/content-model.md).

---

## 📦 Installation

### From GitHub (Recommended)

```
/plugin marketplace add https://github.com/LeanderLXZ/paper-guide.git
/plugin install paper-guide@paper-guide
```

### From a Local Clone

```bash
git clone https://github.com/LeanderLXZ/paper-guide.git
```

Then in Claude Code:

```
/plugin marketplace add /path/to/paper-guide
/plugin install paper-guide@paper-guide
```

### As a Personal Skill (No Plugin)

```bash
git clone https://github.com/LeanderLXZ/paper-guide.git
cp -r paper-guide/skills/paper-guide ~/.claude/skills/
```

The skill is then available as `/paper-guide` in all your projects.

### Updating

```
/plugin marketplace update paper-guide
/reload-plugins
```

### Requirements

- **Claude Code** — plugin support is needed only for the plugin install.
- **Python 3** with **PyMuPDF** and **Beautiful Soup 4**. With `uv` they are
  fetched on demand; otherwise run `pip install pymupdf beautifulsoup4`.
- *Optional:* **Playwright** with Chromium or Chrome for the browser check
  (`--browser-bin /path/to/chrome`, or `playwright install chromium`). The
  validator never downloads a browser itself.
- *Optional:* local OCR for scanned PDFs.

---

## 🗂️ Repository Layout

```
paper-guide/
├── .claude-plugin/
│   ├── plugin.json            # plugin manifest
│   └── marketplace.json       # self-hosted marketplace listing this plugin
├── skills/paper-guide/        # the skill — copy this folder for a personal install
│   ├── SKILL.md               # workflow: inspect → author → build → validate → deliver
│   ├── references/
│   │   ├── content-model.md   # guide.json schema (paper-guide/v1)
│   │   ├── authoring.md       # fidelity, figure, AI-note and roadmap rules
│   │   └── reader-contract.md # reader behavior and acceptance checks
│   ├── scripts/
│   │   ├── source_pdf.py      # inspect pages; crop figures with provenance
│   │   ├── build_reader.py    # guide.json → one self-contained HTML
│   │   └── validate_reader.py # static + optional browser checks
│   ├── assets/
│   │   ├── shell.html         # outer document: guide/PDF switch, zoom, embedded PDF
│   │   └── reader.html        # inner reader: map, contents, pages, AI notes
│   └── agents/openai.yaml     # interface metadata for OpenAI Codex (ignored by Claude Code)
├── README.md
└── LICENSE
```

---

## ⚠️ Scope and Responsibility

- The scripts **package and validate** what was written. They do not
  translate, summarize or certify scientific accuracy — check the translation
  and notes against the PDF before relying on any detail.
- The skill does not send papers to third-party OCR or translation services
  unless you allow it, and it never publishes, shares or commits anything on
  its own.
- Translations are unofficial; the generated reader says so and credits the
  original rights holders. **The reader embeds the complete original PDF**, so
  sharing a reader means sharing the paper. Process and share only papers you
  are entitled to use.

---

## 📄 License

[MIT](LICENSE) © LeanderLXZ
