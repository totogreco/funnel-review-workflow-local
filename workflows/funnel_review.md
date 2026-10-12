# Funnel Review Workflow

## Objective

Compare a competitor funnel against our localized version and generate a feedback page with all translation and visual issues, so a funnel builder can fix them without guessing.

## Required Review Scope

The funnel has three steps: **advertorial → product page → checkout**. Review the
first **two** steps on **both** sides in every run:

| Stage | Competitor | Our funnel |
|---|---|---|
| Advertorial | Required: capture and review completely | Required: capture and review completely |
| Product page | Required: capture and review completely | Required: capture and review completely |
| Checkout | Price/offer context, captured best effort (a failure is recorded, never blocking) | Dutch reviews: required, seven checkout checks. Swedish reviews: every offer-button handoff. Other markets: price/offer check, best effort (if our checkout cannot be reached the review continues and the result says so) |

A complete review covers **four pages / two matched page pairs**, plus **our
checkout for Dutch-market funnels** (NL/NLBE and Dutch-language BE), and the
**clicked checkout state for every Swedish offer button**. Completing the
advertorial pair alone is an incomplete review, even if it contains many findings.
A product page with no issues still requires a full review and an explicit completion
record. **Offer placement may differ between templates.** First inspect the product
page for the offer. If the complete offer/selector is absent (even if a teaser price
is shown), follow its purchase CTA to the next checkout page and review the prices
and offer presentation there. Compare our checkout offer against the competitor's
offer wherever it actually appears. Do not flag the absence of product-page offer
cards when they are correctly presented at checkout. For Dutch-market funnels,
also apply the [Dutch checkout checks](../skills/funnel-comparison/references/dutch-checkout.md)
regardless of where the offer lives. Inspect reviews, expanded FAQs, guarantee
consistency and visible iDEAL/Bancontact options. Customer-data entry, payment
submission and transaction processing remain outside scope.

### Custom funnel mode

