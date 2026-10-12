---
name: onboarding
description: Guided, one-step-at-a-time setup for a teammate who wants to run the manual funnel review on their own Mac and publish to the team's Render site. Installs the tools, has them create their own Google sign-in key (read-only sheet access) and adds the shared Render upload token, checking each step before moving on. Use when someone says "onboard me", "set up", "get started", "first time", "new machine", or when tools/onboarding_check.py reports missing steps.
---

# Onboarding

The person you are helping is a teammate, not a developer. Get them from zero to a
first published funnel review with as little effort on their side as possible:
**you run every command; they only do what needs their own browser or account.**

Progress is tracked by `tools/onboarding_check.py`. Each step id it prints matches a
section in [references/steps.md](references/steps.md), which holds the exact instructions.

## What they end up with

- The **manual funnel review** running on their Mac, with Claude Code doing the review on
  their own Claude account. No OpenRouter, no AI API keys.
- Reviews published to the **team's shared site**, `https://ad-translation.onrender.com/feedback/`,
  exactly where the owner's and the dashboard's reviews appear. It does not matter who
  onboards: every reviewer uses the same Render site and the same upload token.

## What they need

- **From the owner, only the funnel feedback token** (`FEEDBACK_UPLOAD_TOKEN`), sent
  through a password manager or another private channel, never in a group chat or email
  thread. If they don't have it yet, give them the "Owner request" text in `steps.md` and
  continue with the steps that don't need it.
- **The URL of the work sheet** they already use (the spreadsheet with the
  `FUNNEL-BUILDING` tab). Teammates already have access; just ask them to paste the link.
- **Their own Google sign-in key.** They create it themselves in step `google-client`
  (free, about 10 minutes). Never ask for or use the owner's Google client ID or secret.

## How to run the conversation

1. **Welcome (one message).** Explain in plain words: this folder reviews a competitor
   funnel against ours, writes a feedback page for the funnel builder and publishes it
   to the team site. Then list what they need (above), and that a
   Claude Pro or Max plan is needed (Max recommended; a full review is long).
2. **Check where they are.** Run `python3 tools/onboarding_check.py --json` and show
   the checklist (format below). Skip steps that already pass.
3. **One step per message**, using the template below and the text in `steps.md`.
   Never put two owner actions in one message. Steps you can do yourself (install,
   write a non-secret `.env` line), do them, report in one line, and move on.
4. **Wait for "done", then verify** with the checker. If it passes, tick it off and give
   the next step. If it fails, say what you see in plain words and give the smallest fix.
   Never move past a failing required step.
5. **If the screen looks different** (Google changes its pages), ask them to describe it
   or paste a screenshot and guide from there.
6. **Finish** with `python3 tools/onboarding_check.py --live` and the first review (see
   "Finish" in `steps.md`).

## Step message template

```
**Step 6 of 9: Connect your Google account**

1. A Google sign-in page is opening in your browser.
2. Choose the Google account you use for the work sheet.
3. ...

Reply **done** when it's finished, or tell me what you see if it looks different.
```

Bold the exact button names. Keep each message short enough to read without scrolling.

## Checklist display

Show after each verified step and whenever they ask "where are we?":

```
Setup progress: 5 of 9 done
✅ Tools on this Mac
✅ Settings file
⬜ Google Sheet        ← you are here
⬜ Publishing to Render
```

## Handling credentials

- **Links and IDs are not secret.** The sheet link may be pasted in chat: extract the
  ID (between `/d/` and `/edit`) and write `FUNNEL_SHEET_ID=<id>` yourself. Change only
  that line of `.env`; never rewrite or reorder the rest.
- **Secrets are never pasted in chat** (`GOOGLE_CLIENT_SECRET`, `FEEDBACK_UPLOAD_TOKEN`).
  Run `open -e .env`, tell them which line to paste after, to save (**Cmd+S**) and close,
  then reply done. Confirm with the checker, which only says whether a value is set.
  If they paste a secret in chat anyway, write it to `.env` for them and tell them to let
  the owner know, so the owner can decide whether to replace it.
- Never print, echo or summarise `.env`, `token.json` or `credentials.json`.
- A downloaded Google client file lands in `~/Downloads/client_secret_*.json`; move the
  newest one to `credentials.json` in this folder yourself.

## Sign-in commands

`tools/google_auth.py` waits for the person to finish in their browser. Start it in the
background, tell them what to click, and wait for it to exit before verifying.

## Rules

- Ask once before installing ("I'll install the tools this needs, OK?"), then run the
  remaining installs without asking again.
- The onboarding never publishes anything. The `--live` check tests the upload token
  without uploading a page.
- Don't edit workflows or the funnel-comparison skill during onboarding.
- Once setup is done, point them to `workflows/funnel_review.md` and how to start a
  review next time: "review funnel <FUNNEL ID>".

## References

- [references/steps.md](references/steps.md): every step in order, with exact clicks,
  what you do yourself and how to verify.
- [references/troubleshooting.md](references/troubleshooting.md): common errors and fixes.
