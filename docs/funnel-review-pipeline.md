# Funnel review capture and evidence pipeline

The project workflow remains the source of review scope and owner preferences.
This pipeline reduces repeated capture, matching and image decoding; it does not
reduce the required review. Run commands from the project root with `.venv/bin/python`.
Dependencies are pinned in `requirements.txt`. When changing Playwright, install
its matching Chromium build and rerun the browser fixtures before adopting it.

## Capture once per observed state

Prepare a JSON array of independent jobs. Discover product URLs from each actual
advertorial CTA before adding them. Use `page: "product"` on product jobs to add
explicit priority-element checks. Example (replace URLs and selectors with observed values):

```json
[
  {"name":"competitor_page2","page":"product","url":"https://source.example/product",
   "faq_selector":".faq","faq_toggle_selector":".faq-header","faq_open_class":"active"},
  {"name":"ours_page2","page":"product","url":"https://target.example/product",
   "faq_selector":".faq","faq_toggle_selector":".faq-header","faq_open_class":"active"}
]
```

```bash
.venv/bin/python tools/capture_funnel.py --jobs .tmp/jobs.json --run-id REVIEW_ID --concurrency 2
```

At most two jobs run concurrently, with a fresh browser context per job. Use
`--concurrency 1` if resources or site behavior require it. The default viewport is
390×844 at 2× with mobile/touch emulation; desktop is an explicit separate capture.
The tool progressively scrolls, rechecks page height, waits for visible images,
fonts and stable geometry, then verifies the DOM index stayed unchanged during
the screenshot. The per-page budget defaults to 120 seconds (`--budget`). Never
interpret a timeout as review completion. Sustained movement/infinite content
requires targeted capture and an explicit limitation.

Looping CSS/Web Animations are paused at their current frame inside the capture
context and recorded in `paused_animations`. Screenshotting keeps that same frame;
it does not rewind a marquee after measuring its text. Finite transitions must
settle normally. This is static evidence, not a test of animation or carousel
behavior. Test moving/sticky controls separately and inspect every unique image.
Continuously changing JavaScript layout still times out rather than being hidden.

Read file paths from `.tmp/captures/REVIEW_ID/NAME/manifest.json`. Each attempt has
its own directory with a full image, text, DOM occurrence index, static section
tiles, expanded FAQ states and SHA-256 hashes. Do not hardcode files directly under
the page folder. Section tiles come from the same full-page image; they do **not**
prove sticky-bar behavior at each scroll position. Test those interactions live.

Native `details` FAQs work by default. Custom widgets require observed row/toggle
selectors and either `aria-expanded`, an explicit expanded class, or
`faq_answer_selector` (a row-scoped answer element whose visibility is the state). Every answer
is captured individually, including mutually exclusive accordions. Zero discovered
FAQs is **not** proof there are none. Check the live page and complete the FAQ
inventory; capture unsupported widgets through the browser. Hidden tabs, image
text, non-semantic clickable elements and offer states still require review.

Countdown timers are excluded from review checks and feedback. Do not test their
ticking, reset or expiry, or wait for them to finish. If a ticking widget prevents
stable capture, add `"freeze_selectors": ["<observed timer selector>"]` to that job: after
scrolling, each match is replaced by a static clone of its current frame and listed
in the manifest's `frozen_elements`. This is static evidence only; it does not test
the timer. Keep the selector limited to the timer, preserving adjacent offer copy
and functioning purchase controls. Offer-handoff jobs accept the same option for
the source page.

Jobs may specify `radio_selections: [{"selector":"#observed-native-radio"}]` to
capture a known offer state in isolation. Give different states distinct job names.
The tool rejects non-unique/non-native selectors. Use targeted browser evidence
for custom selectors; never automate arbitrary purchase or submission clicks.

## Prepare a comparison packet

