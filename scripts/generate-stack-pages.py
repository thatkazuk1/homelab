#!/usr/bin/env python3
"""Generate handbook stack pages from stacks/*/compose.yml (or compose.<host>.yml)."""

import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from ruamel.yaml import YAML

STACKS_DIR = Path("stacks")
HANDBOOK_STACKS_DIR = Path("handbook/docs/stacks")
HANDBOOK_DECISIONS_DIR = Path("handbook/docs/decisions")
TEMPLATE_DIR = Path("scripts/templates")
MKDOCS_PATH = Path("handbook/mkdocs.yml")

# Stacks with no stacks/<name>/compose.yml or compose.<host>.yml files that this
# generator's model can represent — excluded deliberately (Sprint 3o), not an
# oversight:
#   - coolify: three separately-named compose files (proxy/source/source.prod),
#     deliberately outside Komodo/git reconciliation (ADR-0016); already
#     documented at handbook/docs/architecture/coolify.md.
EXCLUDED_STACKS = {"coolify"}

# Hand-written pages in handbook/docs/stacks/ that don't correspond to a stack
# directory — never pruned as orphans.
EXCLUDED_PAGES = {"index.md"}


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


def read_compose(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def build_service_details(compose: dict) -> list:
    service_details = []
    for name, config in compose.get("services", {}).items():
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
    return service_details


def classify_stack(stack_dir: Path):
    """Return (shape, files) for a stack directory.

    shape is "single" (compose.yml), "multi" (compose.<host>.yml, one or
    more), "ambiguous" (both present — not allowed, caller should skip), or
    None (neither — not a stack this generator handles).
    """
    single = stack_dir / "compose.yml"
    multi_files = sorted(stack_dir.glob("compose.*.yml"))
    if single.exists() and multi_files:
        return "ambiguous", [single, *multi_files]
    if single.exists():
        return "single", [single]
    if multi_files:
        return "multi", multi_files
    return None, []


def has_compose_file(stack_dir: Path) -> bool:
    shape, _ = classify_stack(stack_dir)
    return shape in ("single", "multi")


def parse_single_stack(stack_dir: Path, compose_path: Path) -> dict:
    """Extract metadata + structure from a single-file stack's compose.yml."""
    compose = read_compose(compose_path)

    meta = compose.get("x-meta")
    if not meta:
        raise ValueError(
            f"{compose_path} has no x-meta: block. Every in-scope stack must "
            "declare one — add it or add the stack to EXCLUDED_STACKS with a reason."
        )

    services = compose.get("services", {})
    volumes = compose.get("volumes", {})
    has_sops = (stack_dir / "secrets.enc.env").exists()
    is_meta_infra = any(
        "komodo.skip" in (svc.get("labels") or {}) for svc in services.values()
    )
    notes_path = stack_dir / "notes.md"
    notes = notes_path.read_text() if notes_path.exists() else None

    return {
        "meta": meta,
        "services": build_service_details(compose),
        "named_volumes": sorted(volumes.keys()),
        "has_sops": has_sops,
        "is_meta_infra": is_meta_infra,
        "notes": notes,
        "is_multi": False,
        "hosts": [],
    }


def parse_multi_stack(stack_dir: Path, compose_files: list) -> dict:
    """Extract metadata + per-host host list from a multi-file stack.

    compose_files is already sorted alphabetically by filename (classify_stack
    globs and sorts). The first file is canonical for shared metadata; each
    file's x-meta.host (or, failing that, its filename) contributes one entry
    to the per-host list.
    """
    first_path = compose_files[0]
    first_compose = read_compose(first_path)

    meta = dict(first_compose.get("x-meta") or {})
    if not meta:
        raise ValueError(
            f"{first_path} has no x-meta: block. Every in-scope stack must "
            "declare one — add it or add the stack to EXCLUDED_STACKS with a reason."
        )

    # Multi-file stacks' per-file x-meta.name is host-suffixed (e.g.
    # "hawser-core-01") so each file is self-describing on its own — but the
    # page is one-per-directory, so the directory name is the canonical title,
    # not whichever host happened to sort first.
    canonical_name = stack_dir.name
    if meta.get("name") != canonical_name:
        print(
            f"NOTE: {first_path} declares x-meta.name={meta.get('name')!r}; "
            f"page will use directory name {canonical_name!r} instead "
            "(one page per multi-file stack, not per host)."
        )
    meta["name"] = canonical_name

    hosts = []
    for fp in compose_files:
        compose = read_compose(fp)
        file_meta = compose.get("x-meta") or {}
        host = file_meta.get("host")
        if not host:
            # compose.<host>.yml -> <host>
            host = fp.name[len("compose.") : -len(".yml")]
        hosts.append({"host": host, "filename": fp.name})

    services = first_compose.get("services", {})
    volumes = first_compose.get("volumes", {})
    has_sops = (stack_dir / "secrets.enc.env").exists()
    is_meta_infra = any(
        "komodo.skip" in (svc.get("labels") or {}) for svc in services.values()
    )
    notes_path = stack_dir / "notes.md"
    notes = notes_path.read_text() if notes_path.exists() else None

    return {
        "meta": meta,
        "services": build_service_details(first_compose),
        "named_volumes": sorted(volumes.keys()),
        "has_sops": has_sops,
        "is_meta_infra": is_meta_infra,
        "notes": notes,
        "is_multi": True,
        "hosts": hosts,
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


def prune_orphans(expected_names: set) -> list:
    """Delete handbook/docs/stacks/*.md pages with no corresponding stack dir."""
    pruned = []
    for page in sorted(HANDBOOK_STACKS_DIR.glob("*.md")):
        if page.name in EXCLUDED_PAGES:
            continue
        if page.stem in expected_names:
            continue
        page.unlink()
        pruned.append(page)
    return pruned


def update_nav(expected_names: set) -> None:
    """Rewrite mkdocs.yml's nav.Stacks section from the current stack list."""
    yaml_rt = YAML()
    yaml_rt.preserve_quotes = True
    yaml_rt.indent(mapping=2, sequence=4, offset=2)
    yaml_rt.width = 4096  # don't let ruamel reflow long lines elsewhere in the file

    data = yaml_rt.load(MKDOCS_PATH)
    nav = data["nav"]

    found = False
    for entry in nav:
        if isinstance(entry, dict) and "Stacks" in entry:
            stacks_nav = [{"Overview": "stacks/index.md"}]
            for name in sorted(expected_names):
                stacks_nav.append({name: f"stacks/{name}.md"})
            entry["Stacks"] = stacks_nav
            found = True
            break

    if not found:
        raise ValueError(f"{MKDOCS_PATH} has no nav entry containing 'Stacks'.")

    yaml_rt.dump(data, MKDOCS_PATH)


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
    had_errors = False
    expected_names = set()

    for stack_dir in sorted(STACKS_DIR.iterdir()):
        if not stack_dir.is_dir():
            continue
        if stack_dir.name in EXCLUDED_STACKS:
            continue

        shape, files = classify_stack(stack_dir)
        if shape is None:
            continue
        if shape == "ambiguous":
            print(
                f"ERROR: {stack_dir} has both compose.yml and compose.<host>.yml "
                "files — ambiguous, skipping. Pick one shape.",
                file=sys.stderr,
            )
            had_errors = True
            continue

        try:
            if shape == "single":
                stack_data = parse_single_stack(stack_dir, files[0])
            else:
                stack_data = parse_multi_stack(stack_dir, files)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            had_errors = True
            continue

        rendered = render(stack_data, template, adr_pages)
        output_path = HANDBOOK_STACKS_DIR / f"{stack_dir.name}.md"
        output_path.write_text(rendered)
        generated.append(output_path)
        expected_names.add(stack_dir.name)
        print(f"Generated {output_path}")

    print(f"\n{len(generated)} page(s) generated.")

    pruned = prune_orphans(expected_names)
    for page in pruned:
        print(f"Pruned orphan page: {page}")
    if pruned:
        print(f"{len(pruned)} orphan page(s) pruned.")

    update_nav(expected_names)
    print(f"Updated {MKDOCS_PATH} nav.Stacks section.")

    if had_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
