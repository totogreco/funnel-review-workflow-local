# Funnel Review (manual, local)

Reviews a competitor funnel against our translated funnel (advertorial, product page,
checkout), builds a feedback page for the funnel builder and publishes it to the team
site: **https://ad-translation.onrender.com/feedback/**

Runs on your own Mac with Claude Code. No OpenRouter and no AI API keys: Claude does the
review on your own Claude account.

## For the teammate: getting started

1. Install Claude Code and sign in with your Claude account (Pro or Max; Max recommended,
   because a full review is long): https://claude.com/claude-code
2. Open this folder in Claude Code (in VS Code: **File → Open Folder**, then open Claude Code).
3. Type: **onboard me**

Claude walks you through the setup one step at a time and checks each step. You'll need
three things from the owner: access to the funnel sheet, the team's Google sign-in client
and the upload token. Claude tells you exactly what to ask for.

After setup, start a review with: **review funnel NLBE 250** (any FUNNEL ID from the sheet).

## For the owner: adding a teammate

Do these once per teammate. Nothing here goes into the folder or into git.

1. **Sheet:** share the funnel spreadsheet (tab `FUNNEL-BUILDING`) with their Google
   account as **Viewer**, and send them the link.
2. **Google sign-in:** in Google Cloud for the app behind your `GOOGLE_CLIENT_ID`, open
   https://console.cloud.google.com/auth/audience → **Test users** → **Add users** → their
   email. Send them `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` through a password manager.
   (Sign-ins expire every 7 days while the app is in Testing; **Publish app** stops that.)
3. **Upload token:** send them `FEEDBACK_UPLOAD_TOKEN` through a password manager. It is
   the same token for everyone. To revoke access for everyone, change it in Render →
   Environment (that restarts the service) and send the new one to the remaining reviewers.
4. Give them this folder (zip, or a private git repo). `.env`, `token.json` and
   `credentials.json` are never included.

## Check the setup without publishing

```sh
python3 tools/onboarding_check.py --live
```

Reads the sheet, opens the Render site and tests the upload token. Publishes nothing.

## What's inside

See [CLAUDE.md](CLAUDE.md) for how the folder is organised and
[workflows/funnel_review.md](workflows/funnel_review.md) for the full review process.
