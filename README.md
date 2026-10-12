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
4. **Add the funnel feedback token.** The owner provides the `FEEDBACK_UPLOAD_TOKEN`
   privately. Open the `.env` file in this folder, paste the token right after
   `FEEDBACK_UPLOAD_TOKEN=`, save and close. (Claude opens the file for you at this step.)

Claude walks you through the setup one step at a time and checks each step. You'll:
- create your own Google sign-in key (free, about 10 minutes, Claude guides every click),
- paste the link of the work sheet you already use (the one with the FUNNEL-BUILDING tab),
- add the funnel feedback token, which the owner sends you privately.

After setup, start a review with: **review funnel NLBE 250** (any FUNNEL ID from the sheet).

## For the owner: adding a teammate

1. **Funnel feedback token:** send them `FEEDBACK_UPLOAD_TOKEN` through a password manager.
   It is the same token for everyone. To revoke access for everyone, change it in Render →
   Environment (that restarts the service) and send the new one to the remaining reviewers.
2. Give them this folder (the GitHub repo, or a zip). `.env`, `token.json` and
   `credentials.json` are never included.

That's all: teammates already have access to the work sheet, and each one creates their
own Google sign-in key during onboarding. You never share your Google credentials.

## Check the setup without publishing

```sh
python3 tools/onboarding_check.py --live
```

Reads the sheet, opens the Render site and tests the upload token. Publishes nothing.

## What's inside

See [CLAUDE.md](CLAUDE.md) for how the folder is organised and
[workflows/funnel_review.md](workflows/funnel_review.md) for the full review process.
