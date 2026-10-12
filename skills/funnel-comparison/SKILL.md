---
name: funnel-comparison
description: Checklists and editorial rules for comparing a competitor funnel page against our localized version. Covers translation, content completeness, product-page elements, visual issues, cross-page consistency, checkout offer fallback, button/interaction testing, standing exclusions, copy formatting, evidence quality and pre-publication QA.
---

# Funnel Comparison

Read this skill before reviewing any page pair. Apply every applicable checklist
top-to-bottom on each page, then complete the cross-page checks after both stages
are reviewed. The workflow owns execution order, capture, evidence, issue format
and delivery; this skill owns what to check and what passes.

## Owner Decisions Are Chat-Only

Keep unresolved owner decisions in the private review records (`decisions`), with
their IDs and evidence intact. After running the workflow, give any outstanding
owner decisions only in the chat, including the specific choice or action needed.
Never include them in the output/review page, cards, appendices or hidden HTML.
The delivered report contains confirmed fixes only. Do not convert uncertainty
into a finding merely to display it, remove coverage references, or mark an
unverified check as passed. Standing exclusions still apply to chat questions.

## Using Prepared Comparison Facts

When continuing or revising a known run, first read its private correction records
and any final owner-approved disposition matrix beside that revision. Apply the
latest explicit owner decisions before these default checks; a scoped exclusion
does not become a universal rule. A final accepted matrix supersedes earlier
tentative recommendations for that run, while preserving accepted shared rules
for future reviews. Keep original delivered findings immutable and retain their
IDs. This is a reviewer input step, not an automatic renderer lookup: pass the
resolved findings explicitly when an actual report revision is authorized.

The comparison packet is an inspection aid, not a completed review. Confirm
semantic matches yourself; identical text and similar reading positions can point
to the wrong slot. Allow split/merged paragraphs, explicitly account for unmatched
content, and map each expanded FAQ separately. Check the actual first visible
testimonial before following a suggested quote match elsewhere on the page.

Supply component roles appropriate to the page: `editorial_headlines`,
`body_emphasis`, `callout_panels`, and `testimonials`; product pages also need
`first_testimonial`, `offer_cards`, and `offer_headings`. Add `doctor_verified`
only when the template context establishes that requirement below. These roles
make priority checks easy to find; they do not replace the remaining checklists.
Record role assignments in the agent alignment, with the observed slot/location
in the reason. Keep the doctor block and customer testimonial as separate mappings.
For SE + Health, record the intentional first-review-to-doctor-recommendation
substitution described below instead of treating it as unmatched missing content.

Compare captured style/ancestor facts against the screenshots: a style difference
is not automatically a defect, and absent attributes in older indexes are unknown.
Inline background/underline may belong to an ancestor; card geometry may belong to
an outer container. Apply the existing body-bold tolerance only after the complete
semantic inventory; DOM token counts and candidate matches are not its denominator.
Save exact evidence refs with each finding while reviewing. Full-card framing and
missing-element placement still need visual verification of the intended component.

## Standing Owner Exclusions

These exclusions override all checklists below. Do not include these in feedback:

- **Competitor-only free gifts** — A free gift included in the competitor's offer
  but absent from our offer is an accepted offer difference. Do not flag its
  absence, require adding it to our bundle/order summary, or raise an owner
  question about matching it. This overrides source-completeness and offer-parity
  checks for that gift. If our own funnel explicitly promises a gift, consistency
  between our promise and our checkout remains in scope; do not invent a promise.
- **Countdown timers** — Skip checking the timer's displayed time, labels,
  ticking, reset and expiry behavior. Do not create timer findings or owner
  questions, or wait for a countdown to finish. If its movement prevents a stable
  screenshot, use the capture tool's existing `freeze_selectors` option on the
  observed timer only. This is capture preparation, not a timer check or a live
  page edit. Keep adjacent offer copy, prices and purchase-link functionality
  under their normal rules; do not freeze the whole offer or checkout button.
- **Final CTA section** — Do not give feedback or owner questions on the final
  closing CTA/offer section, except the wrong-product template leftovers below.
  This is a section-wide exception, not just the button
  label: exclude its introduction, headline, benefit bullets, support promises,
  guarantee/shipping summary wording, presentation and section-specific controls.
  **Missing content is always reported** (owner rule, 2026-10-07): a section,
  paragraph, bullet or element the competitor has and we lack is a finding even
  when it sits just before or inside the closing offer, such as an urgency block
  ("Every week without acting…") before the last offer. The exception covers how the
  final CTA section is worded and presented, never what is missing.
  Identify its boundaries by component role; do not exclude unrelated FAQs,
  editorial paragraphs or other sections merely because they appear nearby or
  after it. This does not exempt the separate checkout, earlier hero benefits or
  other offer components. Record the section boundary and excluded candidate
  findings privately before delivery. Do not repackage an excluded final-CTA
  finding as a cross-page inconsistency or owner decision; independently evidenced
  defects in an eligible section retain their own scope.
- **Wrong-product template leftovers** — Always flag unmistakable remnants of a
  different product in non-button text or images, including inside the final
  CTA/offer section. A sleep-product headline on a joint-care product or a pillow
  question in its FAQ needs a direct, product-relevant correction. This narrow
  exception does not reopen final-section omissions, styling, offer promises,
  button labels or discount-percentage feedback. For image text, classify the
  correction as an image edit and give exact replacement copy without inventing
  stronger product claims.
- **Button/CTA text** — Never flag wording, translation, spelling, capitalization,
  missing/different copy or claims/numbers in a button label. No replacement text
  or owner questions. Outside the excluded final CTA section, this button-text
  exclusion does not exempt button functionality or unrelated non-button content.
- **Footer email links (former V01)** — Skip their functionality, protocol and
  destination checks. Do not flag a broken email link or ask the owner to approve
  fixing it. Other footer content and purchase CTAs outside the excluded final
  CTA section remain in scope.
- **Guarantee duration differing from the competitor** — This is not a defect. Use
  the majority across our own advertorial and product page; correct only our
  internal exceptions.
- **Review counts** — Do not check, compare or flag review-count totals or
  discrepancies, including between pages. Do not ask the owner to choose a count.
  Other testimonial and review-content checks still apply. Advertorial testimonial
  presentation remains in scope; product-page review presentation is excluded below.
- **Product-page review presentation** — Do not give feedback on product-page
  review layout, portrait presentation, star rows, verified-purchase labels or
  their styling. This does not exclude review content: the first product testimonial
  remains critical, and heading mistakes, wrong identities and missing copy still
  follow their own checks. Do not route excluded presentation feedback through a
  generic trust-signal finding.
- **Blurry review portraits** — Do not flag portrait pixelation or request higher
  resolution merely because a small review photo is enlarged (former V40).
- **Intentional scrolling endorsement-strip overlap** — Never flag the template
  design where scrolling organization logos pass behind the fixed endorsement
  heading and stars, including temporary obscuring of logo names. This overlap
  is intentional and owner-approved. Do not request separating the heading/stars
  from the logo row, extra spacing, or an owner decision about this design; do not
  reintroduce it under readability, clipping, trust-signal or generic overlap
  findings. Reuse this exception whenever the same template design appears.
  Unrelated accidental overlaps in other components remain subject to their
  normal checks. This design acceptance does not independently verify endorsements.
- **Minor card styling** — Missing treatment-card backgrounds (former V32) and
  different ingredient-card backgrounds, corners or image scale (former V42) are
  not feedback by themselves. Flag only clearly broken formatting that makes the
  section difficult to use or visibly untrustworthy, such as overlaps, clipping
  or a severely disordered layout. Benefits panels and offer presentation have
  their own mandatory checks and are not covered by this tolerance.
- **Discount percentages: all feedback excluded** — Never give feedback or owner
  questions about discount percentages (50% off, 60% off, etc.). This includes
  wrong or missing percentages, source/approved-offer differences, cross-page
  mismatches, flat versus "up to" wording, formatting, arithmetic and rounding.
  Apply this everywhere: banners, headlines, body copy, images, badges, offer
  cards and checkout as well as buttons. Do not calculate a replacement percentage
  or reclassify an excluded percentage correction as translation, missing content,
  offer consistency or a visual finding. This is not limited to small differences.
  Actual payable prices, bundle quantities and checkout charges remain in scope.
  This discount exclusion does not by itself exempt non-discount outcome statistics.
  Remove findings/decisions tagged `discount_calculation`,
  `discount_percentage_calculation` or `discount_rounding` before generation;
  the tool rejects them. Also inspect the substance of broadly tagged translation,
  pricing and offer findings: tag validation alone will not catch every discount
  percentage correction. Remove the excluded part while retaining independently
  valid price/quantity/charge corrections in the same finding.
- **Swedish whole-krona unit prices** — Accept whole-`kr` merchandising prices
  instead of requiring exact decimal unit prices. The owner accepts `189 kr /st.`
  for a three-bottle bundle costing `565 kr`; do not demand `188,33 kr` or flag
  the small multiplication difference. This does not excuse a wrong payable
  bundle total, wrong quantity or materially different unit price.
- **Marketplace availability notices** — Our template omits the competitor's
  “not available on Amazon or eBay” notice. Ignore its absence; do not request
  that copy. This specific template exception does not exempt other missing
  sales paragraphs in the same finding or section.
