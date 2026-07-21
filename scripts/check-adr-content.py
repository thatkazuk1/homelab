#!/usr/bin/env python3
"""Warn-only checks that specific ADR content still matches live/repo state.

Covers ADR-0011 (flat stack layout, pure git-tree check), ADR-0010 (SOPS wrapper
for stacks with secrets, requires Komodo API), and ADR-0005 (custom Periphery
image, git-tree check against per-host compose files). Always exits 0 — findings
are printed for the operator to review, never block a build.

Run via: sops exec-env scripts/secrets.enc.env python3 scripts/check-adr-content.py
"""

import os
import sys
from pathlib import Path

import requests
import yaml

KOMODO_URL = "https://komodo.ts.kazuki.uk"

# Known drift between this repo's stack-directory name and the name the stack is
# actually registered under in Komodo (per Sprint 3s). Applies to single-compose
# stacks only; multi-file (per-host) stacks are matched as "<dirname>-<host>".
NAME_MAP = {
    "sure": "sure-finance",
    "homeassistant": "home-assistant",
}


def komodo_headers() -> dict:
    api_key = os.environ.get("KOMODO_API_KEY")
    api_secret = os.environ.get("KOMODO_API_SECRET")
    if not api_key or not api_secret:
        print("ERROR: KOMODO_API_KEY and KOMODO_API_SECRET must be set", file=sys.stderr)
        print(
            "Run via: sops exec-env scripts/secrets.enc.env python3 scripts/check-adr-content.py",
            file=sys.stderr,
        )
        sys.exit(1)
    return {
        "X-Api-Key": api_key,
        "X-Api-Secret": api_secret,
        "Content-Type": "application/json",
    }


def komodo_read(read_type: str, params: dict, headers: dict):
    response = requests.post(
        f"{KOMODO_URL}/read",
        headers=headers,
        json={"type": read_type, "params": params},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def load_compose(path: Path):
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        return {"__parse_error__": str(e)}


def adr_exceptions(data: dict) -> set:
    exceptions = ((data.get("x-meta", {}) or {}).get("adr_exceptions", {}) or {})
    return set(exceptions.keys())


def check_adr_0011_flat_layout() -> list:
    """Every stack directory should contain compose files directly, no nesting."""
    warnings = []
    for stack_dir in sorted(Path("stacks").iterdir()):
        if not stack_dir.is_dir():
            continue
        for nested in stack_dir.rglob("compose*.yml"):
            if nested.parent != stack_dir:
                warnings.append(
                    f"ADR-0011 deviation: {nested} — nested compose file "
                    f"(expected all composes directly in stacks/<name>/)"
                )
    return warnings


def check_adr_0005_periphery_image() -> list:
    """Periphery hosts should run the komodo-periphery-sops custom image."""
    warnings = []
    periphery_dir = Path("stacks/komodo-periphery")
    if not periphery_dir.is_dir():
        return warnings
    for compose_file in sorted(periphery_dir.glob("compose.*.yml")):
        data = load_compose(compose_file)
        if "__parse_error__" in data:
            warnings.append(f"ADR-0005 check: {compose_file}: parse error: {data['__parse_error__']}")
            continue
        if 5 in adr_exceptions(data):
            continue
        for service_name, service in (data.get("services") or {}).items():
            image = service.get("image", "")
            if "komodo-periphery-sops" not in image:
                warnings.append(
                    f"ADR-0005 deviation: {compose_file} service '{service_name}' "
                    f"uses image '{image}' (expected komodo-periphery-sops variant)"
                )
    return warnings


def check_adr_0010_sops_wrapper(headers: dict) -> list:
    """Every stack with secrets.enc.env should use sops exec-env in its Komodo wrapper."""
    warnings = []

    try:
        all_stacks = komodo_read("ListStacks", {}, headers)
    except requests.RequestException as e:
        return [f"ADR-0010 check: could not reach Komodo API (ListStacks): {e}"]
    known_names = {s["name"] for s in all_stacks}

    for stack_dir in sorted(Path("stacks").iterdir()):
        if not stack_dir.is_dir():
            continue
        if not (stack_dir / "secrets.enc.env").exists():
            continue

        compose_files = sorted(stack_dir.glob("compose*.yml"))
        if not compose_files:
            continue

        for compose_file in compose_files:
            data = load_compose(compose_file)
            if "__parse_error__" in data:
                warnings.append(f"ADR-0010 check: {compose_file}: parse error: {data['__parse_error__']}")
                continue
            if 10 in adr_exceptions(data):
                continue

            # Determine the Komodo Stack name this compose file corresponds to.
            fname = compose_file.name
            if fname == "compose.yml":
                komodo_name = NAME_MAP.get(stack_dir.name, stack_dir.name)
            else:
                # compose.<host>.yml -> "<dirname>-<host>" per-host registration (Sprint 3s pattern)
                host = fname[len("compose."):-len(".yml")]
                komodo_name = f"{stack_dir.name}-{host}"

            if komodo_name not in known_names:
                warnings.append(
                    f"ADR-0010 check: {compose_file} has secrets.enc.env but no matching "
                    f"Komodo Stack found (tried '{komodo_name}') — name-drift mapping may be "
                    f"missing, or the stack isn't registered in Komodo"
                )
                continue

            try:
                stack = komodo_read("GetStack", {"stack": komodo_name}, headers)
            except requests.RequestException as e:
                warnings.append(f"ADR-0010 check: could not fetch Komodo Stack '{komodo_name}': {e}")
                continue

            wrapper = (stack.get("config", {}) or {}).get("compose_cmd_wrapper", "") or ""
            if "sops exec-env" not in wrapper:
                warnings.append(
                    f"ADR-0010 deviation: stack '{stack_dir.name}' ({compose_file.name}) has "
                    f"secrets.enc.env but Komodo Stack '{komodo_name}' wrapper doesn't include "
                    f"'sops exec-env': got {wrapper!r}"
                )
    return warnings


def main() -> None:
    headers = komodo_headers()

    all_warnings = []
    all_warnings.extend(check_adr_0011_flat_layout())
    all_warnings.extend(check_adr_0005_periphery_image())
    all_warnings.extend(check_adr_0010_sops_wrapper(headers))

    if all_warnings:
        print("ADR content check found deviations (warn-only, not blocking):")
        for warning in all_warnings:
            print(f"  {warning}")
    else:
        print("ADR content check passed — no deviations found (ADR-0005, ADR-0010, ADR-0011).")

    sys.exit(0)


if __name__ == "__main__":
    main()
