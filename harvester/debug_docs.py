#!/usr/bin/env python3
"""Triage script: enumerate all ClickUp docs across every scope and check page access."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CLICKUP_API_KEY")
WORKSPACE_ID = os.getenv("CLICKUP_WORKSPACE_ID")
HEADERS = {"Authorization": API_KEY, "Accept": "application/json"}
BASE = "https://api.clickup.com/api/v3"
OUT = "/tmp/clickup_triage.txt"


def fetch_docs(parent_type=None):
    """Paginate through /docs for a given parent_type (or no filter).
    Stops when cursor exhausted, batch empty, or cycling detected."""
    docs = {}
    seen_ids = set()
    cursor = None
    page = 0
    label = parent_type or "NONE"
    while True:
        params = {"limit": 100}
        if parent_type:
            params["parent_type"] = parent_type
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{BASE}/workspaces/{WORKSPACE_ID}/docs", headers=HEADERS, params=params, timeout=30)
        except Exception as e:
            print(f"  [{label}] page {page}: timeout/error ({e}), stopping")
            break
        if r.status_code != 200:
            print(f"  [{label}] page {page}: HTTP {r.status_code}")
            break
        data = r.json()
        batch = data.get("docs", [])
        new_ids = {d.get("id") for d in batch if d.get("id")} - seen_ids
        if not new_ids and batch:
            print(f"  [{label}] page {page}: cycle detected (all {len(batch)} IDs already seen), stopping")
            break
        for d in batch:
            did = d.get("id")
            if did and did not in docs:
                docs[did] = {"name": d.get("name", ""), "scopes": set()}
            if did:
                docs[did]["scopes"].add(label)
                seen_ids.add(did)
        cursor = data.get("next_cursor")
        print(f"  [{label}] page {page}: {len(batch)} docs ({len(new_ids)} new), has_more={bool(cursor)}")
        page += 1
        if not cursor or not batch:
            break
    return docs


def fetch_pages(doc_id):
    """Try to fetch pages for a doc; return (count, error_str)."""
    for did in [doc_id, f"d-{doc_id}"]:
        try:
            r = requests.get(
                f"{BASE}/workspaces/{WORKSPACE_ID}/docs/{did}/pages",
                headers=HEADERS,
                params={"content_format": "text/md", "max_page_depth": -1},
                timeout=30,
            )
            if r.status_code == 200:
                pages = r.json() if isinstance(r.json(), list) else r.json().get("pages", [])
                return len(pages), "-"
            if r.status_code == 404:
                continue
            return 0, str(r.status_code)
        except Exception as e:
            return 0, type(e).__name__
    return 0, "404"


def main():
    all_docs = {}

    scopes = ["WORKSPACE", "SPACE", "FOLDER", "LIST", "EVERYTHING", None]
    for scope in scopes:
        print(f"\nFetching scope: {scope or 'NONE (no filter)'}")
        batch = fetch_docs(scope)
        for did, info in batch.items():
            if did not in all_docs:
                all_docs[did] = {"name": info["name"], "scopes": set()}
            all_docs[did]["scopes"] |= info["scopes"]

    print(f"\nUnique docs found: {len(all_docs)}")
    print("Fetching pages for each doc...")

    rows = []
    for did, info in sorted(all_docs.items()):
        count, err = fetch_pages(did)
        rows.append((did, info["name"], ",".join(sorted(info["scopes"])), count, err))
        if count > 0:
            print(f"  {did}: {count} pages")

    with open(OUT, "w") as f:
        f.write(f"{'doc_id':<20} {'page_count':>10} {'error':<8} {'found_in':<40} doc_name\n")
        f.write("-" * 120 + "\n")
        for did, name, scopes, count, err in rows:
            f.write(f"{did:<20} {count:>10} {err:<8} {scopes:<40} {name}\n")

    with_pages = sum(1 for *_, c, _ in rows if c > 0)
    errors_404 = sum(1 for *_, _, e in rows if e == "404")
    other_errors = sum(1 for *_, _, e in rows if e not in ("-", "404"))
    print(f"\nDone. {len(rows)} docs total: {with_pages} with pages, {errors_404} 404s, {other_errors} other errors")
    print(f"Results written to {OUT}")


if __name__ == "__main__":
    main()
