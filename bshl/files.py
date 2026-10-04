"""Exclusive JSON output; changing an existing artifact requires a new path."""
import json
from pathlib import Path
from .serialization import dumps


def write_json(value, path):
    target = Path(path)
    content = dumps(value) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        if json.loads(target.read_text(encoding="utf-8")) != json.loads(content):
            raise ValueError(f"Refusing to overwrite a different artifact: {target}")
    return target
