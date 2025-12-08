"""Provenance helpers for pipeline v2 outputs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ProvenanceRecord:
    scenario: str
    config_path: str
    config_hash: str
    input_path: str
    input_hash: str
    git_commit: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _config_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_commit(root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def build_provenance(scenario: str, config_path: Path, input_path: Path, repo_root: Path) -> ProvenanceRecord:
    return ProvenanceRecord(
        scenario=scenario,
        config_path=str(config_path.resolve()),
        config_hash=_config_hash(config_path),
        input_path=str(input_path.resolve()),
        input_hash=_sha256(input_path),
        git_commit=_git_commit(repo_root),
    )


def write_manifest(record: ProvenanceRecord, output_path: Path) -> None:
    output_path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")
