#!/usr/bin/env python3
"""Check that every ADR reference in the fleet points at a real ADR file."""

import re
import sys
from pathlib import Path

import yaml

ADR_DIR = Path("docs/adrs")

# Known, accepted, permanent exceptions: (file, referenced-but-missing ADR number).
# docs/adrs/0006-periphery-ip-anomaly.md's own H1 heading reads "ADR-0008" (a pre-existing
# labeling typo — the file was never renamed, per Sprint 3m and the operator's Sprint 3x
# decision to document rather than renumber). docs/adrs/README.md's "Known numbering gap"
# section explains that same typo by quoting it. Neither is real drift; both will always
# trip the inline-mention pattern otherwise. See docs/adr-audit-2026-07-21.md.
KNOWN_EXCEPTIONS = {
    (str(Path("docs/adrs/0006-periphery-ip-anomaly.md")), 8),
    (str(Path("docs/adrs/README.md")), 8),
}


def load_existing_adrs() -> set:
    """Return set of ADR numbers with corresponding files."""
    adrs = set()
    for adr_file in ADR_DIR.glob("*.md"):
        match = re.match(r"^(\d+)-", adr_file.name)
        if match:
            adrs.add(int(match.group(1)))
    return adrs


def check_compose_files(existing_adrs: set) -> list:
    """Check x-meta.adrs in stacks/*/compose*.yml files."""
    failures = []
    for compose in sorted(Path("stacks").glob("*/compose*.yml")):
        try:
            data = yaml.safe_load(compose.read_text())
        except Exception as e:
            failures.append(f"{compose}: parse error: {e}")
            continue
        adrs = ((data or {}).get("x-meta", {}) or {}).get("adrs", []) or []
        for adr_num in adrs:
            if adr_num not in existing_adrs:
                failures.append(
                    f"{compose}:x-meta.adrs: references ADR-{adr_num:04d} but "
                    f"docs/adrs/{adr_num:04d}-*.md not found"
                )
    return failures


def check_markdown_references(existing_adrs: set, paths: list) -> list:
    """Check markdown links and inline ADR-NNNN mentions."""
    failures = []
    link_pattern = re.compile(r"\[.*?\]\([^)]*?/(?:decisions|adrs)/(\d{4})-[^)]*\.md\)")
    inline_pattern = re.compile(r"\bADR-(\d{4})\b")

    for md_file in paths:
        content = md_file.read_text()
        linked_spans = []
        for match in link_pattern.finditer(content):
            linked_spans.append(match.span())
            adr_num = int(match.group(1))
            if adr_num not in existing_adrs:
                failures.append(
                    f"{md_file}: link references ADR-{adr_num:04d} but "
                    f"docs/adrs/{adr_num:04d}-*.md not found"
                )
        for match in inline_pattern.finditer(content):
            # Skip inline mentions that are actually inside a link already
            # reported above (the [ADR-0010](...) text itself matches both
            # patterns; reporting it twice would be noise).
            if any(start <= match.start() < end for start, end in linked_spans):
                continue
            adr_num = int(match.group(1))
            if adr_num not in existing_adrs:
                if (str(md_file), adr_num) in KNOWN_EXCEPTIONS:
                    continue
                failures.append(
                    f"{md_file}: mention of ADR-{adr_num:04d} but "
                    f"docs/adrs/{adr_num:04d}-*.md not found"
                )
    return failures


def main() -> None:
    existing_adrs = load_existing_adrs()

    all_failures = []
    all_failures.extend(check_compose_files(existing_adrs))

    md_paths = list(Path("handbook/docs").rglob("*.md"))
    md_paths.extend(Path("stacks").rglob("notes.md"))
    md_paths.extend(Path("docs/adrs").glob("*.md"))
    md_paths.append(Path("docs/project-state.md"))
    md_paths.append(Path("CLAUDE.md"))
    md_paths = [p for p in md_paths if p.exists()]

    all_failures.extend(check_markdown_references(existing_adrs, md_paths))

    if all_failures:
        print("ADR reference validation failed:", file=sys.stderr)
        for failure in all_failures:
            print(f"  {failure}", file=sys.stderr)
        sys.exit(1)

    print(f"ADR reference validation passed ({len(existing_adrs)} ADRs, all references valid)")


if __name__ == "__main__":
    main()