After capture, Python prepares facts once; the agent applies the comparison skill.
Create `.tmp/captures/REVIEW_ID/comparison-config.json`. Paths below are relative
to that config file (absolute paths also work):

```json
{
  "context": {"market": "Sweden", "template": "beauty", "template_basis": "owner confirmed"},
  "pairs": [
    {"id": "advertorial", "page": "advertorial",
     "source": "competitor/manifest.json", "target": "ours/manifest.json",
     "components": ["editorial_headlines", "body_emphasis", "callout_panels", "testimonials"]},
    {"id": "product", "page": "product",
     "source": "competitor_page2/manifest.json", "target": "ours_page2/manifest.json",
     "components": ["first_testimonial", "doctor_verified", "testimonials", "offer_cards", "offer_headings", "body_emphasis"]}
  ]
}
```

Use the actual context and skill-selected roles, not the example's Swedish template
for every funnel. Python does not infer template requirements from a URL or language.

```bash
.venv/bin/python tools/prepare_comparison.py --config .tmp/captures/REVIEW_ID/comparison-config.json --output .tmp/captures/REVIEW_ID/comparison.json
```

The JSON contains every indexed block and expanded FAQ state, intersecting section screenshot paths,
exact occurrence queries, controls/images, and candidate pairings. Exact-text and
relative-position suggestions are explicitly unconfirmed, including duplicate text.
New captures include a deduplicated style table, inline style runs, ancestor
containers, image natural/rendered dimensions and line counts. Coordinates remain
document CSS pixels; the evidence locator handles origin and device scale.
These measurements are facts, not defect decisions. No CSS threshold substitutes
for inspecting headline prominence, cards, testimonial presentation or offer layout.

Old indexed captures retain geometry/bold facts with a warning that other visual
attributes are unknown. Legacy captures expose manual text/image paths and no
invented index. Recapture when indexed evidence is needed. Failed schema-2 captures,
missing hashes and changed files are rejected. The packet does not mark any page,
component or control as passed. All existing coverage/report gates remain in force.

Read the packet by pair/state; avoid repeatedly loading its entire style registry.
Save confirmed semantic mappings in `alignment.json`, copying the packet's exact
`input_fingerprint` and block `ref` values:

```json
{
  "input_fingerprint": "FROM_PACKET",
  "mappings": [
    {"id": "first-review", "role": "first_testimonial",
     "source": ["product/source/full_page/SOURCE_BLOCK_ID"],
     "target": ["product/target/full_page/TARGET_BLOCK_ID"],
     "reason": "These are the actual first visible customer review slots."}
  ]
}
```

Regenerate using the same command plus `--alignment PATH/alignment.json`. A mapping
can contain multiple blocks on either side for split/merged paragraphs; one side
may be empty for absent or template-only content, with a reason. Blocks cannot be
reused across mappings. Distinct FAQ states stay distinct. Unmapped blocks remain
in `unmapped_refs`; matched role assignments remain `pending_review`. A match is
not a pass. Changed input manifests, context or tool version invalidate alignment.

While deciding findings, collect exact evidence refs in `selections.json`:

```json
{
  "input_fingerprint": "FROM_PACKET",
  "items": [
    {"id": "V01-source", "ref": "product/source/full_page/SOURCE_BLOCK_ID"},
    {"id": "V01-target", "ref": "product/target/full_page/TARGET_BLOCK_ID", "find": "Optional narrower exact phrase"}
  ]
}
```

```bash
.venv/bin/python tools/prepare_comparison.py --config .tmp/captures/REVIEW_ID/comparison-config.json --output .tmp/captures/REVIEW_ID/comparison.json --alignment .tmp/captures/REVIEW_ID/alignment.json --selections .tmp/captures/REVIEW_ID/selections.json --plan .tmp/captures/REVIEW_ID/annotation-plan.json --evidence-dir .tmp/captures/REVIEW_ID/evidence
.venv/bin/python tools/annotate_screenshot.py --plan .tmp/captures/REVIEW_ID/annotation-plan.json --receipt .tmp/captures/REVIEW_ID/annotation-receipt.json
```

