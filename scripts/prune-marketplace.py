#!/usr/bin/env python3
"""Remove stale local marketplace entries whose package directories are gone."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "apm.yml"


def main() -> None:
    lines = MANIFEST.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    index = 0
    removed: list[str] = []

    while index < len(lines):
        line = lines[index]
        if line.startswith("    - name:"):
            entry_start = index
            entry_name = line.split(":", 1)[1].strip()
            entry_end = index + 1
            while entry_end < len(lines) and not lines[entry_end].startswith("    - name:"):
                entry_end += 1
            entry = lines[entry_start:entry_end]
            source = next(
                (item.split(":", 1)[1].strip().strip("'\"") for item in entry if item.startswith("      source:")),
                None,
            )
            if source and source.startswith(".") and not (ROOT / source).is_dir():
                removed.append(entry_name)
            else:
                output.extend(entry)
            index = entry_end
            continue
        output.append(line)
        index += 1

    if removed:
        MANIFEST.write_text("".join(output), encoding="utf-8")
        print("Removed stale marketplace entries: " + ", ".join(removed))


if __name__ == "__main__":
    main()
