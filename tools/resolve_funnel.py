#!/usr/bin/env python3
"""Resolve a funnel row from the FUNNEL-BUILDING sheet.

Reads the configured Google Sheet, matches the requested funnel by
FUNNEL ID, Brand name + COUNTRY, or Nr. + COUNTRY, and returns
structured data the funnel review workflow needs.

Usage:
    python3 tools/resolve_funnel.py --id "SE 195"
    python3 tools/resolve_funnel.py --brand Manvra --country SE
    python3 tools/resolve_funnel.py --nr 195 --country SE
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path

COUNTRY_MAP = {
    "SE": {"market": "Sweden", "language": "Swedish", "currency": "SEK"},
    "NLBE": {"market": "Netherlands/Belgium", "language": "Dutch", "currency": "EUR"},
    "NL": {"market": "Netherlands", "language": "Dutch", "currency": "EUR"},
    "BE": {"market": "Belgium", "language": "Dutch", "currency": "EUR"},
    "DE": {"market": "Germany", "language": "German", "currency": "EUR"},
    "FR": {"market": "France", "language": "French", "currency": "EUR"},
    "ES": {"market": "Spain", "language": "Spanish", "currency": "EUR"},
    "IT": {"market": "Italy", "language": "Italian", "currency": "EUR"},
    "DK": {"market": "Denmark", "language": "Danish", "currency": "DKK"},
    "NO": {"market": "Norway", "language": "Norwegian", "currency": "NOK"},
    "FI": {"market": "Finland", "language": "Finnish", "currency": "EUR"},
    "PT": {"market": "Portugal", "language": "Portuguese", "currency": "EUR"},
    "AT": {"market": "Austria", "language": "German", "currency": "EUR"},
    "CH": {"market": "Switzerland", "language": "German", "currency": "CHF"},
    "PL": {"market": "Poland", "language": "Polish", "currency": "PLN"},
    "UK": {"market": "United Kingdom", "language": "English", "currency": "GBP"},
    "US": {"market": "United States", "language": "English", "currency": "USD"},
}

HEADERS = [
    "Funnel Status",
    "FunnelBuilder",
    "Store",
    "COUNTRY",
    "Nr.",
    "FUNNEL ID",
    "Competitor Funnel",
    "Brand name",
    "Our Funnel Link",
    "Prices/Bundles",
    "Template",
    "Note",
]


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).strip().lower()


def _id_key(text: str) -> str:
    """FUNNEL ID compared without any whitespace and case: 'NLBE235', 'nlbe 235' and 'NLBE\u00a0235' are one ID."""
    return "".join(unicodedata.normalize("NFKC", text or "").split()).upper()


def _load_env() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    result: dict[str, str] = {}
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip("'\"")
    return result


def _get_credentials(env: dict[str, str]):
    from google.oauth2.credentials import Credentials

    token_path = Path(env.get("GOOGLE_TOKEN_PATH", "token.json"))
    if not token_path.is_absolute():
        token_path = Path(__file__).resolve().parents[1] / token_path
    if not token_path.exists():
        print(f"error: token not found at {token_path}", file=sys.stderr)
        print("Sign in to Google first: .venv/bin/python tools/google_auth.py", file=sys.stderr)
        sys.exit(1)
    # Reuse the token's granted scopes. Requesting a different readonly scope
    # during refresh fails for the shared Sheets/Drive authorization.
    # This resolver still performs only Sheets read operations.
    return Credentials.from_authorized_user_file(str(token_path))


def _read_sheet(env: dict[str, str]) -> list[dict[str, str]]:
    from googleapiclient.discovery import build

    sheet_id = env.get("FUNNEL_SHEET_ID") or env.get("SHEET_ID")
    tab = env.get("FUNNEL_SHEET_TAB", "FUNNEL-BUILDING")
    if not sheet_id:
        print("error: FUNNEL_SHEET_ID (or SHEET_ID) not set in .env", file=sys.stderr)
        sys.exit(1)

    creds = _get_credentials(env)
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=f"{tab}!A1:L1000")
        .execute()
    )
    raw_rows = result.get("values", [])
    if not raw_rows:
        print(f"error: tab '{tab}' is empty", file=sys.stderr)
        sys.exit(1)

    headers = [h.strip() for h in raw_rows[0]]
    rows: list[dict[str, str]] = []
    for raw in raw_rows[1:]:
        row = {}
        for i, header in enumerate(headers):
            row[header] = raw[i].strip() if i < len(raw) else ""
        rows.append(row)
    return rows


def _derive_locale(country_code: str) -> dict[str, str]:
    code = country_code.strip().upper()
    if code in COUNTRY_MAP:
        return COUNTRY_MAP[code]
    return {"market": code, "language": "unknown", "currency": "unknown"}


def _match_rows(
    rows: list[dict[str, str]],
    *,
    funnel_id: str | None = None,
    brand: str | None = None,
    country: str | None = None,
    nr: str | None = None,
) -> list[dict[str, str]]:
    matches = []
    for row in rows:
        if funnel_id and _id_key(funnel_id):
            if _id_key(row.get("FUNNEL ID", "")) == _id_key(funnel_id):
                matches.append(row)
                continue
        if brand and country:
            row_brand = _normalize(row.get("Brand name", ""))
            row_country = _normalize(row.get("COUNTRY", ""))
            if _normalize(brand) in row_brand and _normalize(country) == row_country:
                matches.append(row)
                continue
        if nr and country:
            row_nr = _normalize(row.get("Nr.", ""))
            row_country = _normalize(row.get("COUNTRY", ""))
            if _normalize(nr) == row_nr and _normalize(country) == row_country:
                matches.append(row)
                continue
        if brand and not country and not nr:
            row_brand = _normalize(row.get("Brand name", ""))
            if _normalize(brand) in row_brand:
                matches.append(row)
    return matches


def _format_result(row: dict[str, str]) -> dict:
    country_code = row.get("COUNTRY", "").strip()
    locale = _derive_locale(country_code)
    result = {
        "funnel_id": row.get("FUNNEL ID", ""),
        "brand_name": row.get("Brand name", ""),
        "country": country_code,
        "store": row.get("Store", ""),
        "competitor_url": row.get("Competitor Funnel", ""),
        "our_url": row.get("Our Funnel Link", ""),
        "target_market": locale["market"],
        "target_language": locale["language"],
        "currency": locale["currency"],
        "prices_bundles": row.get("Prices/Bundles", "") or None,
        "template": row.get("Template", ""),
        "funnel_status": row.get("Funnel Status", ""),
        "funnel_builder": row.get("FunnelBuilder", ""),
        "note": row.get("Note", "") or None,
    }
    return result


def main() -> None:
    os.chdir(Path(__file__).resolve().parents[1])

    parser = argparse.ArgumentParser(
        description="Resolve a funnel from the FUNNEL-BUILDING sheet."
    )
    parser.add_argument("--id", dest="funnel_id", help="FUNNEL ID (e.g. 'SE 195')")
    parser.add_argument("--brand", help="Brand name (e.g. 'Manvra')")
    parser.add_argument("--country", help="COUNTRY code (e.g. 'SE', 'NLBE')")
    parser.add_argument("--nr", help="Nr. (e.g. '195')")
    parser.add_argument(
        "--list", action="store_true", help="List all funnels instead of matching"
    )
    args = parser.parse_args()

    if not args.funnel_id and not args.brand and not args.nr and not args.list:
        parser.error("provide --id, --brand, --nr, or --list")

    env = _load_env()
    rows = _read_sheet(env)

    if args.list:
        for row in rows:
            fid = row.get("FUNNEL ID", "")
            brand = row.get("Brand name", "")
            country = row.get("COUNTRY", "")
            status = row.get("Funnel Status", "")
            print(f"{fid:<12} {brand:<20} {country:<6} {status}")
        return

    matches = _match_rows(
        rows,
        funnel_id=args.funnel_id,
        brand=args.brand,
        country=args.country,
        nr=args.nr,
    )

    if not matches:
        print("error: no matching funnel found", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        print(
            f"error: {len(matches)} rows match — add --country or --nr to disambiguate:",
            file=sys.stderr,
        )
        for m in matches:
            print(
                f"  {m.get('FUNNEL ID', '')}  {m.get('Brand name', '')}  {m.get('COUNTRY', '')}",
                file=sys.stderr,
            )
        sys.exit(1)

    result = _format_result(matches[0])

    missing = []
    if not result["competitor_url"]:
        missing.append("Competitor Funnel")
    if not result["our_url"]:
        missing.append("Our Funnel Link")
    if missing:
        print(f"error: row matched but missing: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