Selections automatically use green for source and red for target, verify hashes
again and batch resolution once per index. Optional phrases stay pinned to their
selected block; ambiguous repeated phrases require the direct locator's occurrence
selection below. Exports frame continuous wrapped passages once, not every line
or a whole card. Distinct passages remain separate and overlapping/touching boxes
are rejected by the annotator. Verify strokes do not obscure words at report size.
Use inspected ancestor
geometry and the existing annotation tool for component boxes, and the direct
locator for insertion anchors. All annotations still require visual QA. No review
copy, translations or findings are generated by the preparation tool.

Measure packet preparation separately from semantic comparison, evidence review
and report publication. Its `duration_seconds` is local preparation time only;
an end-to-end speed improvement must be measured on the next complete review.

## Exact occurrence matching

Use the full-page index or the index for the relevant expanded FAQ. Search first:

```bash
.venv/bin/python tools/locate_evidence.py --index PATH/full_page.index.json --find 'Exact visible phrase'
```

The result lists all occurrences, stable block/occurrence IDs, neighboring block
text and headings. Paragraph ownership avoids matching the same text again in
every ancestor. Choose the intended occurrence from the evidence. The tool refuses
ambiguous matches. A full price phrase such as `€177 per jaar` avoids confusing it
with an endpoint of `€177–€399`. Matching normalizes whitespace and a small set of
typographic equivalents, not translation, fuzzy meaning or arbitrary punctuation.
Text split across separate semantic blocks may need separate verified marks.

Prepare a query array (IDs must be unique safe filenames):

```json
[
  {"id":"T1-target","find":"Exact visible phrase","block_id":"ID_FROM_SEARCH",
   "decision_context":{"offer_reference":"competitor, explicitly approved by owner"}},
  {"id":"T2-insertion","insert":"after","anchor":"Complete text of the indexed paragraph.",
   "block_id":"ID_FROM_SEARCH"}
]
```

```bash
.venv/bin/python tools/locate_evidence.py --index PATH/full_page.index.json --queries .tmp/queries.json --output .tmp/annotation-plan.json --evidence-dir .tmp/evidence
.venv/bin/python tools/annotate_screenshot.py --plan .tmp/annotation-plan.json --receipt .tmp/annotation-receipt.json
```

Combine generated plans by concatenating their `jobs` arrays into one version-2
plan; preserve unique IDs and outputs. The batch renderer groups by source, decodes
one source image at a time, and writes each PNG once. Its geometry/context rules
are the same as the single-image command. Coordinates use the actual capture
origin, scale and pixel dimensions. Insertion anchors must be the entire indexed
block, so a match on its first line cannot stand in for its bottom edge. An insertion
line is a proposed location: inspect the full paragraph and the actual gap before
accepting it. Use an explicit `region` when additional landmarks are needed.

Every generated crop starts `pending_visual_review`. Read the marked words,
insertion position and surrounding context in every output and in the rendered
card. Geometry validation cannot judge whether the feedback is correct. Image-only
text and controls can use the existing manually measured annotation command.
Do not run an extra PNG optimization pass after batch generation.

## Checkpoints and review completion

Capture reuse is **opt-in**: repeat the same run/jobs with `--resume`. Reuse requires
a complete packet, unchanged configuration/tool/dependency/browser fingerprint,
intact files and a capture no more than 30 minutes old. A reused packet is a snapshot
from its recorded `captured_at`, not a fresh live-site check. Omit `--resume` after
site edits, when freshness matters, or for a new review. Never infer live freshness
from the age window. Interrupted captures restart only the failed page; successful
siblings can be reused. Original attempt files remain available for diagnosis.

