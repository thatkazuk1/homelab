#!/usr/bin/env python3
"""Generate handbook fleet inventory page from Komodo Core's ListServers API."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader

KOMODO_URL = "https://komodo.ts.kazuki.uk"
OUTPUT_PATH = Path("handbook/docs/architecture/fleet.md")
TEMPLATE_DIR = Path("scripts/templates")
TEMPLATE_NAME = "fleet-inventory.md.j2"


def fetch_servers() -> list:
    api_key = os.environ.get("KOMODO_API_KEY")
    api_secret = os.environ.get("KOMODO_API_SECRET")
    if not api_key or not api_secret:
        print("ERROR: KOMODO_API_KEY and KOMODO_API_SECRET must be set", file=sys.stderr)
        print("Run via: sops exec-env scripts/secrets.enc.env python3 scripts/generate-fleet-inventory.py", file=sys.stderr)
        sys.exit(1)

    response = requests.post(
        f"{KOMODO_URL}/read",
        headers={
            "X-Api-Key": api_key,
            "X-Api-Secret": api_secret,
            "Content-Type": "application/json",
        },
        json={"type": "ListServers", "params": {}},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def render_page(servers: list) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_NAME)

    hosts = [
        {"name": s["name"], "address": s["info"]["address"]}
        for s in servers
    ]
    hosts.sort(key=lambda h: h["name"])

    return template.render(
        hosts=hosts,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="minutes"),
    )


def main():
    servers = fetch_servers()
    rendered = render_page(servers)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered)
    print(f"Generated {OUTPUT_PATH} ({len(servers)} hosts)")


if __name__ == "__main__":
    main()
