"""Small shared primitives for immutable evidence and resumable local jobs."""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def child_path(root, relative):
    """Manifest references cannot escape their packet directory."""
    root = Path(root).resolve()
    candidate = (root / relative).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError("Evidence reference escapes its packet directory")
    return candidate


def verify_files(root, hashes):
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("Missing evidence hashes")
    for name, expected in hashes.items():
        path = child_path(root, name)
        if not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"Missing or changed evidence: {name}")
