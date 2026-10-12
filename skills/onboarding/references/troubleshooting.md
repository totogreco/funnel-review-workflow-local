# Troubleshooting

Explain the cause in plain words, then fix it. Re-run `python3 tools/onboarding_check.py`
(with `--live` for the last three checks) afterwards.

## Google

| Symptom | Cause | Fix |
| --- | --- | --- |
| "Access blocked: app has not completed verification" | Their Google email isn't a Test user on their app | Add it in part 4 of `google-client` |
| "unverified app" warning | Normal for their own app | **Advanced** → **Go to Funnel Review (unsafe)** |
| "Google Sheets API has not been used in project" | Sheets API not enabled | Redo part 2 of `google-client` in the same project |
| `credentials.json` missing after download | The file is named `client_secret_….json` in Downloads | Move it into this folder as `credentials.json` |
| `google-signin` fails with "sign in again", or it worked last week | In Testing mode, Google sign-ins last 7 days | Rerun `.venv/bin/python tools/google_auth.py` |
| `invalid_client` | Wrong or deleted key file | Download the JSON again (part 5 of `google-client`) and replace `credentials.json` |
| `live-sheet` fails with 403 / "permission" | They signed in with a Google account that can't open the work sheet | Delete `token.json` and sign in again with the account they use for the sheet |
| `live-sheet` fails with 404 / "not found" | Wrong `FUNNEL_SHEET_ID` | Paste the sheet link again |
| "tab ... is empty" / range error | `FUNNEL_SHEET_TAB` isn't `FUNNEL-BUILDING` | Set it back to `FUNNEL-BUILDING` |

## Render (publishing)

| Symptom | Fix |
| --- | --- |
| `live-upload-token` says "rejected: wrong token" | Paste the token again; ask the owner if it was changed |
| `live-render` times out or 502/503 | The service may be waking up or redeploying; wait a minute and rerun `--live` |
| Upload says "the live page differs and is newer" | Someone (or the dashboard) published the same funnel more recently. Ask the owner before using `--force` |
| Upload says "draft page" | The review is not complete; finish the missing checks instead of uploading a draft |

## Tools

| Symptom | Fix |
| --- | --- |
| `command not found: uv` right after installing | Use `~/.local/bin/uv`, or open a new terminal |
| "Executable doesn't exist" (Playwright) | `.venv/bin/python -m playwright install chromium` |
| macOS blocks Chromium | Allow it in **System Settings → Privacy & Security** |
| A tool fails with `ModuleNotFoundError` | Use `.venv/bin/python`, not `python3`; or reinstall: `uv pip install --python .venv/bin/python -r requirements.txt` |
| Something asks for `OPENROUTER_API_KEY` | Not used in this folder; the command came from the main project. Use the steps in `workflows/funnel_review.md` |
