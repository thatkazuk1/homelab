#!/usr/bin/env python3
"""Generate handbook stack pages from stacks/*/compose.yml."""

import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

STACKS_DIR = Path("stacks")
HANDBOOK_STACKS_DIR = Path("handbook/docs/stacks")
HANDBOOK_DECISIONS_DIR = Path("handbook/docs/decisions")
TEMPLATE_DIR = Path("scripts/templates")

# Stacks with no single stacks/<name>/compose.yml, so they fall outside this
# generator's model — excluded deliberately (Sprint 3o), not an oversight:
#   - coolify: three separately-named compose files, deliberately outside
#     Komodo/git reconciliation (ADR-0016); already documented at
#     handbook/docs/architecture/coolify.md.
#   - komodo-periphery: per-host compose.<host>.yml files (ADR-0011), because
#     Periphery's config genuinely diverges per host (Sprint 3i). A future
#     sprint can teach the generator to handle multi-file stacks.
EXCLUDED_STACKS = {"coolify", "komodo-periphery"}


def format_port(port) -> str:
    """Render a compose port entry (short string or long-syntax mapping)."""
    if isinstance(port, dict):
        target = port.get("target")
        published = port.get("published")
        protocol = port.get("protocol", "tcp")
        if published:
            return f"{published}:{target}/{protocol}"
        return f"{target}/{protocol}"
    return str(port)


def parse_stack(stack_dir: Path) -> dict:
    """Extract metadata + structure from a stack's compose.yml."""
    compose_path = stack_dir / "compose.yml"
    with compose_path.open() as f:
        compose = yaml.safe_load(f)

    meta = compose.get("x-meta")
    if not meta:
        raise ValueError(
            f"{compose_path} has no x-meta: block. Every in-scope stack must "
            "declare one — add it or add the stack to EXCLUDED_STACKS with a reason."
        )

    services = compose.get("services", {})
    volumes = compose.get("volumes", {})

    service_details = []
    for name, config in services.items():
        service_details.append(
            {
                "name": name,
                "image": config.get("image"),
                "container_name": config.get("container_name"),
                "restart": config.get("restart"),
                "network_mode": config.get("network_mode"),
                "ports": [format_port(p) for p in config.get("ports", [])],
            }
        )

    has_sops = (stack_dir / "secrets.enc.env").exists()

    is_meta_infra = any(
        "komodo.skip" in (svc.get("labels") or {}) for svc in services.values()
    )

    notes_path = stack_dir / "notes.md"
    notes = notes_path.read_text() if notes_path.exists() else None

    return {
        "meta": meta,
        "services": service_details,
        "named_volumes": sorted(volumes.keys()),
        "has_sops": has_sops,
        "is_meta_infra": is_meta_infra,
        "notes": notes,
    }


def build_adr_pages() -> dict:
    """Map ADR number -> handbook decisions filename, for ADRs published there.

    Not every ADR in docs/adrs/ has a handbook/docs/decisions/ counterpart
    (some are operator-internal). Linking to a number that has no handbook
    page would break the --strict build, so unresolved numbers render as
    plain text instead (see the template).
    """
    pages = {}
    for path in HANDBOOK_DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"):
        pages[int(path.name[:4])] = path.name
    return pages


def render(stack_data: dict, template, adr_pages: dict) -> str:
    """Render a stack page, collapsing the runs of blank lines that jinja2's
    trim_blocks leaves behind whenever an optional section is empty."""
    rendered = template.render(adr_pages=adr_pages, **stack_data)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    return rendered.strip() + "\n"


def main():
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("stack-page.md.j2")
    adr_pages = build_adr_pages()

    HANDBOOK_STACKS_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    for stack_dir in sorted(STACKS_DIR.iterdir()):
        if not stack_dir.is_dir():
            continue
        if stack_dir.name in EXCLUDED_STACKS:
            continue
        if not (stack_dir / "compose.yml").exists():
            continue

        stack_data = parse_stack(stack_dir)
        rendered = render(stack_data, template, adr_pages)

        output_path = HANDBOOK_STACKS_DIR / f"{stack_dir.name}.md"
        output_path.write_text(rendered)
        generated.append(output_path)
        print(f"Generated {output_path}")

    print(f"\n{len(generated)} page(s) generated.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