- **Offer deferred to checkout** — Our template may place its offer on the product
  page or checkout. Verify the actual offer and prices at checkout when needed; do
  not request approval solely for this placement difference.
- **Template elements** — Footer logos, header branding, and other elements that are
  part of our own template and intentionally different from the competitor. Do not
  infer that missing styling within copied editorial/sales content is an approved
  template difference: apply the scoped card, benefits, offer and advertorial-review
  presentation rules below. Required components of our own template must also
  be populated correctly; apply the Swedish beauty-template rule below.
- **Accepted NLBE Health-template additions** — Leave the added outcome-statistics
  component and “Goedgekeurd door” logo strip out of feedback and owner questions
  when reusing this same template. The owner reaffirmed the NLBE 234 acceptance
  for FlexiJoint NLBE 236 on 2026-10-02. Their presence beyond the competitor is
  accepted; this is not verification of the statistics or endorsements and does
  not create a general exclusion for unrelated statistics or components.
- **Pack supply-duration labels in the reviewed Beauty template** — The owner
  confirms that our GutFlow SE Beauty template does not include the competitor's
  months-of-supply labels. Their absence is an accepted template difference, not
  missing-copy feedback or an owner question. Reuse this exception for this same
  template; do not infer it for every other template. Still flag incorrect duration
  labels when present, missing quantities/prices, or an explicit sheet requirement
  that has not been implemented.
- **CalmSoothe SE 235 decisions (2026-10-02)** — Exclude the added product-page
  95/93/97% outcome-statistics approval question (D01) and the absence of the
  competitor's 2/6/10-month supply labels (D02). Do not ask either question again
  when reviewing this funnel. The statistics are accepted for review scope, not
  independently verified claims. Supply labels are not required here; actual
  bundle quantities, payable prices and checkout handoffs remain in scope.
  These decisions do not extend the NLBE Health or Beauty-template exceptions
  to every Swedish Health funnel or unrelated statistics.
- **FlexiJoint SE 237 shipping-insurance decision (2026-10-02)** — The owner
  dismissed D01: our offer cards and checkout do not need the competitor's
  pre-ticked €4.95 shipping-insurance option. Exclude its absence from findings
  and owner questions when reviewing this funnel. This acceptance is scoped to
  SE 237; actual shipping charges, payable totals, and the existing express-shipping
  checks remain in scope.
- **Reviewer and comment names** — Leave native-looking names alone. Flag only
  obvious mistakes, such as clear foreign-market carryovers, corrupted text or a
  reply addressing a different named commenter. An unfamiliar or uncommon name
  alone is not evidence of an error and must not become an owner question. Do not
  guess a replacement identity. Continue checking evidenced name consistency;
  different localized names from the competitor are allowed.
- **Missing disclaimers** — If the competitor has a medical/legal disclaimer and ours
  doesn't, don't flag it. Disclaimer requirements are handled separately.
- **Minor stylistic differences** — Small layout or design differences that are
  intentional brand choices, not errors. Apply the scoped headline, benefits,
  offer and content-panel rules below: substantial lost prominence remains in
  scope, while isolated decorative differences and accepted minor card styling do not.

## Localization Rule

The reviewer must identify source-country references left in our adapted copy and
replace them with the corresponding established local reference. Check places,
regions, names, institutions, shipping wording and other market-specific references
across our advertorial, product page, image text and expanded FAQs.

If our advertorial already establishes a localized dispatch city but a product FAQ
retains the competitor's region, report a translation fix using our established
city — not an owner decision asking which of those two to use. Apply explicit owner
mappings first, then matching references already established in our funnel. Use the
local reference for the same entity/role; a customer's home city is not a dispatch
city. Only escalate when the intended local counterpart is genuinely unknown or our
own applicable references conflict. A city approved for one funnel is not a
universal replacement for every other funnel.

Deliberate localizations are not errors. When our funnel consistently changes a
source nationality, place, institution or company to a local one (for example
Spanish researchers near Barcelona becoming Dutch researchers near Haarlem), do not
give feedback that restores the source reference. If the change looks risky (for
example a real, named institution behind a scientific claim), raise it as an owner
decision, not a builder fix. Inconsistent localization within our funnel (Dutch in
one place, Spanish in another) remains a normal finding. Approved by the owner on
2026-10-07.

**Foreign currencies are fixed to our market's currency** (owner rule, 2026-10-07).
An amount left in the source currency (`tussen de 30 en 80 pond`) is a translation
fix, not an owner question. The target currency follows the sheet's `COUNTRY`:
- **NL, NLBE, BE (euro markets):** write the amount in euros with the same numbers
  in Dutch notation, e.g. `tussen de €30 en €80`.
- **SE:** write it in Swedish kronor with `kr` after the amount, in Swedish notation.
  The numbers change, so use a realistic rounded kronor amount for the same cost and
  state in the finding which source amount it replaces.
- **Other markets:** use that market's currency and notation; when the right amount
  is genuinely unclear, ask the owner.
Prices of our own offer are not converted this way: they follow the sheet and the
offer rules.

## Swedish Health-Template Doctor Recommendation

For sheet `COUNTRY: SE` + `Template: Health`, the product-page doctor
recommendation intentionally replaces the competitor's first customer review.
Resolve both sheet fields together, as for the most-popular offer rule. Do not
request that review above, below or instead of the doctor recommendation, and do
not add its customer name, portrait, verified-customer label or translated quote.
The owner confirmed this template rule when dismissing Airvexa SE 239 T08 on
2026-10-02. Record the first-testimonial check as an accepted template substitution
with the observed doctor-recommendation location, not a missing-content issue.

Still inspect the doctor recommendation for missing/empty content, unrelated
product copy and applicable identity/content defects. This substitution accepts
the component's role, not every statement inside it. Other customer reviews,
advertorial stories and their completeness checks remain in scope. Do not extend
the substitution to other countries or templates: the Swedish Beauty rule below
requires its doctor component and intended customer-review slots separately.

## Swedish Beauty-Template Doctor Block

Owner requirement: the Swedish beauty-funnel template always includes a
doctor-verified (`Läkarverifierad`) component on the product page. Review this
component separately from customer testimonials. Apply this rule when the sheet
template or owner context identifies this template, including when it is reused
for a different product category; do not infer the rule for every Swedish funnel
solely from its language or URL. The owner identifies the reviewed GutFlow SE
funnel as using this template.

- Check that the doctor block exists, is populated and reads as product-relevant
  expert copy, with the template's doctor identity/specialty presentation. A missing
  block, empty placeholder, unrelated product copy or pasted customer testimonial
  is actionable. Its absence from the competitor does not excuse the omission:
  this is a required component of our own template.
- The funnel builder must draft/generate suitable Swedish expert copy for the
  actual product and the relevant specialty. Preserve the component; instruct the
  builder to replace incorrect contents rather than delete it, rename a customer
  as a doctor, or merely localize the customer's name. Apply the existing
  doctor/authority-reference requirements for real qualifications and approved
  statements; generated wording is a draft, not evidence of medical verification.
- Keep customer reviews in their intended testimonial slots. For this GutFlow run,
  the owner maps the competitor's Paola review to Linn's first-review slot. The
  same customer story placed beneath `Läkarverifierad` does not fulfil the doctor
  component and does not resolve the first-review mismatch. Record these as
  separate corrections to their respective locations.
- Give a direct instruction identifying the doctor block, the incorrect content
  and the need for the builder to create the appropriate expert copy. Reviewer-
  supplied replacement prose is not required for this component assignment. Use
  target evidence and `evidence_pairs[].instruction`; use an approved template
  example as a design reference when available, not an unrelated competitor
  testimonial as the doctor-block reference. Do not reuse the example product's
  claims, doctor identity or specialty as facts about another product.
- Record a separate `doctor_verified_component` result in `review_checks.json`.
  Incorrect customer-review copy is a **translation/content** finding in the
  current two-category schema; a missing or malformed visual component is a
  **visual** finding. Group one component's related repairs coherently and retain
  the existing issue ID when correcting an earlier diagnosis of that same block.

## Issue Categorization

Use **translation** for missing/incorrect non-button copy and **visual** for
presentation or button/interaction defects under the current two-category report
format. For a button defect, state its exact location, expected action, observed
result and required functional correction in `description`; never include
replacement button copy. Button-text findings and owner decisions are excluded
(`check: "button_text"`, including button/CTA copy/label/translation aliases);
remove these before report generation. A working button with different wording
receives no finding.

Resolve clear localization carryovers as actionable **translation** findings.
Use the exact remaining foreign phrase as FIND and the established local equivalent
as REPLACE, with the affected screenshot and location. Do not put an obvious
localization correction into the owner-decision list. When converting an existing
decision into a finding, retain its ID for continuity and preserve the original
question plus its resolution in private correction history.

## Translation Checklist

### Importance threshold

Inspect all eligible copy, but publish only important feedback. A translation
finding must materially change the message, contradict an important offer or
instruction, confuse the reader, or visibly undermine trust. Do not promise that
a particular error will cause a reader to leave; this is editorial prioritization.

Skip understandable imperfections: isolated verb/agreement errors, minor awkward
phrasing, one duplicated phrase, punctuation spacing that remains readable,
incidental geographic wording, or interchangeable examples such as holiday versus
Christmas routines. Do not turn every difference from ideal Swedish into a task.

