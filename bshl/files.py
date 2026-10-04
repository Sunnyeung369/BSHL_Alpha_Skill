"""Exclusive JSON output; changing an existing artifact requires a new path."""
import json
import os
from pathlib import Path
import tempfile
from .serialization import dumps


def write_text(content, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix="bshl-artifact-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.read_text(encoding="utf-8") != content:
                raise FileExistsError(f"Refusing to overwrite a different artifact: {target}")
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def write_json(value, path):
    return write_text(dumps(value) + "\n", path)