Annotation `--resume` verifies source, index, geometry/options, decision context,
renderer version and output hashes. Changing any of these rerenders the affected
job or requires relocalization. Checkpoint JSON is replaced atomically after each
completed image. Do not overwrite a source/index with output or a receipt.

Each capture creates `review-checks.template.json`. Copy it to `review-checks.json`
and complete each required row **after reviewing it**. Keep `manifest_sha256`.
Each row needs a `reason` describing the actual result, and a status:

- `pass`: reviewed successfully; link detailed evidence/inventories in the reason.
- `issue`: reviewed defect or owner decision, with existing `finding_ids`.
- `not_applicable`: only for excluded controls, with the precise reason (e.g. footer
  email or submission boundary). This is not a verified interaction pass.
- `pending` / `blocked`: unfinished; blocks a finished report.

The automatic inventory is a starting point. Keep the workflow's detailed
`review_checks.json` for all content, FAQ pairs, sticky/extra controls and states,
guarantee occurrences and offer arithmetic. A zero-match or partial automatic
inventory cannot replace that work. For missing priority product elements, record
whether they are genuinely absent on the source or are a target omission; do not
invent a pass on omitted content.

Button/CTA text is permanently excluded from findings and owner decisions.
Recorded labels identify controls for functional testing; they are not copy-review
targets. Keep click/destination/offer-state checks and report functional defects
without suggesting button-text replacements. The report gate rejects findings
tagged `button_text` and button/CTA copy, label or translation aliases.

Add `checks_file` to each `meta.pages` entry, alongside its existing manifest,
URL, side, page and reviewed status. For indexed runs also provide:

```json
"cross_page_checks": {
  "guarantee": {"status":"pass","reason":"Reviewed own-funnel occurrence inventory in review_checks.json."},
  "pricing": {"status":"issue","reason":"Compared equivalent offers at their actual locations.","finding_ids":["T7"]}
}
```

These examples describe the schema, not reusable review results. Guarantee duration
still follows our own funnel majority. Prices follow the source or explicit owner
decision; the approval to use the competitor offer applies to the CalmSoothe review,
not automatically to unrelated future funnels. Regenerated manifests invalidate
old review completion records. The report generator checks hashes, every required
row and cross-page completion. It does not perform the judgments. Legacy manifests
remain readable but do not gain new verification claims.

## Timing, fallback and validation

New advertorial/product packets include `sticky_states` and `sticky_states_file`:
six genuine viewport captures (top, after hero, middle, bottom, back up to middle
and top). These are separate from static full-page tiles. Capture records visible
CSS `fixed` and `sticky` candidates, including parent containers; the reviewer
still judges which are actionable bottom CTAs and checks JavaScript positioning.
An empty candidate array is not an automatic absence or pass decision.

Complete the separate `sticky_cta` check with boolean `present`, all six screenshot
paths in `evidence_files`, and a reason. Our missing sticky CTA must be `issue`
with a finding ID. A present passing CTA additionally needs `placement: bottom`,
`scroll_behavior`, `click_result` and `actual_destination`. Missing source CTAs
are observations, not defects in the competitor. Legacy packets retain their
original scope; supplement an old review with fresh evidence rather than changing
its immutable capture manifest. The canonical skill requires bottom sticky CTAs
on both target stages for every funnel, independently of source presence.

`capture-run.json` records batch elapsed time and individual capture durations;
each page manifest records its start/end and browser build. Each annotation receipt
records job completion/duration and total elapsed time. Reused entries are labeled.
Capture invocations also keep immutable receipts under `capture-runs/`, so later
phases do not erase earlier capture timings. Use distinct annotation receipt paths
per phase. Parallel job durations overlap; do not sum them as wall-clock time.
Continue recording review, owner-wait, visual QA and publishing start/end times in
the run timing log. These remain real work; do not estimate them from tool time.
Page manifests also record navigation, settle/scroll, base snapshot, tile creation,
expanded FAQ and finalize timings, plus the failing phase on an incomplete attempt.