**Words running together are always feedback** (owner rule, 2026-10-07): a missing
space between two words (`levertkrachtige`, `omje`, `resultatendie`), often next to
bold text, or after a comma (`risico,alleen`), looks sloppy to a buyer and is never a
readable imperfection. The same applies to a sentence whose word order broke during
editing (`Met Vigorix™ Ze komt…`). Group all such spots in one section into one
finding, with an exact FIND/REPLACE pair per spot. The "punctuation spacing that
remains readable" tolerance above covers only extra or missing spaces around
punctuation that do not join words, such as `zo ,` or a double space.
Likewise, small secondary inconsistencies such as support six versus seven days
or same-day versus next-day dispatch are low priority; promising same-day delivery
while stating delivery takes several days is an important contradiction.

Repeated pronoun/identity shifts may disrupt a whole passage even when each word
is understandable. If they do, create one finding with the relevant screenshots
and minimal corrections, rather than separate cards for each shift. Heading
mistakes are an exception to the minor-language threshold: always report actual
spelling, grammar and meaning errors in headlines, subheadlines, section headings
and offer-card headings on either page, even when the intended meaning is clear.
Identify headings by their visible role, not only HTML tags. This does not include
optional stylistic rewrites or override explicit exclusions such as button text
and all discount-percentage feedback. Prominent foreign-language trust labels, nonsensical medical
word choices, reversed discount stories, confused refund promises, wrong doctor
content and conflicting guarantee terms remain important.

Mechanism explanations must always be clear: report unclear, garbled or materially
changed explanations of how the product works, even when the affected wording is
short or appears in body copy. Do not dismiss these as minor language polishing.
Clear, accurate paraphrases do not require stylistic rewrites.

The first product testimonial is critical. Missing source elements, bullet points,
paragraphs and headlines are always important feedback, as are heading mistakes
and missing comments under their dedicated rules. Do not downgrade omissions
because the benefit is mentioned elsewhere, the copy seems repetitive, or its
individual conversion impact is uncertain. The explicit standing/template
exclusions still apply. Do not use this importance threshold to silently discard
required completeness findings or extend it to unrelated visual checks.

Check for these in every review, excluding button/CTA text:

- [ ] **Mechanism clarity** — Read each explanation of how the product works as
  a customer, across the advertorial, product page, diagrams and expanded FAQs.
  The reader must be able to understand what acts, where it acts, what it does
  and how the described steps relate to the claimed benefit. Always report
  untranslated or unexplained mechanism labels, ambiguous causal connections,
  broken step descriptions and wording that changes the action (for example,
  moisturizing versus forming a protective coating). Include comparative
  explanations of why another approach does not perform the described function
  when their wording is unclear. Give exact, plain-language replacement copy
  supported by the source and approved product facts; do not invent mechanisms,
  strengthen claims or equate source wording with scientific verification. Keep
  an already clear, accurate paraphrase, and avoid replacing one obscure term
  with another. Group related mechanism repairs while preserving evidence for
  every affected location. Standing exclusions, including button text, still apply.
- [ ] **Heading language** — Always report actual spelling, grammar or meaning
  mistakes in every heading, including section and offer-card headings. Do not
  discard heading corrections as low-impact proofreading. Keep all affected
  headings evidenced; group related corrections when that keeps feedback concise.
- [ ] **Source-language text remaining** — Any text still in the original language
  (could be any language, not just English)
- [ ] **Unlocalized places and market references** — Even grammatically translated
  sentences can retain a foreign city, region, name, institution or delivery
  reference. Compare against the corresponding established local entity in our
  funnel. Correct clear carryovers directly and make the same reference consistent
  across pages, FAQs and images; preserve meaningful geography that is not a
  localization carryover. Record the mapping and its owner/own-funnel basis in
  `review_checks.json` so the builder gets a concrete replacement rather than an
  unnecessary decision question.
