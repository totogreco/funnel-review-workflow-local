# Swedish offer buttons and checkout prices

For every new Swedish (SE) funnel review, test **each offer-selection button** in
our funnel, even when prices and bundles already appear on the product page.
Include repeated offer buttons and relevant selected-offer states of shared or
sticky purchase buttons. A working first offer does not establish that the other
offers work. Use the existing interaction inventory to enumerate every instance.

Resolve the sheet's `COUNTRY` and `Template` together and retain both in report
metadata. Apply the main skill's most-popular rule: SE + Health uses 5x, regardless
of the competitor's most-popular quantity. Keep this presentation check separate
from initial preselection and from the clicked handoff: clicking a different
bundle must still open that bundle's checkout, not silently switch it to 5x.

1. Record the source page, exact location, observed selector, offered product,
   variant, quantity, displayed total, currency and shipping terms.
2. Click that specific offer in a fresh state. Follow redirects/new tabs until the
   checkout loads. Allow up to **3 seconds** for the new tab/navigation after the
   click; continue sooner if it appears. If the page stays on the source, fail the
   capture rather than save the product page as checkout evidence. Then allow the
   destination to load and settle under the capture budget. Verify that this is
   our intended checkout and that the selected
   product, variant and bundle are the ones that were clicked.
3. Read the selected checkout summary. Compare the bundle total against the
   presentation on the source page. **The product-page price is leading** (owner
   rule, 2026-10-02): when checkout differs, the feedback is to set the checkout
   price to the product-page price, never to change the product page to match
   checkout. If the product page itself shows conflicting prices for one bundle,
   take the price its savings/reference figures support and also align the
   outliers on the page. Keep per-piece prices separate from bundle
   totals. Retain accepted Swedish per-piece rounding; actual bundle-total errors
   still need feedback. Check currency, shipping and final payable total. Explain
   legitimate shipping/other charge differences; flag undisclosed or incorrect
   charges. Never give discount-percentage feedback.
4. Save source and resulting checkout screenshots for **each click**. Do not
   reopen a generic checkout URL in an empty session and assume its default offer
   proves which option the button selected. Do not manually switch the checkout
   offer before capturing the clicked result. Repeat for every offer/button state.
5. Record pass, evidenced issue, or blocked. A dead button, wrong checkout, wrong
   selected bundle or price mismatch needs feedback. Access failures that prevent
   inspection are blocked, not proof of a defect. Do not submit an order or enter
   customer/payment information.

## Capture the actual handoff

The indexed capture tool accepts this job in `--jobs` JSON. Use observed URLs and
selectors, not these placeholders:

```json
{
  "name": "ours_checkout_offer_three_top",
  "url": "https://our.example/checkout",
  "page": "checkout",
  "scope": "price_and_offer",
  "offer_handoff": {
    "source_url": "https://our.example/product",
    "selector": "#observed-three-bottle-button"
  }
}
```

This opens the source page, captures it, clicks the unique selector, follows the
navigation/new tab in the same isolated browser context, then captures checkout.
It records the click and final URL in the manifest. `radio_selections` cannot be
combined with this job because changing the checkout selection would hide a
broken handoff. A selector that only selects a product-page offer, followed by a
separate purchase button, requires testing/capturing that selected state through
the browser; do not mislabel the selector's no-navigation behavior as broken.
The handoff job supports a verified click sequence via `offer_handoff.selectors`
when the offer selector and purchase button are separate controls. Record the
same ordered `selectors` list on the offer result instead of its single `selector`.

## Completion gate

New runs set `meta.review_policy_version: 3`; capture manifests also carry version
3. Add `meta.swedish_offer_checks_file`, pointing to the structured record below.
Old reviews keep their historical scope; a new review cannot omit these checks.

```json
{
  "source_manifest_sha256": {"advertorial": "ACTUAL_HASH", "product": "ACTUAL_HASH"},
  "inventory": {
    "status": "pass", "reason": "Enumerated every offer/button location and state.",
    "button_ids": ["three-bottles-top"]
  },
  "offers": [{
    "id": "three-bottles-top", "page": "product", "location": "Three-bottle offer · top",
    "selector": "#observed-three-bottle-button", "action": "Clicked the three-bottle offer",
    "status": "pass", "reason": "Correct checkout, selected bundle and price.",
    "source_evidence": ["attempts/ACTUAL_SOURCE/section_003.png"],
    "checkout_loaded": true, "correct_destination": true,
    "actual_url": "https://our.example/checkout?offer=three",
    "checkout_manifest": "PATH_TO_THIS_CLICK_CAPTURE/manifest.json",
    "checkout_manifest_sha256": "ACTUAL_HASH",
    "checkout_evidence": ["attempts/ACTUAL_CHECKOUT/full_page.png"],
    "presented": {"product": "Example", "variant": "standard", "quantity": 3,
      "currency": "SEK", "offer_total_minor": 59900, "shipping_minor": 0},
    "checkout": {"product": "Example", "variant": "standard", "quantity": 3,
      "currency": "SEK", "offer_total_minor": 59900, "shipping_minor": 0,
      "payable_total_minor": 59900},
    "shipping_reason": "Free shipping advertised and selected. No additional charges."
  }]
}
```

Inventory both source pages and preserve their manifest hashes. Each button/state
needs a unique result and its own clicked checkout capture. Normalize money to
integer öre (599 kr = 59900), without changing the literal displayed evidence.
Optional `other_charges_minor` defaults to zero; document every such charge in
`shipping_reason` and verify it against the presentation before marking pass.
Pass results require matching product/variant/quantity/currency/bundle total and
reconciled payable amounts. Issue rows need existing `finding_ids`; pending or
blocked rows stop completed delivery. Proven dead buttons/navigation errors may
use `checkout_loaded: false` and `outcome: dead_button|navigation_error` with
source evidence and an actual observed failure reason, without invented checkout
values. Keep working offer checks even if another button fails.

Use `check: offer_checkout_handoff` for routing/selection failures and
`check: checkout_offer_price` or the existing pricing checks for price errors.
Normally place the finding on the source product/advertorial page, with the
clicked checkout evidence attached. If the finding is on checkout, retain a
reviewed `price_and_offer` checkout entry in `meta.pages`. Give one clear action
with exact expected bundle/price; use the orange `price_offer` presentation and
expanded comparison evidence when helpful. Keep button-wording exclusions intact.
When comparing our displayed offer with our checkout, set evidence-pair
`source_label: OUR OFFER` and `target_label: OUR CHECKOUT`; do not mislabel our
offer screenshot as the competitor. Normal competitor comparisons keep their
default banners.
