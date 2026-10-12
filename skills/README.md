# Project skills

- **Workflow:** the overall process, its inputs, ordered steps and outputs. Stored in `workflows/`.
- **Skill:** instructions and rules for one step or capability. Stored here.
- **Tool:** executable code that carries out an operation. Stored in `tools/`.

## Available skills

| Skill | Used for | Origin |
| --- | --- | --- |
| [funnel-comparison](funnel-comparison/SKILL.md) | Translation, visual, content, consistency and interaction checklists for funnel review, and the report format | Copied from the main project (all-ecom-automations-v1), 2026-10-12 |
| [onboarding](onboarding/SKILL.md) | First-time setup for a teammate: tools, Google sheet access, Render upload token, checked by `tools/onboarding_check.py` | Written for this folder |

The [funnel review workflow](../workflows/funnel_review.md) uses the funnel-comparison skill
for all review checklists and its [report-format contract](funnel-comparison/references/report-format.md).
Dutch-market runs also require its [checkout checklist](funnel-comparison/references/dutch-checkout.md).
Swedish runs require [offer-button and checkout-price checks](funnel-comparison/references/swedish-offers.md).
Custom funnels use the [custom funnel rules](funnel-comparison/references/custom-funnel.md).

Only load the skill the current step needs. Storing a skill does not run it.

## Keeping in sync with the main project

The funnel-comparison skill and the tools are copies. When the owner changes review rules
in the main project, copy the updated `skills/funnel-comparison/` and changed `tools/`
files here, and note the date above.

## Folder format

```text
skills/
  <skill-name>/
    SKILL.md        # YAML frontmatter with name and description, then the instructions
    references/     # Optional supporting instructions
```
