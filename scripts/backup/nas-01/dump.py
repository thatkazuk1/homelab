#!/usr/bin/env python3
"""Make consistent copies of the live SQLite databases of the nas-01 apps.

The apps keep their databases in WAL mode. A plain file copy of a running
database can be inconsistent, so this script uses SQLite's backup API. The
copies go to /Volume1/@apps/homelab/_backup-dumps/<same relative path>.dump.
The pull script excludes the live *.db files and takes the .dump files.

Run by gate.sh (forced command). It only reads the databases and only writes
below _backup-dumps. Exit code 1 when any copy fails its integrity check.
"""
import os
import sqlite3
import sys

ROOT = "/Volume1/@apps/homelab"
OUT = os.path.join(ROOT, "_backup-dumps")
SUFFIXES = (".db", ".sqlite3")
SKIP_NAMES = {"logs.db", "search.db"}            # logs and search cache: not worth keeping
SKIP_PARTS = ("/cache/", "/MediaCover/", "/_backup-dumps/", "/logs/", ".bak.")


def candidates():
    for dirpath, _dirs, files in os.walk(ROOT):
        for name in files:
            path = os.path.join(dirpath, name)
            if not name.endswith(SUFFIXES) or name in SKIP_NAMES:
                continue
            if any(part in path + "/" for part in SKIP_PARTS) or any(part in path for part in SKIP_PARTS):
                continue
            yield path


def main():
    failed = 0
    wanted = set()
    for src in sorted(candidates()):
        rel = os.path.relpath(src, ROOT)
        dst = os.path.join(OUT, rel + ".dump")
        wanted.add(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        tmp = dst + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        try:
            source = sqlite3.connect(src, timeout=60)
            target = sqlite3.connect(tmp)
            with target:
                source.backup(target)
            source.close()
            ok = target.execute("PRAGMA quick_check").fetchone()[0]
            target.close()
            if ok != "ok":
                raise RuntimeError("quick_check: " + str(ok))
            os.replace(tmp, dst)
            print("ok   %8d KB  %s" % (os.path.getsize(dst) // 1024, rel))
        except Exception as exc:                  # keep going: report every database
            failed += 1
            print("FAIL %s: %s" % (rel, exc), file=sys.stderr)
            if os.path.exists(tmp):
                os.remove(tmp)
    # Remove dumps of databases that no longer exist.
    for dirpath, _dirs, files in os.walk(OUT):
        for name in files:
            path = os.path.join(dirpath, name)
            if path not in wanted:
                os.remove(path)
                print("removed stale dump", os.path.relpath(path, OUT))
    print("%d database(s) copied, %d failed" % (len(wanted) - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
