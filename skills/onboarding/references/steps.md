# Onboarding steps

Each `##` heading is a step id printed by `tools/onboarding_check.py`, in the checker's
order. **You:** what Claude does without asking. **Teammate:** the message to send (one
action group per message). **Verify:** how to confirm before ticking it off.

Web pages change. If a button has a different name, ask what they see.

---

# Owner request

The only thing the teammate needs from the owner is the funnel feedback token. When they
don't have it yet, give them this text to send, then continue with the other steps:

> Hi! I'm setting up the manual funnel review. Could you send me the funnel feedback
> token (`FEEDBACK_UPLOAD_TOKEN`) through the password manager?

Teammates already have access to the work sheet, and they create their own Google
sign-in key (step `google-client`); the owner never shares Google credentials.

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
The teammate creates their **own** Google Cloud project and sign-in key. Free, no billing
needed. It's five small steps: send them one at a time as "part 1 of 5" etc. Tell them up
front: "This is the longest part, about 10 minutes. After this it gets quick."
Use the Google account they use for the work sheet.

**Part 1: Create a Google Cloud project**
1. Open https://console.cloud.google.com/projectcreate
2. If asked, sign in and accept the terms.
3. **Project name:** `Funnel Review`. Leave the rest as is.
4. Click **Create** and wait about 30 seconds.

**Part 2: Turn on Google Sheets access**
1. Open https://console.cloud.google.com/apis/library/sheets.googleapis.com
2. Check the project at the top is **Funnel Review** (switch it there if not).
3. Click **Enable**.

**Part 3: Set up the sign-in screen**
1. Open https://console.cloud.google.com/auth/overview
2. Click **Get started**.
3. **App name:** `Funnel Review`. **User support email:** your email. Click **Next**.
4. **Audience:** choose **External**. Click **Next**.
5. **Contact information:** your email. Click **Next**.
6. Tick the agreement box, click **Continue**, then **Create**.

**Part 4: Allow your own account to sign in**
1. Open https://console.cloud.google.com/auth/audience
2. Under **Test users**, click **Add users**.
3. Enter your own Google email (the one you use for the work sheet). Click **Save**.

**Part 5: Create the key file**
1. Open https://console.cloud.google.com/auth/clients
2. Click **Create client**.
3. **Application type:** **Desktop app**. **Name:** `Funnel Review`.
4. Click **Create**.
5. In the pop-up, click **Download JSON**. (If it closed: click the client name, then
   the download icon next to the client secret.)

**You (after part 5):** move the newest `~/Downloads/client_secret_*.json` to
`credentials.json` in this folder. If none is there, ask where it saved. Leave
`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` empty.
**Verify:** checker shows `google-client` done.

## funnel-sheet
**Teammate:**
> **Step N: Link the work sheet**
> Open the sheet we work in (the one with the **FUNNEL-BUILDING** tab), copy the link
> from the address bar and paste it here.

**You:** extract the ID (between `/d/` and `/edit`), set `FUNNEL_SHEET_ID=<id>`. Keep
`FUNNEL_SHEET_TAB=FUNNEL-BUILDING`.

## google-signin
**You:** start in the background: `.venv/bin/python tools/google_auth.py`
**Teammate:**
> **Step N: Connect your Google account**
> A Google sign-in page is opening in your browser.
> 1. Choose the Google account you use for the work sheet.
> 2. If you see **"Google hasn't verified this app"**: that's expected, because it's
>    your own app. Click **Advanced**, then **Go to Funnel Review (unsafe)**.
> 3. Allow access to view your spreadsheets and click **Continue**.
> 4. When the page says the flow is complete, close the tab.
>
> Reply **done** when finished.

**Verify:** the command printed `saved token.json` and exited 0; checker shows
`google-signin` done.
If Google says **"Access blocked"**, their email is missing from Test users (part 4).

**Tell them:** while their Google app is in *Testing* mode, this sign-in expires after
7 days, and they repeat only this step ("sign me in to Google again"). Optional fix: on
https://console.cloud.google.com/auth/audience click **Publish app** → **Confirm**. The
"unverified app" warning stays, but sign-ins stop expiring weekly. Then delete
`token.json` and redo this step once.

---

# Phase 4: Publishing to Render

## upload-token
The funnel feedback token is always provided by the owner;
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
