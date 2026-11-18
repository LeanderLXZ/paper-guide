# Editorial model and build inputs

`build_reader.py` reads UTF-8 JSON with `schema: "paper-guide/v1"`. Paths resolve relative to that JSON file. HTML fragment values are literal authored HTML, not filenames; load page files into these values when assembling a large model. Keep those editable inputs after delivery. The HTML's embedded manifest audits identities and coverage but does not round-trip all editorial inputs.

## Top level

| Field | Contract |
|---|---|
| `paper` | `pdf` local path, `title_zh`, `title_en`, `authors`; optional paired `citation_zh`/`citation_en` and `doi` |
| `summary` | Optional `{ "zh": "…", "en": "…" }` roadmap introduction |
| `screen_zoom` | Optional number, default `1.25`; screen only, outer shell once |
| `initial_mode` | Optional `zh`, `en` or `both`, default `zh`; use only to honor an explicit requested initial view |
| `ai_default` | Optional boolean, default `true`; static and initialized state must agree |
| `pages` | One entry per physical PDF page in source order, exactly `1..N` |
| `stages` | Nonempty, paper-specific ordered research stages; never fixed to seven |

If title/authors cannot yet be recovered, use an explicitly labeled unknown value and retain the coverage gap; do not invent bibliographic facts.

All paired labels require nonempty `zh` and `en`. Author content uses plain text for metadata, labels and AI notes; the builder escapes it. Page bodies and optional teaching diagrams accept trusted authored HTML fragments, not executable scripts. The builder embeds local raster image paths, rejects remote rendering assets/active document elements, and allows normal clickable citation links. It is a content packager, not a general-purpose sanitizer for hostile arbitrary websites.

## Page record

| Field | Meaning |
|---|---|
| `pdf_page` | Integer, physical PDF page index starting at 1; use this for every navigation target |
| `printed_label` | Optional printed label such as `iv`, `17`, `A-2`; copy what the source shows; `null` if unknown |
| `source_status` | `verified`, `uncertain`, or `image_only`; verified means the whole page has been checked against the visible source, including text, labels and notes; extraction success or verification of a selected excerpt alone is insufficient |
| `translation_status` | `complete`, `partial`, or `unavailable`; a page with a figure alone is not a complete translation if captions/notes are absent |
| `english_html` | Faithful English source in paragraphs/headings/lists; aligned math/data may use `pre.source-layout` |
| `translation_html` | Full Chinese text/structure, including source cross-references, captions, footnotes and disclosures |
| `ai` | Chinese `title`, `summary`, nonempty `blocks` array of `{title, body}`; each page needs its own explanation |
| `originals` | Optional source-image records described below |

For a page consisting entirely of original images, full original/Chinese captions in `originals` may supply the otherwise-empty page text; the English caption is also used in the source search index. Inspect the page to ensure no surrounding material is omitted.

The builder rejects unverified or incomplete records by default. `--allow-incomplete` is for a deliberately partial deliverable: visible page warnings and a partial-coverage badge remain. It is not permission to label unknown material verified. Every physical page still has an entry; no missing page disappears from the count. An OCR gap can have empty source/translation strings and a useful AI note explaining the gap and directing readers to the original PDF. Do not fabricate scientific explanation from unread text.

Use actual `<p>` paragraphs with natural wrapping. Reconstruct PDF hard line breaks and footnote boundaries against the page image. Preserve real words such as `out-of-sample`; remove discretionary wrap hyphens only when supported. Do not put an entire extracted page into `<pre>` or silently run broad dehyphenation over numbers/identifiers. Paragraph boundaries must remain whitespace in the search index.

## Original-image record

Each `originals` item contains:

- `id`: globally unique lower-case ID (`figure-1`, `table-2-cont`); `kind`: `figure` or `table`.
- `path`: local PNG/JPEG/WebP/GIF file; `label`: the original figure/table label.
- `caption_en`: complete original caption/notes; optional `caption_zh`: full Chinese explanation/translation. Long captions may also be translated in the surrounding page body.
- `orientation_verified: true`: set only after inspecting the image, not merely after running a crop command.
- `region`: `{ "bbox": [x0,y0,x1,y1], "units": "pt", "origin": "top-left", "rotation_degrees": 0 }`. Coordinates are on the unrotated physical page. Preserve `source_page_rotation` from the crop record when present. Positive quarter-turn rotations follow PyMuPDF's matrix rotation in page coordinates; inspect the result before deciding it is upright.

Place `<figure data-original="figure-1"></figure>` at the correct point in `translation_html`. Unplaced originals are appended to that page. The English view reuses these originals without translating or redrawing the scientific image. The comparison view shows them with the Chinese source card, avoiding a false new scientific rendering.

For a multi-page table, use one record per source page/crop, retaining continuation headers, all rows and footnotes. A crop must show enough context to identify its meaning. When a reader is updated, do not rewrite original image bytes merely to alter a caption.

## Research-stage record

Required paired labels: `title`, `subtitle`, `purpose`, `takeaway`, `next`. Titles are formal descriptions; subtitles explain the idea plainly. `next` closes the argument or states the transition, not a fabricated new experiment.

- `page_start`, `page_end`: physical range, within the source PDF.
- `auto_start`: optional physical page at which this stage takes over automatic contents highlighting; defaults to `page_start`. Values are nondecreasing in stage order.
- `steps`: nonempty array of `{ "title": paired_label, "body": paired_label, "page": physical_page }`. Explain concrete intermediate work and why it is performed. Derive numbering from the hierarchy.
- `links`: optional nested `{ "label": paired_label, "page": physical_page, "children": [...] }` contents tree. Defaults to the concrete steps. Keep map and contents stage titles identical; preserve section/figure/table nesting.
- `diagram_html`: optional native explanatory HTML/CSS/inline-SVG fragment. Scope IDs/styles and clearly distinguish teaching diagrams from source figures.

Several topics may legitimately point to one physical page. `auto_start` controls scroll-driven stage ownership; explicit navigation keeps the selected overlapping stage while that page is current. Do not “fix” this by inventing page numbers or duplicate page IDs.

## Minimal synthetic model

This example illustrates structure only; its content is fictional and its PDF must exist locally.

```json
{
  "schema": "paper-guide/v1",
  "paper": {
    "pdf": "example.pdf",
    "title_zh": "合成测量示例",
    "title_en": "Synthetic Measurement Example",
    "authors": "Example Research Group"
  },
  "pages": [{
    "pdf_page": 1,
    "printed_label": "i",
    "source_status": "verified",
    "translation_status": "complete",
    "english_html": "<p>A calibrated vessel stores water.</p>",
    "translation_html": "<p>校准后的容器用于储水。</p>",
    "ai": {
      "title": "先理解测量对象",
      "summary": "这一合成页面只介绍容器，不包含实验结果。",
      "blocks": [{"title": "读到哪里", "body": "校准是测量准备，不能当作有效性证据。"}]
    }
  }],
  "stages": [{
    "title": {"zh": "测量安排", "en": "Measurement design"},
    "subtitle": {"zh": "先看测量什么。", "en": "Establish what is measured."},
    "purpose": {"zh": "识别研究对象。", "en": "Identify the object of study."},
    "takeaway": {"zh": "本页没有结果。", "en": "This page reports no findings."},
    "next": {"zh": "回到原文核对。", "en": "Return to the source for verification."},
    "page_start": 1,
    "page_end": 1,
    "steps": [{
      "title": {"zh": "核对容器", "en": "Check the vessel"},
      "body": {"zh": "理解校准的作用。", "en": "Understand the role of calibration."},
      "page": 1
    }]
  }]
}
```