When the owner starts the run as a **custom funnel** (for example "run the funnel
review for NLBE 235, it's a custom funnel"), the competitor has no real product
page and our builder made a custom product page based on our advertorial. Read
and apply the [custom funnel rules](../skills/funnel-comparison/references/custom-funnel.md)
before step 2. The advertorial and checkout keep their full review; the product
page is reviewed against our own advertorial instead of the competitor. All
capture, coverage, evidence and publishing steps below stay the same. If the
competitor's second URL is clearly not a real product page and the owner did not
say "custom", ask before reviewing the product page.

Standing owner preferences, exclusions and the localization rule are defined in the
[funnel-comparison skill](../skills/funnel-comparison/SKILL.md). That skill is the
single source of truth; do not duplicate those rules here.

## Sheet-Driven Funnel Lookup

Before any review starts, run `tools/resolve_funnel.py` to resolve the funnel
from the configured sheet instead of asking the user to paste URLs manually.

### Sheet configuration

The funnel review reads from the sheet and tab configured in `.env`:

- `FUNNEL_SHEET_ID` — the Google Sheet ID (default: the project sheet)
- `FUNNEL_SHEET_TAB` — the tab name (default: `FUNNEL-BUILDING`)

### Supported selection inputs

The review may be triggered with any of the following:

- `FUNNEL ID` (preferred, e.g. `SE 195`)
- `Brand name + COUNTRY` (e.g. `Manvra + SE`)
- `Nr. + COUNTRY` (e.g. `195 + SE`)
- `Brand name` alone when unique in the sheet

If the user gives a brand name and country, the agent must read the
sheet, match the row by the available identifiers, and extract the row's funnel
links automatically. The agent should not ask for `competitor_url` and `our_url`
if they can be resolved from the sheet.

### Lookup via `tools/resolve_funnel.py`

The tool reads `FUNNEL_SHEET_ID` / `FUNNEL_SHEET_TAB`, matches the row, derives
the target market/language/currency from the country code, and returns structured
JSON. It exits non-zero when the match is ambiguous, missing, or lacks URLs.

```bash
# By funnel ID
python3 tools/resolve_funnel.py --id "SE 195"

# By brand + country
python3 tools/resolve_funnel.py --brand Manvra --country SE

# By number + country
python3 tools/resolve_funnel.py --nr 195 --country SE

# List all funnels
python3 tools/resolve_funnel.py --list
```

The output provides:
- `competitor_url` ← `Competitor Funnel`
- `our_url` ← `Our Funnel Link`
- `target_market` / `target_language` / `currency` ← derived from `COUNTRY`
- `prices_bundles` ← `Prices/Bundles` (when present, used as offer reference)
- `brand_name`, `store`, `template`, `funnel_status`, `funnel_builder`, `note`

Copy `funnel_builder`, `brand_name`, `country`, `template` and `funnel_id` from the resolved
row into the report's `meta`. Publishing requires the first three fields to
name the review `[funnelbuilder name]-productname-country`. Use `brand_name`
as the product name and the sheet's `COUNTRY` code (for example `SE` or `NLBE`).
If any naming field is missing, resolve it before publishing; never invent a
builder or fall back to a run ID.

Use the sheet's `COUNTRY` and `Template` together for scoped review rules. In
particular, SE + Health uses the 5x most-popular offer and a doctor recommendation
in place of the first customer review under the canonical skill. Do not apply a
competitor's different most-popular quantity or restore that substituted review.
Resolve missing template context before making a template-dependent finding.

Product page URLs (`competitor_product_url` / `our_product_url`) are not in the
sheet; discover them via each advertorial's CTA during capture.

### Example

User request:

> Review the funnel for `Manvra`, country `SE`.

The workflow should:

1. read `FUNNEL_SHEET_TAB` (`FUNNEL-BUILDING`),
2. find the row where `Brand name` = `Manvra™` and `COUNTRY` = `SE`,
3. extract `Competitor Funnel` → `competitor_url`, `Our Funnel Link` → `our_url`,
4. derive target market (Sweden) and target language (Swedish) from `COUNTRY`,
5. use `Prices/Bundles` as offer reference when present,
6. start the review using those values,
7. only ask for clarification if the row is missing or ambiguous.

This contract applies to all funnel-review runs. Manual URL entry remains a
fallback only when the sheet cannot be read or the row is genuinely unavailable.

## Required Inputs

| Input | Sheet column | Example | Notes |
|---|---|---|---|
| Funnel identifier or selector | `FUNNEL ID`, `Brand name`, `COUNTRY`, `Nr.` | `SE 195` or `Manvra + SE` | Preferred; the workflow resolves the row and extracts URLs |
| Competitor funnel URL | `Competitor Funnel` | `https://www.herbenity.com/mandura/adv` | Resolved from the sheet; manual entry is fallback only |
| Our funnel URL | `Our Funnel Link` | `https://www.halsoland.com/manvra/health-adv` | Resolved from the sheet; manual entry is fallback only |
| Product page URLs | (not in sheet) | Competitor and our product URLs | Discovered independently through each advertorial's CTA |
| Prices/bundles | `Prices/Bundles` | `1 for 349 kr` / `2 + 1 FREE for 569 kr` | Used as offer reference when present |
| Target market | derived from `COUNTRY` | `Sweden` (from `SE`) | Determines expected currency, names, formats |
| Target language | derived from `COUNTRY` | `Swedish` (from `SE`) | The language everything should be translated into |

## How this local version runs

This folder is the **manual** funnel review: no OpenRouter, no engine, no API keys for AI
models. The agent in Claude Code (signed in with the reviewer's own Claude account) does
the comparison and the review judgments in steps 2–4. Everything else is deterministic
Python in `tools/`:

| Step | Who | Tool |
| --- | --- | --- |
| Find the funnel in the sheet | Python | `tools/resolve_funnel.py` (read-only Google Sheets) |
| Capture pages, FAQs, buttons, checkout | Python + Chromium | `tools/capture_funnel.py` |
| Line up pages for comparison | Python | `tools/prepare_comparison.py` |
| Compare, judge, write findings | **Claude Code (you)** | funnel-comparison skill |
| Find and mark evidence | Python | `tools/locate_evidence.py`, `tools/annotate_screenshot.py` |
| Build and check the page | Python | `tools/generate_feedback_page.py`, `tools/publish_feedback_page.py --prepare-only` |
| Publish to the team's Render site | Python | `tools/upload_feedback.py` (needs `FEEDBACK_UPLOAD_TOKEN`) |

Always run tools with `.venv/bin/python`. Cost: no per-run API cost; the review uses the
reviewer's Claude plan limits. A full review is long, so a Max plan is recommended.

Every reviewer publishes to the **same** team site, `https://ad-translation.onrender.com/feedback/{slug}/`,
using the shared `FEEDBACK_UPLOAD_TOKEN`. The Render dashboard's own (OpenRouter) reviews
land in the same place. This local version does not change the sheet's Funnel Status; tell
the owner when a review is published, or set the status by hand.

Before a first run (and whenever something fails with a sign-in or token error) run the
dry check: `.venv/bin/python tools/onboarding_check.py --live`. It reads the sheet, checks the
Render site and validates the upload token without publishing anything.

## Steps

### Execution Contract and Timing

Use this project's scope and standing owner preferences throughout the run. The
default deliverable is the existing HTML feedback page, with 390×844 mobile
captures at 2×. If an installed general-purpose skill proposes a different viewport,
PDF output or sampling, retain this project contract unless the owner requests a
change. Speed improvements must preserve complete content, image, FAQ, button,
offer and cross-page review.

Use the indexed capture and batch evidence pipeline described in
[`docs/funnel-review-pipeline.md`](../docs/funnel-review-pipeline.md). It is the
default for new runs; existing single-page/single-image commands remain compatible.
Record start/end and elapsed time for discovery, capture, comparison, owner wait,
evidence preparation, visual QA, report generation and publishing. Tool receipts
record capture/annotation durations automatically; retain them per phase and add
the agent/manual phases to the run timing log. Overlapping jobs must not be summed
as elapsed wall time. Record retries, cache reuse and blockers separately.

### 1. Discover and Capture Both Required Steps

Run `tools/capture_funnel.py` on both URLs. Mobile viewport is the default
(390×844). Put the two independent advertorial jobs in a JSON array such as:

```json
[
  {"name":"competitor","page":"advertorial","url":"COMPETITOR_URL"},
  {"name":"ours","page":"advertorial","url":"OUR_URL"}
]
```

```bash
# Generate a shared run ID
RUN_ID=$(.venv/bin/python -c "import uuid; print(uuid.uuid4().hex[:8])")
.venv/bin/python tools/capture_funnel.py --jobs .tmp/advertorial-jobs.json --run-id "$RUN_ID" --concurrency 2
```

Output lands in `.tmp/captures/{run_id}/competitor/` and `.tmp/captures/{run_id}/ours/`.

Read file paths from each `manifest.json`; evidence lives in an immutable attempt
directory. The packet includes settled full-page evidence, text and occurrence
index, section tiles cropped from that image, separately expanded FAQs, file hashes,
timing and a pending `review-checks.template.json`. Static section tiles do not test
sticky controls or prove behavior while scrolling. The tool waits for geometry,
visible images and fonts, revisits growing page height and bounds stalled captures.
Inspect custom FAQ selectors before capture; supply them in each job as documented.
Zero automatic FAQ/control matches never establishes complete coverage.

**Product-page capture is mandatory, not conditional:**
1. Follow the main purchase/product CTA on the competitor advertorial, then independently follow the corresponding CTA on our advertorial. Inspect the destination to confirm it is the product page. Do not guess URL paths or assume the two sites have identical routing. A CTA may scroll to another section or open an overlay rather than navigate; continue locating the actual product page.
2. Record each product-page URL and capture both with the same run ID. Put them in
   a second job array with `name: "competitor_page2"` / `"ours_page2"` and
   `page: "product"`; include observed custom FAQ selectors when needed:

```bash
.venv/bin/python tools/capture_funnel.py --jobs .tmp/product-jobs.json --run-id "$RUN_ID" --concurrency 2
```

3. Confirm that `competitor/`, `ours/`, `competitor_page2/` and `ours_page2/` each have their own `manifest.json`, text and screenshots. Capturing a page is not the same as reviewing it.
4. If a product page is unavailable, a CTA goes directly to checkout, or the destination cannot be identified, record that page as `blocked`, describe the blocker and request the missing URL/access if needed. Continue independent review work, but do not deliver a completed report. Do not substitute the advertorial or checkout capture for the missing product page.
5. Set `meta.review_policy_version: 3` for every new run. For NL/NLBE or Dutch-language BE, follow our actual purchase CTA and capture the checkout even if its offer is already present on the product page. Use job `page: "checkout", scope: "dutch_checkout"`; preserve and complete all seven checkout-specific rows in the generated checks template, following the linked Dutch checkout contract.
6. For Sweden (SE), follow the [Swedish offer-button contract](../skills/funnel-comparison/references/swedish-offers.md): test every offer button and selected-offer CTA state, capture its actual checkout destination and selected bundle, and compare checkout prices with its presentation. Use isolated `offer_handoff` capture jobs and record `meta.swedish_offer_checks_file`.
7. Locate the complete offer on each side. When it is deferred to checkout, follow the actual purchase CTA, record the destination and capture that page as `ours_checkout` or `competitor_checkout` with the same run ID. For the price/offer fallback, review prices, bundles, offer presentation and offer-selection behavior; our Dutch checkout additionally receives its mandatory localization and visibility checks. Keep the four mandatory page captures; checkout does not substitute for the product page.

8. Reuse intact same-run captures only with explicit `--resume` (maximum age 30
   minutes). A reused snapshot retains its capture time; it is not a fresh live
   check. Omit resume after page edits or when freshness is required. Retry only
   incomplete pages; never convert a failed capture to complete. See the pipeline
   guide for isolated offer states, bounded retries and the legacy/manual fallback.

### 2. Compare Sections (Agent Task)

This is the intelligent part — the agent (Claude) does this, not a script.

**Prepare once before comparing:** run `tools/prepare_comparison.py` on the four
capture manifests, grouped as advertorial and product pairs. Supply the actual
template context and component roles from the funnel-comparison skill. Use the
[comparison packet guide](../docs/funnel-review-pipeline.md#prepare-a-comparison-packet)
for the input, alignment and evidence-selection schemas. The tool organizes text,
screenshots, visual attributes and occurrence references; its suggestions are
unconfirmed. Keep every unmatched block visible and pair expanded FAQs explicitly.
Legacy or older captures retain explicit limitations; do not infer missing styling
from an unavailable field. Record evidence refs as issues are discovered, so Step 4
can export a single annotation plan without searching for the same text again.

**Process — perform this twice: first advertorial vs advertorial, then product page vs product page:**
1. Read the `text_content.txt` from both funnels
2. Look at each section screenshot from our funnel alongside the corresponding competitor section
3. Check every item on the checklists below
4. Record each issue with `page: "advertorial"` or `page: "product"`; use `page: "checkout"` for conditional price/offer checks or the seven mandatory Dutch checkout checks. Use the exact check IDs in the Dutch checkout reference; keep the existing price/offer IDs for offer findings.
5. (Custom funnel: replace this product-page comparison with the scope in the
   [custom funnel rules](../skills/funnel-comparison/references/custom-funnel.md).)
   Review the product page from top to bottom, explicitly comparing the headline, subheadline, every bullet point, first testimonial, offers, prices, discounts, bundles, guarantees, reviews, images, badges, every FAQ question and expanded answer, and footer. Apply all checklists below in full; checking only the hero or price block is not a completed product-page review.
6. Map source content to corresponding target content before calling something missing. Inspect text within tabs, accordions and images as well as initially visible text. Compare bold emphasis in the actual rendered pages. Test every button instance and relevant state; screenshots alone cannot establish that buttons work.
7. Save per-page results in `.tmp/captures/{run_id}/review_checks.json`: check name, location, source/target evidence, and `pass`, `issue` or `blocked` (with finding ID or reason). Include a row for each priority product-page element, each FAQ pair and each button instance/state. Complete the separate `sticky_cta` presence/behavior row using the real down/up viewport captures and the canonical skill's required-bottom-CTA rule; the generic interaction inventory cannot substitute for it. Record missing source elements as not applicable with an explanation rather than inventing content.
8. Only after the entire page and its applicable checks have been inspected, set that page's coverage status to `reviewed`. Confirmed defects become findings and do not prevent review completion; unresolved/untested checks do. Use `pending` or `blocked` otherwise. Zero issues is valid; an absent coverage entry is not. For indexed captures, complete a copy of `review-checks.template.json`, retain its manifest hash, and add its path as `checks_file` in that page's `meta.pages` entry. Every required content/FAQ/control row needs its actual result and reason; issues reference existing finding/decision IDs. Control exclusions must be explicit, not verified passes. The generator validates those records and evidence hashes; it does not make the review judgments. Keep the detailed checklist log as well, including controls/states the DOM inventory did not discover.
9. After both stages are reviewed, complete the Cross-Page Consistency Checklist below. For guarantee duration, use only our combined advertorial/product occurrences and the majority rule below. For pricing, compare within each funnel and then source against target. Record guarantee and pricing checks separately in `review_checks.json`, with all relevant locations and values. Two individually reviewed pages do not establish cross-page consistency.
10. Complete the Dutch Checkout Review for applicable markets, including every review and expanded FAQ, all guarantee occurrences and both loaded payment options. Save screenshot-backed results in the checkout checks file and detailed log.
11. Complete the Swedish offer-button inventory and every clicked checkout/price result for SE. A functioning first button or one generic checkout screenshot does not cover other buttons or offer states.
12. Apply the Checkout Offer Fallback below whenever the complete offer is deferred. Record the actual offer location for both sides; do not mark required but uninspected checkout offers as passed. Skip review-count comparisons throughout all other checklists.

For indexed runs, also add completed `meta.cross_page_checks.guarantee` and
`meta.cross_page_checks.pricing` results (`status`, `reason`, and `finding_ids`
for issues). Link the detailed inventories in the reason. Missing, blocked or
pending records prevent a finished report. The pipeline guide has the schema.

**Compare top-to-bottom.** The funnels may not align perfectly section-by-section since layouts differ. Use the content to match corresponding areas.

### 3. Categorize and Log Issues

Each issue gets classified and recorded in a JSON structure. The
[funnel-comparison skill](../skills/funnel-comparison/SKILL.md) defines when to use
**translation** vs **visual** and how to handle localization carryovers.

```json
{
  "meta": {
    "competitor_url": "...",
    "our_url": "...",
    "target_market": "Netherlands",
    "target_language": "Dutch",
    "run_id": "abc12345",
    "review_policy_version": 3,
    "funnel_builder": "Alex",
    "brand_name": "Example Product",
    "country": "NLBE",
    "pages": [
      {"side": "competitor", "page": "advertorial", "url": "COMPETITOR_URL", "manifest": ".tmp/captures/abc12345/competitor/manifest.json", "status": "pending"},
      {"side": "ours", "page": "advertorial", "url": "OUR_URL", "manifest": ".tmp/captures/abc12345/ours/manifest.json", "status": "pending"},
      {"side": "competitor", "page": "product", "url": "COMPETITOR_PRODUCT_URL", "manifest": ".tmp/captures/abc12345/competitor_page2/manifest.json", "status": "pending"},
      {"side": "ours", "page": "product", "url": "OUR_PRODUCT_URL", "manifest": ".tmp/captures/abc12345/ours_page2/manifest.json", "status": "pending"}
    ]
  },
  "issues": [
    {
      "id": "T1",
      "page": "advertorial",
      "category": "translation",
      "feedback_type": "find_replace",
      "section": 3,
      "description": "Replace the English headline with the Dutch headline below.",
      "feedback": "Replace the English article headline with the Dutch headline below.",
      "wrong_text": "Get Your Free Sample Today",
      "correct_text": "Ontvang Je Gratis Sample Vandaag",
      "evidence_pairs": [{
        "id": "A", "marker": "A", "page": "advertorial",
        "location": "Article headline",
        "target_screenshot": ".tmp/captures/abc12345/annotated/T1.png"
      }]
    },
    {
      "id": "V2",
      "page": "product",
      "category": "visual",
      "feedback_type": "find_replace",
      "section": 5,
      "description": "Use Lisa de Jong for the reviewer shown in this portrait.",
      "feedback": "Use Lisa de Jong for the reviewer name below this portrait.",
      "wrong_text": "Jan de Vries",
      "correct_text": "Lisa de Jong",
      "evidence_pairs": [{
        "id": "A", "marker": "A", "page": "product",
        "location": "Reviewer name below the portrait",
        "target_screenshot": ".tmp/captures/abc12345/annotated/V2.png"
      }]
    }
  ]
}
```

**Do not include a `fix` field** — the `wrong_text` / `correct_text` pair is the fix. The feedback page renders them as copy-pasteable blocks with copy buttons.

Use stable issue IDs and one output image per issue (e.g. `annotated/T1.png`). Do not reuse another issue's crop just because both occur in the same section. Screenshots must show surrounding funnel context with an internal red box around the exact issue (step 4).

`wrong_text` must be a literal, contiguous excerpt from the target page, not a summary stitched together with ellipses. For multiple separated corrections, use separate findings/screenshots or enough context and separate boxes to show every referenced location. Keep existing delivered IDs when correcting a report.

For a product introduction or promotional section left over from another product
category, retain the useful section and recommend exact target-language replacement
copy. Do not default to deleting the component merely because its text discusses
the wrong product. Rewrite every affected paragraph, preserve relevant surrounding
CTAs/layout, and use supported product facts without inventing efficacy claims.
Use `copy_scope: "full"` with a reason when the whole passage needs rewriting.
Show the marked target passage alone if there is no relevant source counterpart;
an unrelated competitor screenshot adds confusion rather than evidence.
Record these findings as `check: "off_topic_introduction"`; the generator requires
actual find/replacement copy for this check and rejects removal-only feedback.

Apply the [copy formatting rules](../skills/funnel-comparison/SKILL.md#copy-formatting-rules)
from the funnel-comparison skill when writing `wrong_text` / `correct_text` and
`replacements[].find` / `replace` pairs.

**Default presentation contract:** Read and apply the
[approved report format](../skills/funnel-comparison/references/report-format.md)
when authoring every finding. Set `feedback_type`, perform the contract's
[instruction-headline pass](../skills/funnel-comparison/references/report-format.md#instruction-headlines)
and save the builder action in `feedback`, then give each evidence pair a short `location`, actual `page`, and
verified `target_anchor` where available. These are presentation fields, separate
from the existing review `category` and `check`. Orange applies to product selection/cart and all checkout
feedback; unrelated editorial price wording is find-and-replace. Use `offer_context`
to distinguish these cases as specified in the report-format contract.

The generator preserves each supplied FIND/REPLACE pair exactly. It does not
shorten sentences or split them into token-level edits. Choose the right copy scope
while reviewing: a meaningful phrase for a local correction, or one complete
sentence/passage when that is the requested implementation. Retain `copy_scope`
and `copy_scope_reason` as authoring metadata for deliberate phrase/full rewrites.
Additions have an empty FIND; deletions have an empty REPLACE. Neither produces
an empty copy button. Unchanged pairs produce no copy fields. Necessary placement
instructions belong in `evidence_pairs[].note`; migrate any essential legacy
replacement-location hints into this note when adding a card location.

For missing comments, follow the skill's simple-feedback exception: one short
instruction plus readable source screenshots. Each `evidence_pairs` entry may
contain only `source_screenshot` and `source_caption`; `target_screenshot` is
optional. Omit replacements for these comments. Each evidence group must contain
at least one screenshot. Other missing text retains its target insertion evidence
and copy requirements.

Save this to `.tmp/captures/{run_id}/issues.json`. Replace the URL placeholders with the exact URLs used by the capture manifests; paths are relative to the project root. The example deliberately starts as `pending`: change each entry to `reviewed` only after completing step 2. For blocked entries also record a `blocker` explanation. Do not mark old first-page-only runs complete just to pass validation.

### 4. Match Evidence, Then Annotate

For issues already located in the comparison packet, export their saved selections
with `prepare_comparison.py --selections ... --plan ...` and use the existing batch
annotator. This verifies the current capture hashes and preserves exact block IDs.
Use the direct locator below for new or narrower occurrences, insertion anchors,
and manual component framing. Inspect every resulting annotated image.

Use `tools/locate_evidence.py` with the packet's full-page or expanded-FAQ index to
list occurrences, then build annotation jobs with explicit block/occurrence IDs
where needed. Never use first-match or ancestor substring heuristics. Save owner
decisions affecting the evidence in each job's `decision_context`. Use a complete
indexed paragraph as an insertion anchor. Run all jobs through
`tools/annotate_screenshot.py --plan PLAN.json --receipt RECEIPT.json`; it decodes
one source at a time and writes each output once. `--resume` reuses only unchanged,
hash-verified jobs and outputs. See the pipeline guide for command examples.
Do not re-encode crops in a separate optimization pass. Manual geometry remains
available for image text, controls and unsupported layouts. Every generated crop
starts pending visual review: the following visual checks remain mandatory.

Apply the [evidence quality standards](../skills/funnel-comparison/SKILL.md#evidence-quality-standards)
from the funnel-comparison skill. The rules below cover tool parameters.

For every issue:
1. Locate its exact `wrong_text` in the target capture before choosing coordinates.
2. Measure the original PNG dimensions. All annotation coordinates are **original image pixels**, not displayed-preview or CSS pixels. A 390px viewport usually produces a 780px-wide image at 2×, but inspect the file rather than assuming this scale.
3. Set `--highlight "[x, y, width, height]"` for existing incorrect content. Use one outer frame around a continuous wrapped passage; never stack padded line boxes. Distinct regions need separate nonoverlapping frames. Use `--insertion-line "[x, y, width]"` for missing content.
4. The tool keeps full screenshot width and at least **1.5 source-image widths of vertical context** (1170px for a 780px-wide capture). Use `--region` to select the context window independently of the marker. All coordinates are original image pixels.
5. If a viewport screenshot cuts off the sentence, inspect and crop `full_page.png` instead. Measure its coordinates independently.
6. Save to an issue-specific filename and inspect the **generated** image. Read the highlighted words and compare them against this issue's `wrong_text` and description. If they do not match, reselect the source/coordinates.

```bash
# Example geometry only: locate and measure the actual issue first.
# Auto-crop context around the highlight; red frame stays INSIDE the image.
python3 tools/annotate_screenshot.py \
  --image .tmp/captures/$RUN_ID/ours/section_005.png \
  --output .tmp/captures/$RUN_ID/annotated/T1.png \
  --highlight "[20, 700, 740, 180]" \
  --context-padding 300
```

For a missing subheadline, use a full-page target capture and an insertion line;
measure the coordinates on that capture before running the command:

```bash
python3 tools/annotate_screenshot.py \
  --image .tmp/captures/$RUN_ID/ours_product/full_page.png \
  --output .tmp/captures/$RUN_ID/annotated/T6-insertion.png \
  --region "[0, 650, 780, 1280]" \
  --insertion-line "[30, 1305, 710]"
```

These example coordinates are illustrative, not reusable across funnels.
In `evidence_pairs`, optional `source_caption` and `target_caption` explain the
markers. See the evidence quality standards in the skill for alignment rules.

`--region`, when supplied, must contain all marks and meet the minimum context
height. The tool rejects missing marks, invalid/out-of-bounds coordinates, clipped
marks and a highlight equal to the whole crop. These geometry checks do **not**
establish that screenshot text or an insertion location matches the feedback;
the visual check is mandatory.

### 5. Generate Feedback Page

Before rendering, complete the instruction-headline pass for all new/revised
findings. Check the explicit `feedback` against the decided correction, every
affected location and the exact copy pairs. The renderer prioritizes `feedback`
over `description`; updating diagnosis alone does not update an existing headline.
Keep the detailed wording rules in the linked report-format contract.

For new Swedish reviews (policy version 3), the completion gate requires
`meta.swedish_offer_checks_file` with the complete button/state inventory, bound
source and clicked checkout evidence, and per-offer selection/price comparisons.
Uninspected buttons or checkout prices prevent completed delivery.

For new Dutch-market reviews, the completion gate also requires our indexed
`dutch_checkout` capture, all seven completed checks, full review/date and FAQ
inventories, guarantee observations, and visible/loaded payment-option evidence.
New capture policy metadata activates this gate even if report metadata omitted
the version. Do not use historical metadata to bypass current review scope.

The generator requires four distinct capture manifests (three for a custom funnel, whose competitor product page may be `blocked` with a reason), existing text/full-page/section screenshots, matching URLs, `reviewed` status for every captured page, and a valid page label on every issue. Finished reports refuse `capture_funnel.py --legacy` captures made on or after 2026-10-02 and any legacy capture in a current-policy report; legacy captures remain for diagnosis and republishing older reports. Indexed captures additionally require complete, hash-verified packets, all required checks bound to the current manifest, and completed guarantee/pricing cross-page checks. Missing product-page coverage blocks finished-report generation. These checks establish recorded coverage and evidence availability; they do not replace the actual visual/text review. Legacy reports retain their recorded historical scope without gaining new verification claims.

For work in progress only, add `--draft` to render a visibly labeled **DRAFT — incomplete or unverified review**. Drafts must not be delivered as finished reviews. Existing incomplete reports require real missing-page review before migration; never invent completion records.

```bash
python3 tools/generate_feedback_page.py \
  --issues-file .tmp/captures/$RUN_ID/issues.json \
  --output .tmp/captures/$RUN_ID/feedback.html \
  --title "Funnel Review: NL Skincare"
```

The standard generator and publisher both use the
[approved report format](../skills/funnel-comparison/references/report-format.md).
`tools/feedback_presentation.py` renders the finding data; shared CSS and controls
are in `tools/templates/funnel_review.css` and `funnel_review.js`. Do not rebuild
this design in a run-specific script or edit only the published HTML.

The heading shows product, country and fix count. Both pages and All Feedback
are selected initially. Whole issue panels use blue for replacements, purple for
image edits, red for missing content and orange for product selection/cart and
all checkout feedback, with white
inner cards. Literal copy edits get a compact target preview; missing/structural
content gets full labeled competitor/target comparisons. Supplied copy is kept
intact. COPY buttons and green Done markers follow the shared contract.

For multiple `evidence_pairs`, assign unique IDs and explicit
`replacements[].evidence_ids`. Keep all edits at their matching location, including
multiple edits per screenshot and edits repeated at several locations. Preserve
existing markers and IDs. Ambiguous mappings must fail rather than lose an edit.
Keep source-only missing-comments and target-only introduction exceptions; never
invent screenshots. For a cross-page finding retain its primary `page`, add
`pages`, and label every evidence pair with its actual `page`.

Checkout findings, including the required Dutch checks, appear under Product page
while retaining the Checkout label. A compact scope note preserves the recorded coverage;
the scope note lists only recorded checks and never implies transaction processing
was tested.
Owner decisions remain in private review records and are delivered only in chat
after the workflow. Never put them in the output/review page or its hidden HTML;
only confirmed fixes render. Preserve decision IDs, evidence and coverage refs.

Trace each finding's page label to the capture manifest and actual URL containing
the quoted text; do not classify a product-introduction block as a PDP simply
because it discusses the product. If an owner correction conflicts with the saved
capture, verify the live occurrence and clarify the intended block before changing
its label. Keep the exact URL and resolution in the private correction history.
Set the finding's `target_url` to this verified URL. The generator checks it against
the recorded review page so a conflicting page label cannot pass unnoticed.

No "fix" text is rendered — it's redundant when wrong/correct text is shown.

### 6. Verify and Deliver

First verify that all four coverage records are `reviewed` (custom funnel: three, plus the blocked competitor product page with its reason) and that the report was generated without `--draft`. If a required page is blocked or pending, report the incomplete scope and blocker instead of publishing a completed review.

Check `review_checks.json` for complete content, FAQ and interaction coverage, including the priority product-page items below. A captured but unopened FAQ answer or an unclicked button is untested, not passed.

Also require completed cross-page guarantee and pricing checks. Every contradiction must have an evidenced finding or an explicit owner-approved resolution; untested comparisons cannot be marked passed. The report generator's page-coverage validation does not automatically perform these comparisons.

Open the generated HTML and run the
[pre-publication QA checklist](../skills/funnel-comparison/SKILL.md#pre-publication-qa-checklist)
from the funnel-comparison skill at desktop and mobile widths.

Record the issue ID, source file, crop/highlight coordinates and the visual match-check result in `.tmp/captures/{run_id}/evidence_checks.json`. A failed or uninspected card blocks delivery; fix it first. Keep previous delivered files intact and generate a new local revision when correcting an existing report.

### 7. Publish and Deliver the Link

Feedback pages live on Render at `https://ad-translation.onrender.com/feedback/{slug}/`.
They are public without login, carry `noindex` and a sandbox header, and the replaced
version is kept in history. The `/feedback/` overview groups them by builder.
Prepare, check, then upload:

```bash
# 1. Render and stage the page, without uploading. Drafts are only ever staged.
.venv/bin/python tools/publish_feedback_page.py \
  --issues-file .tmp/captures/$RUN_ID/issues.json \
  --title "Funnel Review: NL Skincare" \
  --prepare-only

# 2. Open the returned site_dir/{slug}/index.html and complete step 6.

# 3. Upload that review to Render (needs FEEDBACK_UPLOAD_TOKEN).
.venv/bin/python tools/upload_feedback.py --site-dir .tmp/vercel/funnel-reviews/site --slug <slug>
```

`upload_feedback.py` checks the staged page against its receipt hash, refuses drafts
(`--allow-draft`) and refuses to replace a live page that is newer or of unknown age (`--force`,
for example after the dashboard published the same funnel the same day). Only deliver the link
when it reports the page as verified live. Open the live page and check images, layout and Copy
buttons before sending it.

**Naming.** Each review is named `[funnelbuilder name]-productname-country`, for example
`alex-gutflow-se`: lowercase, spaces/punctuation to hyphens, trademark symbols removed, accents
normalized (`José` → `jose`), the whole builder name kept. `funnel_id` is metadata, not the
public name. Resolve missing naming fields from the sheet; never fall back to a run ID. Two
funnels with the same builder, product and country share a URL: the newer review replaces the
older one (the old version stays in history).

**Overview.** `tools/feedback_dashboard.py` renders the builder-grouped overview (product,
country flags, fix count, publication date, open button). Builder colours come from
`config/funnel_builder_colors.json` (matched to the sheet's builder dropdown on 2026-10-01; not
a live sync). Counts are recorded findings, not a live count of open fixes. Missing historical
fields show as Unassigned/Not recorded. Republishing old feedback does not re-review the funnel.

In the final chat, separately give any outstanding owner decisions and the exact choice or
action needed, or say that none remain. Follow the canonical skill's chat-only rule; never add
these questions to the published review page.

**Staging folder.** `publish_feedback_page.py --prepare-only` stages pages in
`.tmp/vercel/funnel-reviews/site` (the folder name is historical). Always use
`--prepare-only`; without it the tool tries an old Vercel deploy this team no longer uses.

---

## Review Checklists

All review checklists, standing owner exclusions, cross-page consistency rules,
checkout offer fallback, mandatory Dutch checkout checks, button/interaction testing
and edge cases live in the
[funnel-comparison skill](../skills/funnel-comparison/SKILL.md). Read it before
step 2 and apply every applicable checklist during the review.

## Lessons Learned

These lessons come from the main project. Entries about the engine, the Render dashboard,
OpenRouter models or Vercel describe the hosted version and are context only here; the
capture, review and report lessons apply fully.

- 2026-10-09 (SE 265 OdorPaws, local run without the engine): The Milvino product page failed every
  capture with "Capture changed during screenshot". Cause: an FAQ "+ → ×" icon finishing its rotation
  moved glyph rects by 0.00002 px, and the before/after index digest compared raw floats. `capture_packet.py`
  now compares coordinates rounded to 0.1 CSS px (`layout_key`, regression test `tests/test_capture_layout_key.py`).
  Milvino FAQ job: `faq_selector: "div.milvo-clean-accordion-item"`, toggle `:scope > button.milvo-clean-accordion-question`,
  answer `:scope > .milvo-clean-accordion-answer`, freeze `.milvino-countdown-timer` and `.milvo-stock-dot-wrap`.
  An advertorial image wider than the screen (here x −252 to 643 px) widens the mobile layout viewport, which
  pushes a CSS-sticky bottom bar below the visible screen: the DOM candidate exists but a viewport screenshot shows
  no bar. Check the full-page PNG width (should be 780 px) and the candidate's y against 844 before passing
  `sticky_cta`. Halsoland PDP: "Gilla/Svara" under the first review linked to herabella.com/climacool (another
  funnel's leftover); the PDP "BESTÄLL NU" buttons are `div.btn` (not in the control inventory) and must be
  clicked separately. When our product page is the generic Halsoland template, ask the owner (reviewed on its own here).

- 2026-10-08 (NLBE 247 Tinniva, dashboard runs hung): Three runs on 2026-10-07 sat 17–50 minutes in
  the button test of our Gezondbenelux advertorial (`controls:ours:advertorial`) until a deploy killed
  them; memory (1.5 of 2 GB) and CPU (~40%) stayed flat, nothing crashed. The same test takes 35 s on
  the Mac, also with the server's Playwright 1.62, so the hang only happens on Render and is not yet
  explained. Those runs predate the per-button/per-page time limits and stack dumps (deployed 16:16
  that day). Added: the dashboard stops a review after 30 quiet minutes. Also fixed: Gezondbenelux
  CTAs (`href="#next-step"`) leave the page by script a moment after the click; the tester read the
  page while it was being replaced and reported 11 of 26 working buttons as "not tested". A page that
  is leaving now counts as navigated. If a review hangs again, read its `stacks.log` first.
  The next dashboard run finished all button tests in 2 minutes and the whole review in 18, but ended
  *blocked*: the engine passes no FAQ selector, so capture only knew native `<details>`. Our
  Gezondbenelux PDP uses the site builder's `div.faq` rows (`.faq-header` toggles, `active` = open), so
  none of its 14 answers were captured; on the competitor's Shopify PDP the first `<details>` was the
  header menu drawer, whose click timed out and failed the capture. `capture_packet.py` now skips
  `<details>` in the site header/nav and, without a job selector, also tries the site-builder FAQ
  template. The competitor's three Shopify accordions really are empty (titles only).

- 2026-10-07 (full audit): A read-only review of the engine, dashboard and report tools found
  the run-recovery promises were not true and several crashes. Fixed with regression tests:
  - Resume: captures in one run folder are reused at any age (before, a resume after 30 minutes
    recaptured and re-paid every step); the dashboard resumes an interrupted review into its old
    engine folder and re-queues it after a deploy; multi-call steps checkpoint per call.
  - Crashes: browser timeouts, empty sheet URL cells and unexpected errors end as `failed` with
    the step named; non-ISO checkout review dates are parsed instead of failing the run.
  - Wrong findings: the Dutch checkout must really be a checkout; Swedish checkout detection
    covers more URL shapes and the page text; control-tester errors are "not tested", not fixes.
  - Money: the cost cap is checked again just before each call; a cap stop is never hidden by
    another error; models come only from `OR_MODEL_FR_*` (no built-in fallbacks).
  - Dashboard: status keeps the funnel name (the duplicate check was blind), one lock guards the
    queue and starts, a reused PID after a deploy no longer looks alive, queuing works while a
    review runs, failed starts are shown with their reason.
  - Gate: legacy captures cannot finish a current review; owner questions closing a check must
    exist; uploads check hashes, refuse drafts and refuse to overwrite a newer live page.
  - Checkout: every non-Swedish market now tries our checkout for the price/offer check (required
    only for Dutch markets), and the competitor checkout is captured best effort. Checkouts that
    are reviewed for price/offer only are not control-tested.
  Run the tests with the commands in `docs/funnel-review-pipeline.md` (`tests/` is not a package,
  so `unittest discover -s tests` fails).

- 2026-10-07 (funnel engine on Render): The engine evaluation on saved reviews showed that the
  first misses were never model judgment. Steps did not get the information a single reviewer
  has: whole-page context, every screenshot, the checkout prices, the funnel's market. They also
  dropped findings silently (chained model steps compound losses, as CLAUDE.md warns). Fixes:
  - page-wide screens and consistency passes;
  - Python-detected missing content and rule-decided findings that verify cannot drop;
  - a crop check that flags instead of deleting;
  - funnel facts given to every step.
  The remaining gap was noticing subtle translation errors: a review task, so the find step now
  uses a strong model (`anthropic/claude-sonnet-5.5`) with a short look-for list instead of 57k
  characters of rules. Owner rules added to the skill: deliberate localizations, words running
  together, missing content always reported, foreign currency per market. A 1x price conflict
  with no evidence for either number asks for the approved price instead of guessing.

- 2026-10-07 (tool fixes): The generator now supports custom funnels
  (`meta.funnel_type: "custom"` + `meta.owner_scope`): the competitor product
  page may be `status: "blocked"` with a `blocker` reason, and the report's scope
  line says the product page was reviewed against our advertorial instead of
  claiming a 4-page comparison. Single-page capture gained `--faq-answer-selector`
  and repeatable `--freeze-selector`. Publish receipts are now per review
  (`deployments/{slug}.json`), fixing the shared-receipt overwrite from SE 240;
  `--verify-only` falls back to the old `deployment.json` for earlier reviews.

- 2026-10-06 (NLBE 235 MagnesiumFreeze): "First in the queue" has no sheet column;
  the owner picked the first unreviewed row in sheet order (status Ready / Ready for
  Revision without a staged review). The competitor had no real product page, so the
  owner scoped our custom PDP to alignment with our advertorial, translation,
  cross-page consistency and conversion-killing bugs (no source-completeness
  pairing); ask about this when a competitor's second URL is not a real PDP. The
  competitor CTA went to a tracking redirect returning 400; the sheet's second URL
  stood in. A lazy image inside a closed native `<details>` FAQ has width but no
  visible box and never loads, which stalled capture; `capture_packet.py` readiness
  now skips images that fail `checkVisibility()` (regression test added). The report
  CSS now wraps long URLs in evidence notes (mobile overflow). Gezondbenelux again:
  checkout reviews link to /upsell, stale review dates, and the AI translation left
  meta phrases like "volgens de oorspronkelijke advertentietekst" in the copy.

- 2026-10-02 (NLBE 248 Arthrovia): The competitor product URL served two random
  A/B variants (countdown + custom inline-display button accordions vs native
  `<details>`). One job can handle both: `faq_selector: "details, div:has(> button[data-dc-tpl])"`,
  `faq_toggle_selector: ":scope > button"`, `faq_answer_selector: ":scope > button + div"`;
  `freeze_selectors` that match nothing are harmless. Retesting source controls
  later may hit the other variant, so record those as source-side not applicable.
  Our PDP was the generic Gezondbenelux Health template, not a translation; the
  owner chose to accept it for that run and review it on its own (no
  source-completeness findings). Ask when this happens again. Gezondbenelux
  pages again had Like/Comment links to shop2cen.com/dermashield and checkout
  review elements linking to /upsell. PDP FAQ expanded-state captures can be
  covered by the sticky “HERFSTDEAL” banner, so use the collapsed question on
  the full page as evidence.

- 2026-10-02 (NLBE 250 FlexiCore): The heilkompass-magazin.de competitor uses
  accordions that only toggle the answer's inline `display` (no aria/class), so
  `capture_packet.py` now accepts `faq_answer_selector` (expanded = answer visible).
  Observed job: `faq_selector: "div:has(> button > span.sc-interp)"`,
  `faq_toggle_selector: ":scope > button"`, `faq_answer_selector: ":scope > button + div"`.
  Its product page timed out once on a lazy image; a solo retry with `--budget 300`
  succeeded (run long captures in the background; one foreground run was killed, exit 137).
  Owner decision for this funnel: keep our generic Gezondbenelux PDP template when it does
  not follow the competitor's page; flag only real errors inside it. Gezondbenelux again
  showed checkout review links to /upsell and 404 inline product/comment links, so check
  every advertorial link destination, not just the CTAs.

- 2026-10-02 (SE 251 FlexiCore): The competitor product page stalled capture
  with 2 "pending" images: lazy carousel slides that sit off-screen to the side
  never load, but the readiness check only tested vertical position.
  `capture_packet.py` now ignores images that are horizontally out of view (tests
  pass). The heilkompass-magazin product page serves two A/B variants (chevron
  `<details>` FAQ vs "+" accordions), so a custom FAQ selector can match 0 rows.
  Record which variant was captured and capture its expanded FAQs in a targeted
  session after reloading until the same variant appears. Halsoland checkout
  summaries collapse on mobile; add
  `faq_selector: "body"` + the "Ordersammanfattning/Totalpris" toggle (as in
  SE 242) to read the selected bundle. A Halsoland product template can contain
  an empty `sticky_show_after` section (0 px tall): DOM candidates exist but no
  bar is visible, so judge the screenshots, not the candidates.

- 2026-10-02 (SE 240 OsteoShield): Halsoland product pages render hidden desktop
  copies of each offer button, so `a[href*="/cart/…"]` matches two elements and
  `offer_handoff` rejects it. Use the visible mobile container selector (e.g.
  `.el-465416 a.btn`). Several sessions publish to the same staging site and share
  `.tmp/vercel/funnel-reviews/deployment.json`, so another run can overwrite the
  receipt (a `--verify-only` then fails with "does not match"). Re-running
  `--prepare-only` changes the content hash (timestamped), so after that only a
  full publish can verify; one transient `HTTP Error 404` during deploy succeeded
  on a plain retry. The publisher itself was not changed.

- 2026-10-02 (NLBE 241 Vigorix): `freeze_selectors` failed on the serraphea.com
  countdown because its script updates spans by `id` (`#sec`), and the frozen clone
  kept those ids. The freeze now moves ids to `data-frozen-id` (styles are inlined
  first, so the frame looks the same). If a frozen capture still drifts, diff two
  `capture_index.js` snapshots to find the changing block. The checkout phone prefix
  is set by IP geolocation (the reviewer's IP showed +66/TH); it is not funnel
  configuration. Gezondbenelux checkouts repeat the NLBE 236 bugs (1x total €29,85,
  review images linking to /upsell, stale review dates), so check them every time.

- 2026-10-02: CalmSoothe SE 235 D01–D03 were review-judgment decisions, not
  capture or rendering failures. The owner dismissed the added-statistics approval
  question and missing supply-label question for this funnel, and clarified that
  article-story names are the identity reference. Apply the scoped decisions and
  story-identity check in the canonical funnel-comparison skill before generating
  questions. A matching testimonial's isolated name must not displace the narrative
  name. Preserve existing related corrections and stable IDs; keep superseded
  answers in private revision history. The existing tools already support removing
  decisions and converting a resolved decision into an evidenced finding.

- 2026-10-02 (SE 235 CalmSoothe): Our Halsoland product page has a live countdown
  timer, so every capture failed with "Capture changed during screenshot". Added a
  `freeze_selectors` job option (e.g. `[".timer-container"]`) that swaps the ticking
  widget for a static clone; frozen elements are recorded in the manifest. Offer
  cart links (`target=_blank`) open their checkout tab after ~1.2 s, but the handoff
  waited only 1 s and silently saved the product page as "checkout". The tool
  now uses the owner's **3-second** wait (replacing the initial 10-second fix),
  and a handoff that stays on the source page fails loudly. Countdown timers are
  excluded from review checks by the comparison skill; freezing is only capture
  preparation when needed, not a timer behavior test. Always
  read each checkout capture's text before trusting it. Shopify checkout never
  reaches `networkidle`; wait for `load` when expanding the order summary.

- 2026-10-02: The approved interactive design is now the standard generator and
  publisher output. Follow the report-format reference, including intact supplied
  copy and compact target previews for literal edits. This supersedes historical
  universal full-size screenshot and automatic token-diff presentation rules.

- 2026-10-02: Missing-comment screenshots should be compact and side by side.
  Root cause: the renderer stacked every source-only evidence group as a full row.
  Added a responsive gallery for `missing_comments` with image enlargement; the
  skill now requires that check tag and preserves discussion order and full crops.

- 2026-10-02: Visual feedback calibration: keep broken purchase actions, wrong
  product imagery, advertorial review presentation, benefits formatting, offer
  visuals and undersized headings. Combine offer image/layout defects into one
  point with one marked offer screenshot. Exclude product-review presentation,
  blurry review portraits and minor treatment/ingredient card styling. Narrow
  heading-format feedback to unclear or substantial mismatches. Body bolding keeps
  its existing threshold, but delivery is one short note plus one example screenshot.
  Full comparisons stay private. Root cause was over-detailed skill requirements;
  inspected annotator/renderer already support multiple marks, one image, concise
  instructions and shared page filters, so no tool change is required.

- 2026-10-02: Heading spelling, grammar and meaning mistakes always receive
  feedback, including section and offer-card headings. This overrides the earlier
  suggestion to drop grammar-only parts of T24; restore both T24 corrections and
  the T16 offer-heading spelling finding. Skill change required; renderer inspected
  and already supports these evidenced corrections, so no tool change is needed.

- 2026-10-02: Owner approved the translation importance threshold: keep material
  meaning/trust/offer problems; omit readable grammatical polish and low-impact
  inconsistencies. Consolidate repeated pronoun shifts when they disrupt the
  passage. The canonical skill defines the threshold and required completeness
  exceptions. This is a review judgment, not a renderer keyword filter; visual
  checks retain their existing scope.

- 2026-10-02: Owner calibration: the first product testimonial is critical; missing
  paragraphs always receive feedback. Accept Swedish whole-krona unit prices
  such as 189 kr for the 565 kr three-bottle bundle. Never issue discount-percentage
  calculation/rounding feedback. Omit the competitor's Amazon/eBay availability
  notice. Missing comments need source screenshots and one short restoration
  instruction, without translated copy for each comment. Rules live in the
  funnel-comparison skill. Tool assessment: add source-only evidence panels for
  this simpler output and reject explicitly classified discount-math findings;
  preserve other price checks and paired evidence.

- 2026-10-02: For every owner correction, inspect both the relevant tool and the canonical skill, then record whether the fix belongs in one or both. The page selector required a renderer change plus a report-contract update. Name tolerance, missing paragraphs/comments, and the scoped supply-duration exception change review judgment in `skills/funnel-comparison/SKILL.md`; the existing renderer already supports omitted decisions, insertion evidence, full replacement copy, and multiple evidence groups. Do not infer these semantic judgments from names or description keywords in the renderer.

- 2026-10-02: Owner resolved the GutFlow review's four questions. Native-looking
  reviewer/comment names are accepted; only obvious mistakes receive feedback.
  Missing source paragraphs and missing comments/replies are direct findings,
  never routine questions about intentional omission. Missing months-of-supply
  labels are accepted in the reviewed Beauty template, which does not use them;
  this exception does not apply to quantities, prices or incorrect visible labels.
  The canonical checks and boundaries are in the funnel-comparison skill.

- 2026-10-01: The root is now a builder-grouped dashboard, automatically rebuilt
  from review receipts. Restore older reports only with actual builder/country
  metadata and valid evidence mappings. Numbered submarkers need explicit
  screenshot IDs; check the image text rather than mapping solely by a prefix.

- 2026-10-01: Owner requires builder-product-country naming for review URLs and
  index entries. Resolve the builder, product/brand and country from the sheet;
  missing fields block publishing instead of falling back to funnel/run IDs.
  The resolver must reuse the saved OAuth token's granted scopes; substituting
  `spreadsheets.readonly` during refresh can fail with `invalid_scope` for the
  shared Sheets/Drive token. Its operations remain read-only.
  A newly deployed path can briefly return 404 while the custom domain updates;
  recheck the saved deployment with `--verify-only` before attempting a redeploy.

- 2026-10-01: Single-project publishing must preserve sibling review directories,
  validate every staged report, exclude nested receipts and retain a deployment
  receipt before URL discovery/verification. Custom-domain verification must use
  the report path. The five legacy review projects were removed; their old URLs
  no longer work. Keep historical review scope unchanged when republishing.

- 2026-10-01: Owner explicitly excluded button-text feedback from every future
  review. Preserve functional button checks; never turn their labels into copy
  corrections, including through price/guarantee consistency feedback.

- 2026-10-01: Build reusable capture packets and occurrence indexes once, then batch annotations by source. Verify stable capture geometry and growing page height; reject ambiguous occurrences; bind resume to configuration/content/decision hashes; cap independent capture concurrency at two isolated contexts. Preserve every semantic/visual check and the existing publisher. Static full-page tiles are not evidence of sticky behavior. See the pipeline guide and regression fixtures before changing these guarantees.

- 2026-09-30: Clear localization carryovers should be actionable corrections, not owner questions. Use an owner-approved local counterpart or the equivalent reference already established in our funnel. Match the role (e.g. dispatch city to dispatch city), preserve stable IDs when converting a decision, and scope concrete place-name mappings to their funnel.
- 2026-09-30: Owner requires guarantee duration to follow the majority of our own advertorial/product mentions: 90 wins over isolated 60, and 60 wins over isolated 90. Competitor guarantees do not determine the answer. Count distinct locations; ties/incomplete evidence stay unresolved. Footer email-link feedback, including V01, is excluded from future runs.
- 2026-09-30: Owner resolved D03: review-count checking is not useful feedback and is excluded for future runs. Owner resolved D02: offers may live on the product page or checkout; follow the CTA and verify checkout prices and presentation when the product page defers the offer. This supersedes the earlier checkout exclusion below.
- 2026-09-30: Owner explicitly requires guarantee and pricing consistency across the advertorial and product page. Review all occurrences and record separate cross-page results; individual page reviews are insufficient. Compare equivalent offers and distinguish source conflicts from localization errors.

- 2026-09-30: A travel-wording finding displayed a nearby research-cost paragraph. Section matching and estimated crop coordinates were insufficient. Each issue now requires an exact visual text match before and after annotation and again in the rendered card.
- 2026-09-30: Cropping and highlighting must be independent. Keep funnel context, draw the frame around the issue inside it, and display the image up to 520px wide. This supersedes the earlier 280px thumbnail and crop-border guidance recorded in feedback rounds 01–02.

- 2026-09-30: Conditional next-page instructions allowed an advertorial-only report. Both advertorials and both product pages remain mandatory, with explicit coverage records and a finished-report generation gate. The initial checkout exclusion was later narrowed by the D02 decision above.
- 2026-09-30: Owner added explicit content-completeness, product headline/subheadline/bullets, price/discount, first-testimonial, age/name, bold-emphasis, offer-presentation, exact FAQ and button checks. Record each priority element, expanded FAQ and button instance/state rather than relying on a generic pass. The later D02 decision extends price/offer verification to checkout when needed.

- 2026-10-02 (sticky CTA correction): Owner requires a mobile bottom sticky CTA on
  both target stages in every funnel. A fixed-only DOM search missed a CSS-sticky
  source component; one-offset inspection and a generic interaction pass hid the
  missing target components. The canonical skill now states the presence rule,
  capture_packet retains six down/up viewport states and fixed/sticky candidates,
  and review_coverage requires a separate presence/behavior result. Missing target
  CTAs cannot pass; normal footer buttons and fixed headers do not qualify. The
  existing renderer already supports the correction; no presentation change needed.

- 2026-10-02 (owner-decision delivery correction): Owner decisions belong only in
  chat after the workflow, never in the output/review page. The renderer previously
  appended them as an explicit section. It now renders confirmed issues only;
  private decisions and their coverage references remain intact. Regression checks
  cover absent decision content/evidence, retained confirmed findings and filters.

- 2026-10-02 (GIF branding correction): For brand-name feedback inside a GIF,
  the canonical skill requires the owner's exact conditional skip note. Store it
  in `important_note`; the standard renderer shows it prominently above the
  finding's headline. A still frame does not prove that the moving product can be
  edited. The exception is conditional and does not exempt static branding edits.

- 2026-10-02 (overlapping annotation correction): T06 exposed a locator defect:
  each wrapped line got independent padding, causing intersecting red/green
  strokes through the words. The locator now groups continuous passages before
  padding; the annotator rejects overlapping/touching boxes. Visual QA must check
  legibility at report size as well as exact evidence identity. Regenerate affected
  evidence from clean captures, preserving original delivered revisions.

- 2026-10-02 (competitor gift exclusion): A free gift offered only by the
  competitor is an accepted offer difference, not missing-content feedback or an
  owner question. Apply the canonical standing exclusion during offer review;
  retain checks on gifts actually promised by our own funnel. NLBE 243 T14 was
  removed with its ID preserved in correction history and coverage refs updated.