The existing single-image annotation command remains available. If a page cannot
use the new capture, first retry just that page with concurrency 1 or a justified
larger budget. Then use targeted browser capture or `capture_funnel.py --legacy`
for diagnosis only. Legacy capture lacks the settled-height/index guarantees, and a
finished report refuses legacy captures made on or after 2026-10-02 (and any legacy
capture in a current-policy report). Never use legacy mode to bypass a review gate.
Publishing stages an isolated page, checks its receipt hash and verifies it live:
`publish_feedback_page.py --prepare-only`, then `upload_feedback.py --slug <slug>`.

```bash
# tests/ is not a package: name the modules.
bash -c 'PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest $(ls tests/test_*.py | sed "s#/#.#; s#\.py$##")'
RUN_BROWSER_TESTS=1 .venv/bin/python -m unittest tests.test_capture_packet_browser -v
```

Browser fixtures run a local server and need permission to launch Chromium where
the sandbox restricts it. They cover delayed page growth, duplicate/nested text,
Unicode, native and custom FAQs, selected radios/cookie isolation, hash/age reuse,
independent failures and bounded unstable captures. Live smoke tests are separate
from the deterministic fixtures; timing depends on network and page behavior.

## Default feedback presentation

The standard `generate_feedback_page.generate()` and publisher preparation path
use `feedback_presentation.py` plus `tools/templates/funnel_review.css` and `.js`.
The approved [report-format contract](../skills/funnel-comparison/references/report-format.md)
is mandatory during finding authoring and QA. It adds `feedback_type`, evidence
`location`, optional verified `target_anchor`/`open_hint`, and optional
`display: comparison`; existing categories, checks and evidence mappings remain.
The renderer keeps supplied replacement strings intact. Legacy fragment helpers
remain available for historical callers but are not the report generation path.
No run-specific renderer or prototype file is required for future reviews.

Regression checks:

```bash
.venv/bin/python -m unittest tests.test_feedback_presentation tests.test_publish_feedback_page tests.test_review_coverage
RUN_BROWSER_TESTS=1 .venv/bin/python -m unittest tests.test_feedback_presentation_browser
```

The browser fixtures exercise combined filters, cross-page cards, clipboard
success/failure/reset, Done/uncheck, expanded comparisons, preview dialogs, empty
reports and narrow layouts. Before delivery, also inspect the actual report's
screenshots and exact copy; generic fixture tests cannot establish evidence truth.

The subsequently approved Dutch checkout extension is now active. See the
[Dutch checkout contract](../skills/funnel-comparison/references/dutch-checkout.md).
The Dutch checks were introduced in review policy version 2 (current captures use
version 3). Dutch-market completion requires our
indexed checkout with `scope: dutch_checkout`, all seven screenshot-backed results,
review/date and expanded FAQ inventories, guarantee values, and individually
loaded iDEAL/Bancontact options. Historical packets keep their original scope.

## Swedish offer handoffs

Capture policy version 3 adds mandatory per-button/state checkout and price checks
for Swedish runs. Follow the [Swedish offer contract](../skills/funnel-comparison/references/swedish-offers.md).
`capture_packet.py` accepts `offer_handoff` checkout jobs: source URL plus a unique
selector or short ordered selector sequence. It records source evidence, clicks
into checkout in the same isolated context and captures the resulting selected
offer. After each click, wait up to **3 seconds** for the checkout tab to open or
the current tab to navigate (within the remaining capture budget). Continue when
the destination appears; page loading/settling has its own capture checks. If the
handoff remains on the source page, fail instead of saving it as checkout evidence.
Checkout radio overrides are rejected. The generator validates the bound
per-button record in `meta.swedish_offer_checks_file`, quantities and SEK amounts.
The reviewer still judges actual routing, inventory completeness and displayed
shipping terms; capture alone never marks a button as working. Historical policy
versions retain their original scope.
