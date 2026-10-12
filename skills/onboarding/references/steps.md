# Onboarding steps

Each `##` heading is a step id printed by `tools/onboarding_check.py`, in the checker's
order. **You:** what Claude does without asking. **Teammate:** the message to send (one
action group per message). **Verify:** how to confirm before ticking it off.

Web pages change. If a button has a different name, ask what they see.

---

# Owner request

When the teammate does not have the three things from the owner yet, give them this
text to send (filled in with their Google email), then continue with Phase 1:

> Hi! I'm setting up the manual funnel review. Could you:
> 1. Share the funnel sheet (FUNNEL-BUILDING) with **<their Google email>** as Viewer, and send me the link.
> 2. Add **<their Google email>** as a Test user on our Google sign-in app
>    (https://console.cloud.google.com/auth/audience → **Add users**), and send me the
>    `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (or the credentials.json file).
> 3. Send me the `FEEDBACK_UPLOAD_TOKEN` through the password manager.

The owner's side of this is in the README ("For the owner: adding a teammate").

---

# Phase 1: Tools on this Mac

All Phase 1 steps are yours. Ask once ("I'll install the tools this needs, OK?"), then
work through them, one line per step.

## system-python
**You:** macOS ships Python 3. If the check fails: `brew install python@3.12`, or send
them to https://www.python.org/downloads/ → **Download Python** → open the installer →
click **Continue** / **Install**.
**Verify:** `python3 --version`.

## system-uv
**You:** `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`). Call it
as `~/.local/bin/uv` if `uv` is not found yet.

## venv
**You:**
```sh
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```
**Verify:** checker shows `venv` done.

## chromium
**You:** `.venv/bin/python -m playwright install chromium`
**Verify:** checker shows `chromium` done. If macOS blocks Chromium, see troubleshooting.

---

# Phase 2: Settings file

## env-file
**You:** `.env` normally ships with placeholders. If it's missing: `cp .env.example .env`
(never overwrite an existing `.env`). Leave `PUBLIC_BASE_URL` at
`https://ad-translation.onrender.com`: that is the team site every reviewer publishes to.

---

# Phase 3: Google Sheet (read-only)

## google-client
Needs item 2 from the owner.
**Teammate (when they have the two values):**
> **Step N: Add the team's Google sign-in client**
> I've opened your `.env` file in TextEdit.
> 1. Paste the client ID right after `GOOGLE_CLIENT_ID=`
> 2. Paste the client secret right after `GOOGLE_CLIENT_SECRET=`
> 3. Save (**Cmd+S**) and close.
>
> Reply **done**.

**You:** `open -e .env` before sending. If the owner sent a `credentials.json` instead,
move it (or the newest `~/Downloads/client_secret_*.json`) into this folder as
`credentials.json`.
**Verify:** checker shows `google-client` done.

## funnel-sheet
**Teammate:**
> **Step N: Link the funnel sheet**
> Open the sheet the owner shared with you, copy the link from the address bar and paste it here.

**You:** extract the ID (between `/d/` and `/edit`), set `FUNNEL_SHEET_ID=<id>`. Keep
`FUNNEL_SHEET_TAB=FUNNEL-BUILDING`.

## google-signin
**You:** start in the background: `.venv/bin/python tools/google_auth.py`
**Teammate:**
> **Step N: Connect your Google account**
> A Google sign-in page is opening in your browser.
> 1. Choose the Google account the sheet is shared with.
> 2. If you see **"Google hasn't verified this app"**: that's expected for our team's
>    own app. Click **Advanced**, then **Go to … (unsafe)**.
> 3. Allow access to view your spreadsheets and click **Continue**.
> 4. When the page says the flow is complete, close the tab.
>
> Reply **done** when finished.

**Verify:** the command printed `saved token.json` and exited 0; checker shows
`google-signin` done.
If Google says **"Access blocked"**, the owner hasn't added them as a Test user yet.

**Tell them:** while the team's Google app is in *Testing* mode, this sign-in expires
after 7 days. Then they only repeat this one step ("sign me in to Google again").

---

# Phase 4: Publishing to Render

## upload-token
Needs item 3 from the owner. The funnel feedback token is always provided by the owner;
the teammate never creates it. If they don't have it yet, give them the Owner request.
**Teammate:**
> **Step N: Add the funnel feedback token**
> The owner provides this token privately (password manager). It lets your reviews
> publish to the team site.
> 1. I've opened your `.env` file in TextEdit.
> 2. Find the line `FEEDBACK_UPLOAD_TOKEN=`
> 3. Paste the token right after the `=` (no spaces, no quotes).
> 4. Save (**Cmd+S**) and close.
>
> Reply **done**.

**You:** `open -e .env` before sending.
**Verify:** checker shows `upload-token` done. The token itself is tested in Finish.

---

# Finish

## live-sheet
## live-render
## live-upload-token
These appear only with `--live`. They read the sheet (`resolve_funnel.py --list`), open
`https://ad-translation.onrender.com/feedback/` and test the upload token without
publishing anything.

1. **You:** `python3 tools/onboarding_check.py --live`. Fix anything it reports (see
   troubleshooting). Render's first answer can take up to a minute when the service was asleep.
2. **Show them the team site:** https://ad-translation.onrender.com/feedback/. Their
   reviews will appear here, grouped by funnel builder.
3. **First review.** Ask which funnel to review (a FUNNEL ID such as `NLBE 250`, or
   brand + country). Run `.venv/bin/python tools/resolve_funnel.py --id "<FUNNEL ID>"` and
   show the two URLs it found. Then follow `workflows/funnel_review.md` from step 1.
   Before the upload in step 7, show them the staged page and ask for their OK to publish.
4. **Summarise:** what's set up, how to start next time ("review funnel <FUNNEL ID>"),
   and that the Google sign-in may need repeating after 7 days.
