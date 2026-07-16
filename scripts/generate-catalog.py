#!/usr/bin/env python3
"""Generate the static catalogue consumed by the GitHub Pages UI."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
OUTPUT = ROOT / "site" / "catalog.json"


def yaml_value(path: Path, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*)$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            value = match.group(1).strip().strip("'\"")
            return value or None
    return None


def list_files(directory: Path, suffix: str) -> list[str]:
    if not directory.is_dir():
        return []
    return sorted(str(path.relative_to(directory)) for path in directory.rglob(f"*{suffix}") if path.is_file())


def package_details(entry: dict) -> dict:
    source = entry.get("source", "")
    package_path = (ROOT / source).resolve() if source.startswith(".") else None
    relative = Path(source).as_posix().removeprefix("./")
    parts = Path(relative).parts
    owner = parts[2] if len(parts) >= 3 and parts[:2] == ("packages", "teams") else "generic"
    classification = "internal" if parts[:2] == ("packages", "teams") else "approved"

    skills: list[str] = []
    agents: list[str] = []
    if package_path and package_path.is_dir():
        for skill_root in (package_path / "skills", package_path / ".apm" / "skills"):
            for file in skill_root.glob("*/SKILL.md") if skill_root.is_dir() else []:
                name = file.parent.name
                if name not in skills:
                    skills.append(name)
        for agent_root in (package_path / "agents", package_path / ".apm" / "agents"):
            for file in list(agent_root.rglob("*.agent.md")) if agent_root.is_dir() else []:
                name = file.stem.removesuffix(".agent")
                if name not in agents:
                    agents.append(name)

    return {
        "name": entry["name"],
        "displayName": entry["name"].replace("-", " ").title(),
        "description": entry.get("description", ""),
        "version": entry.get("version", ""),
        "owner": owner,
        "classification": classification,
        "install": f"apm install {entry['name']}@marketplace-dev",
        "source": source,
        "skills": sorted(skills),
        "agents": sorted(agents),
        "packageVersion": yaml_value(package_path / "apm.yml", "version") if package_path else None,
    }


def main() -> None:
    marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    packages = [package_details(entry) for entry in marketplace.get("plugins", [])]
    owners = sorted({package["owner"] for package in packages})
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    generated_at = (
        datetime.fromtimestamp(int(source_date_epoch), timezone.utc).isoformat()
        if source_date_epoch and source_date_epoch.isdigit()
        else None
    )
    catalog = {
        "schemaVersion": 1,
        "marketplace": marketplace.get("name", "apex-agent-marketplace"),
        "generatedAt": generated_at,
        "owners": owners,
        "packages": packages,
    }
    OUTPUT.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
