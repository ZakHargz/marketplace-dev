#!/usr/bin/env python3
"""Generate the embedded catalog used by the Flutter-Global Pages UI."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
OUTPUT = ROOT / "site" / "catalog.json"
REPOSITORY = "https://github.com/Flutter-Global/apex-marketplace"
MARKETPLACE_NAME = "apex"


def yaml_value(path: Path, key: str, default: str = "") -> str:
    if not path.is_file():
        return default
    match = re.search(rf"^{re.escape(key)}:\s*(.*)$", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip().strip("'\"") if match else default


def readme_description(path: Path, fallback: str) -> str:
    readme = path / "README.md"
    if not readme.is_file():
        return fallback
    lines = readme.read_text(encoding="utf-8").splitlines()
    paragraph: list[str] = []
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#") or text.startswith("```"):
            if paragraph:
                break
            continue
        paragraph.append(text)
    return " ".join(paragraph) or fallback


def package_item(entry: dict) -> dict:
    source = entry.get("source", "")
    package_path = (ROOT / source).resolve()
    manifest = package_path / "apm.yml"
    relative = package_path.relative_to(ROOT).as_posix()
    parts = Path(relative).parts
    bucket = parts[1] if len(parts) > 1 else "generic"
    team = parts[2] if bucket in {"teams", "valuestreams"} and len(parts) > 2 else None
    package_type = yaml_value(manifest, "type", "skill" if (package_path / "skills").exists() else "hybrid")
    category = {"hybrid": "agents", "skill": "skills", "instructions": "instructions", "prompts": "prompts"}.get(package_type, "unknown")
    version = yaml_value(manifest, "version", entry.get("version", "1.0.0")).lstrip("^")
    author = yaml_value(manifest, "author", "Flutter-Global")
    license_name = yaml_value(manifest, "license", "MIT")
    description = entry.get("description", yaml_value(manifest, "description"))
    install = f"apm install {entry['name']}@{MARKETPLACE_NAME}"
    return {
        "id": entry["name"], "name": entry["name"], "type": package_type,
        "category": category, "version": version, "description": description,
        "extendedDescription": readme_description(package_path, description),
        "author": author, "license": license_name, "homepage": None,
        "repository": REPOSITORY, "installCommand": install, "team": team,
    }


def main() -> None:
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    items = sorted((package_item(entry) for entry in marketplace.get("plugins", [])), key=lambda item: (item["category"], item["name"]))
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    updated = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat() if epoch and epoch.isdigit() else None
    catalog = {
        "version": "1.0.0", "lastUpdated": updated, "repository": REPOSITORY,
        "itemCount": len(items), "teams": sorted({item["team"] for item in items if item["team"]}),
        "categories": {category: sum(item["category"] == category for item in items) for category in ("agents", "skills", "instructions", "prompts")},
        "items": items,
    }
    OUTPUT.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
