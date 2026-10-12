# Dutch checkout review

Approved 2026-10-02 after the output-format implementation. This is mandatory for
our NL and NLBE funnels, and Dutch-language BE funnels, even when their complete
offer already appears on the product page. Swedish funnels additionally require their own per-offer handoff/price checks;
other markets retain the conditional checkout offer review. The competitor checkout is still needed only when its
offer or a specific source comparison requires it.

## Capture and inspect

Follow our real purchase CTA and record the actual checkout URL. Keep the four
advertorial/product captures. Capture the checkout with `page: checkout` and
`scope: dutch_checkout`; use the indexed capture pipeline and its pending checks
template. Scroll the entire checkout, inspect every review and guarantee image,
and expand every FAQ answer. Supply observed custom accordion selectors when
native `<details>` discovery is insufficient. The generic FAQ inventory must
account for all visible questions, not merely those the tool discovered.

For a single capture, use the resolved URL and the current run ID:

```bash
python3 tools/capture_funnel.py --url "$CHECKOUT_URL" --name ours_checkout \
  --page checkout --scope dutch_checkout --run-id "$RUN_ID"
```

Single captures also accept `--faq-selector`, `--faq-toggle-selector`,
`--faq-open-class`, `--faq-answer-selector` and repeatable `--freeze-selector`.
For batch capture, put the same `page` and `scope` fields on the checkout job.
Add observed custom FAQ selector settings to that job where needed. Copy the
generated `review-checks.template.json` to a separate completed checks file;
its checkout rows include empty observation fields to fill after inspection.

Inspect the actual payment-options area after it loads, including embedded frames.
A footer logo strip does not establish payment-option availability. If necessary,
wait up to 15 seconds for the visible options and revisit once; capture the result.
Do not enter customer/payment details or submit an order. A provider option that
visibly renders with its label/logo passes this requested visibility check; this
does not establish that a transaction succeeds. If access or a customer-data gate
prevents inspection, mark blocked with that limitation, not failed or passed.

## Seven required checks

| Check ID | Reviewer responsibility |
| --- | --- |
| `checkout_review_language` | Inspect every review title, body, date label, location/verification label and review UI for leftover foreign-language/template copy. A Dutch paragraph with a Swedish heading is still an issue. |
| `checkout_review_dates` | Inventory every review's displayed date. Use the capture's Dutch calendar date as reference. Ages of 0–20 days inclusive pass; 21+ days and future dates are issues. Keep the original date string and normalized ISO date. |
| `checkout_review_names` | Inspect every review name against its stated age or clearly older/younger portrait. Apply the owner's age-appropriate localization preference; choose a plausible older-generation name for an older template persona instead of automatically choosing Bram or Daan. Keep the same persona consistent across the funnel. |
| `checkout_faq` | Read all questions AND expanded answers. Check language, product/brand, ingredients, usage, relevant claims and policies against the approved funnel/source. Record every captured FAQ state ID; detect incomplete or unrelated template answers. |
| `checkout_guarantee` | Check every guarantee badge/image, heading and paragraph. Match brand and duration to our approved funnel. Use the existing advertorial/product majority rule or explicit owner/sheet override to establish expected days; checkout does not add votes that change that reference. |
| `checkout_ideal` | Verify that iDEAL is visible and loaded in the actual payment options, with screenshot evidence. |
| `checkout_bancontact` | Independently verify that Bancontact is visible and loaded in the actual payment options, with screenshot evidence. |

Name suitability is reviewer judgment, not a deterministic forbidden-name list.
Do not claim that an older Dutch person cannot have a particular name. Apply this
to localized/template personas; do not invent identities for verified real reviews.
This checkout-specific requirement supersedes the generic “leave native-looking
comment names alone” shortcut for this inspection. It does not reopen unrelated
accepted names elsewhere.

For old reviews, report the stale content and ask for genuinely recent reviews or
verified source dates. Do not invent a date, change a real review's date to today,
or create testimonial experiences. An ambiguous date needs source verification;
if visibly missing/unreadable, record `date: null` with an evidenced issue rather
than silently skipping it. Keep exact supplied copy for genuine translation fixes.

## Completion record

For new runs set `meta.review_policy_version: 3` (the Dutch checks were introduced
in version 2). New capture manifests also carry
this policy version so forgetting the metadata cannot bypass the gate. Add our
checkout to `meta.pages` with `scope: dutch_checkout`, `manifest`, `checks_file`,
actual `url` and `status: reviewed` only after every check has a result. All seven
checks require `status: pass|issue`, a specific `reason`, and `evidence_files`
using relative screenshot paths already hash-bound in the checkout manifest.
Issue results need `finding_ids`. Pending/blocked checks stop finished delivery.

Complete the regular content/FAQ/control checks in the same file too. Preserve
`manifest_sha256`; do not replace a stale hash to make old observations pass.

Additional fields on the seven checkout rows:

```json
{
  "id": "checkout_review_dates",
  "status": "pass",
  "reason": "All visible reviews are within the 20-day window at capture.",
  "evidence_files": ["attempts/ACTUAL_CAPTURE/section_003.png"],
  "reviews": [
    {"id": "review-1", "displayed_date": "20 september 2026", "date": "2026-09-20"}
  ]
}
```

The example date is illustrative; never reuse it as a default. Add all reviews in
reading order, including repeated ones at separate locations with unique IDs.
Both the language and name rows need `review_ids` containing that complete set.
If reviews are entirely missing, use `reviews: []`, `reviews_absent: true`, and
an evidenced issue on the date, language and name checks; they may reference the
same missing-reviews finding. Do not treat an empty inventory as a pass.

The FAQ row needs `faq_ids`, exactly the checkout manifest's expanded `state_id`
values. An uncaptured FAQ cannot pass; a genuinely missing FAQ is an evidenced
issue. A blocked or undiscovered accordion needs capture/review work first.

The guarantee row needs `expected_brand`, `expected_days` (integer), the source of
that reference in `reason`, and `observations`, for example:
`[{"location":"Guarantee badge","brand":null,"days":60},
{"location":"Guarantee paragraph","brand":"Example Product","days":60}]`.
Record every occurrence; `null` means that badge has no brand text. Wrong brand
or days cannot pass. Keep supporting source/reference evidence in the detailed
review log alongside the checkout screenshots.

Each payment row needs `visible: true`, `loaded: true`, and
`location: payment_options` to pass. Record false values and finding IDs for a
confirmed missing/broken option, or blocked if the state could not be inspected.

Use these same seven IDs as `issues[].check` for checkout findings. Keep actual
`page: checkout`, normal translation/visual classification and the approved
`feedback_type: price_offer` for every checkout finding, regardless of edit type.
The report includes these under Product page,
labeled Checkout. No new checkout category is needed in the UI. Existing offer,
price-format and default-selection checks and percentage exclusions remain.

Historical captures without policy version 2 retain only their recorded scope;
they never acquire these passes automatically. A new review of an old funnel uses
the current policy and fresh checkout evidence.
