---
name: paper-guide
description: Create or refine a complete offline Chinese HTML guide to an English research paper, with flowing English source text, original PDF/figures, an interactive research roadmap and page-level AI notes. Triggers include paper guide, 论文导读, 论文精读 HTML and /paper-guide; ordinary paper questions or experiment-report generation alone do not need this workflow.
---

> **Language**: honor explicit user instructions and the project's language config when present. Skill/code/log prose uses the project's `content_language`; conversation uses `conversation_language`. For the reader, default to Chinese translation and Chinese AI notes with English source text. Its comparison mode is labeled **中文/英文**, including in the English UI. Reader translation, Chinese AI notes and the required dual-language UI are product-language exceptions to disk-prose rules. Code identifiers remain English. A project-specific config file is optional; this skill works outside holo projects.

# /paper-guide — Offline paper reading guide

Turn a supplied English paper into a usable, source-grounded reading document. Follow the proven reader design in this bundle, adapting the argument, page count and content to the actual paper. Keep the original PDF, full translation and AI explanations distinct. The scripts package and validate authored content; they do not translate, summarize or certify scientific accuracy.

## Inputs and scope

Resolve the source PDF, output HTML path and whether the task is **new**, **continue**, or **edit**. Reuse attachments, local references and existing working files before asking. If only a paper PDF is supplied, default to a complete Chinese guide with the defaults below; infer a sensible output location from the workspace.

- **New / continue:** preserve editable `guide.json` and local source assets in a work directory. Write page records in batches for a long paper; resume from saved coverage, not memory. A single offline HTML is the reader deliverable.
- **Edit:** inspect the existing reader and the exact requested change first. Prefer its existing generator/input model when available; otherwise patch the relevant document or embedded `srcdoc` carefully. Preserve unrelated content, PDF/image bytes, current settings and output naming. A wording fix does not require regenerating a whole paper.
- Local experiment comparisons are optional, added only when requested. This skill does not launch experiments or invent measurements. For comparisons, show original charts in closed-by-default expandable panels with source pages and explicit differences in data, periods, windows, weighting and metrics.

Use concise progress updates for source inspection, authoring, construction and verification. Follow the host project's logging conventions where applicable. Do not introduce branch/commit/approval workflows merely because this skill is used.

## Reader defaults

| Concern | Default and invariant |
|---|---|
| Reading modes | Chinese → English → **中文/英文**; default Chinese; one shared source/translation pair per page |
| AI notes | On by default, Chinese in every mode, independent toggle before the language control |
| Document views | Reading guide and original PDF in the same HTML; preserve state and scroll when switching |
| Screen size | Effective 125% once; do not multiply outer-shell and iframe zoom; print at 100% |
| Navigation | Fixed-width left hierarchical contents, active stage, paper-specific interactive roadmap and reading progress |
| English prose | Semantic paragraphs with natural wrapping; aligned tables/formulas alone may use scrollable `pre.source-layout` |
| Images | Original scientific images, upright and complete, with source captions, Chinese explanation and keyboard-accessible zoom |
| Scrolling | AI cards are siblings of paper cards; normal document scrolling, no trapped wheel events or clipped explanation endings |
| Offline | Inline styles/scripts, embedded image assets and byte-identical original PDF; no network needed to read |

User choices override defaults. For an existing reader, preserve an explicit existing preference unless asked to change it. Read [references/reader-contract.md](references/reader-contract.md) before building or changing layout/interactions.

## Step 0: Inspect the authoritative source

Identify the exact PDF/version and SHA-256. Read visual pages as well as extracted text; extraction is not ground truth. Derive actual physical page count, headings, appendix/reference coverage, figures/tables, rotations, and printed page labels. Do not assume printed labels follow a constant offset.

The helper records extraction status without claiming transcription verification:

```bash
uv run --no-project --with pymupdf python "$skill_dir/scripts/source_pdf.py" inspect paper.pdf --out work/source --render-pages
```

`skill_dir` means the directory containing this SKILL.md (in Claude Code: `${CLAUDE_SKILL_DIR}`); resolve it in the current installation. With an existing Python environment, invoke `python3` directly instead of `uv`. Dependencies are Beautiful Soup (`beautifulsoup4`) and PyMuPDF (`pymupdf`); Playwright is needed only for browser checks. Use locally available equivalents when appropriate.

If the PDF is scanned or ambiguous, use available local OCR and inspect its result. Do not upload a paper to a third-party OCR/translation service unless authorized. Missing OCR/source access is a specific coverage gap: do useful available work, mark it clearly, and request only the missing input needed. An intentionally partial reader must be visibly labeled partial.

## Step 1: Build the content and research route

Read [references/content-model.md](references/content-model.md) for the exact input model, page status and source-image coordinates. Read [references/authoring.md](references/authoring.md) for editorial checks. Author from the paper, not from the previous example's claims or layout numbers.

