# Source-grounded authoring

## Completeness and fidelity

Work from the exact supplied paper/version. Translate every source page in order, including title material, captions, footnotes, formulas and symbol definitions, appendix, acknowledgments/disclosures, and reference sections. Preserve bibliographic identity, author names, identifiers, URLs and original copyright attribution. Do not add a title page to the source pagination or omit an awkward page to make the layout uniform.

Text extraction/OCR is an aid, not authority. View the PDF where extraction splits words, joins columns, loses mathematical symbols, transposes table entries or misreads superscripts. Record unresolved ambiguity. Use complete flowing English paragraphs rather than displaying PDF lines verbatim; tables/equations retain separate aligned blocks. Reconstruct footnote and paragraph boundaries conservatively, including page continuations.

Before calling a page complete, check:

- Original numbers, signs, units, dates, sample definitions and qualifiers remain exact.
- Named populations, data providers and filters are not conflated; sample counts state their units.
- Empirical time periods, train/validation/test roles and actual split definitions are accurately distinguished. An intended ratio is not the observed count ratio; a temporal test holdout is not a random train/test split.
- Metric definitions, denominators, horizons, aggregation and benchmarks are preserved. Distinguish probability from realized outcome, accuracy from ranking quality, and return from risk-adjusted performance where relevant.
- Negation, uncertainty, assumptions and scope survive translation. Correlation, a robustness check and causal identification are different claims.
- Citation labels and source cross-references resolve to the appropriate physical page or external bibliographic target.

## Original figures and tables

Use the original scientific images with unchanged labels/values. Keep all panels, axes, units, legends, significance markers, headers, notes and continued rows. Place full original captions and Chinese explanations outside the image. A teaching schematic must be labeled explanatory, with illustrative numbers clearly identified.

Inspect sideways/landscape tables visually: a page rotation flag may not describe the orientation of the table ink. Rotate the whole table crop into reading orientation, retain enough context, and keep portrait headings/folios separate when needed. Do not crop away a caption or relabel a continuation as a new table. Record source page, printed label, coordinate convention, rotation and SHA identity.

## Page-specific Chinese AI notes

Each source page gets an independent, clearly labeled Chinese note card, including appendix and references. Summarize the whole page, explain concepts and relevant figure/table reading, and connect it to the surrounding argument. A reference page may explain the cited research strands without inventing new paper findings.

Use familiar language and define a technical term before relying on its abbreviation. A small concrete example is helpful when it resolves a difficult step; mark invented numbers/examples as illustrative. Identify an interpretation, analogy or suspected limitation as such. Attribute reported findings to the authors. Keep separately sourced local results in explicitly separate comparisons.

Prefer notes shorter than their source page in ordinary use. Do not impose a fixed character count across papers or repeat a template three times on every page. Ensure the explanation has enough coverage and an ending. Tighten prose instead of imposing a max-height, inner scrollbar, wheel handler or hidden overflow; let the main document scroll naturally.

## Research roadmap

Derive stages from the paper's actual argument and experimental progression. Do not impose a finance pipeline, seven stages or a specific page count on another field. Pair formal descriptive headings with plain-language subtitles. Number concrete intermediate steps and explain what is constructed/tested, why it is needed, what the evidence shows and how the next step follows. Link each step to its real source page.

Use the same stage titles and hierarchy in the map and contents. Include nested sections and supporting figures/tables where they help reading. Overlapping topics may point to the same page; keep explicit navigation intent rather than assigning invented source pages.

For an empirical paper, make its fundamental setup easy to find near the beginning: source/population, observations and units, dates, any train/validation/test periods and split policy, task/target, models/baselines, evaluation and limitations. State absent information as unknown or not applicable. Do not transfer one paper's configuration or our reproduction's settings into another paper.

## Existing-reader edits

Identify the requested content/control first and reuse the established builder if available. Snapshot relevant HTML content groups and original PDF/image hashes. Preserve the unaffected source, translations, AI notes, user preferences and file naming. Compare changed meaning against the PDF and unaffected bytes against the snapshot. Layout-only changes never authorize scientific reruns or altered experiment evidence.
