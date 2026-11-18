# Reader behavior and acceptance

The bundled two-template design comes from a working offline reader. `shell.html` owns the guide/original-PDF switch and effective screen zoom. `reader.html` owns the paper map, contents, page cards, source/translation modes and Chinese AI notes. A new paper's content arrives through JSON; no source title, author, DOI, fixed printed-page offset or topic-specific page/stage count belongs in the templates.

## Language and state

- Default to Chinese. Cycle Chinese → English → 中文/英文; the comparison display name remains exactly **中文/英文**, including English UI. Internal state names may stay `zh`, `en`, `both`.
- Keep source and translation page-aligned, with one shared language state. Per-page “show other language” controls enter comparison and return to the prior single language. Visible labels, expanded/pressed state and actual layout must agree.
- AI is a separate toggle before the mode control, enabled by default and available with every mode. AI text remains Chinese and has a language annotation even when navigation is English.
- Switch surrounding UI/map/contents to English for the English reading context; do not leave the toolbar and roadmap in an inconsistent language. Preserve the current anchor/reading position and AI state during a mode change.
- Original PDF is a separate document view, not a fourth language mode. Load its byte-identical Blob lazily. Physical page buttons open the corresponding original page; returning preserves reading mode, AI state and position. Keep inactive iframes laid out but hidden/inert so switching does not destroy viewport/scroll state.
- One visible navigation toolbar at a time. Tabs/controls need clear labels, keyboard behavior and consistent ARIA state.

## Map, contents and reading tools

Derive both map and contents from the same research-stage model. Use paper-specific stage titles, approachable subtitles, concrete substeps, purpose, takeaway and next-step explanation. Contents stay hierarchical, with physical-page links for sections and supporting figures/tables. Keep sidebar width/position stable within a viewport when AI or language controls change.

Automatically open the active contents branch and collapse the previously auto-opened branch; maintain active-link feedback and a top reading-progress indicator. Explicit links on overlapping source pages retain their selected stage. Map tabs support click plus Left/Right/Home/End with a single selected/focusable tab and one visible panel.

Search the chosen language(s), normalize paragraph boundaries, show counts and an understandable empty state, and recover completely when cleared. Filtering applies to a whole page row, including its AI card. Page-jump inputs clamp to actual physical page count; maps, contents, page labels and PDF buttons share that source mapping. Local-file `srcdoc` history updates must resolve against the actual iframe URL rather than an invented outer URL.

## Typography, sizing and scroll

English ordinary prose uses semantic paragraphs and `white-space: normal`, with readable line length and spacing. A full-page PDF extract in `pre-wrap` is not an acceptable reader. Equations/table columns alone may retain aligned preformatted blocks, with local horizontal scrolling. Preserve true lexical hyphens, numbers and punctuation when repairing extraction artifacts.

Default effective screen zoom is 1.25 exactly once. In the provided design, outer root zoom plus a percentage-height flex shell preserves the full viewport; the inner reader remains at zoom 1. Test actual frame bounds and text scaling, not just a CSS literal. Viewport-sized dialogs/sidebars need dimensions consistent with whichever level is zoomed. Print must not inherit screen scaling.

AI cards are sibling cards aligned beside source cards at wide widths and stacked at narrow widths. Their content participates in normal document scrolling; no max-height/inner-scroll/wheel trap. Prefer concise authored notes but never clip their ending. A long note must remain fully accessible even if source/AI heights differ. Do not change the sidebar width just to accommodate an added AI column.

Wide source tables scroll inside their own container. Normal page content must not force horizontal scrolling of the whole document. Mobile navigation opens/closes accessibly and returns focus appropriately. Themes preserve readable contrast, and scientific image pixels stay unchanged on white rather than being inverted.

## Original-image viewer

Original scientific images retain original English labels/values and complete captions; Chinese explanations sit outside. Clicking or Enter/Space opens a keyboard-accessible modal with readable alt/label text. Offer fit-to-window and original-size views, Escape and explicit close, background-click dismissal, and focus restoration to the opener. Large diagrams may scroll inside the dedicated image viewer; this exception does not apply to AI prose.

## Offline and print

Embed source PDF bytes, source/teaching image resources and all required styles/scripts. No runtime network call, remote font, CDN script or external image may be required. Normal citation links can remain clickable. Escape text and inline JSON correctly, especially `</script>`, quotes and markup inside source text. User-authored fragments are content, not permission to execute fetched scripts.

Record source-PDF identity, physical/printed page mapping, source/translation status, original-image/crop identity and builder/template identity. Do not claim the manifest alone certifies scientific fidelity or can reconstruct all authoring inputs.

Print at 100%, with navigation, AI cards and viewer chrome hidden. Print the language selected by the reader. Preserve legible figures, table notes, equations and page references. If a different deliverable explicitly needs original page geometry, use appropriate portrait/landscape print layouts; do not force every normal reading card to mimic PDF page coordinates.

## Acceptance matrix

Run checks proportionate to the change; a new shell needs the complete matrix. The bundled validator covers many but not every editorial/visual condition below. Mark unexecuted checks as not run.

| Area | Required observable check |
|---|---|
| Source | Embedded PDF equals supplied PDF; counts/mapping and original image hashes match; partial pages remain labeled |
| Content | Review source vs translation/AI meaning, formulas, table values and at least prose/figure/table/appendix/reference pages |
| Modes | All 3 language modes × AI on/off, independent controls, correct 中文/英文 label and matching ARIA state |
| Responsive | Representative wide/medium/narrow widths, typically 1920/1280/768/390 and 320 if applicable; no global overflow |
| Position | Mode/AI changes and PDF return preserve the visible anchor; sidebar bounds remain stable within each viewport |
| Navigation | Nested contents targets, active branch collapse, overlapping-page intent, keyboard map tabs, physical-page jump and PDF page targeting |
| Scroll | Actual mouse wheel over AI heading, summary and last detail scrolls the document in both directions; no inner trap |
| Search | Positive/no-result queries, counts, selected-language scope and clearing recovery including AI rows |
| Images | Upright complete original, all panels/continuations, modal fit/original, keyboard close/backdrop/focus restore |
| Theme | UI/content legible, original chart image pixels not recolored |
| Offline | Open local file with network unavailable; no external render requests and no JavaScript errors |
| Print | Screen 125%, print 100%; chosen-language source visible, AI/navigation hidden, tables/formulas legible |
| Update | Original bytes and unaffected content/settings preserved; no experiment runs or unrelated artifact changes |

Playwright may compute iframe child click coordinates without inherited CSS zoom. The bundled browser helper converts frame-local bounds to outer viewport coordinates and sends real mouse clicks. Diagnose this automation limitation rather than changing a correctly working document solely to satisfy a locator click.

For a zoomed iframe, avoid unconditional automation scrolling of an already-visible sticky-toolbar control: it can move the document before the actual click and produce a false reading-position failure. Check local viewport bounds first; scroll only an off-screen target.
