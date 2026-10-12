# Funnel review output contract

This is the default HTML design approved on 2026-10-02. Apply it to every new
review. The workflow prepares findings; `tools/generate_feedback_page.py` renders
them through `tools/feedback_presentation.py` and `tools/templates/funnel_review.*`.
Publishing calls this same generator. Do not create a separate one-off renderer.

## Write the feedback

- Keep stable issue IDs, evidence markers, issue order and every accepted edit.
- For every new or deliberately rewritten finding, write an explicit `feedback`
  headline after deciding the correction. This is the large, bold builder
  instruction. Keep diagnosis/provenance in `description` or private notes.
  Existing reports may fall back to `description`; that compatibility path is
  not a substitute for the headline-writing pass on new work.
- Set `feedback_type` on each finding. This is separate from the review's existing
  `category: translation|visual` and `check`, which retain their judgment meaning.

| feedback_type | Whole issue background | Use |
| --- | --- | --- |
| `find_replace` | Light blue | Literal text replacement |
| `image_edit` | Light purple | Editing/replacing an image |
| `missing_content` | Light red | Missing/incomplete content or a structural comparison |
| `price_offer` | Light orange | Product/offer selection, cart, and ALL checkout feedback |

Orange is scoped to selecting the product/variant/bundle for the cart or checkout,
and **all feedback inside checkout**, including reviews, dates, names, FAQs,
guarantees, image edits and payment-option visibility. This work-area rule takes
precedence over the mechanical edit type. A price or number in unrelated editorial
copy (for example an advertorial's annual treatment-cost comparison) is ordinary
find-and-replace feedback, not orange just because it mentions money.

Set `offer_context: product_selection|cart|checkout` for offer-area work outside
checkout, or `offer_context: editorial` for unrelated price wording. Checkout page
findings are always classified orange. Advertorial `price_offer` findings need an
explicit product-selection/cart context; otherwise they render as find-and-replace.
Keep image/missing-content screenshot layouts where needed with pair
`display: comparison`; category color does not remove evidence requirements.
For other visual/layout findings use `missing_content` with `display: comparison`
when comparing structure, or `image_edit` for a marked visual edit. The action
heading explains the actual task. Never classify by a specific issue ID.
Legacy JSON has a conservative fallback; do not rely on it for new reviews.

## Instruction headlines

For brand-name feedback inside a GIF, set the finding's `important_note` to this
exact text:

> NOTE: IF THIS IS A MOVING PRODUCT INSIDE A VIDEO YOU CAN'T EDIT - THEN SKIP THIS FEEDBACK

The renderer displays this as a prominent note at the top of the affected finding,
before its headline and evidence cards. Do not bury it in `description` or repeat
it as ordinary card copy. This condition takes precedence over the edit instruction.
Use it for the animated-media case defined in the canonical skill, not every
static image correction. The renderer displays explicit `important_note` text;
it must not guess media type or editability from an issue ID or wording.

Write the instruction as a small task the builder can execute, using **action +
target/location + intended result**. Prefer one or two direct sentences. This is
an editorial pass over already-decided findings, not a new review or translation.

- Lead with the repair: “Use”, “Replace”, “Add”, “Restore”, “Remove”, “Move” or
  another concrete action. State the chosen name, wording, value or visual result
  when it is needed to understand the task. “Fix the translation” is insufficient.
- Name the affected role/component and its scope: “this author in the byline,
  introduction and signature”, “the one-bottle checkout price”, or “FAQ 8's
  treatment range”. Do not make the builder infer the scope from an error analysis.
  Use card locations for longer inventories; the headline must still describe
  the entire finding without implying an unsupported global replacement.
- Add a short “Keep …” sentence only when it prevents a plausible related
  mistake, such as changing the guarantee while correcting treatment duration,
  or renaming a different person. Do not append generic preservation boilerplate
  to every finding. Preserve correct related content regardless of whether it is
  mentioned in the headline.
- Keep explanations of mistranslated words, arithmetic and source comparisons
  in the diagnostic record. Include a brief reason in the visible instruction
  only when the builder needs it to choose or implement the correct action.
  Essential location-specific context belongs in `evidence_pairs[].note` or
  `instruction`; `description` is not separately shown when `feedback` is present.
- Give the exact pasteable text in the existing FIND/REPLACE blocks. The headline
  states the task; it need not repeat a whole replacement paragraph or explain
  target-language grammar. Retain the established exceptions where the builder
  supplies the translation, such as missing comments and whole-testimonial repair.
- Preserve all approved actions, evidence locations, copy pairs and factual
  limits when shortening. Do not turn “check the configured price” into a claim
  that an incorrect payment was observed. Do not choose unresolved identities,
  prices or claims merely to produce a decisive headline; keep real owner
  questions in private records and deliver them only in chat. A heading rewrite
  does not authorize a new content change.
- If `feedback` already exists, revise that field explicitly. Editing only
  `description` leaves the old visible headline in place because the renderer
  gives `feedback` precedence. Keep the two fields consistent in substance.

Examples (illustrative identities and values, not defaults for another funnel):

| Diagnostic wording | Builder instruction |
| --- | --- |
| “The author has different names in three places.” | “Use Dr. Eva de Vries for this author in the byline, introduction and signature. Keep the colleague's existing reference to Eva.” |
| “The phrase says the patient is nine years old; the source means nine years of symptoms.” | “Change the story introduction to say nine years of symptoms.” |
| “The FAQ shortens the treatment range to 60 days.” | “Restore the 60–90-day treatment range in FAQ 8. Keep the 60-day money-back guarantee unchanged.” |
| “The checkout and product page show different one-bottle prices.” | “Set the one-bottle checkout price to the approved €29,95, matching the product page.” |

Before generation, read only each `feedback` headline and ask: **Can the builder
tell what to do, where, and what the result should be without interpreting the
diagnosis?** Then compare it with every evidence card and replacement. Rewrite
unclear headlines before rendering; the tool displays supplied wording and does
not judge writing quality. Do not enforce an arbitrary word count or automatically
rewrite findings with keyword substitutions.

Group locations only when they belong to the same feedback category. A reviewer-name
correction on the product page belongs in blue Find & replace; the corresponding
checkout correction belongs in orange. Give them separate findings with consistent
replacement names instead of hiding the product-page edits inside a checkout-led
orange finding. When splitting a delivered finding, retain its original ID for one
part, assign a new unused ID to the other, and record the moved edits privately.
Keep genuine offer-versus-checkout comparisons together in orange.

## Evidence and copy

- Each `evidence_pairs` entry gets a unique `id`, its existing `marker` (A/B/C), a
  short `location` (e.g. “Byline · top of article”), its actual `page`, and genuine
  annotated screenshots. Preserve nonconsecutive markers from accepted reports.
- Assign replacements explicitly using `replacements[].evidence_ids`. Several
  edits at one location share one card/screenshot. An edit affecting several
  locations lists each ID. Unknown or ambiguous mappings block generation.
- Supply literal complete FIND and REPLACE values, with no ellipses or paraphrases.
  Choose a meaningful phrase or a complete sentence/passage using the skill's copy
  rules. The renderer preserves supplied strings exactly; it never splits a
  supplied sentence into word-by-word edits. `copy_scope` and its reason remain
  authoring/provenance metadata, not permission for the renderer to rewrite copy.
- Literal replacements show **only our funnel's compact thumbnail**, with a clear
  **Click here to preview** button opening the full screenshot. Source evidence can
  stay in JSON without appearing in this layout.
- Missing/incomplete/structural comparisons show full competitor and target
  screenshots already open: side by side on desktop, stacked on mobile. Set
  `display: comparison` on a pair if another category also needs this evidence.
  Keep both genuine images for missing content, including the insertion marker.
  Existing missing-comments source-only and target-only introduction exceptions
  remain valid; do not invent a counterpart to fill a column.
- Banner text is large, centered, uppercase **COMPETITOR** / **OUR FUNNEL**. The
  competitor banner/border is grey; our funnel banner/border is near black.
  For an explicit comparison within our own funnel (offer versus checkout), use
  `source_label: OUR OFFER` / `target_label: OUR CHECKOUT` so neither image is
  falsely attributed to the competitor. The normal comparison defaults stay intact.
- Missing-content additions have empty FIND and full insertion copy. Show the
  copy in a light-red box with a black border, no “Add this text/bullet” label,
  and vertically centered text and COPY button. Include the precise insertion
  location in the heading or `evidence_pairs[].note`.
- FIND stays light red and REPLACE stays light green, labeled **1. Find this** and
  **2. Replace with this**. Image copy can say “Text in the image” / “New image text”.
  Deletions show a delete instruction, never an empty replacement COPY button.
- Use optional `note` or `instruction` for necessary location-specific context.
  When adding an explicit pair `location`, move any essential legacy
  `replacements[].location` detail into that note. The new card does not repeat
  old location hints below its location heading. Without an explicit card
  location, legacy replacement-location hints are retained. Do not put essential
  placement details only in obsolete `action` fields.

## Navigation and controls

- Heading: **Product name · country · N fixes to be done**. Use `meta.brand_name`
  and `meta.country`. Count confirmed findings, excluding owner decisions.
- Top links: **Competitor funnel** and **Our funnel**, using the recorded entry URLs.
- Page selector: **Both pages** first/default, **Advertorial**, **Product page**.
  Checkout findings, including the mandatory Dutch checkout checks, appear under
  Product page and retain their Checkout label. The review contract determines scope.
- Category selector: **All Feedback** first/default, followed by the four types.
  The purple `image_edit` tab is labeled **Edit image / section**.
  Filters combine; unavailable categories are disabled. For cross-page findings,
  set `pages` on the finding and `page` on each pair, so filtering also hides
  evidence and instructions for the other page. Owner questions are chat-only.
- The whole issue is colored; inner cards and page background are white. Letter,
  letter outline, preview borders/button and Done outline are neutral black/grey.
- Done changes the letter into a white checkmark inside a filled green square and
  updates the issue progress bar. Unchecking restores the original letter.
- Both copy buttons start white with uppercase **COPY**. Successful copy shows a
  blue **Copied ✓** state for 2.5 seconds, then restores white COPY. Copy failures
  select the text for manual copying; never claim success without copying.

## Owner decisions

Render only confirmed `issues`. Retain `decisions` privately for coverage and
follow-up, but never embed their questions, evidence, cards or data in the output
page, including hidden HTML. After the workflow finishes, deliver outstanding
owner decisions in chat with the required choice/action, or state that none remain.
Preserve their stable IDs; a resolved decision converted into a confirmed finding
still renders normally. Do not weaken coverage gates to omit this section.

## Open the correct location

Use recorded target URLs, never guessed builder routes. Add `target_anchor` to an
evidence pair only after verifying that exact visible text at the desired location.
For an expanded FAQ answer, use the visible question. For an image or insertion,
use a nearby visible heading. For duplicate text use unique nearby text in the
same block; do not fabricate context spanning unrelated blocks. Optional
`open_hint` can explain opening an FAQ or selecting an offer.

The generator creates text-fragment links (`#:~:text=`), with properly encoded
text. If no explicit anchor exists, it uses FIND only when uniquely present in the
saved page text; otherwise it opens the recorded page. A text-fragment link does
not select an offer, open a builder editor or guarantee pixel-perfect scrolling:
hidden content and lazy-loaded images can affect its position. Test the resulting
links in a browser; keep manual location context in the screenshot.

## Verify before delivery

Generate using the standard command and inspect desktop and mobile output. Check
all issue IDs, evidence markers, exact copy values and evidence mappings against
the input. Test both selectors together, COPY/reset/failure, Done/uncheck, preview
open/close and the funnel/location links. Confirm comparisons are already open,
addition text/buttons are centered, and no card overflows at 320–390px widths.
Verify that each page's corrections appear under their intended category filter;
presence under All Feedback alone does not establish that the grouping is clear.
Keep existing evidence, draft, coverage and standing-exclusion gates. Formatting
must not silently remove findings or introduce new review judgments.