1. Map the paper's argumentative progression: question → method/design → evidence → robustness/interpretation → limitations, adapting to the actual discipline. Use formal stage titles, plain-language subtitles and concrete numbered substeps with physical page links. Each stage explains its purpose, takeaway and connection to the next. Keep its hierarchy and titles aligned with the contents; preserve overlapping page ownership explicitly.
2. Supply complete page-aligned Chinese translation and flowing English HTML, including captions, formulas, footnotes, acknowledgments, appendices and references. Preserve names/citation identity. Restore paragraphs and repair PDF wrap artifacts after checking the visible source; do not strip real compound-word hyphens or flatten tables into prose.
3. Write independent Chinese AI notes for every page: whole-page summary, concepts, relevant figure/table reading guidance and a small marked illustrative example when helpful. Explain rather than paraphrase jargon. Notes should be shorter than their source page in normal use; edit for clarity without height caps, inner scrolling or hidden text. Reference pages need useful context, not fabricated scientific conclusions.
4. Surface empirical setup when it matters: data sources, population/sample units and counts, periods, Train/Validation/Test boundaries and actual split definitions, evaluation/aggregation and baselines. Use prominent cards/icons and a compact settings table near the beginning when the data setup is central, then give details afterward. State input size or selected-versus-observed coverage when supported and relevant; do not invent unavailable counts or train/test ratios. Mark unknowns. Distinguish original claims, AI interpretation, inference and any separately sourced local results.

Add native HTML/CSS/inline-SVG teaching diagrams selectively for difficult mechanisms; label them explanatory and keep invented numbers explicit. Do not replace original scientific charts with schematic approximations.

## Step 2: Preserve original figures and construct the reader

Crop/rasterize original figures and tables, retaining all panels, labels, legends, units, significance notes and continuation rows. Inspect sideways tables and rotate the complete scientific content upright. English text inside originals stays intact; Chinese captions/explanations sit outside the image. Record physical PDF page, printed label, crop box, rotation and image identity.

```bash
uv run --no-project --with pymupdf python "$skill_dir/scripts/source_pdf.py" crop paper.pdf --page 6 --bbox 40 80 570 700 --rotate 0 --out work/images/figure-1.png
uv run --no-project --with beautifulsoup4 --with pymupdf python "$skill_dir/scripts/build_reader.py" work/guide.json --out Paper_Guide.html
```

The example coordinates are placeholders for the inspected page, not recommended crops. `crop` records coordinates on the **unrotated** physical page in PDF points, top-left origin; its metadata marks orientation unverified until a human/agent has actually viewed the image. Build inputs require that confirmation. If completing only an authorized subset, use `--allow-incomplete`; the builder then exposes unverified/partial pages instead of claiming full coverage.

Use the bundled assets directly for a new reader. If adapting them, keep data-driven counts and labels. The two templates deliberately separate the outer PDF switcher/zoom from the inner reading document. Preserve the single visible toolbar and lazy original-PDF initialization.

## Step 3: Validate content and behavior

```bash
uv run --no-project --with beautifulsoup4 --with pymupdf python "$skill_dir/scripts/validate_reader.py" Paper_Guide.html --pdf paper.pdf --report work/static-check.json
uv run --no-project --with beautifulsoup4 --with pymupdf --with playwright python "$skill_dir/scripts/validate_reader.py" Paper_Guide.html --pdf paper.pdf --browser --screenshots work/previews --report work/browser-check.json
```

Use `--browser-bin /path/to/chromium` for an available browser, or Playwright's installed Chromium. The validator does not download browsers. For a reader without this bundle's manifest, `--existing` checks its compatible structure and original PDF without claiming model coverage. Adapt checks explicitly for a different existing shell; do not rewrite it solely to satisfy this helper.

Run the relevant acceptance checks in [references/reader-contract.md](references/reader-contract.md): all reading/AI combinations, narrow/wide screens, preserved position/sidebar width, real wheel scrolling, search and empty recovery, nested contents/map keyboard navigation, image modal, PDF page targeting, themes and language-specific printing. Inspect representative prose, figure, table, appendix and reference pages, not just the cover. Audit source/translation/AI meaning against the PDF separately; automated checks cannot prove factual fidelity or complete translation.

For edits, compare before/after PDF and original-image bytes and unaffected content groups. Report any check that could not run as **not run**, with its concrete limitation; do not describe static inspection as a browser pass. Fix layout/content problems within the requested scope and rerun the checks they affect.

## Step 4: Deliver and retain reproducibility

Provide the HTML path, source identity and actual coverage, summarize relevant verification and disclose unresolved pages. Retain the editable model/source assets and QA report in the working area; the standalone HTML embeds its PDF and provenance manifest for reading and audit. The manifest is not a substitute for saved editorial inputs. Do not auto-publish, send the paper to others, commit, or change unrelated project experiments.
