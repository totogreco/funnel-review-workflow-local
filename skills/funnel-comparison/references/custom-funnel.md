# Custom funnel review

Approved by the owner on 2026-10-06 (first used for NLBE 235 MagnesiumFreeze).
Use this mode when the owner says the run is a **custom funnel**: the competitor
has no real, detailed product page, so our funnel builder made our own product
page based on our advertorial. Everything not changed here follows the normal
workflow, the canonical [funnel-comparison skill](../SKILL.md) and its standing
exclusions.

## When it applies

- The owner says so when starting the run ("run the funnel review, it's a custom
  funnel"). Record that instruction; do not infer custom mode yourself.
- If the competitor's second URL clearly is not a real product page (a thin
  offer/landing page, or the advertorial CTA ends on a tracking redirect), and
  the owner has not said "custom", ask once before reviewing the product page.
- Custom mode changes the **product page** scope only. The advertorial and the
  checkout keep their full normal review.

## Scope per stage

| Stage | Custom-funnel review |
|---|---|
| Advertorial | Full normal review against the competitor advertorial: every checklist, missing content, bold audit, sticky CTA, images, buttons. |
| Product page | Review against **our own advertorial**, not the competitor page (see below). |
| Checkout | Full normal checkout review: it must work, prices must match the funnel and the owner's offer; Dutch checkout checks for NL/NLBE, Swedish offer handoffs for SE. |

Still capture the competitor's second URL (from the sheet) as `competitor_page2`.
It is context and an offer reference only. If it cannot be reached, record that
and continue; it does not block a custom review: give its `meta.pages` entry
`status: "blocked"` and a `blocker` reason (URL, HTTP status/redirect observed).
The generator accepts this only when `meta.funnel_type` is `custom`.

## Product page: what to check

Report only what would confuse the buyer, undermine trust or break the sale:

1. **Alignment with our advertorial.** Same product, story, claims, mechanism,
   ingredients, results and numbers (customer counts, percentages, supply per
   jar). When the two pages disagree, use the advertorial as the reference and
   correct the product page, unless the owner decides otherwise.
2. **Translation.** Weird, unnatural or confusing Dutch/Swedish, leftover source
   language, foreign names copied from the competitor (e.g. American reviewer
   names), and any text that reads like translation-tool output. The normal
   importance threshold applies; heading mistakes are always reported.
3. **Cross-page consistency.** Guarantee duration (our majority rule), prices and
   price anchors, shipping promises and customer numbers across advertorial,
   product page and checkout.
4. **Wrong-product leftovers.** Statistics, banners, FAQ answers or images from
   another product (e.g. sleep-apnea or pillow statistics on a knee product).
   Always reported, also inside the final offer box.
5. **Conversion-killing bugs and visuals.** Broken or misrouted buttons, missing
   bottom sticky CTA, broken layout, clipped or overlapping content, empty
   sections, unreadable offer elements. Minor styling choices are not feedback.

Do **not** on a custom product page:

- compare element by element with the competitor page or report "missing"
  competitor sections, bullets, paragraphs, testimonials or FAQs;
- match the first testimonial or reviewer identities to competitor slots;
- run the bold-emphasis comparison (there is no source counterpart; the bold
  audit uses the advertorial only).

If nothing on the product page meets the bar above, a clean result is valid.

## Records

- Save the owner's instruction in the run folder as `owner-scope.json`
  (date, source, scope per stage) and add `meta.funnel_type: "custom"` plus a
  one-line `meta.owner_scope` to `issues.json`. The generator rejects a custom
  review without `owner_scope`, and the report's scope line then states that our
  product page was reviewed against our own advertorial.
- The product page still needs `status: reviewed` and every generated check row.
  Complete the `product:*` rows with the custom-scope result, for example
  "Custom PDP: headline matches advertorial claim" or "No source counterpart;
  bold audit applied to advertorial". Never leave them pending.
- In `content_and_visuals` for the product page, state that the custom scope
  applied and list the findings.
- Owner choices made during the run (offer prices, which number wins, branding
  to keep) go into `owner-scope.json` and the private correction history, not
  into the report.

## Lessons from the first custom run (NLBE 235)

- Translation tools may leave meta phrases such as "volgens de oorspronkelijke
  advertentietekst" or hedges like "volgens dit verhaal". Always report them.
- If the translation systematically softens the competitor's claims, ask the
  owner once (restore or keep). For MagnesiumFreeze the owner chose to restore
  the competitor claims; do not apply that to other funnels without asking.
- Keep the owner's offer price over the competitor price when given in chat;
  check bundle prices still give a per-jar saving and ask if they do not.
