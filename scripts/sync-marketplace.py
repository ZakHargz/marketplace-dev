#!/usr/bin/env python3
"""Register package directories in the root marketplace manifest."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "apm.yml"


def value(manifest: Path, key: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*)$")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1).strip().strip("'\"")
    return ""


def package_paths() -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    for path in sorted((ROOT / "packages" / "generic").glob("*/apm.yml")):
        paths.append((path, "generic"))
    for path in sorted((ROOT / "packages" / "teams").glob("*/*/apm.yml")):
        paths.append((path, path.parent.parent.name))
    return paths


def main() -> None:
    lines = MANIFEST.read_text(encoding="utf-8").splitlines(keepends=True)
    existing_sources = {
        line.split(":", 1)[1].strip().strip("'\"")
        for line in lines
        if line.startswith("      source:")
    }
    entries: list[str] = []
    for package_manifest, tag in package_paths():
        source = "./" + package_manifest.parent.relative_to(ROOT).as_posix()
        if source in existing_sources:
            continue
        name = value(package_manifest, "name") or package_manifest.parent.name
        version = value(package_manifest, "version") or "0.1.0"
        description = value(package_manifest, "description") or f"APM package: {name}"
        entries.extend(
            [
                f"    - name: {name}\n",
                f"      description: {description}\n",
                f"      source: {source}\n",
                f"      version: \"^{version}\"\n",
                "      tags:\n",
                f"        - {tag}\n",
                "\n",
            ]
        )

    if not entries:
        return
    insertion = next(index for index, line in enumerate(lines) if line.startswith("    - name:"))
    lines[insertion:insertion] = entries
    MANIFEST.write_text("".join(lines), encoding="utf-8")
    print(f"Registered {len(entries) // 7} new marketplace package(s).")


if __name__ == "__main__":
    main()