- [ ] **Country-specific number formatting** — Resolve the target country AND
  language before reviewing visible numbers; currency alone does not determine
  number notation. Check decimal and grouping separators separately, across
  prices, narrative figures, percentages, quantities, image text and expanded
  FAQs, subject to the standing exclusions. Dutch in NL/BE uses a decimal comma
  (`49,95`, `2,9 miljard`); English in GB/US uses a decimal point (`49.95`,
  `2.9 billion`); Swedish in SE uses a decimal comma (`49,95`) and normally a
  space for thousands (`18 000`, preferably a nonbreaking space). In `18,000`
  intended as eighteen thousand, the comma is a grouping error, not a decimal
  precision issue. Do not replace correct Swedish `18 000 kr` with `18.000 kr`
  merely by applying Dutch punctuation conventions. For other locales,
  resolve the actual locale's decimal/group symbols from Unicode CLDR or an
  authoritative local language reference; never apply a universal comma/point
  substitution. Record the resolved locale and conventions in the review notes.
  Preserve the numeric value when correcting notation. Distinguish decimal
  separators from thousands grouping (`1.234,56` in conventional Dutch monetary
  notation versus `1,234.56` in English); accept valid local spacing variants
  rather than flagging harmless style preferences. Verify the currency separately.
  Apply scoped owner-approved compact price formatting before proposing spacing
  changes. For Airvexa SE 239, the crossed-out `2400kr` on the 5x offer is
  intentionally kept together (owner correction to T13, 2026-10-02); do not request
  `2 400 kr` or reopen that finding. This accepts that presentation, not incorrect
  amounts, currencies, or unreadable/clipped prices, and is not a universal ban
  on number-format checks.
  References: [Dutch decimal notation](https://taaladvies.net/komma-of-punt-bij-decimale-getallen/)
  [Swedish amounts, section 12.5](https://www.isof.se/download/18.17dda5f1791cdbd2873a99/1620030264840/Mynd-skrivreg2014-1.pdf),
  and [CLDR number symbols](https://cldr.unicode.org/translation/number-currency-formats/number-symbols).
- [ ] **Decimal precision fits the context** — A correct separator does not make
  an unnecessarily precise number good sales copy. Flag conspicuous conversion
  residue in broad narrative figures, such as four decimal places in a billion
  amount; identify excess precision separately from a wrong decimal separator
  or a materially wrong amount. A Dutch `2,9205 miljard` already uses the correct
  comma, but may need sensible narrative rounding (for example `2,9 miljard`),
  not a change to `2.9205`. Explain rounding as a value approximation, not a
  formatting-only transformation. Do not impose a universal two-decimal limit:
  respect currency minor units and approved merchandising conventions for prices,
  and preserve meaningful precision in doses, measurements and supported statistics.
  Do not extend a precision finding into unrelated minor amount corrections or
  override accepted scoped amounts, excluded review counts, button text or discount
  arithmetic. Give one complete numeric phrase to copy, not individual digits.
- [ ] **Swedish currency display** — Owner preference for Swedish customer-facing
  monetary amounts: use `kr` after the amount, rather than the ISO code `SEK`
  (for example, `2 100 kr`). Flag actual `SEK` currency occurrences in eligible
  non-button copy, including image text and expanded FAQs, as translation findings
  with exact, occurrence-specific FIND/REPLACE text. Preserve the amount; this is
  formatting, not currency conversion. Keep legitimate spelled-out `kronor` and
  internal currency metadata such as `currency: "SEK"`. Inspect context: `SEK` on
  a countdown can mean seconds and is not a currency occurrence. Verify the
  original Swedish page/capture before flagging: browser-translated English may
  display `SEK` where the original correctly uses `kr`. If owner feedback quotes
  `SEK 18,000` but the original capture and live Swedish page show `18 000 kr`,
  record that discrepancy privately; do not add a false builder task or infer
  browser translation as proven without observing it. A genuine original-page
  `SEK 18,000` occurrence still needs both currency-placement and grouping fixes.
- [ ] **Price/number accuracy** — When competitor and our funnel use the **same
  currency** (e.g., both EUR), monetary values, statistics, and quantities must
  match the competitor or an explicit owner-approved offer. Exclude review counts
  entirely. The AI translation tool sometimes applies a phantom currency conversion
  to EUR→EUR prices. Compare relevant numbers against the original at the actual
  offer location.
- [ ] **Review names** — Apply the native-looking-name tolerance above to both
  testimonials and comments. Report obvious errors, not uncommon-name preferences.
- [ ] **Date formats** — Local format (DD-MM-YYYY for NL, not MM/DD/YYYY)
- [ ] **Phone numbers** — Local format with correct country code
- [ ] **Unnatural translations** — Report wording that meets the importance
  threshold above, not merely language that could flow more naturally.
- [ ] **Units of measurement** — Metric vs imperial where relevant
- [ ] **Legal/compliance text** — Terms, disclaimers in the correct language

## Content Completeness and Product-Page Checklist

Apply completeness, identity and emphasis checks on both reviewed stages. The named
product-page elements are mandatory individual checks, not implied by a general
translation pass.

- [ ] **Missing text or information** — Compare every source section, paragraph,
  heading, bullet, caption and relevant detail with the target, including content in
  images, tabs and expanded accordions. Detect omissions and truncated copy. Search
  the full target before calling moved content missing; distinguish a genuinely
  relocated equivalent element from a similar benefit mentioned in other copy.
  A results timeline mentioning speed does not replace a missing speed-of-results
  bullet in the corresponding hero list. Preserve the explicit
  template/disclaimer exceptions above; they do not excuse unrelated missing sales
  content.
  **Missing source elements, bullets, paragraphs and headlines always receive
  feedback**, including attributed expert paragraphs. Once absence is confirmed
  in the corresponding component and no genuinely relocated counterpart exists, report the
  omission directly with source evidence, target insertion location and the full
  translated paragraph. Do not ask whether it was intentionally removed. Preserve
  the source's attribution; this copy comparison does not verify its claims or
  authorize an invented local expert. Apply the explicit standing exclusions to
  their own elements, not as a general excuse for missing paragraphs.
- [ ] **Missing comments and replies** — Compare the complete source discussion
  with the target. Always flag missing comments/replies; a shortened discussion is
  not an accepted template difference and does not need an owner decision. Show
  the missing comments in readable source screenshots and give one short instruction:
  “These comments are missing. Add them to our funnel in the target language.”
  Group the omission into one finding. Use `evidence_pairs` with source screenshots
  only when the comments section is obvious; a target screenshot is optional when
  needed to identify the location. Do not supply translations for every comment,
  repeated insertion instructions, or FIND/REPLACE blocks. The builder restores
  the comments and reply relationships. Leave existing native-looking names alone.
  Set `check: "missing_comments"`. Multiple source-only screenshots render in a
  compact side-by-side gallery (three columns on desktop, two on medium screens,
  one on narrow screens), with click/tap to enlarge each original screenshot.
  Keep their discussion order and complete highlighted content; do not stack six
  full-width screenshots on desktop or crop away comments to shorten the report.
  This is content completeness, not a comparison of review-count or
  reaction-count totals; the review-count exclusion remains in force.
- [ ] **Product-page headline** — Compare the complete headline with the source:
  meaning, promise, numbers and qualifiers. Check for missing words,
  mistranslation, truncation and appropriate visual prominence.
- [ ] **Product-page subheadline** — Compare the entire supporting statement and its
  relationship to the headline. Preserve benefits, conditions and qualifiers; do not
  accept a shortened paraphrase that drops information.
- [ ] **Product-page bullet points** — Match every bullet individually. Check count,
  complete meaning, benefits, numbers, qualifiers and accompanying icons; identify
  missing, duplicated or mismatched bullets. Equal counts alone do not establish a
  match.
- [ ] **Prices and quantities** — Compare regular/reference price, sale price,
  bundle total, unit price, monetary savings amount and paid/free quantities
  with the competitor offer by default, on the same quantity basis. Override only
  the offer fields explicitly specified differently in the sheet. A blank sheet
  field means use the competitor reference, not permission to invent a different
  offer. An unread/unavailable sheet is not a verified blank sheet: retain the
  input uncertainty rather than guessing. Record the sheet field/value or source
  evidence used for each offer override in the review notes. Explicit instructions
  from the owner in the current task still take precedence.

  **Offer structure and bundle labels must match the selected reference.** Preserve
  the competitor's quantities, paid/free structure, sale prices and terms except
  where the sheet explicitly changes them, with appropriate target
  language, brand and currency localization. Equal bottle counts do not make
  `2+1` equivalent to an approved `3x` label, or `3+2` equivalent to `5x`: these
  present different offers. Report an unapproved change in framing even when the
  total quantity and payable amount are the same. Check selectors and selected
  summaries at the actual offer location, including checkout when offers are
  deferred there. Do not ask the owner to choose again when the sheet/source
  already establishes the reference.

  **Crossed-out reference-price exception:** Do not require an exact competitor
  match for crossed-out prices. The owner's merchandising criterion is roughly
  double the 1x purchase price; for example, a crossed-out `€60` alongside a 1x
  price of `€29,95` is acceptable, and must not be changed solely because the
  competitor uses `€40`. Check reference amounts on the appropriate unit/bundle
  basis; do not assume every bundle's reference must be exactly twice its
  discounted bundle total. "Roughly double" has no owner-specified numerical
  tolerance or universal multi-bundle formula: do not invent one or round approved
  anchors to exact doubles. Report clearly unsuitable anchors using the observed
  price basis, not source mismatch alone. Respect explicit sheet/owner reference
  prices and scoped acceptances. Acceptance of existing copy is not independent
  verification of historical selling prices and does not authorize inventing new
  reference prices. This exception does not change payable-price checks, offer
  structure fidelity or the exclusion of all discount-percentage feedback.

  Apply the discount-percentage exclusion and accepted Swedish whole-krona unit
  pricing above. Check currency formatting and actual-price consistency across
  hero, offer cards, selectors and sticky bars; button labels remain excluded.
  The final-CTA section and other explicit standing exclusions still apply; offer
  matching must not reintroduce excluded percentage or final-CTA feedback.
  Do not invent a reference price or silently fix an inconsistency also present in
  the source; report the evidence for resolution.

  **Displayed totals versus per-piece rounding:** In eligible sections, report
  incorrect or inconsistent displayed total/sale prices and genuinely wrong local
  number formatting even when the monetary difference is small; they can look
  unprofessional. Do not require proof of a payment error before flagging a visible
  total-price mismatch, and do not claim the charged amount is wrong without
  evidence. A total of `€29,85` beside an established one-bottle price of `€29,95`
  merits feedback. Correct local style variants are not formatting errors.

  For EUR prices explicitly labeled per piece/unit, ignore an absolute rounding
  discrepancy of `€0,01` or `€0,02`; always report a discrepancy greater than
  `€1,00`. Compare with the same approved bundle total divided by its quantity,
  rounded to the applicable currency precision. These are per-unit tolerances,
  not permission for incorrect bundle totals or checkout charges. The owner has
  not set a blanket pass/fail threshold for `€0,03` through `€1,00` inclusive;
  apply the existing misleading-price/materiality criteria without describing
  that interval as owner-approved. Preserve the separately accepted Swedish
  whole-krona rule; do not silently convert the EUR thresholds to other currencies.
- [ ] **First testimonial text** — First apply the Swedish Health-template doctor
  recommendation substitution above when the sheet says SE + Health. Do not
  restore the source customer review in that intentionally replaced slot. For
  other applicable testimonial slots, explicitly compare the first testimonial on the
  product page, including its full quote, attribution, age and any
  result/timeframe. This is a critical conversion element: always report a missing,
  wrong or materially mistranslated first testimonial, even if the substituted
  story reads coherently. Do not downgrade it to optional feedback or minor polish.
  Check omitted sentences, incorrect translation and association
  with the right person/image. This priority check does not replace reviewing the
  remaining testimonials. Identify the first visible testimonial on each page
  before matching by wording or name: an unrelated template review above the
  matching translated quote must not be overlooked. Check the content assigned
  to the intended first-review slot, including owner-specified source-to-target
  mappings. Finding the right quote farther down does not resolve a wrong quote
  in that slot. Localized reviewer names may differ; they do not establish which
  source testimonial belongs there. Record both the first-slot mismatch and any
  matching quote elsewhere without calling content absent when it is present.

  **Whole-testimonial replacement feedback:** when the first review contains the
  wrong testimonial, show a green box around the complete source review and a red
  box around the target quote to replace, retaining the target name and surrounding
  page context outside the red box so the builder can locate it. Follow the paired
  screenshots with a direct instruction to replace that target review text with
  a faithful target-language translation of the green-boxed source review. The
  funnel builder supplies the translation; do not generate replacement copy or
  empty FIND/REPLACE blocks for this whole-review correction. This is a scoped
  exception to the usual exact-copy requirement; ordinary wording corrections
  still receive exact replacement text. Store the instruction on the relevant
  `evidence_pairs[].instruction` so it renders immediately below that pair.
- [ ] **Age and name consistency** — Check that the stated age and localized name
  plausibly fit the intended character and target market, and that the same person's
  age/name remain consistent across the article and testimonials. Localized names
  should suit the person's established age/generation and role; do not introduce a
  less suitable name merely because it appears elsewhere as a complete full name.
  Preserve source ages unless an owner-approved change exists. A name alone cannot
  establish age: treat age suitability as contextual editorial judgment, not proof
  that a name belongs exclusively to young/old people or a particular profession.
  Apply explicit owner name preferences and never invent a new age to make a name fit.
  On the product page, inspect every testimonial's attribution alongside its stated
  age or portrait, not only the first testimonial or reviewers repeated at checkout.
  Record those observations under `product:age_and_name`. Apply the owner's
  age-appropriate template-persona preference where authorized; the native-name
  tolerance does not cancel that explicit preference. Preserve verified real
  reviewer identities. When the same approved name correction affects product and
  checkout, give each location its proper report category under the report-format
  contract instead of burying product-page copy edits in checkout feedback.
  **Article-story identity takes priority:** establish who is named or written
  about in the article narrative, including its closing references, before
  comparing testimonial attributions. Map the same person's story by its events,
  speaker and source counterpart. Use the established localized narrative name
  as the reference for a clearly matching testimonial; do not rewrite the story
  to fit an isolated testimonial name or portrait. Keep unrelated reviewers and
  commenters separate, even when their names match. A spouse/daughter reference
  alone does not establish the speaker's gender or identity. Preserve established
  story facts and inspect any associated portrait separately. Correct only the
  evidenced mismatching occurrences, retaining suitable existing surname text
  unless it too conflicts; do not invent an identity or apply a global replacement.
  Explicit current owner choices override this reference. When the narrative
  itself is inconsistent, or no narrative reference exists, inventory distinct
  visible occurrences of **the same person** across our reviewed pages and use
  the most-mentioned suitable name.
  Count each physical occurrence once; duplicate captures, indexes and repeated DOM
  copies do not add votes. Match identity by the story, speaker and attribution,
  not merely a shared first name or profession. An explicit owner choice takes
  precedence; ties without that choice remain unresolved rather than defaulting to
  whichever occurrence supplies a surname. A missing surname is a completeness
  issue: retain the suitable first name and use the established/approved surname
  for formal attribution. Do not replace an accepted first name just to add one.
  Example: if Erik is the established majority name for one author, correct that
  author's stray Bram references to Erik and complete an incomplete author byline;
  leave an unrelated customer named Bram or a genuinely different doctor alone.
  Keep any chosen display-name localization distinct from verification of an actual
  physician's identity or credentials; the doctor/authority rule still applies.
- [ ] **Correct bold text** — Compare which words or phrases are bold in the rendered
  source and target, matching meaning across languages rather than word positions.
  Check missing or misplaced emphasis, broken bold spans and entire paragraphs
  accidentally bolded. Key promises, numbers and qualifiers must receive the
  intended emphasis without making different claims stand out. Apply this to every
  matched content block on both advertorial and product page, including ordinary
  story paragraphs; a hero/headline check does not cover body copy. Check both
  directions: source emphasis missing from the translation, and target emphasis
  added where the corresponding source text is regular. Localized names, amounts
  and sentence order retain the emphasis of their corresponding source meaning,
  not the source's literal words or currency value. A different base font or
  template is not permission to move emphasis within copied content.

  Record the source bold spans, their exact target-language counterparts, and any
  extra target bold spans by matched block in `review_checks.json`, with a result
  for each comparison. Use captured token `bold` flags when
  available to locate candidates, then verify the rendered screenshots; plain
  extracted text cannot establish a formatting pass. Do not use a generic
  "content reviewed" result as evidence that emphasis was compared.

  **Owner tolerance for body-copy bolding: report only when more than 10% is
  incorrect.** Headlines and section headings have a separate, higher-priority
  check below and are not subject to this tolerance.
  Measure this across the combined advertorial and product-page comparison using
  matched text blocks: `affected eligible blocks / all eligible matched blocks ×
  100`. Use semantic blocks (body paragraphs, individual bullets and FAQ
  questions/answers), not words, screenshot tiles or DOM text fragments. A source
  block split across several target elements remains one comparison unit. Count
  each block once, even when it has several missing/extra bold spans; include
  correctly matched regular-text blocks in the denominator. Exclude headlines and
  section headings from both counts, including visually styled headings implemented
  as paragraphs. Also exclude button labels,
  approved template-only differences and other out-of-scope content. Missing text
  is a completeness issue, not an additional bolding mismatch.

  Record numerator, denominator, percentage and the reviewed scope in
  `review_checks.json`. At or below 10%, retain the discrepancies privately as
  accepted within tolerance; do not create bolding findings or owner questions.
  Above 10%, create one consolidated **visual** feedback point with the affected
  scope and link the private block-level mismatches to it. Apply the threshold to the
  combined funnel, not independently to a small section, individual screenshot or
  each page. Do not infer the percentage from a sample; incomplete comparison
  leaves the threshold decision pending. This tolerance applies only to bold
  formatting in body copy and does not suppress headline-formatting findings or
  separate copy, number or missing-content errors.

  For a reportable bolding finding, show **one short note and one example screenshot**:
  “Go over the advertorial and product page again and match the bold text to the
  competitor. Add missing bold and remove extra bold.” A short example instruction
  may name the marked phrase. Do not publish a screenshot or detailed instruction
  for every mismatch, and do not generate FIND/REPLACE blocks for formatting.
  Keep the complete comparison and threshold calculation private. State the full
  affected page scope; keep the single labeled example visible under each affected
  page filter, even when the example comes from only one of those pages.
- [ ] **Offer presentation** — Check that a buyer can immediately understand what is
  included, paid/free quantities, selected bundle, total versus per-unit price,
  discount, savings and purchase action. Check visual hierarchy, spacing, alignment,
  badges, selected states, readable labels and consistency with the actual offer.
  Flag concrete ambiguity, contradiction, clipping or poor readability with an
  actionable correction; do not flag a harmless brand preference merely because it
  differs from the source. Changed offer structure or paid/free framing is not a
  harmless brand preference: apply the sheet/source reference rule above.

  **Required initial selections and most-popular offer:** Resolve the sheet's
  `COUNTRY` and `Template` columns together before applying an offer-selection
  rule; retain them as `meta.country` and `meta.template`. Trim whitespace and
  compare case-insensitively. Do not infer the template from a URL, page styling,
  product category or country alone; resolve a missing sheet value first.
  **For Sweden (`SE`) + `Health`, the most-popular offer is always 5x** under
  the owner's 2026-10-02 rule. Do not move its emphasis to the competitor's 3x
  (or another quantity), or demand a competitor-style badge on that other card.
  The existing template emphasis on 5x is accepted; no literal “MEST POPULÄR”
  badge is required solely because the competitor has one. This exception
  concerns most-popular presentation, not proof of a preselected checkout state.
  For other country/template combinations, follow the competitor's default bundle
  and make that bundle the most-popular option, unless an explicit sheet or current
  owner instruction specifies otherwise. Check actual initial selection separately
  using the applicable sheet/owner instruction or otherwise the source default.
  Match the bundle by quantity/offer,
  not by its position; this replaces the former always-middle rule and applies
  to even-numbered offer layouts too. Never turn one run's 3x choice into a
  universal quantity. Distinguish a most-popular badge from observed preselection:
  record both, and resolve an unknown/conflicting source default from explicit
  configuration or owner input instead of guessing. Keep express shipping
  preselected under the separate existing owner rule. An already-selected express
  upgrade is intentional, including its displayed charge; do not recommend
  unchecking it or removing it from the initial summary merely because it is
  preselected or differs from the source's default. Preserve the approved upgrade
  identity and price; this rule does not impose one universal shipping charge.

  Capture the untouched initial state before clicking any offer/shipping controls;
  a state reached after reviewer interaction cannot establish the default. Check
  that the required bundle and express shipping agree with the initial
  summary and displayed total. Report a wrong/unselected default or an actual
  summary/charge mismatch, not the presence of the intended express charge. For
  a source default already established by evidence or owner input, do not ask
  again merely because our layout has no unique middle option. Keep this inspection
  separate from submitting an order or testing payment. Standing final-CTA
  exclusions still apply; inspect the eligible checkout offer.

  **Bundle images:** compare all offer cards together at the review viewport.
  Check consistent image-container dimensions, aspect-ratio handling, alignment
  and padding across the stack; flag visibly undersized/oversized artwork,
  inconsistent image footprints, distortion or clipping. Different bundle
  quantities can legitimately change the composition and individual bottle size.
  Request consistent presentation of the complete bundle artwork, not identical
  bottle sizes at the cost of cropping products or baked-in offer labels. Preserve
  aspect ratios and all paid/free units. Give the affected card locations and a
  concrete resizing/alignment instruction without inventing unmeasured pixel sizes.

  **Bundle-heading line breaks:** keep the product/paid quantity together and the
  free-quantity phrase together. For a compact two-line heading, put the product
  bundle on line one and the complete bonus phrase on line two, rather than letting
  the browser strand `Gratis` on its own line. For the owner-reviewed GutFlow
  offer, use `3x GutFlow™` / `+2 Gratis`; the corresponding second card should use
  `2x GutFlow™` / `+ 1 Gratis`. Treat these as layout instructions, not changes to
  the offer quantities or wording. Apply equivalent grouping to other localized
  bundle headings where this compact layout is used, without forcing every
  possible heading or single-unit offer onto two lines. Verify wrapping at the
  captured mobile width and check narrower widths if the layout remains uncertain.

  These offer image/layout defects are **visual** findings, independent of the
  body-bold tolerance. Non-button offer titles remain in scope despite the
  button-text exclusion. Use marked target evidence and clear styling instructions;
  no replacement translation is necessary when the copy is already correct.

  **One offer feedback point:** combine related offer image, scale, alignment and
  heading-wrap defects into one finding. Use **one genuine screenshot of the offer
  section**, retaining all relevant offer cards, with multiple boxes around the
  affected parts. Give one concise explanation of the mistakes and repairs. Do not
  split image sizing and heading wrapping into separate findings or show a separate
  screenshot for each card. When revising, keep the earlier surviving ID and record
  merged IDs privately. Preserve separate actual-price or heading-language fixes
  when they require exact replacement copy.
- [ ] **Precise FAQ match** — Pair every source question with its target question and
  expand every answer on both pages. Compare all information, conditions, claims,
  quantities, prices, timeframes, guarantee details and instructions, subject to the
  standing owner rules: market references must be localized consistently, review
  counts are excluded, and money-back guarantee duration follows our funnel's
  majority, not the competitor. Do not preserve a foreign region just because the
  source FAQ uses it. The translation must preserve other meaning precisely;
  matching only question count or topic is insufficient. Flag missing/extra/
  duplicated topics and omitted, added or changed answer information unless
  explicitly approved. Retain evidence of expanded answers, not just the closed FAQ
  headings.

## Visual Checklist

Check for these in every review:

- [ ] **Images with source-language text** — Text baked into images (banners,
  badges, infographics) that wasn't recreated in the target language
- [ ] **Brand name inside a GIF** — When feedback specifically concerns the brand
  name on a product inside a GIF/animated product asset, add this exact prominent
  note at the top of that finding using `important_note`:
  **NOTE: IF THIS IS A MOVING PRODUCT INSIDE A VIDEO YOU CAN'T EDIT - THEN SKIP THIS FEEDBACK**
  The builder may skip the affected brand edit if the moving product cannot be
  edited. Do not assume editability from a still screenshot, require a frame-by-frame
  repair regardless of this condition, or remove all animated-media feedback.
  Static product-image branding and editable animated branding remain actionable.
  If an issue mixes static and animated brand edits, separate their scopes so the
  skip condition applies only to the animated edit. Follow the report-format
  contract for placement; keep this implementation condition in the review itself.
- [ ] **Competitor logos/branding** — Any competitor brand elements still visible
- [ ] **Doctor/authority references** — Use appropriate localized names and
  accurately supported titles/certifications. A different doctor on our product
  page, advertorial, or versus the competitor is allowed; identity difference alone
  is not a defect. Check that the expert's specialty and endorsement concern the
  actual product topic. For a gut-health funnel, flag leftover dermatology/skin-care
  authority copy and suggest a relevant gastroenterology expert plus exact
  target-language wording. Keep the authority component when the problem is its
  specialty/copy, instead of automatically deleting it. Do not simply relabel a
  dermatologist as a gastroenterologist: use an actual suitably qualified expert,
  their verified name/title and an approved statement. Clearly label proposed copy
  that awaits expert approval, and do not invent credentials, endorsements or
  treatment results. Unrelated product/skin claims remain actionable even when a
  different doctor is permitted.
- [ ] **Gender consistency** — Photo gender must match the reviewer name
- [ ] **Advertorial testimonial presentation (priority)** — Visually compare every
  matched testimonial/review component on the advertorial, including in-article
  reviews. Product-page review presentation is excluded; its content checks remain.
  Check portrait size, shape/crop and placement; name-to-photo alignment;
  star-rating rows; clear placement of existing verified-purchase labels;
  quote typography and readability;
  spacing within and between reviews; and any source container treatment. Each
  review must remain a clear visual unit. Exact decorative colour matching is not
  required when the same information remains clear.
  Correct translated text alone is not a visual pass. A tiny square portrait in
  place of a larger circular avatar, names displaced below the portrait, missing
  stars or a verification label merged into the name line are actionable visual
  mismatches, unless the specific presentation change was explicitly approved.

  Record source/target visual comparisons for every review location. Report
  confirmed presentation defects as **visual** findings independently of the 10%
  body-bold tolerance; do not dismiss them as minor template differences. Group
  repeated defects in the same review component into one finding with evidence
  for its affected locations and exact repair instructions. For example: restore
  circular portraits with names alongside, the source star row, a separate styled
  `Verifierat köp` line and comparable spacing. Keep the instructions short and
  focused on the missing/unclear elements. Preserve correct localized names
  and quotes. Match existing source ratings/verification labels; do not invent
  new ratings or purchase-verification claims. Review-count totals remain excluded.
- [ ] **Trust signals** — Local trust badges (e.g., Thuiswinkel Waarborg for NL),
  local payment methods (iDEAL for NL), correct shipping references
- [ ] **Formatting/layout issues** — Broken headlines, misaligned elements, cut-off
  text, wrong font sizes
- [ ] **Content panels, cards and visual grouping** — Compare the rendered structure
  of every matched editorial/sales section on both stages, not just its text and
  icons. Check colored backgrounds, borders, rounded corners, internal padding,
  space between items, grouping boundaries and heading hierarchy. **Benefits must
  always be formatted correctly:** preserve a distinct benefits panel, prominent
  heading, readable separation and source-like grouping of its benefits. Retaining
  check icons in a cramped text block does not meet that requirement. Other card
  differences use the minor-card-styling tolerance above; missing red treatment
  backgrounds or grey ingredient containers alone are not findings. Natural
  translated text wrapping need not match pixel for pixel.

  Record each component comparison with source/target screenshot evidence and
  flag reportable structural mismatches independently of the 10% body-bold
  tolerance. Give short instructions identifying the exact target section,
  what belongs inside each container, the source background treatment, corners,
  padding and item spacing to restore. Keep surrounding paragraphs outside the
  component and preserve correct localized wording and amounts. Use one finding
  per component/group with all affected locations shown; do not duplicate the same
  repair as separate background, spacing and heading findings. Do not create
  identical FIND/REPLACE text for a styling-only correction, and do not invent
  exact CSS measurements without measuring the reference.
- [ ] **Headline clarity and formatting fidelity** — Check every headline and
  section heading individually on both advertorial and product page, including
  headings midway through an editorial. Identify headings by their visual/content
  role even if the DOM uses a `p` or `div`, rather than an `h1`–`h6` tag. Report
  headings that have become unclear, lost substantial prominence, or differ greatly
  from the competitor's formatting. Skip isolated missing underlines, italics or
  decorative highlights when the heading remains clear and comparably prominent.
  Do not require exact typography or identical line breaks across languages.

  Undersized headings still receive feedback. Use direct wording such as “Make
  these headlines larger so they stand out from the body text,” with the affected
  headings shown. For a major combined size/highlight loss, ask for the larger
  source-like format. Avoid a long checklist of minor decorative changes. Keep
  related locations in one finding without duplicating the same repair elsewhere.
  These visual checks are separate from the body-bold threshold; actual heading
  spelling, grammar and meaning mistakes always receive translation feedback.
  Keep correct copy unchanged; no FIND/REPLACE blocks for formatting-only edits.
- [ ] **Unswapped images** — Old images from the competitor funnel that should have
  been replaced
- [ ] **Anything that looks off** — Anything unconvincing that could hurt conversion
  rate, subject to the explicit visual exclusions and importance rules above.

## Cross-Page Consistency Checklist

Collect occurrences across **our advertorial and product page**, including body
copy, images/badges, offer cards, sticky bars, CTA labels, expanded FAQ answers and
footer guarantee text. Both within-page and between-page contradictions count.
Button labels may provide inventory context but must never become correction
targets or standalone findings. Apply corrections only at eligible non-button
locations; a discrepancy confined to button text is excluded from feedback.
Guarantee duration uses our funnel alone. Pricing still compares within each funnel
and against the competitor; the guarantee-duration exception must not change pricing
rules.

- [ ] **Guarantee duration across our two stages** — Inventory each distinct visible
  money-back guarantee mention on our advertorial and product page, including image
  text and expanded FAQs. Count physical page locations once: repeated captures,
  OCR/DOM duplicates, sticky elements seen at several scroll positions and
  desktop/mobile versions of the same element are not extra votes. Count only
  durations of our actual guarantee; exclude delivery times, treatment schedules,
  competitors' guarantees mentioned in the copy, and undated "money back" text. The
  duration appearing in more than half the eligible mentions is the intended
  duration. For 90-day majority, change **all** 60-day exceptions to 90; for 60-day
  majority, change **all** 90-day exceptions to 60. Apply the same rule to any
  other explicit durations. Never choose 90 merely because it is longer, copy the
  competitor's duration, or flag a consistent 60-day funnel because the competitor
  offers 90. If counts tie, there is no strict majority, or incomplete evidence
  could change the result, leave the duration undecided and record the specific
  owner question/blocker instead of guessing. A completely consistent funnel needs
  no guarantee-duration finding.
- [ ] **Guarantee evidence and corrections** — Save the own-funnel occurrence
  inventory, locations, exact text, normalized duration, counts, majority and every
  exception in `review_checks.json`. Show our majority wording as the reference
  evidence and our conflicting occurrence as the target; label them accordingly, not
  "competitor/source". Give minimal duration replacements at every conflicting
  location while retaining surrounding copy and emphasis.
- [ ] **Other guarantee terms** — Continue checking whether money-back versus results
  guarantees, start dates, refund eligibility and conditions contradict one another
  within our funnel. Identical meaning can use different wording; abbreviated badges
  need not repeat every condition. Do not infer these non-duration terms by counting
  days or silently rewrite them while correcting the duration. Escalate an
  unresolved contradiction in those terms separately.
- [ ] **Pricing consistency across both stages** — Check that every mention of the
  same product, variant and bundle agrees between the advertorial and product page:
  regular price, sale price, bundle total, per-unit price, monetary savings amount
  and any stated shipping charges. Normalize currency/formatting and
  compare on the same quantity and payment basis. A clearly labeled per-unit price
  and bundle total may differ legitimately, including the accepted Swedish
  whole-krona unit-price rounding; different
  bundles or explicitly stated conditions are not automatically contradictions. Flag
  conflicting payable amounts and misleading unlabeled totals/unit prices.
  Apply the displayed-total versus per-piece rounding rule above; a small visible
  total-price mismatch is still feedback, while an accepted per-piece rounding
  discrepancy is not.
  Never create any discount-percentage feedback here.
  Record the offer identity, exact amounts and all
  affected locations; provide consistent corrections from the source or an
  owner-approved offer. Do not choose a price arbitrarily when the source also
  conflicts.

For pricing, an inconsistency also present in the competitor funnel is a source
conflict for resolution rather than a newly introduced translation error. This
source-conflict rule does not apply to selecting guarantee duration: use our
majority rule even when the competitor differs or conflicts. Include the checkout
offer in pricing consistency checks whenever the offer is deferred there; do not
expand this into an unrelated checkout audit. The separately required Dutch
checkout checks below still apply.

## Swedish Offer Buttons and Checkout Prices

For every new Swedish (SE) run, apply the required
[offer-button handoff and checkout-price contract](references/swedish-offers.md).
Test each offer button and relevant shared-CTA state, verify the actual selected
checkout product/bundle, and compare prices against its presentation. This is
required even when the complete offer appears on the product page. Preserve the
button-copy and discount-percentage exclusions.

## Custom Funnel Product Pages

When the owner starts a run as a custom funnel (no real competitor product page;
our builder made a custom product page from our advertorial), apply the
[custom funnel rules](references/custom-funnel.md) to the product page instead of
the competitor completeness and product-page element comparisons. Standing
exclusions, the guarantee majority rule, wrong-product leftovers and the sticky
CTA requirement still apply.

## Dutch Checkout Review

For our Dutch-market funnels, apply the mandatory
[Dutch checkout checklist and completion contract](references/dutch-checkout.md)
in every new run, regardless of offer placement. Inspect review language/dates/
names, expanded FAQs, guarantee brand/days, and visibly loaded iDEAL/Bancontact
options. This extends checkout scope for NL/NLBE and Dutch BE only; keep the
existing price/offer fallback below for other markets.

## Checkout Offer Fallback

1. Look for the complete offer on the product page: all available bundles,
   quantities, prices and purchase options. A lone starting price does not establish
   that the full offer is present. If the offer is deferred, follow the real
   purchase CTA to checkout, rather than guessing a URL or flagging missing
   product-page cards.
2. At checkout, inspect every offered bundle/variant and its readable selected
   state. First capture the untouched initial bundle and express-shipping
   selections under the required-defaults rule above. Check paid/free quantities,
   total and per-unit prices, reference price,
   monetary savings, currency, visible shipping charges and payment frequency.
   Apply the Prices and Quantities and Offer Presentation checks there, including
   the discount-percentage exclusion and accepted whole-krona unit pricing.
3. Compare equivalent bundles with the source offer at its actual location and with
   earlier price claims in our advertorial/product page. Check the arithmetic on
   the same quantity basis, excluding all discount-percentage feedback. Follow the
   competitor to checkout too if its product
   page also defers the offer. A change of page is not a missing offer.
4. Inspect price changes when selecting bundles/variants without entering personal
   or payment details or submitting an order. Retain screenshots/text of the offer
   and the inspected states. If access prevents checking the offer, record `blocked`
   with the specific limitation; do not infer that prices match from a working CTA.
5. Save the URL, capture manifest, offer values, arithmetic, source mapping,
   presentation observations and `pass`/`issue`/`blocked` in `review_checks.json`.
   Use new unused issue IDs for actual checkout defects. Keep resolved D02/D03 IDs
   in private correction history; never reuse them for different questions.

For new runs, include `meta.offer_locations`, e.g.
`{"competitor": "product", "ours": "checkout"}`. Add each required checkout
capture to `meta.pages` with `side`, `page: "checkout"`, `scope: "price_and_offer"`
(or `"dutch_checkout"` for our mandatory Dutch review),
`url`, `manifest` and `status: "reviewed"` after completing this limited review.
The renderer requires evidence for recorded checkout offer locations and restricts
checkout findings to these checks unless our Dutch checkout has the completed
`dutch_checkout` scope above. It does not discover offers or judge prices
itself. Older reports without offer-location metadata retain their historical scope
and must not be described as having passed a checkout offer review.

## Button and Interaction Checklist

Test on mobile on both advertorials and both product pages. Use a location-based
inventory so repeated labels at the hero, middle, footer and sticky bar are tested
separately. Record each control's page/location, label, initial state, expected
action, actual destination/result and pass/issue/blocked result in
`review_checks.json`.

Labels identify the tested controls only. Do not review their wording or include
button-text corrections or owner decisions. Continue reporting actual functional
failures, such as a dead click, wrong destination or an obstructed purchase button.

- [ ] **Required bottom sticky CTA** — Every target advertorial and target product
  page must have an actionable CTA at the bottom of the mobile viewport while
  scrolling, even if the competitor lacks one. Record presence explicitly on
  each page; no discovered control is not a pass. A normal button near the end of
  the document, a fixed header, or a timer does not meet this requirement. Missing
  on either target page requires an evidenced `sticky_cta` finding. This page-wide
  requirement is separate from the excluded final closing CTA section.
  Inspect actual viewport screenshots at the top, after the hero, middle, bottom,
  then middle and top on the way back up. A bar may intentionally hide while the
  equivalent main CTA is visible, but must remain available through the long body.
  CSS fixed/sticky candidates are discovery aids only: visually confirm behavior,
  including JavaScript-positioned controls and fixed parent containers. Do not
  infer absence from one scroll offset or from static full-page tiles. If loading
  or overlays prevent inspection, record blocked rather than absent or passed.
  For missing-CTA evidence, mark the intended viewport-bottom placement on a real
  scrolled screenshot. Use a genuine competitor example only when one exists;
  otherwise use target-only evidence and cite this owner requirement.
- [ ] **Sticky-button behavior** — Scroll down and back up to verify appearance/
  disappearance, fixed placement and readability. Check that the sticky bar neither
  covers essential content/controls nor becomes hidden behind an overlay. Tap it in
  the visible state and verify the correct destination or scroll target, including
  the currently selected bundle/variant where relevant.
- [ ] **All buttons** — Test every visible actionable instance except footer email
  links, including hero/middle/footer purchase CTAs, image/link CTAs, offer and
  variant selectors, quantity controls, FAQ toggles, tabs, carousel controls and
  modal open/close controls where present. Confirm taps register, enabled/disabled
  states make sense, and the intended action occurs; check for dead links, wrong
  destinations, no-op clicks, wrong anchor offsets, overlays blocking taps and
  stale offer selections. Test relevant states after changing a bundle/variant and
  return to the prior state after each navigation. A working hero CTA does not
  prove the footer or sticky CTA works. Do not include footer email-link behavior
  in this inventory or create replacement feedback for V01.
- [ ] **Product-to-checkout handoff** — Verify that the destination loads and
  carries the intended product/offer. Swedish runs require the per-offer handoff
  and checkout-price checks above even when the offer is on the product page.
  If the offer is deferred there, complete the
  Checkout Offer Fallback, including offer selectors and displayed price changes.
  Then return. Do not fill customer/payment fields or submit an order. Record any
  blocked handoff or offer check honestly.

Interactions that submit contact details, subscribe, send messages or make
purchases are not routine button tests. Inspect their visible configuration and
record the untested submission boundary; do not submit real data or trigger a
transaction just to test a control. Do not treat an untested submission as a
verified pass.

## Edge Cases

- **Funnels with popups or modals**: Dismiss cookie banners/popups before
  capturing. If a popup is part of the funnel flow, capture it separately.
- **Funnels behind age gates or splash pages**: Navigate past them before the main
  capture.
- **Very long or continuously changing funnels**: Capture progressively scrolls
  within a time/step budget. A timeout is incomplete evidence. Retry the affected
  page with a justified larger budget or use targeted browser capture and record
  the limitation; never silently truncate or claim complete coverage.
- **Different routing/page structures**: Match advertorial and product content by
  role, not URL patterns or section numbers. Do not silently omit either mandatory
  stage. An offer deferred to checkout is an approved template difference: follow
  it and perform the limited price/offer check without requesting placement
  approval.

## Copy Formatting Rules

Before authoring findings or generating a report, read the mandatory
[report-format contract](references/report-format.md). It defines the approved
layout, `feedback_type`, evidence locations, copy interactions and navigation.

Apply these rules when writing `wrong_text` / `correct_text` and
`replacements[].find` / `replace` pairs.

**Copy the smallest meaningful replacement, not the smallest possible token.**
Use the smallest meaningful exact fragment needed for the correction. Keep entire
prices, numbers, words and phrases intact; do not reduce a price correction to
individual digits. Omit unchanged surrounding sentences. For example, FIND
`€12.827,10 tot €20.984,80` → REPLACE `€11.000 tot €18.000`, not the full
sentence containing those amounts.

Keep a short, recognizable phrase together when its unchanged words identify the
thing being corrected. For an age correction, FIND `Marieke is 68` → REPLACE
`Marieke is 61` is clearer than isolated `68` → `61`. Do not split a single
compact phrase into separate name and age blocks. Retaining a few identifying
words is appropriate; copying an entire unchanged paragraph is not.

Formatting a replacement must not introduce a new content correction or silently
cancel an existing, evidenced correction. Treat a request to change replacement
grouping as a formatting change: preserve all other findings, locations and
replacement pairs unless the owner explicitly rejects their substance. An
age-formatting example does not cancel the name-consistency corrections elsewhere
in the same story. If an example creates an actual ambiguity about the intended
name, clarify that exact value while keeping the other evidenced corrections
intact.

Use the screenshot marker and action/location note to disambiguate repeated text;
do not imply a global replacement. If two independent parts separated by
substantial unchanged copy change, give each its own copy pair. Changes within
one short, meaningful phrase belong in one copy pair, including the connector
between them. Use full sentences, paragraphs or lists only when their wording or
structure genuinely requires a full rewrite. Describe the action consistently:
"Replace only this price range" must not say "Replace the complete line."

An explicit owner request for one complete copy-paste sentence overrides the
fragment default for that finding. Supply the literal full original sentence and
one complete corrected sentence, including punctuation, as a single pair. Set
`copy_scope: "full"` and explain the owner-requested sentence scope in
`copy_scope_reason`. The standard renderer preserves every supplied pair intact;
it never auto-splits the sentence. Check the rendered copy block stays intact. Keep this
exception scoped to the accepted finding; do not expand adjacent sentences or
turn unrelated price/word corrections into full-sentence replacements.

Use `copy_scope: "phrase"` with a nonempty `copy_scope_reason` for a compact
label or identifying phrase (≤1 line, 120 characters, 12 words per field). Use
`copy_scope: "full"` with a nonempty `copy_scope_reason` for a genuine complete
rewrite (reordered bullet list, rewritten testimonial) or the explicit
owner-requested sentence exception above. Otherwise do not use the full-rewrite
option for a one-price or one-word correction. The default is
`copy_scope: "auto"`. These values document the reviewer's copy-scope choice;
the standard report does not shorten or split supplied copy. The legacy diff
helper is not used by report generation or publication.

`wrong_text` must be a literal, contiguous excerpt from the target page, not a
summary stitched together with ellipses. For multiple separated corrections, use
separate findings/screenshots or enough context and separate boxes to show every
referenced location. Keep existing delivered IDs when correcting a report.

For missing text, leave `wrong_text` empty, put the full localized text to
insert in `correct_text`, and specify the insertion location in `description`.
Missing comments use the simpler screenshot-and-instruction exception above;
do not generate per-comment copy blocks.
Do not fabricate a FIND phrase for content that does not exist. For non-copy
defects, omit empty text fields and give the concrete action in `description`.

Before delivery, apply each proposed fragment to the identified original
occurrence and confirm it produces the intended correction without changing
surrounding copy or emphasis. When revising formatting, compare the previous and
new issue IDs, evidence markers and intended content edits; every removed
correction needs an explicit owner rejection or a documented evidence-based
reason. Broader context belongs in the screenshot/action note; a short
identifying phrase may remain in the copyable replacement.

## Evidence Quality Standards

These rules govern annotation and evidence screenshots. The workflow defines the
tool commands; this section defines what constitutes acceptable evidence.

**The context crop and the issue marker serve different purposes.** Show enough
of the funnel to recognize the location; draw a red frame around existing
incorrect content, or a red insertion line where missing content belongs. Never
box unrelated existing content to represent something absent, and never use the
outer screenshot border as the issue marker.

**Missing-comment exception:** readable source screenshots of the missing
comments plus one short restoration instruction are sufficient when the comments
section is obvious. The target insertion screenshot is optional for this case.
All other missing-content findings retain the paired insertion evidence below.

**Consolidated visual evidence:** offer-layout feedback uses one screenshot of
the whole relevant offer with multiple marks. Body-bold feedback uses one labeled
example screenshot, even when the issue affects both pages. Full private inspection
is still required; these are exceptions to publishing every affected location.

For every issue:
1. Locate its exact `wrong_text` in the target capture. Read the actual source
   screenshot, including the nearby heading/paragraph/image, before choosing
   coordinates. A section number or nearby paragraph is not evidence of a match.
   If the text occurs more than once, use the surrounding content to identify the
   intended occurrence. For missing content, retain the source evidence and
   highlight the intended insertion location on the target; for button defects,
   highlight the actual control and record the action/result evidence. Do not
   pretend absent content or a static screenshot proves a failed interaction.
2. For existing incorrect content, set the highlight around the exact problem
   with roughly 8–12 image pixels of clearance so the frame does not cover
   letters. Use **one outer frame for a continuous wrapped sentence or paragraph**,
   not a padded box on every line. Separate boxes are only for distinct regions;
   they must not overlap, touch, or put a stroke through text. If a single frame
   would misleadingly include unrelated content, inspect and manually separate
   the regions with enough clearance, or select a more meaningful text span.
   Check readability at the actual report display size, not only the original PNG.
   For missing content,
   box the existing source text in green and use an insertion line in the
   target's actual insertion gap. A missing subheadline belongs between the
   complete headline and first bullet; boxing the bullet list fails this check.
3. Keep full screenshot width and at least **1.5 source-image widths of vertical
   context** (1170px for a 780px-wide capture), plus the normal 300px padding
   when that requires a larger crop. Smaller padding cannot bypass this floor. If
   the original image is shorter, all available height is retained. There is no
   fixed height cap. For product-hero findings, retain the product-image tail,
   review row, complete headline, subheadline/insertion gap, all benefit bullets
   and the nearby price/CTA where available — typically about 1280–1500px tall at
   780px wide. Choose boundaries by these landmarks, not a tiny radius around the
   defect.
4. If a viewport screenshot cuts off the sentence or leaves inadequate context,
   inspect and crop `full_page.png` instead. Measure its coordinates
   independently; do not assume section offsets are exact. Use another genuine
   capture if a sticky button covers the issue. Never fill in or redraw page
   content.
5. For source/target comparisons, retain full width on each side, use comparable
   context-window heights, and align the same semantic landmarks (usually the
   hero headline) approximately within each window. Never stretch, redraw or pad
   the captured page to manufacture alignment.

## Pre-Publication QA Checklist

Inspect **every card** at desktop and mobile widths before publication:

- [ ] The highlighted text/element corresponds to that card's description and
  exact FIND text; a screenshot of a nearby issue fails this check.
- [ ] The full problematic phrase is visible and the red frame surrounds it
  without obscuring letters.
- [ ] Surrounding funnel content makes the location recognizable; the frame is
  inside the context image rather than around its outer edge.
- [ ] Missing-content evidence shows a green source box and a red line at the
  actual target insertion gap. Both screenshots retain the complete shared
  heading and adjacent content; a boxed neighboring bullet list or a clipped
  headline fails this check.
  Apply the source-only evidence exception for missing comments; do not add a
  repeated target screenshot or translated comment blocks just to meet this check.
- [ ] Literal copy edits use a compact target thumbnail with a working full-image
  preview. Missing/structural comparisons are already expanded and readable.
  Full previews preserve original aspect ratio and context without overflow.
- [ ] The approved report-format contract is applied: default Both pages and All
  Feedback; correct category colors; neutral outlines; working COPY/reset and
  Done/uncheck states; exact complete copy; centered addition text and button.
- [ ] Each new/revised finding passed the report contract's instruction-headline
  check: explicit `feedback` tells the builder the action, target/location and
  intended result. The visible headline agrees with all evidence cards and copy
  pairs; no accepted repair or necessary limitation disappeared during shortening.
- [ ] Every separate location mentioned by the finding has visible evidence. Do
  not silently use one screenshot for several unseen corrections.
  For body-bold findings, follow the single-example exception and retain the full
  location inventory privately. Offer findings mark all relevant defects within
  one offer screenshot.
- [ ] Every confirmed missing element, bullet, paragraph and headline is included
  in feedback or has a specific standing exclusion/owner acceptance recorded.
  "Similar benefit elsewhere", "repetitive" and "unlikely to affect conversion"
  are not valid reasons to suppress a completeness finding. A moved equivalent
  must have an identified target counterpart, not just a matching topic.
- [ ] No finding or owner question targets the excluded final CTA section,
  including missing copy or bullets, except a confirmed wrong-product template
  leftover in non-button copy/images. Confirm the recorded section boundaries
  without extending this exclusion to adjacent FAQs, earlier benefits or checkout.
- [ ] No finding or owner question corrects a discount percentage, regardless of
  its check tag or location. A 50% versus "up to 70%" banner difference is excluded
  just like percentage arithmetic; retain unrelated valid price/charge findings.
- [ ] Price findings distinguish displayed totals from explicit per-piece prices:
  retain small total-price mismatches, suppress EUR per-piece rounding differences
  of one or two cents, and flag per-piece discrepancies greater than one euro.
  Do not infer an actual payment-charge error from a display-only observation.
- [ ] Offer quantities, framing, labels and eligible prices follow the competitor
  unless a specific sheet override (or explicit current owner instruction) is
  recorded. Do not dismiss `2+1` versus `3x` merely because the unit count matches.
  Apply the crossed-out reference-price exception: an acceptable approximately
  double 1x anchor or scoped owner-approved anchor need not match the competitor.
- [ ] The sheet's country/template pair determines most-popular presentation:
  SE + Health uses 5x; otherwise apply the source/default and explicit overrides
  above. Separately verify actual preselection from untouched initial-state
  evidence, with express shipping and a matching summary where selection controls
  exist. Do not infer preselection from a badge or recommend removing intentional
  express selection/charge or mistake a reviewer-selected state for the default.
- [ ] No visual finding or owner question flags the intentional scrolling-logo
  overlap behind the endorsement heading/stars; apply the standing template
  exception before generic overlap/readability checks.
- [ ] Copy blocks contain only the meaningful fragment that needs changing, with
  no unnecessary unchanged sentence text. Full rewrites remain complete, and
  separated changes have separate copy pairs. Copy labels and action notes agree
  with the actual scope of the replacement.
